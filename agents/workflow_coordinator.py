"""
多智能体工作流协调器
基于微软 Agent Framework 实现三个智能体的协调工作
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from agent_framework import WorkflowBuilder, ChatAgent, WorkflowEvent, AgentRunEvent
from config.mcp_config_manager import MCPConfigManager

from .hotspot_agent import create_hotspot_agent, Hotspot, parse_hotspot_response
from .analysis_agent import create_analysis_agent, AnalysisReport, parse_analysis_response
from .content_agent import create_content_agent, Content, parse_content_response
from utils.workflow_monitor import get_monitor

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    hotspot_id: str
    hotspots: List[Hotspot] = field(default_factory=list)
    analysis: Optional[AnalysisReport] = None
    contents: Dict[str, Content] = field(default_factory=dict)
    status: str = "pending"  # pending/running/completed/failed
    errors: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hotspot_id": self.hotspot_id,
            "status": self.status,
            "hotspots_count": len(self.hotspots) if self.hotspots else 0,
            "has_analysis": self.analysis is not None,
            "platforms_count": len(self.contents),
            "errors": self.errors,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp
        }


class MultiAgentCoordinator:
    """
    多智能体协调器
    使用微软 Agent Framework 的 WorkflowBuilder 来协调三个智能体的执行流程
    """

    def __init__(self, chat_client, mcp_tool_configs: List):
        """
        初始化协调器

        Args:
            chat_client: 聊天客户端（DeepSeek适配器）
            mcp_tool_configs: MCP工具配置列表
        """
        self.chat_client = chat_client
        self.mcp_tool_configs = mcp_tool_configs
        self.agents = {}
        self.workflow = None

    async def initialize_agents(self):
        """异步初始化所有智能体"""
        logger.info("开始初始化多智能体系统...")

        try:
            # 使用配置管理器为不同智能体挑选对应的 MCP 工具
            mcp_manager = MCPConfigManager()
            hotspot_tool_configs = mcp_manager.get_tool_configs_for_agent('hotspot')
            analysis_tool_configs = mcp_manager.get_tool_configs_for_agent('analysis')
            content_tool_configs = mcp_manager.get_tool_configs_for_agent('content')

            # 1. 创建热点获取智能体
            logger.info("正在创建热点获取智能体...")
            self.agents["hotspot"] = await create_hotspot_agent(
                self.chat_client, hotspot_tool_configs
            )

            # 2. 创建内容分析智能体
            logger.info("正在创建内容分析智能体...")
            self.agents["analysis"] = await create_analysis_agent(
                self.chat_client, analysis_tool_configs
            )

            # 3. 创建内容生成智能体
            logger.info("正在创建内容生成智能体...")
            self.agents["content"] = await create_content_agent(
                self.chat_client, content_tool_configs
            )

            logger.info(f"✅ 成功初始化 {len(self.agents)} 个智能体")
            for name, agent in self.agents.items():
                logger.info(f"  - {name}: {agent.name}")

        except Exception as e:
            logger.error(f"❌ 初始化智能体失败: {e}")
            raise

    def build_workflow(self):
        """构建工作流：热点获取 -> 内容分析 -> 内容生成"""
        logger.info("构建多智能体工作流...")

        # 获取智能体实例
        hotspot_agent = self.agents["hotspot"]
        analysis_agent = self.agents["analysis"]
        content_agent = self.agents["content"]

        # 使用 WorkflowBuilder 构建顺序执行的工作流
        workflow_builder = WorkflowBuilder()

        # 定义执行顺序：热点获取 -> 内容分析 -> 内容生成
        workflow_builder.set_start_executor(hotspot_agent)
        workflow_builder.add_edge(hotspot_agent, analysis_agent)
        workflow_builder.add_edge(analysis_agent, content_agent)

        # 构建工作流
        self.workflow = workflow_builder.build()

        logger.info("✅ 工作流构建完成")
        logger.info("执行顺序: 热点获取 -> 内容分析 -> 内容生成")

    async def execute_workflow(self, hotspot_id: str) -> WorkflowResult:
        """
        执行完整工作流

        Args:
            hotspot_id: 热点ID

        Returns:
            WorkflowResult: 工作流执行结果
        """
        monitor = get_monitor()

        # 开始监控
        monitor.start_workflow(hotspot_id)

        result = WorkflowResult(hotspot_id=hotspot_id, status="running")
        start_time = datetime.now()

        try:
            logger.info(f"开始执行工作流: {hotspot_id}")

            # 构建输入消息
            input_message = f"""
请执行完整的热点到内容生成工作流，热点ID: {hotspot_id}

工作流程：
1. 热点获取智能体：获取最新的热点资讯
2. 内容分析智能体：对热点进行深度分析
3. 内容生成智能体：生成多平台适配的内容

请确保每个步骤都严格按照智能体的指令执行，返回标准格式的JSON结果。
"""

            # 执行工作流
            logger.info("执行工作流...")
            workflow_events = await self.workflow.run(input_message)

            # 解析结果
            result = await self._parse_workflow_results(workflow_events, hotspot_id)

            # 计算执行时间
            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()
            result.status = "completed"

            logger.info(f"工作流 {hotspot_id} 执行完成，耗时: {result.execution_time:.2f}秒")
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            result.status = "failed"
            result.errors.append(str(e))

            # 计算执行时间（即使失败也要记录）
            end_time = datetime.now()
            result.execution_time = (end_time - start_time).total_seconds()

        # 完成监控
        monitor.complete_workflow(result)

        return result

    async def _parse_workflow_results(self, events, hotspot_id: str) -> WorkflowResult:
        """解析工作流执行结果"""
        result = WorkflowResult(hotspot_id=hotspot_id)

        try:
            # 从事件中提取每个智能体的输出
            agent_outputs = {}

            for event in events:
                if isinstance(event, AgentRunEvent):
                    agent_name = event.executor_id
                    output = event.data

                    logger.info(f"解析 {agent_name} 的输出...")
                    # 如果是 AgentRunResponse 对象，提取 text 属性
                    if hasattr(output, 'text'):
                        agent_outputs[agent_name] = output.text
                    elif isinstance(output, str):
                        agent_outputs[agent_name] = output
                    else:
                        # 尝试转换为字符串
                        agent_outputs[agent_name] = str(output)

            # 解析热点获取结果
            if "热点获取智能体" in agent_outputs:
                hotspots = parse_hotspot_response(agent_outputs["热点获取智能体"])
                result.hotspots = hotspots
                logger.info(f"解析到 {len(hotspots)} 个热点")

            # 解析内容分析结果
            if "内容分析智能体" in agent_outputs:
                analysis = parse_analysis_response(agent_outputs["内容分析智能体"])
                result.analysis = analysis
                if analysis:
                    logger.info(f"解析到分析报告: {analysis.hotspot_id}")

            # 解析内容生成结果
            if "内容生成智能体" in agent_outputs:
                contents = parse_content_response(agent_outputs["内容生成智能体"])
                result.contents = contents
                logger.info(f"解析到 {len(contents)} 个平台的内容")

        except Exception as e:
            logger.error(f"解析工作流结果失败: {e}")
            result.errors.append(f"结果解析失败: {str(e)}")

        return result

    async def execute_parallel_workflow(self, hotspot_ids: List[str]) -> Dict[str, WorkflowResult]:
        """
        并行执行多个工作流

        Args:
            hotspot_ids: 热点ID列表

        Returns:
            多个工作流的结果字典
        """
        logger.info(f"开始并行执行 {len(hotspot_ids)} 个工作流")

        # 创建并行任务
        tasks = []
        for hotspot_id in hotspot_ids:
            task = self.execute_workflow(hotspot_id)
            tasks.append(task)

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        workflow_results = {}
        for i, result in enumerate(results):
            hotspot_id = hotspot_ids[i]
            if isinstance(result, Exception):
                logger.error(f"工作流 {hotspot_id} 执行异常: {result}")
                workflow_results[hotspot_id] = WorkflowResult(
                    hotspot_id=hotspot_id,
                    status="failed",
                    errors=[str(result)]
                )
            else:
                workflow_results[hotspot_id] = result

        logger.info(f"并行执行完成，共 {len(workflow_results)} 个结果")
        return workflow_results

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态信息"""
        return {
            "agents_initialized": len(self.agents) == 3,
            "workflow_built": self.workflow is not None,
            "agent_names": list(self.agents.keys()) if self.agents else [],
            "timestamp": datetime.now().isoformat()
        }


async def create_multi_agent_coordinator(chat_client, mcp_tool_configs: List) -> MultiAgentCoordinator:
    """
    创建多智能体协调器

    Args:
        chat_client: 聊天客户端
        mcp_tool_configs: MCP工具配置

    Returns:
        MultiAgentCoordinator: 协调器实例
    """
    coordinator = MultiAgentCoordinator(chat_client, mcp_tool_configs)

    # 初始化智能体
    await coordinator.initialize_agents()

    # 构建工作流
    coordinator.build_workflow()

    logger.info("✅ 多智能体协调器创建完成")
    return coordinator


def create_coordinator(chat_client, mcp_tool_configs: List) -> MultiAgentCoordinator:
    """
    同步创建协调器（包装器）

    Args:
        chat_client: 聊天客户端
        mcp_tool_configs: MCP工具配置

    Returns:
        MultiAgentCoordinator: 协调器实例
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        # 如果已经在 event loop 中，返回 coroutine
        logger.warning("检测到运行中的 event loop，返回 coroutine")
        return create_multi_agent_coordinator(chat_client, mcp_tool_configs)
    except RuntimeError:
        # 创建新的 event loop
        return asyncio.run(create_multi_agent_coordinator(chat_client, mcp_tool_configs))


# 便捷函数
async def run_social_media_workflow(chat_client, mcp_tool_configs: List, hotspot_id: str) -> WorkflowResult:
    """
    运行完整的社交媒体工作流

    Args:
        chat_client: 聊天客户端
        mcp_tool_configs: MCP工具配置
        hotspot_id: 热点ID

    Returns:
        WorkflowResult: 工作流结果
    """
    coordinator = await create_multi_agent_coordinator(chat_client, mcp_tool_configs)
    return await coordinator.execute_workflow(hotspot_id)


def run_workflow(chat_client, mcp_tool_configs: List, hotspot_id: str) -> WorkflowResult:
    """
    同步运行工作流（包装器）

    Args:
        chat_client: 聊天客户端
        mcp_tool_configs: MCP工具配置
        hotspot_id: 热点ID

    Returns:
        WorkflowResult: 工作流结果
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        return run_social_media_workflow(chat_client, mcp_tool_configs, hotspot_id)
    except RuntimeError:
        return asyncio.run(run_social_media_workflow(chat_client, mcp_tool_configs, hotspot_id))
