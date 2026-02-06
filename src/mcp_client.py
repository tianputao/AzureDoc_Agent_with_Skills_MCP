"""
MCP Client - Unified MCP tool management using Agent Framework

Encapsulates MCPStreamableHTTPTool for clean separation of concerns and extensibility
"""

import logging
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Import Agent Framework MCP support
from agent_framework import MCPStreamableHTTPTool

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP Server Configuration"""
    name: str
    url: str
    headers: Optional[Dict[str, str]] = None
    description: str = ""


class MCPClient:
    """
    MCP Client - Manages MCP tools using Agent Framework's built-in support
    
    This class encapsulates MCPStreamableHTTPTool and provides:
    - Clean separation of concerns
    - Easy extensibility for multiple MCP servers
    - Unified interface for Agent to use MCP tools
    
    MCP servers can be configured via environment variables:
    - MCP_SERVERS: Comma-separated list of server IDs (e.g., "ms-learn,github")
    - MCP_{ID}_NAME: Display name for the server
    - MCP_{ID}_URL: Server URL
    - MCP_{ID}_DESCRIPTION: Server description (optional)
    - MCP_{ID}_AUTH_TOKEN: Authorization token (optional)
    """
    
    @staticmethod
    def load_from_env() -> list[MCPServerConfig]:
        """
        Load MCP server configurations from environment variables
        
        Environment variable format:
            MCP_SERVERS=ms-learn,github,internal
            
            MCP_MS_LEARN_NAME=Microsoft Learn MCP
            MCP_MS_LEARN_URL=https://learn.microsoft.com/api/mcp
            MCP_MS_LEARN_DESCRIPTION=Microsoft official documentation
            
            MCP_GITHUB_NAME=GitHub MCP
            MCP_GITHUB_URL=https://api.github.com/mcp
            MCP_GITHUB_AUTH_TOKEN=your-token
            
        Returns:
            List of MCPServerConfig instances
        """
        configs = []
        
        # Get list of server IDs from MCP_SERVERS
        servers_str = os.getenv("MCP_SERVERS", "")
        if not servers_str:
            logger.info("No MCP_SERVERS configured in environment, using defaults")
            return None
        
        server_ids = [s.strip() for s in servers_str.split(",") if s.strip()]
        logger.info(f"Loading {len(server_ids)} MCP servers from environment: {server_ids}")
        
        for server_id in server_ids:
            # Convert server_id to uppercase for env var name
            env_prefix = f"MCP_{server_id.upper().replace('-', '_')}"
            
            name = os.getenv(f"{env_prefix}_NAME")
            url = os.getenv(f"{env_prefix}_URL")
            
            if not name or not url:
                logger.warning(f"Skipping MCP server '{server_id}': missing NAME or URL")
                continue
            
            description = os.getenv(f"{env_prefix}_DESCRIPTION", "")
            auth_token = os.getenv(f"{env_prefix}_AUTH_TOKEN")
            
            # Build headers if auth token exists
            headers = None
            if auth_token:
                headers = {"Authorization": f"Bearer {auth_token}"}
            
            config = MCPServerConfig(
                name=name,
                url=url,
                headers=headers,
                description=description
            )
            configs.append(config)
            logger.info(f"Loaded MCP server config: {name} ({url})")
        
        return configs if configs else None
    
    def __init__(self, server_configs: Optional[list[MCPServerConfig]] = None):
        """
        Initialize MCP client with one or more MCP server configurations
        
        Args:
            server_configs: List of MCP server configurations. 
                          If None, loads from environment variables.
                          If env vars not set, uses default Microsoft Learn MCP.
        """
        if server_configs is None:
            # Try to load from environment variables first
            server_configs = self.load_from_env()
            
        if server_configs is None:
            # Fallback to default if no env config
            logger.info("Using default MCP server configuration")
            server_configs = [
                MCPServerConfig(
                    name="Microsoft Learn MCP",
                    url="https://learn.microsoft.com/api/mcp",
                    description="Microsoft official documentation MCP server"
                )
            ]
        
        self.server_configs = server_configs
        self.mcp_tools: Dict[str, MCPStreamableHTTPTool] = {}
        self._initialized = False
        
    async def initialize(self) -> bool:
        """
        Initialize MCP tools using Agent Framework's MCPStreamableHTTPTool
        
        Returns:
            Whether initialization succeeded for at least one MCP server
        """
        success_count = 0
        
        for config in self.server_configs:
            try:
                logger.info(f"Initializing MCP tool: {config.name} ({config.url})")
                
                # Create MCPStreamableHTTPTool using Agent Framework
                mcp_tool = MCPStreamableHTTPTool(
                    name=config.name,
                    url=config.url,
                    headers=config.headers or {}
                )
                
                self.mcp_tools[config.name] = mcp_tool
                logger.info(f"✅ MCP tool '{config.name}' initialized successfully")
                success_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to initialize MCP tool '{config.name}': {e}")
                logger.info(f"💡 {config.name} will not be available")
        
        self._initialized = success_count > 0
        
        if self._initialized:
            logger.info(f"✅ MCP Client initialized with {success_count}/{len(self.server_configs)} tools")
        else:
            logger.warning("⚠️ No MCP tools initialized. Agent will use built-in knowledge.")
        
        return self._initialized
    
    def get_tools(self) -> list[MCPStreamableHTTPTool]:
        """
        Get all initialized MCP tools for use by Agent
        
        Returns:
            List of MCPStreamableHTTPTool instances
        """
        return list(self.mcp_tools.values())
    
    def get_tool(self, name: str) -> Optional[MCPStreamableHTTPTool]:
        """
        Get specific MCP tool by name
        
        Args:
            name: Tool name
            
        Returns:
            MCPStreamableHTTPTool instance or None
        """
        return self.mcp_tools.get(name)
    
    def get_tool_names(self) -> list[str]:
        """
        Get names of all initialized MCP tools
        
        Returns:
            List of tool names
        """
        return list(self.mcp_tools.keys())
    
    def has_tools(self) -> bool:
        """
        Check if any MCP tools are initialized
        
        Returns:
            True if at least one tool is available
        """
        return len(self.mcp_tools) > 0
    
    async def close(self) -> None:
        """Close all MCP tool connections"""
        for name, tool in self.mcp_tools.items():
            try:
                # MCPStreamableHTTPTool is async context manager
                await tool.__aexit__(None, None, None)
                logger.info(f"Closed MCP tool: {name}")
            except Exception as e:
                logger.warning(f"Error closing MCP tool '{name}': {e}")
        
        logger.info("MCP client closed")
    
    def get_tools_info(self) -> list[Dict[str, str]]:
        """
        Get information about all initialized MCP tools
        
        Returns:
            List of tool information
        """
        return [
            {
                "name": name,
                "url": config.url,
                "description": config.description
            }
            for name, config in zip(self.mcp_tools.keys(), self.server_configs)
            if name in self.mcp_tools
        ]
    
    def is_initialized(self) -> bool:
        """Check if MCP client is initialized with at least one tool"""
        return self._initialized
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
