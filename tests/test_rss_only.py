"""
快速测试 RSS 新闻获取功能
"""
import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from utils.deepseek_adapter import create_deepseek_client
from agents.hotspot_agent import create_hotspot_agent_async
from config.mcp_config_manager import MCPConfigManager

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rss_detailed():
    """测试 RSS 获取完整新闻内容"""
    print("\n" + "="*70)
    print("🧪 测试 RSS 新闻获取（完整内容）")
    print("="*70)
    
    # 初始化
    chat_client = create_deepseek_client(debug=False)
    mcp_manager = MCPConfigManager("config/mcp_servers.json")
    tool_configs = mcp_manager.get_tool_configs_for_agent('hotspot')
    agent = await create_hotspot_agent_async(chat_client, tool_configs)
    
    # 测试查询
    test_rss_url = "https://justlovemaki.github.io/CloudFlare-AI-Insight-Daily/rss.xml"
    
    query = f"""请使用 RSS Reader 工具从以下 RSS 源获取最新的 3 条新闻：

RSS 源: {test_rss_url}

要求：
1. 使用 fetch_feed_entries 工具
2. 获取最新的 3 条新闻
3. 对于每条新闻，返回工具提供的所有字段信息，包括：
   - title（标题）
   - published（发布时间）
   - description 或 summary（摘要/描述）
   - link 或 url（链接）
   - 以及工具返回的任何其他字段
4. 不要编造内容，只返回工具实际获取的数据
5. 以清晰的格式展示每条新闻的所有字段

请开始执行。"""
    
    print("\n查询内容：")
    print(query)
    print("\n" + "="*70)
    print("⏳ 正在执行...\n")
    
    # 执行
    response = await asyncio.wait_for(agent.run(query), timeout=60)
    response_text = response.text if hasattr(response, 'text') else str(response)
    
    # 显示结果
    print("\n" + "="*70)
    print("📰 获取到的新闻内容：")
    print("="*70)
    print(response_text)
    print("\n" + "="*70)
    
    # 保存结果
    output_file = Path("output/hotspots/rss_test_detailed.txt")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(response_text)
    
    print(f"\n✅ 结果已保存到: {output_file}")


if __name__ == "__main__":
    # 设置 Windows 控制台编码
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    asyncio.run(test_rss_detailed())
