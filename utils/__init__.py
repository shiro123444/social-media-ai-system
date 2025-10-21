"""
工具模块
包含DeepSeek适配器和MCP工具池
"""

from .deepseek_adapter import create_deepseek_client, DeepSeekChatClient
from .mcp_tool_pool import get_tool_pool

__all__ = [
    'create_deepseek_client',
    'DeepSeekChatClient',
    'get_tool_pool',
]
