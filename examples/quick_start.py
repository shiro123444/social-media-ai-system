"""
快速入门 - 最简单的调用方式
只需要 3 步就能使用分析智能体！
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def quick_analyze():
    """3 步快速分析"""
    
    # 第 1 步：导入和初始化
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    from utils.deepseek_adapter import DeepSeekChatClient
    from config.mcp_config_manager import MCPConfigManager
    from agents.analysis_agent import create_analysis_agent_async, parse_analysis_response
    
    # 第 2 步：创建智能体
    client = DeepSeekChatClient(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL")
    )
    
    mcp_config = MCPConfigManager()
    tools = mcp_config.get_tool_configs_for_agent('analysis')
    
    agent = await create_analysis_agent_async(client, tools)
    print("✅ 智能体已就绪！")
    
    # 第 3 步：运行分析
    result = await agent.run("""
    请分析这个热点：
    
    标题：ChatGPT 发布多模态功能
    摘要：OpenAI 发布了 ChatGPT 的图像识别和语音对话功能，用户可以通过拍照或语音与 AI 交互。
    关键词：ChatGPT, 多模态, AI, 图像识别
    
    请提供完整的分析报告（JSON 格式）。
    """)
    
    # 解析结果
    if hasattr(result, 'messages') and result.messages:
        last_message = result.messages[-1]
        response = last_message.contents if hasattr(last_message, 'contents') else str(last_message)
    else:
        response = str(result)
    
    report = parse_analysis_response(response)
    
    if report:
        print("\n📊 分析完成！")
        print(f"关键词: {', '.join(report.keywords)}")
        print(f"情感: {report.sentiment}")
        print(f"趋势: {report.trend}")
        print(f"\n洞察:\n{report.insights}")
    else:
        print("\n原始响应:")
        print(response)


if __name__ == "__main__":
    asyncio.run(quick_analyze())
