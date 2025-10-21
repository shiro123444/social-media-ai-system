"""
多智能体工作流协调器 V2
优化版本：简化MCP工具，优化数据传递
"""
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any
from pathlib import Path

from agent_framework import WorkflowBuilder

from agents.hotspot_agent import create_hotspot_agent_async, Hotspot
from agents.analysis_agent import create_analysis_agent_async, AnalysisReport
from agents.content_agent import create_content_agent_async, Content
from config.workflow_config import get_workflow_config
from config.mcp_config_manager import MCPConfigManager

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    hotspot_id: str
    hotspots: list[Hotspot]
    analysis: Optional[AnalysisReport]
    contents: Optional[dict[str, Content]]
    execution_time: float
    timestamp: str
    success: bool
    error: Optional[str] = None
    published_paths: Optional[dict[str, str]] = None

    def to_dict(self):
        """转换为字典"""
        return {
            "hotspot_id": self.hotspot_id,
            "hotspots": [asdict(h) for h in self.hotspots] if self.hotspots else [],
            "analysis": asdict(self.analysis) if self.analysis else None,
            "contents": {k: asdict(v) for k, v in self.contents.items()} if self.contents else None,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
            "success": self.success,
            "error": self.error,
            "published_paths": self.published_paths or {}
        }


class MultiAgentCoordinatorV2:
    """多智能体工作流协调器 V2"""
    
    def __init__(self, client, config_manager: Optional[MCPConfigManager] = None):
        """
        初始化协调器
        
        Args:
            client: DeepSeek 聊天客户端
            config_manager: MCP 配置管理器
        """
        self.client = client
        self.config_manager = config_manager or MCPConfigManager()
        self.agents_initialized = False
        
    async def initialize_agents(self):
        """初始化所有智能体"""
        if self.agents_initialized:
            logger.info("智能体已初始化，跳过")
            return
            
        logger.info("=" * 80)
        logger.info("开始初始化工作流智能体...")
        logger.info("=" * 80)
        
        # 1. 热点获取智能体 - 使用 daily-hot-mcp
        logger.info("\n[1/3] 初始化热点获取智能体...")
        # get_tools_for_agent 返回 MCPServerConfig 对象列表
        tool_names = self.config_manager.AGENT_TOOLS_MAPPING.get("hotspot", [])
        hotspot_configs = [
            self.config_manager.get_server(name)
            for name in tool_names
            if self.config_manager.get_server(name) and self.config_manager.get_server(name).is_active
        ]
        logger.info(f"加载 {len(hotspot_configs)} 个 MCP 工具配置")
        
        self.hotspot_agent = await create_hotspot_agent_async(
            chat_client=self.client,
            mcp_tool_configs=hotspot_configs
        )
        logger.info("✅ 热点获取智能体初始化完成")
        
        # 2. 分析智能体 - 不使用 MCP 工具
        logger.info("\n[2/3] 初始化分析智能体...")
        self.analysis_agent = await create_analysis_agent_async(
            chat_client=self.client,
            mcp_tool_configs=[]  # 不使用 MCP 工具
        )
        logger.info("✅ 分析智能体初始化完成")
        
        # 3. 内容生成智能体 - 不使用 MCP 工具
        logger.info("\n[3/3] 初始化内容生成智能体...")
        self.content_agent = await create_content_agent_async(
            chat_client=self.client,
            mcp_tool_configs=[]  # 不使用 MCP 工具
        )
        logger.info("✅ 内容生成智能体初始化完成")
        
        self.agents_initialized = True
        logger.info("\n" + "=" * 80)
        logger.info("所有智能体初始化完成！")
        logger.info("=" * 80 + "\n")
    
    async def build_workflow(self, user_query: str):
        """
        构建工作流
        
        Args:
            user_query: 用户查询（例如："获取今天完整的B站热点，并且描述一下"）
            
        Returns:
            构建好的工作流
        """
        await self.initialize_agents()
        
        logger.info("构建工作流...")
        
        # 使用 Agent Framework 的工作流构建器（显式设置 Agent ID，便于事件识别）
        workflow = WorkflowBuilder()
        workflow.add_agent(self.hotspot_agent, id="hotspot", output_response=True)
        workflow.add_agent(self.analysis_agent, id="analysis", output_response=True)
        workflow.add_agent(self.content_agent, id="content", output_response=True)

        # 设置起始节点：热点获取智能体
        workflow.set_start_executor(self.hotspot_agent)
        
        # 添加边：热点 -> 分析
        workflow.add_edge(self.hotspot_agent, self.analysis_agent)
        
        # 添加边：分析 -> 内容生成
        workflow.add_edge(self.analysis_agent, self.content_agent)
        
        # 构建工作流
        built_workflow = workflow.build()
        
        logger.info("✅ 工作流构建完成")
        logger.info(f"   流程: Hotspot Agent → Analysis Agent → Content Agent")
        
        return built_workflow
    
    async def run_workflow(self, user_query: str, hotspot_id: Optional[str] = None) -> WorkflowResult:
        """
        执行工作流
        
        Args:
            user_query: 用户查询（例如："获取今天完整的B站热点，并且描述一下"）
            hotspot_id: 热点ID
            
        Returns:
            工作流执行结果
        """
        start_time = asyncio.get_event_loop().time()
        hotspot_id = hotspot_id or f"workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        logger.info("\n" + "=" * 80)
        logger.info(f"开始执行工作流: {hotspot_id}")
        logger.info(f"用户查询: {user_query}")
        logger.info("=" * 80 + "\n")
        
        try:
            # 构建工作流
            workflow = await self.build_workflow(user_query)
            
            # 执行工作流 - 直接传入用户查询
            logger.info(f"执行工作流，起始输入: {user_query}")
            result_events = await workflow.run(user_query)
            
            # 解析结果
            logger.info(f"工作流返回 {len(result_events)} 个事件")
            
            # 提取各个智能体的输出
            hotspots_data = None
            analysis_data = None
            content_data = None
            
            for event in result_events:
                # 检查是否是Agent运行事件（有executor_id和data属性）
                if hasattr(event, 'executor_id') and hasattr(event, 'data'):
                    executor_id = event.executor_id
                    response = event.data
                    
                    logger.info(f"处理事件: {executor_id}")
                    
                    # 提取文本内容
                    if hasattr(response, 'text'):
                        text_output = response.text
                    elif hasattr(response, 'data') and hasattr(response.data, 'text'):
                        text_output = response.data.text
                    else:
                        text_output = str(response)
                    
                    # 诊断日志：打印前200字符
                    preview = text_output[:200] if text_output else "(empty)"
                    logger.info(f"   响应预览 ({executor_id}): {preview}...")
                    
                    # 根据 executor_id 判断是哪个智能体的输出（兼容中英文与ID）
                    eid_lower = executor_id.lower() if isinstance(executor_id, str) else str(executor_id).lower()
                    if ("hotspot" in eid_lower) or ("热点" in str(executor_id)):
                        hotspots_data = text_output
                        logger.info(f"✅ 获取到热点数据 ({len(text_output)} 字符)")
                    elif ("analysis" in eid_lower) or ("分析" in str(executor_id)):
                        analysis_data = text_output
                        logger.info(f"✅ 获取到分析数据 ({len(text_output)} 字符)")
                    elif ("content" in eid_lower) or ("内容" in str(executor_id)):
                        content_data = text_output
                        logger.info(f"✅ 获取到内容数据 ({len(text_output)} 字符)")
            
            # 解析数据
            from agents.hotspot_agent import parse_hotspot_response
            from agents.analysis_agent import parse_analysis_response
            from agents.content_agent import parse_content_response
            
            hotspots = parse_hotspot_response(hotspots_data) if hotspots_data else []
            analysis = parse_analysis_response(analysis_data) if analysis_data else None
            contents = parse_content_response(content_data) if content_data else None
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            published_paths = {}
            # 发布（dry-run 或 API）
            try:
                if contents:
                    from utils.publishers.registry import get_publishers
                    cfg = get_workflow_config()
                    publishers = get_publishers(cfg.enabled_platforms, dry_run=cfg.dry_run)
                    for platform, content_obj in contents.items():
                        if platform not in publishers:
                            continue
                        pub = publishers[platform]
                        pub_result = pub.publish(hotspot_id, content_obj)
                        if pub_result.ok and pub_result.output_dir:
                            published_paths[platform] = pub_result.output_dir
                        else:
                            logger.warning(f"发布失败 {platform}: {pub_result.error}")
            except Exception as e:
                logger.error(f"发布阶段异常: {e}")

            result = WorkflowResult(
                hotspot_id=hotspot_id,
                hotspots=hotspots,
                analysis=analysis,
                contents=contents,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                success=True,
                published_paths=published_paths or None
            )
            
            logger.info("\n" + "=" * 80)
            logger.info(f"✅ 工作流执行成功: {hotspot_id}")
            logger.info(f"   执行时间: {execution_time:.2f}秒")
            logger.info(f"   热点数量: {len(hotspots)}")
            logger.info(f"   分析状态: {'完成' if analysis else '未完成'}")
            logger.info(f"   内容状态: {'完成' if contents else '未完成'}")
            logger.info("=" * 80 + "\n")
            
            return result
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = str(e)
            
            logger.error(f"❌ 工作流执行失败: {error_msg}", exc_info=True)
            
            return WorkflowResult(
                hotspot_id=hotspot_id,
                hotspots=[],
                analysis=None,
                contents=None,
                execution_time=execution_time,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=error_msg
            )


async def main():
    """主函数 - 示例用法"""
    from utils.deepseek_adapter import create_deepseek_client
    
    # 创建客户端
    client = create_deepseek_client()
    
    # 创建协调器
    coordinator = MultiAgentCoordinatorV2(client)
    
    # 用户查询示例
    user_query = "获取今天完整的B站热点，并且描述一下这些热点的特点和趋势"
    
    # 执行工作流
    result = await coordinator.run_workflow(user_query)
    
    # 打印结果（保持向后兼容）
    if result.success:
        print("\n工作流执行成功！")
        print(f"热点数量: {len(result.hotspots)}")
        if result.analysis:
            print(f"分析主题: {result.analysis.topic}")
        # 兼容旧字段
        if getattr(result, 'content', None):
            print(f"内容标题: {getattr(result.content, 'title', '')}")
        if getattr(result, 'contents', None):
            print(f"生成平台: {len(result.contents)}")
    else:
        print(f"\n工作流执行失败: {result.error}")


if __name__ == "__main__":
    asyncio.run(main())

