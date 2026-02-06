"""
Skill Registry - Skill discovery and index management

Implements automatic skill discovery, parsing, and indexing based on agentskills.io standard
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """Skill metadata"""
    name: str
    description: str
    context: str
    compatibility: str
    tags: List[str]
    path: str
    full_content: Optional[str] = None


class SkillRegistry:
    """Skill Registry - Manages skill discovery, parsing, and indexing"""
    
    def __init__(self, skills_directory: str = "skills"):
        """
        Initialize skill registry
        
        Args:
            skills_directory: Path to skills directory
        """
        self.skills_directory = Path(skills_directory)
        self.skills: Dict[str, SkillMetadata] = {}
        
    def discover_skills(self) -> int:
        """
        Scan skills directory and discover all available skills
        
        Returns:
            Number of skills discovered
        """
        logger.info(f"Starting to scan skills directory: {self.skills_directory}")
        
        if not self.skills_directory.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_directory}")
            return 0
            
        skill_count = 0
        
        # Iterate through skills directory
        for skill_path in self.skills_directory.iterdir():
            if skill_path.is_dir():
                skill_file = skill_path / "SKILL.md"
                if skill_file.exists():
                    try:
                        metadata = self._parse_skill_file(skill_file)
                        self.skills[metadata.name] = metadata
                        skill_count += 1
                        logger.info(f"Discovered skill: {metadata.name}")
                    except Exception as e:
                        logger.error(f"Failed to parse skill file {skill_file}: {e}")
                        
        logger.info(f"Skill discovery completed, found {skill_count} skills")
        return skill_count
    
    def _parse_skill_file(self, skill_file: Path) -> SkillMetadata:
        """
        Parse SKILL.md file and extract metadata
        
        Args:
            skill_file: Path to SKILL.md file
            
        Returns:
            SkillMetadata object
        """
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract YAML front matter
        metadata = self._extract_yaml_frontmatter(content)
        
        # Create SkillMetadata object
        skill_metadata = SkillMetadata(
            name=metadata.get('name', ''),
            description=metadata.get('description', ''),
            context=metadata.get('context', 'fork'),
            compatibility=metadata.get('compatibility', ''),
            tags=metadata.get('tags', []),
            path=str(skill_file.parent),
            full_content=content
        )
        
        return skill_metadata
    
    def _extract_yaml_frontmatter(self, content: str) -> Dict:
        """
        Extract YAML front matter from Markdown file
        
        Args:
            content: File content
            
        Returns:
            Parsed metadata dictionary
        """
        # Match YAML front matter (content between ---)
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)
        
        if not match:
            raise ValueError("YAML front matter not found")
        
        yaml_content = match.group(1)
        metadata = {}
        
        # Simple YAML parsing (use PyYAML for complex cases)
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle list format (simple implementation)
                if value.startswith('[') and value.endswith(']'):
                    # Remove brackets and split
                    value = value[1:-1]
                    value = [v.strip().strip('"').strip("'") for v in value.split(',')]
                
                metadata[key] = value
        
        return metadata
    
    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """
        Get skill by name
        
        Args:
            name: Skill name
            
        Returns:
            SkillMetadata if exists, None otherwise
        """
        return self.skills.get(name)
    
    def list_skills(self) -> List[SkillMetadata]:
        """
        List all available skills
        
        Returns:
            List of SkillMetadata
        """
        return list(self.skills.values())
    
    def search_skills(self, query: str, min_score: int = 40) -> List[SkillMetadata]:
        """
        Search for relevant skills based on query using intelligent keyword matching
        
        Args:
            query: Search query
            min_score: Minimum score required for a match (default: 40)
            
        Returns:
            List of matching skills sorted by relevance
        """
        query_lower = query.lower()
        
        # Extract keywords from query
        keywords = self._extract_keywords(query_lower)
        
        results = []
        for skill in self.skills.values():
            score = self._calculate_skill_match_score(skill, query_lower, keywords)
            if score >= min_score:  # Only include if score meets minimum threshold
                results.append((skill, score))
        
        # Sort by score (descending) and return skills only
        results.sort(key=lambda x: x[1], reverse=True)
        matched_skills = [skill for skill, score in results]
        
        logger.info(f"Search '{query}' found {len(matched_skills)} skills (min_score={min_score})")
        for skill, score in results:
            logger.info(f"  - {skill.name}: score={score}")
        
        return matched_skills
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from query (supports Chinese)
        
        Args:
            query: Query string
            
        Returns:
            List of keywords
        """
        # Common English stop words to filter out
        stop_words = {'i', 'me', 'my', 'want', 'need', 'how', 'what', 'when', 'where', 
                      'who', 'give', 'show', 'tell', 'the', 'a', 'an', 'and', 'or', 'but',
                      'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'about',
                      'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        
        # Chinese stop words
        chinese_stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都',
                              '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
                              '会', '着', '没有', '看', '好', '自己', '这'}
        
        # Split by space first (for mixed Chinese/English)
        words = query.lower().split()
        
        keywords = []
        for w in words:
            # Skip English stop words
            if w in stop_words:
                continue
            
            # Check if contains Chinese characters
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in w)
            
            if has_chinese:
                # For Chinese text, add the whole word (could be multiple characters)
                if w not in chinese_stop_words and len(w) >= 1:
                    keywords.append(w)
            else:
                # For English, filter short words
                if len(w) > 2:
                    keywords.append(w)
        
        return keywords
    
    def _calculate_skill_match_score(self, skill: SkillMetadata, query: str, keywords: List[str]) -> int:
        """
        Calculate match score for a skill
        
        Args:
            skill: Skill metadata
            query: Full query string
            keywords: Extracted keywords
            
        Returns:
            Match score (0 = no match)
        """
        score = 0
        skill_desc_lower = skill.description.lower()
        skill_name_lower = skill.name.lower()
        
        # Exact name match = high score
        if skill_name_lower in query or query in skill_name_lower:
            score += 100
        
        # Tag matches = high score
        for tag in skill.tags:
            tag_lower = tag.lower()
            if tag_lower in query:
                score += 50
            # Check if any keyword matches the tag
            for keyword in keywords:
                if keyword in tag_lower or tag_lower in keyword:
                    score += 30
        
        # Keyword matches in description
        for keyword in keywords:
            if keyword in skill_desc_lower:
                score += 20
            if keyword in skill_name_lower:
                score += 40
        
        # Generic matching (no hardcoded language-specific keywords)
        # This is just a fallback - LLM matching should be primary
        
        return score
    
    def get_skills_summary(self) -> str:
        """
        Generate skills summary (for system prompts)
        
        Returns:
            Skills list in XML format
        """
        if not self.skills:
            return ""
        
        summary_parts = ["<available_skills>"]
        
        for skill in self.skills.values():
            skill_xml = f"""  <skill>
    <name>{skill.name}</name>
    <description>{skill.description}</description>
    <tags>{', '.join(skill.tags)}</tags>
    <location>{skill.path}/SKILL.md</location>
  </skill>"""
            summary_parts.append(skill_xml)
        
        summary_parts.append("</available_skills>")
        
        return '\n'.join(summary_parts)
    
    def reload_skills(self) -> int:
        """
        Reload all skills
        
        Returns:
            Number of skills reloaded
        """
        logger.info("Reloading skills...")
        self.skills.clear()
        return self.discover_skills()
