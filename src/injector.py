"""
Skill Injector - Dynamic skill injection and context management

Implements progressive disclosure pattern, loading skill content on demand
"""

import logging
from typing import Dict, List, Optional
from .registry import SkillRegistry, SkillMetadata

logger = logging.getLogger(__name__)


class SkillInjector:
    """Skill Injector - Manages dynamic loading and context injection of skills"""
    
    def __init__(self, registry: SkillRegistry):
        """
        Initialize skill injector
        
        Args:
            registry: SkillRegistry instance
        """
        self.registry = registry
        self.active_skills: Dict[str, SkillMetadata] = {}
        
    def activate_skill(self, skill_name: str) -> Optional[str]:
        """
        Activate skill and return complete content
        
        Args:
            skill_name: Skill name
            
        Returns:
            Complete skill content, or None if skill doesn't exist
        """
        skill = self.registry.get_skill(skill_name)
        
        if not skill:
            logger.warning(f"Skill does not exist: {skill_name}")
            return None
        
        # Mark as activated
        self.active_skills[skill_name] = skill
        logger.info(f"Activated skill: {skill_name}")
        
        # Return formatted skill content
        return self._format_skill_content(skill)
    
    def deactivate_skill(self, skill_name: str) -> bool:
        """
        Deactivate skill
        
        Args:
            skill_name: Skill name
            
        Returns:
            Whether deactivation succeeded
        """
        if skill_name in self.active_skills:
            del self.active_skills[skill_name]
            logger.info(f"Deactivated skill: {skill_name}")
            return True
        
        logger.warning(f"Skill not activated: {skill_name}")
        return False
    
    def deactivate_all(self) -> None:
        """Deactivate all skills"""
        self.active_skills.clear()
        logger.info("Deactivated all skills")
    
    def get_active_skills(self) -> List[str]:
        """
        Get list of currently activated skills
        
        Returns:
            List of activated skill names
        """
        return list(self.active_skills.keys())
    
    def is_skill_active(self, skill_name: str) -> bool:
        """
        Check if skill is activated
        
        Args:
            skill_name: Skill name
            
        Returns:
            Whether skill is activated
        """
        return skill_name in self.active_skills
    
    def _format_skill_content(self, skill: SkillMetadata) -> str:
        """
        Format skill content for context injection
        
        Args:
            skill: Skill metadata
            
        Returns:
            Formatted content
        """
        # Wrap skill content using XML format
        formatted = f"""
<skill_activated>
  <name>{skill.name}</name>
  <description>{skill.description}</description>
  
  <skill_content>
{skill.full_content}
  </skill_content>
  
  <instructions>
You have now activated the '{skill.name}' skill. Follow the guidelines in the skill content above to assist the user with their request.
  </instructions>
</skill_activated>
"""
        return formatted
    
    def build_context_injection(self, user_query: str) -> str:
        """
        Build context injection content based on user query
        
        Args:
            user_query: User query
            
        Returns:
            Content to inject into context
        """
        # Search for relevant skills
        relevant_skills = self.registry.search_skills(user_query)
        
        if not relevant_skills:
            return ""
        
        # Auto-activate relevant skills (up to 2 most relevant)
        injection_parts = []
        
        for skill in relevant_skills[:2]:
            if not self.is_skill_active(skill.name):
                content = self.activate_skill(skill.name)
                if content:
                    injection_parts.append(content)
        
        return "\n".join(injection_parts)
    
    def get_skills_for_llm(self) -> str:
        """
        Get summary info of currently activated skills (for LLM context)
        
        Returns:
            Formatted text of skill information
        """
        if not self.active_skills:
            return ""
        
        parts = ["<active_skills>"]
        
        for skill in self.active_skills.values():
            skill_info = f"""
  <skill>
    <name>{skill.name}</name>
    <description>{skill.description}</description>
    <tags>{', '.join(skill.tags)}</tags>
  </skill>"""
            parts.append(skill_info)
        
        parts.append("</active_skills>")
        
        return '\n'.join(parts)
    
    def match_skill_by_query(self, user_query: str) -> Optional[str]:
        """
        Intelligently match and activate skill based on user query
        
        Args:
            user_query: User query
            
        Returns:
            Matched skill name, or None if no match
        """
        user_query_lower = user_query.lower()
        
        # Define keyword to skill mapping
        skill_keywords = {
            "microsoft-docs": [
                "documentation", "docs", "learn", "tutorial", 
                "quickstart", "guide", "overview", "concepts", 
                "documentation", "tutorial", "azure", "microsoft"
            ],
            "microsoft-code-reference": [
                "code", "api", "sdk", "sample", "example",
                "implementation", "code", "sample", "API", "reference"
            ]
        }
        
        # Calculate match score for each skill
        scores = {}
        for skill_name, keywords in skill_keywords.items():
            score = sum(1 for keyword in keywords if keyword in user_query_lower)
            if score > 0:
                scores[skill_name] = score
        
        # Select skill with highest score
        if scores:
            best_skill = max(scores, key=scores.get)
            logger.info(f"Matched skill based on query: {best_skill}")
            return best_skill
        
        return None
    
    def get_injection_summary(self) -> Dict[str, any]:
        """
        Get injection status summary
        
        Returns:
            Dictionary containing injection information
        """
        return {
            "active_count": len(self.active_skills),
            "active_skills": list(self.active_skills.keys()),
            "available_count": len(self.registry.skills),
            "available_skills": [s.name for s in self.registry.list_skills()]
        }
