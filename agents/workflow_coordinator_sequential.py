"""
基于 Microsoft Agent Framework 官方 SequentialBuilder 的工作流协调器

按照官方文档规范：
1. 使用 SequentialBuilder 构建顺序工作流
2. Agent 之间通过共享 list[ChatMessage] 传递上下文
3. 每个 Agent 将其助手消息追加到共享对话上下文
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass
from contextlib import AsyncExitStack

from agent_framework import SequentialBuilder, ChatAgent, MCPStreamableHTTPTool

from config.workflow_config import WorkflowConfig
from config.mcp_config_manager import MCPConfigManager
from utils.deepseek_chat_client import DeepSeekChatClient
from utils.publishers.registry import get_publishers
from utils.content_models import PlatformContent

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    success: bool
    hotspots: Optional[list] = None
    analysis: Optional[dict] = None
    contents: Optional[PlatformContent] = None  # 现在是单个 PlatformContent 对象
    published_paths: Optional[dict[str, str]] = None
    error: Optional[str] = None
    execution_time: float = 0.0


class SequentialWorkflowCoordinator:
    """基于 SequentialBuilder 的工作流协调器
    
    工作流：热点获取 → 分析 → 内容生成 → 发布
    """
    
    def __init__(
        self,
        client: DeepSeekChatClient,
        config_manager: Optional[MCPConfigManager] = None,
        workflow_config: Optional[WorkflowConfig] = None
    ):
        self.client = client
        self.config_manager = config_manager or MCPConfigManager()
        self.workflow_config = workflow_config or WorkflowConfig()
        self.agents_initialized = False
        self.workflow = None
        self.mcp_tools = []  # 追踪所有 MCP 工具，用于清理
        
    async def cleanup(self):
        """清理所有资源"""
        logger.info("开始清理工作流资源...")
        try:
            # 关闭所有 MCP 工具
            for tool in self.mcp_tools:
                try:
                    if hasattr(tool, 'close'):
                        await tool.close()
                        logger.info(f"✅ 工具 {tool.name} 已关闭")
                except Exception as e:
                    logger.error(f"❌ 关闭工具 {tool.name} 失败: {e}")
            
            self.mcp_tools.clear()
            logger.info("✅ 所有资源已清理")
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.cleanup()
        return False
        
    async def initialize_agents(self):
        """初始化所有智能体"""
        if self.agents_initialized:
            logger.info("智能体已初始化，跳过")
            return
            
        logger.info("="*80)
        logger.info("开始初始化工作流智能体（SequentialBuilder 模式）...")
        logger.info("="*80)
        
        # 1. 创建热点获取智能体（带 MCP 工具）
        logger.info("\n[1/3] 初始化热点获取智能体...")
        self.hotspot_agent = await self._create_hotspot_agent()
        logger.info("✅ 热点获取智能体初始化完成")
        
        # 2. 创建分析智能体
        logger.info("\n[2/3] 初始化分析智能体...")
        self.analysis_agent = self._create_analysis_agent()
        logger.info("✅ 分析智能体初始化完成")
        
        # 3. 创建内容生成智能体
        logger.info("\n[3/3] 初始化内容生成智能体...")
        self.content_agent = self._create_content_agent()
        logger.info("✅ 内容生成智能体初始化完成")
        
        self.agents_initialized = True
        logger.info("\n" + "="*80)
        logger.info("所有智能体初始化完成")
        logger.info("="*80 + "\n")
    
    async def _create_hotspot_agent(self) -> ChatAgent:
        """创建热点获取智能体（参考 test_daily_hot_only.py 成功经验）"""
        mcp_tools = []
        tool_names = self.config_manager.AGENT_TOOLS_MAPPING.get("hotspot", [])
        
        for tool_name in tool_names:
            config = self.config_manager.get_server(tool_name)
            if not config or not config.is_active:
                continue
                
            logger.info(f"正在连接 MCP 工具: {tool_name} ({config.url})")
            try:
                # 直接创建并连接（参考 test_daily_hot_only.py）
                tool = MCPStreamableHTTPTool(
                    name=config.name,
                    url=config.url,
                    load_tools=True
                )
                await tool.connect()
                
                func_count = len(tool.functions) if hasattr(tool, 'functions') else 0
                logger.info(f"✅ 工具连接成功，加载了 {func_count} 个函数")
                
                if func_count > 0:
                    func_names = [f.name if hasattr(f, 'name') else str(f) 
                                  for f in tool.functions[:10]]
                    logger.info(f"   前10个函数: {func_names}")
                
                mcp_tools.append(tool)
                self.mcp_tools.append(tool)  # 追踪工具，用于后续清理
            except Exception as e:
                logger.error(f"❌ 连接工具 {tool_name} 失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        if not mcp_tools:
            logger.warning("⚠️ 没有成功加载任何 MCP 工具！")
        
        instructions = """你是热点资讯收集专家。使用 daily-hot-mcp 工具获取热点信息。

**工作流程：**
1. 根据用户查询调用相应的 MCP 工具（如 get-bilibili-trending）
2. 将工具返回的结果整理为 JSON 格式

**输出格式（必须严格遵守）：**
```json
{
  "hotspots": [
    {"title": "标题", "url": "链接", "heat_index": 85, "source": "B站", "summary": "摘要"}
  ]
}
```

**重要规则：**
- 必须调用工具，不要编造数据
- 输出必须是有效的 JSON 代码块
- 如果工具调用失败，返回空列表：{"hotspots": []}
"""
        
        return self.client.create_agent(
            name="hotspot_collector",
            instructions=instructions,
            tools=mcp_tools
        )
    
    def _create_analysis_agent(self) -> ChatAgent:
        """创建分析智能体"""
        instructions = """你是数据分析专家。分析热点数据并提取关键信息。

**输入：**前一个Agent收集的热点JSON数据

**任务：**
1. 提取共同话题和趋势
2. 计算热度分布
3. 识别最值得创作的内容

**输出格式：**
```json
{
  "summary": "今日热点概述",
  "top_topics": ["话题1", "话题2"],
  "recommendations": ["建议1", "建议2"]
}
```

只输出 JSON，不要额外解释。
"""
        
        return self.client.create_agent(
            name="analyzer",
            instructions=instructions
        )
    
    def _create_content_agent(self) -> ChatAgent:
        """创建内容生成智能体"""
        enabled_platforms = self.workflow_config.enabled_platforms
        style = self.workflow_config.style_default
        
        platforms_str = ', '.join(enabled_platforms)
        instructions = f"""你是专业的新媒体内容创作者。基于分析结果生成多平台内容。

**目标平台：**{platforms_str}
**内容风格：**{style}

**输出格式：**
```json
{{
  "wechat": {{"title": "标题", "content": "正文(2000-3000字)", "summary": "摘要"}},
  "weibo": {{"title": "标题", "content": "正文(140-2000字)", "summary": "摘要"}},
  "bilibili": {{"title": "标题", "content": "视频脚本(300-1500字)", "summary": "摘要", 
               "metadata": {{"scenes": ["场景1", "场景2"]}}}}
}}
```

只输出 JSON，每个平台生成适配的内容。
"""
        
        return self.client.create_agent(
            name="content_creator",
            instructions=instructions
        )
    
    async def build_workflow(self):
        """构建 Sequential 工作流"""
        if not self.agents_initialized:
            await self.initialize_agents()
        
        logger.info("构建 Sequential 工作流...")
        
        try:
            # SequentialBuilder 使用 participants() 方法传入Agent列表
            builder = SequentialBuilder()
            logger.debug(f"SequentialBuilder 类型: {type(builder)}")
            logger.debug(f"SequentialBuilder 可用方法: {[m for m in dir(builder) if not m.startswith('_')]}")
            
            # 检查是否有 participants 方法
            if not hasattr(builder, 'participants'):
                logger.error("❌ SequentialBuilder 没有 participants() 方法")
                logger.error(f"可用方法: {[m for m in dir(builder) if not m.startswith('_')]}")
                raise AttributeError("SequentialBuilder 没有 participants() 方法")
            
            self.workflow = (
                builder
                .participants([
                    self.hotspot_agent,
                    self.analysis_agent,
                    self.content_agent
                ])
                .build()
            )
            
            logger.debug(f"工作流对象类型: {type(self.workflow)}")
            logger.debug(f"工作流对象方法: {[m for m in dir(self.workflow) if not m.startswith('_')]}")
            
            logger.info("✅ 工作流构建完成")
            return self.workflow
        except Exception as e:
            logger.error(f"❌ 工作流构建失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def run_workflow(self, user_query: str) -> WorkflowResult:
        """执行工作流
        
        Args:
            user_query: 用户查询
            
        Returns:
            WorkflowResult: 执行结果
        """
        import time
        start_time = time.time()
        
        try:
            if not self.workflow:
                await self.build_workflow()
            
            logger.info(f"开始执行工作流: {user_query}")
            
            # 执行工作流（SequentialBuilder 返回事件流）
            print("\n>>> BEFORE workflow.run()")
            try:
                workflow_events = await self.workflow.run(user_query)
            except Exception as context_error:
                logger.error(f"❌ workflow.run() 执行失败: {context_error}")
                import traceback
                logger.error(traceback.format_exc())
                # 尝试获取详细的错误信息
                logger.error(f"错误类型: {type(context_error).__name__}")
                logger.error(f"错误详情: {str(context_error)}")
                
                # 检查是否是 context manager 错误
                if "context manager" in str(context_error).lower():
                    logger.error("⚠️ 检测到 context manager 错误 - 可能是 MCP 工具连接问题")
                
                raise
            
            print(f">>> AFTER workflow.run(), got {len(workflow_events)} events")
            
            # 从事件流中提取 ChatMessage
            result_messages = []
            for event in workflow_events:
                # 查找 WorkflowOutputEvent，其 data 包含最终的 ChatMessage 列表
                if hasattr(event, '__class__') and 'WorkflowOutputEvent' in event.__class__.__name__:
                    if hasattr(event, 'data') and isinstance(event.data, list):
                        result_messages = event.data
                        print(f">>> Found WorkflowOutputEvent with {len(result_messages)} ChatMessages")
                        break
            
            if not result_messages:
                logger.warning("未从工作流事件中找到 WorkflowOutputEvent，尝试提取 AgentRunEvent")
                # 备选：从 AgentRunEvent 中提取
                for event in workflow_events:
                    if hasattr(event, '__class__') and 'AgentRunEvent' in event.__class__.__name__:
                        if hasattr(event, 'data'):
                            print(f">>> Found AgentRunEvent from {event.executor_id}: {str(event.data)[:200]}")
            
            print(f">>> Extracted {len(result_messages)} ChatMessages from events")
            
            execution_time = time.time() - start_time
            logger.info(f"工作流执行完成，耗时: {execution_time:.2f}秒")
            logger.info(f"返回了 {len(result_messages)} 条消息")
            
            # 调试：打印所有消息的角色和前100字符
            print("\n" + "="*80)
            print(f"DEBUG: Workflow returned {len(result_messages)} messages")
            print("="*80)
            for i, msg in enumerate(result_messages):
                role = msg.role.value if hasattr(msg, 'role') else 'unknown'
                text = (msg.text if hasattr(msg, 'text') else str(msg))
                print(f"\n>>> MESSAGE {i+1}: role={role}, length={len(text)}")
                print(f"Content preview: {text[:300]}")
                print("-" * 80)
                logger.info(f"  消息 {i+1}: {role} - {text[:100]}...")
            
            # 解析结果（从最后一条助手消息中提取 JSON）
            final_content = self._extract_final_content(result_messages)
            
            # 发布内容（如果启用 dry-run）
            published_paths = None
            if self.workflow_config.dry_run and final_content:
                # TODO: 修复 publisher 接口后再启用
                logger.info(f"✅ 内容生成成功，包含平台: {final_content.platforms()}")
                # published_paths = await self._publish_contents(final_content)
            
            return WorkflowResult(
                success=True,
                contents=final_content,
                published_paths=published_paths,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"工作流执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return WorkflowResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
        finally:
            # 确保清理资源
            logger.info("执行工作流清理...")
            await self.cleanup()
    
    def _extract_final_content(self, messages: list) -> Optional[dict]:
        """从消息列表中提取最终的内容 JSON"""
        import json
        import re
        
        logger.info(f"开始从 {len(messages)} 条消息中提取内容...")
        
        for i, msg in enumerate(reversed(messages)):
            if hasattr(msg, 'role') and msg.role.value == 'assistant':
                # 尝试从 msg.text 或转换为字符串
                if hasattr(msg, 'text') and msg.text:
                    text = msg.text
                else:
                    text = str(msg)
                
                logger.info(f"检查第 {i+1} 条助手消息（长度: {len(text)}）")
                
                # 尝试多种 JSON 提取模式
                patterns = [
                    r'```json\s*(\{[\s\S]*?\})\s*```',  # 标准 json 代码块
                    r'```\s*(\{[\s\S]*?\})\s*```',      # 无 json 标记的代码块
                    r'(\{[\s\S]*?"bilibili"[\s\S]*?\})',  # 直接查找包含 bilibili 的 JSON
                ]
                
                for pattern in patterns:
                    json_match = re.search(pattern, text)
                    if json_match:
                        logger.info(f"找到JSON匹配")
                        try:
                            json_str = json_match.group(1)
                            logger.info(f"JSON字符串长度: {len(json_str)}")
                            content_dict = json.loads(json_str)
                            logger.info(f"成功解析JSON，包含键: {list(content_dict.keys())}")
                            
                            # 创建 PlatformContent 容器
                            platform_content = PlatformContent()
                            for platform, data in content_dict.items():
                                if platform in self.workflow_config.enabled_platforms:
                                    # 使用 .set() 方法添加平台内容
                                    platform_content.set(platform, {
                                        'title': data.get('title', ''),
                                        'content': data.get('content', ''),
                                        'summary': data.get('summary', ''),
                                        'metadata': data.get('metadata', {})
                                    })
                                    logger.info(f"✅ 提取了 {platform} 平台内容")
                            
                            if platform_content.platforms():
                                return platform_content
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON解析失败: {e}")
                            continue
                
                # 如果没找到JSON，打印消息预览帮助调试
                if len(text) > 0:
                    logger.warning(f"未找到有效JSON，消息预览: {text[:500]}...")
        
        logger.error("❌ 所有消息中都未找到有效的内容JSON")
        return None
    
    async def _publish_contents(self, platform_content: PlatformContent) -> dict[str, str]:
        """发布内容到各平台"""
        published_paths = {}
        platforms = platform_content.platforms()
        
        publishers = get_publishers(
            enabled_platforms=platforms,
            dry_run=self.workflow_config.dry_run
        )
        
        for platform in platforms:
            if platform in publishers:
                content_data = platform_content.get(platform)
                if content_data:
                    publisher = publishers[platform]
                    result = await publisher.publish(content_data)
                    if result.success:
                        published_paths[platform] = result.file_path or ""
                        logger.info(f"✅ {platform} 内容已导出: {result.file_path}")
                    else:
                        logger.error(f"❌ {platform} 导出失败: {result.error}")
        
        return published_paths
