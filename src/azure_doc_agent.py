"""
Azure Doc Agent - Multi-turn conversation agent based on Microsoft Agent Framework

Implements intelligent document assistant with threading and streaming support
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncIterator
from datetime import datetime

# Microsoft Agent Framework imports
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient, AzureOpenAIChatOptions
from azure.identity.aio import DefaultAzureCredential

from .registry import SkillRegistry
from .injector import SkillInjector
from .mcp_client import MCPClient
from .system_prompts import SystemPromptsManager
from .llm_matcher import LLMSkillMatcher

logger = logging.getLogger(__name__)


class AzureDocAgent:
    """Azure Documentation Intelligent Assistant - Multi-turn conversation with threading"""
    
    def __init__(
        self,
        azure_openai_endpoint: str,
        azure_openai_key: str,
        azure_openai_deployment: str,
        mcp_server_url: str = "https://learn.microsoft.com/api/mcp",
        skills_directory: str = "skills"
    ):
        """
        Initialize Azure Doc Agent
        
        Args:
            azure_openai_endpoint: Azure OpenAI endpoint
            azure_openai_key: Azure OpenAI API key  
            azure_openai_deployment: Deployment name (e.g., gpt-4o)
            mcp_server_url: MCP server URL
            skills_directory: Skills directory path
        """
        # Store configuration
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_openai_key = azure_openai_key
        self.deployment = azure_openai_deployment
        
        # Initialize skills system
        self.registry = SkillRegistry(skills_directory)
        self.injector = SkillInjector(self.registry)
        self.prompts_manager = SystemPromptsManager(self.registry, self.injector)
        
        # Initialize LLM-based skill matcher
        self.llm_matcher = LLMSkillMatcher(
            azure_openai_endpoint=azure_openai_endpoint,
            azure_openai_key=azure_openai_key,
            azure_openai_deployment=azure_openai_deployment
        )
        
        # Initialize MCP client (encapsulates MCPStreamableHTTPTool)
        self.mcp_client = MCPClient()  # Uses default Microsoft Learn MCP
        
        # Agent and threading management (using MAF AgentThread)
        self.agent: Optional[ChatAgent] = None
        self.threads: Dict[str, Any] = {}  # thread_id -> AgentThread object
        self.current_thread_id: Optional[str] = None
        
        # Thread history storage (for API/UI access)
        self.thread_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize flag
        self._initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize Agent (discover skills, connect MCP, create ChatAgent)
        
        Returns:
            Whether initialization succeeded
        """
        try:
            logger.info("Initializing Azure Doc Agent...")
            
            # Discover skills
            skill_count = self.registry.discover_skills()
            logger.info(f"Discovered {skill_count} skills")
            
            # Initialize MCP client
            await self.mcp_client.initialize()
            
            # Create Azure OpenAI Chat Client
            chat_client = AzureOpenAIChatClient(
                endpoint=self.azure_openai_endpoint,
                api_key=self.azure_openai_key,
                deployment_name=self.deployment
            )
            
            # Build system instructions (with skill metadata only)
            system_instructions = self.prompts_manager.build_full_system_prompt()
            
            # Create ChatAgent with default options
            # Note: max_tokens increased to 8000 for detailed responses
            default_options: AzureOpenAIChatOptions = {
                "temperature": 0.7,
                "max_tokens": 8000,  # Increased from 2000 to support longer responses
                "top_p": 0.9
            }
            
            # **CRITICAL**: Register all MCP tools at initialization
            # Agent knows these tools exist but doesn't know when to use them
            # Only through SKILL.md instructions will Agent know which tools to use
            all_mcp_tools = self.mcp_client.get_tools() if self.mcp_client.has_tools() else []
            
            self.agent = chat_client.as_agent(
                instructions=system_instructions,
                default_options=default_options,
                tools=all_mcp_tools  # All MCP tools are registered
            )
            
            logger.info(f"Agent created with {len(all_mcp_tools)} MCP tools registered")
            
            self._initialized = True
            logger.info("Azure Doc Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False
    
    def create_thread(self, thread_id: Optional[str] = None) -> str:
        """
        Create new conversation thread (using MAF AgentThread)
        
        Args:
            thread_id: Thread ID (optional, auto-generated if not provided)
            
        Returns:
            Thread ID
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        
        if thread_id is None:
            thread_id = f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Create MAF AgentThread
        agent_thread = self.agent.get_new_thread()
        self.threads[thread_id] = agent_thread
        self.thread_history[thread_id] = []
        self.current_thread_id = thread_id
        
        logger.info(f"Created new thread: {thread_id}")
        return thread_id
    
    def switch_thread(self, thread_id: str) -> bool:
        """
        Switch to specified thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Whether switch succeeded
        """
        if thread_id not in self.threads:
            logger.warning(f"Thread does not exist: {thread_id}")
            return False
        
        self.current_thread_id = thread_id
        logger.info(f"Switched to thread: {thread_id}")
        return True
    
    async def chat(
        self,
        user_message: str,
        thread_id: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        Process user message (multi-turn conversation)
        
        Args:
            user_message: User message
            thread_id: Thread ID (optional)
            stream: Whether to stream response
            
        Returns:
            Agent response (for non-streaming)
        """
        if not self._initialized:
            await self.initialize()
        
        # Determine thread to use
        if thread_id:
            if thread_id not in self.threads:
                self.create_thread(thread_id)
            self.current_thread_id = thread_id
        elif not self.current_thread_id:
            self.create_thread()
        
        thread = self.threads[self.current_thread_id]
        
        try:
            # Update system prompt based on query
            updated_prompt = self.prompts_manager.update_for_query(user_message)
            
            if stream:
                # Streaming response
                return await self._chat_stream(user_message, thread)
            else:
                # Non-streaming response
                return await self._chat_non_stream(user_message, thread)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return f"Sorry, an error occurred while processing your request: {str(e)}"
    
    async def _chat_non_stream(self, user_message: str, thread: Any) -> str:
        """
        Non-streaming chat
        
        Args:
            user_message: User message
            thread: AgentThread object
            
        Returns:
            Complete response text
        """
        # Run agent with thread and MCP tools (MAF handles message history)
        mcp_tools = self.mcp_client.get_tools() if self.mcp_client.has_tools() else None
        
        if mcp_tools:
            response = await self.agent.run(user_message, thread=thread, tools=mcp_tools)
        else:
            response = await self.agent.run(user_message, thread=thread)
        
        # Extract response text
        response_text = response.text
        
        # Store in history
        self.thread_history[self.current_thread_id].append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": response_text
        })
        
        logger.info(f"Non-streaming response generated for thread {self.current_thread_id}")
        return response_text
    
    async def _chat_stream(self, user_message: str, thread: Any) -> str:
        """
        Streaming chat (collects full response)
        
        Args:
            user_message: User message
            thread: AgentThread object
            
        Returns:
            Complete response text
        """
        response_parts = []
        
        # Use run_stream for streaming with MCP tools
        mcp_tools = self.mcp_client.get_tools() if self.mcp_client.has_tools() else None
        
        if mcp_tools:
            stream = self.agent.run_stream(user_message, thread=thread, tools=mcp_tools)
        else:
            stream = self.agent.run_stream(user_message, thread=thread)
            
        async for update in stream:
            if update.text:
                response_parts.append(update.text)
                # In a real streaming scenario, you'd yield these parts
                # For now, we collect them
        
        # Combine all parts
        full_response = "".join(response_parts)
        
        # Store in history
        self.thread_history[self.current_thread_id].append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": full_response
        })
        
        logger.info(f"Streaming response generated for thread {self.current_thread_id}")
        return full_response
    
    async def chat_stream_with_thinking(
        self,
        user_message: str,
        thread_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream chat response with thinking/progress updates
        
        Args:
            user_message: User message
            thread_id: Thread ID (optional)
            
        Yields:
            Progress updates with type: 'thinking', 'text', 'tool_call', etc.
        """
        if not self._initialized:
            await self.initialize()
        
        # Determine thread to use
        if thread_id:
            if thread_id not in self.threads:
                self.create_thread(thread_id)
            self.current_thread_id = thread_id
        elif not self.current_thread_id:
            self.create_thread()
        
        thread = self.threads[self.current_thread_id]
        response_parts = []
        
        try:
            # Step 1: LLM-based skill matching (primary method)
            yield {
                "type": "thinking",
                "message": "🤖 使用LLM智能分析问题，匹配相关技能..."
            }
            
            available_skills = self.registry.list_skills()
            matched_skill = await self.llm_matcher.match_skills(user_message, available_skills)
            
            # Fallback: use keyword-based matching if LLM fails
            if matched_skill is None:
                yield {
                    "type": "thinking",
                    "message": "🔍 LLM匹配未找到，使用关键词辅助匹配..."
                }
                keyword_matched = self.registry.search_skills(user_message, min_score=50)
                matched_skills = keyword_matched[:1] if keyword_matched else []
            else:
                matched_skills = [matched_skill]
                yield {
                    "type": "thinking",
                    "message": f"✅ LLM匹配成功: {matched_skill.name}"
                }
            
            # Step 2: Process matched skills with progressive disclosure
            if matched_skills:
                for skill in matched_skills:
                    yield {
                        "type": "thinking", 
                        "message": f"✅ 匹配到技能: {skill.name}"
                    }
                    
                    # **Progressive Disclosure**: Load full skill content
                    yield {
                        "type": "thinking",
                        "message": f"📚 Loading full instructions for skill '{skill.name}'..."
                    }
                    
                    # Activate skill (loads full SKILL.md content and injects to context)
                    skill_content = self.injector.activate_skill(skill.name)
                    if skill_content:
                        logger.info(f"Activated and injected skill: {skill.name}")
                        yield {
                            "type": "thinking",
                            "message": f"✅ Skill '{skill.name}' 已激活，Agent现在可以使用其工具和方法"
                        }
            else:
                yield {
                    "type": "thinking",
                    "message": "ℹ️ 未匹配到特定skill，将使用通用知识回答"
                }
            
            # Step 3: Determine which tools to use based on activated skills
            # **FIX**: MCP tools are already registered at initialization, here we only inject SKILL.md instructions
            # SKILL.md will tell Agent: "Use microsoft_docs_search when you need to..."
            if matched_skills:
                yield {
                    "type": "thinking",
                    "message": "📋 Skill instructions loaded, Agent now knows how to use relevant tools"
                }
            
            # Step 4: Start streaming response
            yield {
                "type": "thinking",
                "message": "💭 Generating response..."
            }
            
            # Prepare message with activated skill context
            context_message = user_message
            if matched_skills:
                # Prepend activated skill instructions to guide the agent
                # SKILL.md content will guide Agent on which registered MCP tools to use
                active_skills_context = self.injector.get_skills_for_llm()
                if active_skills_context:
                    context_message = f"{active_skills_context}\n\nUser Question: {user_message}"
            
            # **CRITICAL CHANGE**: No conditional tool passing, tools are registered at initialization
            # Agent will decide which tools to use based on SKILL.md instructions
            stream = self.agent.run_stream(context_message, thread=thread)
            
            async for update in stream:
                if update.text:
                    response_parts.append(update.text)
                    yield {
                        "type": "text",
                        "content": update.text
                    }
            
            # Store complete response in history
            full_response = "".join(response_parts)
            self.thread_history[self.current_thread_id].append({
                "timestamp": datetime.now().isoformat(),
                "user": user_message,
                "assistant": full_response
            })
            
            # Deactivate skills after use (cleanup for next query)
            self.injector.deactivate_all()
            
        except Exception as e:
            logger.error(f"Error in streaming chat with thinking: {e}", exc_info=True)
            yield {
                "type": "error",
                "message": f"Error: {str(e)}"
            }
    
    async def chat_stream(
        self,
        user_message: str,
        thread_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Stream chat response (async generator)
        
        Args:
            user_message: User message
            thread_id: Thread ID (optional)
            
        Yields:
            Response text chunks
        """
        if not self._initialized:
            await self.initialize()
        
        # Determine thread to use
        if thread_id:
            if thread_id not in self.threads:
                self.create_thread(thread_id)
            self.current_thread_id = thread_id
        elif not self.current_thread_id:
            self.create_thread()
        
        thread = self.threads[self.current_thread_id]
        response_parts = []
        
        try:
            # Stream response with MCP tools
            mcp_tools = self.mcp_client.get_tools() if self.mcp_client.has_tools() else None
            
            if mcp_tools:
                stream = self.agent.run_stream(user_message, thread=thread, tools=mcp_tools)
            else:
                stream = self.agent.run_stream(user_message, thread=thread)
                
            async for update in stream:
                if update.text:
                    response_parts.append(update.text)
                    yield update.text
            
            # Store complete response in history
            full_response = "".join(response_parts)
            self.thread_history[self.current_thread_id].append({
                "timestamp": datetime.now().isoformat(),
                "user": user_message,
                "assistant": full_response
            })
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}", exc_info=True)
            yield f"\n\nError: {str(e)}"
    
    def get_thread_history(self, thread_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get thread history
        
        Args:
            thread_id: Thread ID (optional, uses current thread if not provided)
            
        Returns:
            Thread message history
        """
        tid = thread_id or self.current_thread_id
        return self.thread_history.get(tid, [])
    
    def clear_history(self) -> None:
        """Clear current thread history"""
        if self.current_thread_id and self.current_thread_id in self.thread_history:
            self.thread_history[self.current_thread_id] = []
            logger.info("Cleared thread history")
    
    async def close(self) -> None:
        """Close Agent and all connections"""
        # Close MCP client
        await self.mcp_client.close()
        
        # Close agent if it exists
        if self.agent:
            # MAF ChatAgent cleanup (if needed)
            pass
        
        logger.info("Azure Doc Agent closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
