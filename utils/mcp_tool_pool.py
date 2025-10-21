"""
MCP 工具连接池
管理 MCP 工具的生命周期，避免重复创建和异步问题

这是一个全局单例，确保：
1. 每个 MCP 工具只创建一次连接
2. 工具在同一 event loop 中被创建和销毁
3. 资源被正确清理
4. 避免异步作用域冲突
"""

import asyncio
import logging
from typing import Dict, Optional, Union
from agent_framework import MCPStdioTool, MCPStreamableHTTPTool, MCPWebsocketTool

logger = logging.getLogger(__name__)

# 工具类型别名
MCPToolType = Union[MCPStdioTool, MCPStreamableHTTPTool, MCPWebsocketTool]


class MCPToolPool:
    """
    MCP 工具连接池 - 单例模式
    
    管理所有 MCP 工具的生命周期，确保：
    - 工具连接的复用（不重复创建）
    - 正确的异步资源管理
    - 工具生命周期追踪
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """
        异步初始化工具池
        这个方法必须在创建任何工具之前调用
        """
        if MCPToolPool._initialized:
            return
        
        MCPToolPool._initialized = True
        self._tools: Dict[str, MCPToolType] = {}  # 支持多种类型的MCP工具
        self._lock = asyncio.Lock()
        self._task_group_tasks = {}  # 追踪任务组
        logger.info("✅ MCP 工具池初始化完成（支持 stdio/http/websocket）")
    
    async def get_or_create_tool(self, config) -> MCPToolType:
        """
        获取或创建工具（使用单例模式）
        支持 stdio、http、websocket 三种类型
        
        Args:
            config: MCP 服务器配置 (MCPServerConfig 对象)
            
        Returns:
            MCP工具实例 (MCPStdioTool | MCPStreamableHTTPTool | MCPWebsocketTool)
            
        Raises:
            Exception: 工具创建失败
        """
        await self.initialize()
        
        async with self._lock:
            tool_name = config.name
            
            # 1. 检查工具是否已存在且连接正常
            if tool_name in self._tools:
                tool = self._tools[tool_name]
                logger.debug(f"🔄 工具 {tool_name} 已存在，复用连接")
                return tool
            
            # 2. 根据类型创建不同的工具
            logger.info(f"🆕 创建新 MCP 工具: {tool_name} (type={config.type})")
            
            try:
                # 根据配置类型创建对应的工具
                if config.type == 'stdio':
                    logger.debug(f"   命令: {config.command}")
                    logger.debug(f"   参数: {config.args}")
                    tool = MCPStdioTool(
                        name=config.name,
                        command=config.command,
                        args=config.args,
                        env=config.env or {},
                        load_tools=True,  # 自动加载工具列表
                    )
                
                elif config.type == 'http':
                    logger.debug(f"   URL: {config.url}")
                    tool = MCPStreamableHTTPTool(
                        name=config.name,
                        url=config.url,
                        load_tools=True,
                    )
                
                elif config.type == 'sse':
                    # SSE 也使用 MCPStreamableHTTPTool
                    logger.debug(f"   URL: {config.url}")
                    tool = MCPStreamableHTTPTool(
                        name=config.name,
                        url=config.url,
                        load_tools=True,
                    )
                
                elif config.type == 'websocket':
                    logger.debug(f"   URL: {config.url}")
                    tool = MCPWebsocketTool(
                        name=config.name,
                        url=config.url,
                        load_tools=True,
                    )
                
                else:
                    raise ValueError(f"不支持的 MCP 类型: {config.type}")
                
                # 3. 连接工具
                logger.info(f"🔗 正在连接工具: {tool_name}")
                await tool.connect()
                
                # 4. 验证连接
                if hasattr(tool, 'functions') and tool.functions:
                    func_names = [f.name if hasattr(f, 'name') else str(f) for f in tool.functions]
                    logger.info(f"✅ 工具连接成功: {tool_name}")
                    logger.info(f"   加载了 {len(tool.functions)} 个函数")
                    logger.debug(f"   函数列表: {func_names}")
                else:
                    logger.warning(f"⚠️ 工具 {tool_name} 连接成功但未加载任何函数")
                
                # 5. 缓存工具
                self._tools[tool_name] = tool
                return tool
                
            except Exception as e:
                logger.error(f"❌ 创建/连接工具 {tool_name} 失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise
    
    async def close_tool(self, tool_name: str):
        """
        关闭并移除单个工具
        
        Args:
            tool_name: 工具名称
        """
        await self.initialize()
        
        async with self._lock:
            if tool_name in self._tools:
                tool = self._tools[tool_name]
                try:
                    logger.info(f"🔌 正在关闭工具: {tool_name}")
                    if hasattr(tool, 'close'):
                        await tool.close()
                    del self._tools[tool_name]
                    logger.info(f"✅ 工具已关闭: {tool_name}")
                except Exception as e:
                    logger.error(f"❌ 关闭工具 {tool_name} 失败: {e}")
                    del self._tools[tool_name]
            else:
                logger.debug(f"⚠️ 工具 {tool_name} 未找到")
    
    async def close_all(self):
        """
        关闭所有工具
        这个方法应该在程序退出时调用
        """
        await self.initialize()
        
        async with self._lock:
            if not self._tools:
                logger.info("✅ 工具池为空，无需关闭")
                return
            
            logger.info(f"🔌 正在关闭所有工具 ({len(self._tools)} 个)...")
            
            failed_tools = []
            for tool_name, tool in list(self._tools.items()):
                try:
                    if hasattr(tool, 'close'):
                        await tool.close()
                    logger.info(f"   ✅ {tool_name} 已关闭")
                except Exception as e:
                    logger.error(f"   ❌ {tool_name} 关闭失败: {e}")
                    failed_tools.append(tool_name)
                finally:
                    del self._tools[tool_name]
            
            if failed_tools:
                logger.warning(f"⚠️ {len(failed_tools)} 个工具关闭失败: {failed_tools}")
            else:
                logger.info("✅ 所有工具已成功关闭")
    
    def get_tool_count(self) -> int:
        """获取当前缓存的工具数量"""
        return len(self._tools)
    
    def list_tools(self) -> list:
        """列出所有缓存的工具名称"""
        return list(self._tools.keys())
    
    async def reset(self):
        """重置工具池（关闭所有工具并清空）"""
        logger.warning("⚠️ 重置工具池...")
        await self.close_all()
        MCPToolPool._initialized = False


# 全局工具池实例
_tool_pool_instance = None


async def get_tool_pool() -> MCPToolPool:
    """
    获取全局 MCP 工具池实例
    
    这是推荐的方式获取工具池。
    
    Returns:
        MCPToolPool 单例实例
        
    Example:
        ```python
        pool = await get_tool_pool()
        tool = await pool.get_or_create_tool(config)
        ```
    """
    global _tool_pool_instance
    
    if _tool_pool_instance is None:
        _tool_pool_instance = MCPToolPool()
        await _tool_pool_instance.initialize()
    
    return _tool_pool_instance


async def cleanup_tool_pool():
    """
    清理全局工具池
    应该在程序退出时调用
    """
    global _tool_pool_instance
    
    if _tool_pool_instance is not None:
        await _tool_pool_instance.close_all()
        _tool_pool_instance = None
        logger.info("✅ 工具池已清理")
