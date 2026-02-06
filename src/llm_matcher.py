"""
LLM-based Skill Matcher

Uses LLM to intelligently match user queries to skills, avoiding hardcoded keywords
"""

import logging
from typing import List, Optional
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from .registry import SkillMetadata

logger = logging.getLogger(__name__)


class LLMSkillMatcher:
    """Use LLM to match user queries to appropriate skills"""
    
    def __init__(
        self,
        azure_openai_endpoint: str,
        azure_openai_key: str,
        azure_openai_deployment: str
    ):
        """
        Initialize LLM Skill Matcher
        
        Args:
            azure_openai_endpoint: Azure OpenAI endpoint
            azure_openai_key: API key
            azure_openai_deployment: Deployment name
        """
        self.endpoint = azure_openai_endpoint
        self.api_key = azure_openai_key
        self.deployment = azure_openai_deployment
        self.client: Optional[ChatAgent] = None
        
    def initialize(self):
        """Initialize the LLM client"""
        chat_client = AzureOpenAIChatClient(
            endpoint=self.endpoint,
            api_key=self.api_key,
            deployment_name=self.deployment
        )
        
        system_prompt = """You are a skill matching assistant. Your job is to analyze user queries and determine which skill (if any) is most relevant.

You will be given:
1. A user query
2. A list of available skills with their names and descriptions

Your task:
- Analyze the user's intent
- Match it to the most relevant skill
- Return ONLY the skill name, or "NONE" if no skill matches

Rules:
- Be strict: only match if the query clearly relates to the skill's purpose
- For documentation/learning queries → microsoft-docs
- For code samples/API reference queries → microsoft-code-reference  
- For general conversation/greetings → NONE
- Consider queries in ANY language (English, Chinese, etc.)

Examples:
Query: "Azure Functions的官方文档" → microsoft-docs
Query: "给我Python代码示例" → microsoft-code-reference
Query: "How does Cosmos DB work?" → microsoft-docs
Query: "Show me API reference for BlobClient" → microsoft-code-reference
Query: "hello" → NONE
Query: "你好" → NONE

Respond with ONLY the skill name or NONE, nothing else."""

        self.client = chat_client.as_agent(
            instructions=system_prompt,
            default_options={
                "temperature": 0.0,  # Deterministic matching
                "max_tokens": 50
            }
        )
        
        logger.info("LLM Skill Matcher initialized")
    
    async def match_skills(
        self,
        query: str,
        available_skills: List[SkillMetadata]
    ) -> Optional[SkillMetadata]:
        """
        Use LLM to match query to best skill
        
        Args:
            query: User query
            available_skills: List of available skills
            
        Returns:
            Best matching skill or None
        """
        if not self.client:
            self.initialize()
        
        if not available_skills:
            return None
        
        # Build skill list for LLM
        skills_info = "\n".join([
            f"- {skill.name}: {skill.description}"
            for skill in available_skills
        ])
        
        # Create matching prompt
        matching_prompt = f"""Available skills:
{skills_info}

User query: {query}

Which skill matches best? (respond with skill name or NONE)"""

        try:
            # Get LLM's decision
            response = await self.client.run(matching_prompt)
            
            if not response:
                logger.warning("LLM returned empty response for skill matching")
                return None
            
            # Extract skill name from response
            # AgentResponse might have different structure, try multiple attributes
            content = None
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'message'):
                content = response.message
            elif hasattr(response, 'text'):
                content = response.text
            elif isinstance(response, str):
                content = response
            else:
                # Try to get string representation
                content = str(response)
            
            if not content:
                logger.warning(f"Could not extract content from LLM response: {type(response)}")
                return None
            
            matched_name = content.strip().lower()
            
            logger.info(f"LLM skill matcher: '{query}' → '{matched_name}'")
            
            # Handle NONE case
            if matched_name == "none" or "none" in matched_name:
                return None
            
            # Find matching skill
            for skill in available_skills:
                if skill.name.lower() in matched_name or matched_name in skill.name.lower():
                    return skill
            
            logger.warning(f"LLM returned skill name '{matched_name}' but not found in available skills")
            return None
            
        except Exception as e:
            logger.error(f"Error in LLM skill matching: {e}")
            return None
