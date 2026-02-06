"""
System Prompts - Dynamic system prompt management

Dynamically generates system prompts based on available skills and context
"""

import logging
from typing import Optional
from .registry import SkillRegistry
from .injector import SkillInjector

logger = logging.getLogger(__name__)


class SystemPromptsManager:
    """System Prompts Manager - Dynamically generates and updates system prompts"""
    
    def __init__(self, registry: SkillRegistry, injector: SkillInjector):
        """
        Initialize system prompts manager
        
        Args:
            registry: Skill registry
            injector: Skill injector
        """
        self.registry = registry
        self.injector = injector
        self.base_prompt = self._get_base_prompt()
    
    def _get_base_prompt(self) -> str:
        """
        Get base system prompt
        
        Returns:
            Base system prompt text
        """
        return """You are AzureDocAgent, an intelligent assistant specialized in helping users find and understand Microsoft documentation.

Your capabilities:
- Search and retrieve official Microsoft documentation from learn.microsoft.com
- Provide accurate, up-to-date information about Azure, .NET, Microsoft 365, and other Microsoft technologies
- Help users understand complex concepts with clear explanations
- Guide users to relevant tutorials, quickstarts, and best practices

Your approach:
1. Listen carefully to user questions and identify their needs
2. Use available skills to search Microsoft documentation
3. Provide clear, concise answers with references to official documentation
4. When appropriate, suggest related topics or deeper dive resources

Important guidelines:
- Always cite sources from official Microsoft documentation
- Prefer official documentation over general knowledge
- If you're unsure, search the documentation rather than guessing
- Provide code examples and configuration samples when relevant
- Be helpful, accurate, and professional
"""
    
    def build_system_prompt(self, include_active_skills: bool = True) -> str:
        """
        Build complete system prompt
        
        Args:
            include_active_skills: Whether to include currently activated skills info
            
        Returns:
            Complete system prompt
        """
        parts = [self.base_prompt]
        
        # Add available skills summary
        skills_summary = self.registry.get_skills_summary()
        if skills_summary:
            parts.append("\n## Available Skills\n")
            parts.append(skills_summary)
            parts.append("""
When a user query matches a skill's capabilities, you can activate that skill by calling the activate_skill function.
Once activated, you will receive detailed instructions on how to use that skill's tools and capabilities.
""")
        
        # Add currently activated skills info
        if include_active_skills:
            active_skills_info = self.injector.get_skills_for_llm()
            if active_skills_info:
                parts.append("\n## Currently Active Skills\n")
                parts.append(active_skills_info)
        
        return '\n'.join(parts)
    
    def update_for_query(self, user_query: str) -> str:
        """
        Update system prompt based on user query
        
        Args:
            user_query: User query
            
        Returns:
            Updated system prompt
        """
        # Inject relevant skills based on query
        context_injection = self.injector.build_context_injection(user_query)
        
        # Build system prompt
        system_prompt = self.build_system_prompt(include_active_skills=True)
        
        # If there's injected content, add to system prompt
        if context_injection:
            system_prompt += "\n\n## Context for Current Query\n"
            system_prompt += context_injection
        
        return system_prompt
    
    def get_skill_activation_prompt(self, skill_name: str) -> Optional[str]:
        """
        Generate prompt for skill activation
        
        Args:
            skill_name: Skill name
            
        Returns:
            Skill activation prompt
        """
        skill_content = self.injector.activate_skill(skill_name)
        
        if not skill_content:
            return None
        
        return f"""
**Skill Activated: {skill_name}**

{skill_content}

You now have access to this skill's capabilities. Use them to assist the user with their request.
"""
    
    def get_tools_instruction(self) -> str:
        """
        Get tools usage instructions
        
        Returns:
            Tools usage instructions text
        """
        return """
## Available Tools

You have access to the following tools to assist users:

1. **activate_skill(skill_name: str)** - Activate a skill to access its specialized capabilities
   - Use when user query matches a skill's domain
   - Returns detailed instructions for using the skill
   
2. **search_microsoft_docs(query: str, max_results: int)** - Search Microsoft documentation
   - Use for finding relevant documentation
   - Returns search results with titles, URLs, and excerpts
   
3. **fetch_microsoft_doc(url: str)** - Fetch complete documentation page
   - Use when you need full content of a specific page
   - Returns the complete text of the documentation page

4. **list_available_skills()** - List all available skills
   - Use to see what skills are available
   - Returns a list of skill names and descriptions

Tool Usage Guidelines:
- Always activate relevant skills before using their specific tools
- Use search first to find relevant documentation
- Fetch full pages only when search excerpts are insufficient
- Provide citations to the documentation URLs in your responses
"""
    
    def get_conversation_guidelines(self) -> str:
        """
        Get conversation guidelines
        
        Returns:
            Conversation guidelines text
        """
        return """
## Conversation Guidelines

Multi-turn Conversation:
- Maintain context across multiple exchanges
- Remember activated skills and previous searches
- Build on previous answers to provide continuity

Threading Support:
- Each conversation thread maintains its own context
- Skills activated in one thread don't affect others
- Conversation history is preserved for the session

Memory Management:
- Short-term memory keeps recent conversation history
- Important facts and user preferences are retained
- You can reference earlier parts of the conversation

Response Format:
- Provide clear, structured answers
- Include relevant code examples when appropriate
- Always cite documentation sources
- Use markdown formatting for better readability
- Break down complex topics into digestible sections

When Unsure:
- Search the documentation rather than guessing
- Ask clarifying questions if the user's intent is unclear
- Suggest related topics that might be helpful
"""
    
    def build_full_system_prompt(self) -> str:
        """
        Build complete system prompt with all components
        
        Returns:
            Complete system prompt
        """
        parts = [
            self.build_system_prompt(),
            self.get_tools_instruction(),
            self.get_conversation_guidelines()
        ]
        
        return '\n'.join(parts)
