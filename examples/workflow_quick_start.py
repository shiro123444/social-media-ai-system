"""
工作流快速入门
最简单的三智能体协作示例
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()


async def quick_workflow():
    """快速运行工作流"""
    
    print("=" * 70)
    print("内容生产工作流 - 快速入门")
    print("=" * 70)
    
    # 第 1 步：检查环境变量
    print("\n[1/4] 检查环境变量...")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 错误: DEEPSEEK_API_KEY 环境变量未设置")
        print("   请在 .env 文件中添加:")
        print("   DEEPSEEK_API_KEY=your_api_key_here")
        return
    
    print(f"✅ API Key: {api_key[:10]}...")
    
    # 第 2 步：导入模块
    print("\n[2/4] 导入模块...")
    from agent_framework import WorkflowBuilder
    from agents import (
        create_hotspot_agent_async,
        create_analysis_agent_async,
        create_content_agent_async
    )
    from config.mcp_config_manager import MCPConfigManager
    from utils.deepseek_adapter import DeepSeekChatClient
    
    print("✅ 模块导入成功")
    
    # 第 3 步：创建智能体
    print("\n[3/4] 创建智能体...")
    
    # 创建客户端
    client = DeepSeekChatClient(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    
    # 加载配置
    config = MCPConfigManager()
    hotspot_tools = config.get_tool_configs_for_agent('hotspot')
    analysis_tools = config.get_tool_configs_for_agent('analysis')
    
    # 创建智能体
    hotspot_agent = await create_hotspot_agent_async(client, hotspot_tools)
    analysis_agent = await create_analysis_agent_async(client, analysis_tools)
    content_agent = await create_content_agent_async(client)
    
    print("✅ 智能体创建成功")
    print(f"   - 热点获取智能体: {hotspot_agent.name}")
    print(f"   - 内容分析智能体: {analysis_agent.name}")
    print(f"   - 内容生成智能体: {content_agent.name}")
    
    # 第 4 步：构建并运行工作流
    print("\n[4/4] 构建并运行工作流...")
    
    workflow = (WorkflowBuilder()
        .set_start_executor(hotspot_agent)
        .add_edge(hotspot_agent, analysis_agent)
        .add_edge(analysis_agent, content_agent)
        .build())
    
    print("✅ 工作流构建成功")
    print("   流程: 热点获取 -> 内容分析 -> 内容生成")
    
    # 运行工作流
    print("\n" + "=" * 70)
    print("开始执行工作流...")
    print("=" * 70)
    
    query = "获取最新的 AI 技术热点"
    print(f"\n查询: {query}\n")
    
    events = await workflow.run(query)
    
    # 显示结果
    print("\n" + "=" * 70)
    print("执行结果")
    print("=" * 70)
    
    from agent_framework import AgentRunEvent
    
    for event in events:
        if isinstance(event, AgentRunEvent):
            print(f"\n[{event.executor_id}]")
            print("-" * 70)
            result_str = str(event.data)
            if len(result_str) > 500:
                print(result_str[:500] + "...")
            else:
                print(result_str)
    
    print("\n" + "=" * 70)
    print(f"最终状态: {events.get_final_state()}")
    print("=" * 70)
    print("\n✅ 工作流执行完成！")


if __name__ == "__main__":
    asyncio.run(quick_workflow())
