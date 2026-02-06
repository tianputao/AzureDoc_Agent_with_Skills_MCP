"""
Azure Doc Agent - Skills & MCP

An intelligent document assistant integrating Agent Skills and MCP
"""

__version__ = "1.0.0"
__author__ = "Azure Doc Agent Team"

from .azure_doc_agent import AzureDocAgent
from .registry import SkillRegistry, SkillMetadata
from .injector import SkillInjector
from .mcp_client import MCPClient
from .system_prompts import SystemPromptsManager

__all__ = [
    "AzureDocAgent",
    "SkillRegistry",
    "SkillMetadata",
    "SkillInjector",
    "MCPClient",
    "SystemPromptsManager",
]
