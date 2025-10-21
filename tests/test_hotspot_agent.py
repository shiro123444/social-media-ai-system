"""
测试热点获取智能体功能
测试 RSS 新闻源获取、热度验证、详细内容获取
"""
import asyncio
import logging
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from utils.deepseek_adapter import create_deepseek_client
from agents.hotspot_agent import (
    create_hotspot_agent_async,
    Hotspot,
    parse_hotspot_response,
    filter_hotspots_by_heat,
    sort_hotspots_by_heat,
    export_hotspots_to_json
)
from config.mcp_config_manager import MCPConfigManager

load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResult:
    """测试结果记录"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.message = ""
        self.details = {}
        self.start_time = datetime.now()
        self.end_time = None
    
    def mark_passed(self, message: str = "", details: dict = None):
        self.passed = True
        self.message = message
        self.details = details or {}
        self.end_time = datetime.now()
    
    def mark_failed(self, message: str, details: dict = None):
        self.passed = False
        self.message = message
        self.details = details or {}
        self.end_time = datetime.now()
    
    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
    
    def to_dict(self):
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "duration_seconds": self.duration()
        }


async def test_rss_feed_retrieval(agent) -> TestResult:
    """
    测试 1: RSS 新闻源获取
    验证智能体能否成功从 RSS 源获取新闻
    """
    result = TestResult("RSS 新闻源获取测试")
    
    try:
        logger.info("\n" + "="*70)
        logger.info("测试 1: RSS 新闻源获取")
        logger.info("="*70)
        
        # 使用可靠的 RSS 源
        test_rss_url = "https://justlovemaki.github.io/CloudFlare-AI-Insight-Daily/rss.xml"
        
        query = f"""请使用 RSS Reader 工具从以下 RSS 源获取最新的 5 条新闻：

RSS 源: {test_rss_url}

要求：
1. 使用 fetch_feed_entries 工具
2. 获取最新的 5 条新闻
3. 对于每条新闻，返回以下完整信息：
   - 标题 (title)
   - 发布时间 (published)
   - 摘要/描述 (description/summary)
   - 链接 (link/url)
4. 不要编造内容，只返回工具实际获取的数据
5. 以清晰的格式展示每条新闻的所有字段

请开始执行。"""
        
        logger.info(f"查询: {query[:200]}...")
        
        # 执行查询（设置超时）
        response = await asyncio.wait_for(agent.run(query), timeout=60)
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        logger.info(f"响应长度: {len(response_text)} 字符")
        
        # 验证响应
        if not response_text or len(response_text) < 50:
            result.mark_failed("响应内容过短或为空", {
                "response_length": len(response_text)
            })
            return result
        
        # 检查是否包含新闻相关内容
        keywords = ["标题", "title", "新闻", "news", "文章", "article"]
        has_content = any(keyword in response_text.lower() for keyword in keywords)
        
        if not has_content:
            result.mark_failed("响应中未找到新闻相关内容", {
                "response_preview": response_text[:500]
            })
            return result
        
        result.mark_passed("成功从 RSS 源获取新闻", {
            "rss_url": test_rss_url,
            "response_length": len(response_text),
            "response_preview": response_text[:500]
        })
        
        logger.info("✅ RSS 新闻源获取测试通过")
        
    except asyncio.TimeoutError:
        result.mark_failed("测试超时（60秒）")
        logger.error("❌ RSS 新闻源获取测试超时")
    except Exception as e:
        result.mark_failed(f"测试异常: {str(e)}")
        logger.error(f"❌ RSS 新闻源获取测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return result


async def test_heat_validation(agent) -> TestResult:
    """
    测试 2: 热度验证
    验证智能体能否使用 Exa Search 验证话题热度
    """
    result = TestResult("热度验证测试")
    
    try:
        logger.info("\n" + "="*70)
        logger.info("测试 2: 热度验证")
        logger.info("="*70)
        
        query = """请使用 Exa Search 工具搜索以下话题的相关内容，并评估其热度：

话题: "人工智能"

要求：
1. 使用 exa_web_search 工具搜索相关内容
2. 获取至少 5 条搜索结果
3. 根据搜索结果评估话题热度（0-100）
4. 说明热度评分的依据

请开始执行。"""
        
        logger.info("查询: 搜索'人工智能'话题并评估热度")
        
        # 执行查询（Exa Search 可能需要更长时间）
        response = await asyncio.wait_for(agent.run(query), timeout=120)
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        logger.info(f"响应长度: {len(response_text)} 字符")
        
        # 验证响应
        if not response_text or len(response_text) < 50:
            result.mark_failed("响应内容过短或为空")
            return result
        
        # 检查是否包含热度相关内容
        heat_keywords = ["热度", "heat", "评分", "score", "指数", "index"]
        has_heat_info = any(keyword in response_text.lower() for keyword in heat_keywords)
        
        if not has_heat_info:
            result.mark_failed("响应中未找到热度评估信息", {
                "response_preview": response_text[:500]
            })
            return result
        
        result.mark_passed("成功验证话题热度", {
            "topic": "人工智能",
            "response_length": len(response_text),
            "response_preview": response_text[:500]
        })
        
        logger.info("✅ 热度验证测试通过")
        
    except asyncio.TimeoutError:
        result.mark_failed("测试超时（120秒）- Exa Search 可能响应较慢")
        logger.error("❌ 热度验证测试超时")
    except Exception as e:
        result.mark_failed(f"测试异常: {str(e)}")
        logger.error(f"❌ 热度验证测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return result


async def test_detailed_content_retrieval(agent) -> TestResult:
    """
    测试 3: 详细内容获取
    验证智能体能否使用 Fetch 工具获取网页详细内容
    """
    result = TestResult("详细内容获取测试")
    
    try:
        logger.info("\n" + "="*70)
        logger.info("测试 3: 详细内容获取")
        logger.info("="*70)
        
        # 使用一个稳定的测试 URL
        test_url = "https://example.com"
        
        query = f"""请使用 Fetch 工具获取以下网页的内容：

URL: {test_url}

要求：
1. 使用 fetch 工具获取网页内容
2. 提取网页的主要文本内容
3. 总结网页的核心信息

请开始执行。"""
        
        logger.info(f"查询: 获取 {test_url} 的详细内容")
        
        # 执行查询
        response = await asyncio.wait_for(agent.run(query), timeout=60)
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        logger.info(f"响应长度: {len(response_text)} 字符")
        
        # 验证响应
        if not response_text or len(response_text) < 50:
            result.mark_failed("响应内容过短或为空")
            return result
        
        # 检查是否包含内容相关信息
        content_keywords = ["内容", "content", "文本", "text", "信息", "information"]
        has_content = any(keyword in response_text.lower() for keyword in content_keywords)
        
        if not has_content:
            result.mark_failed("响应中未找到内容信息", {
                "response_preview": response_text[:500]
            })
            return result
        
        result.mark_passed("成功获取网页详细内容", {
            "url": test_url,
            "response_length": len(response_text),
            "response_preview": response_text[:500]
        })
        
        logger.info("✅ 详细内容获取测试通过")
        
    except asyncio.TimeoutError:
        result.mark_failed("测试超时（60秒）")
        logger.error("❌ 详细内容获取测试超时")
    except Exception as e:
        result.mark_failed(f"测试异常: {str(e)}")
        logger.error(f"❌ 详细内容获取测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return result


async def test_hotspot_data_model():
    """
    测试 4: 热点数据模型
    验证 Hotspot 数据模型的功能
    """
    result = TestResult("热点数据模型测试")
    
    try:
        logger.info("\n" + "="*70)
        logger.info("测试 4: 热点数据模型")
        logger.info("="*70)
        
        # 创建测试数据
        hotspot = Hotspot(
            title="测试热点",
            source="测试来源",
            heat_index=85,
            summary="这是一个测试热点的摘要",
            url="https://example.com/test",
            keywords=["测试", "热点", "AI"],
            category="科技"
        )
        
        # 测试验证
        is_valid, error_msg = hotspot.validate()
        if not is_valid:
            result.mark_failed(f"数据验证失败: {error_msg}")
            return result
        
        # 测试序列化
        hotspot_dict = hotspot.to_dict()
        hotspot_json = hotspot.to_json()
        
        # 测试反序列化
        hotspot_from_dict = Hotspot.from_dict(hotspot_dict)
        
        # 验证反序列化结果
        if hotspot_from_dict.title != hotspot.title:
            result.mark_failed("反序列化后数据不一致")
            return result
        
        result.mark_passed("热点数据模型功能正常", {
            "hotspot_dict": hotspot_dict,
            "json_length": len(hotspot_json)
        })
        
        logger.info("✅ 热点数据模型测试通过")
        
    except Exception as e:
        result.mark_failed(f"测试异常: {str(e)}")
        logger.error(f"❌ 热点数据模型测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return result


async def test_hotspot_utilities():
    """
    测试 5: 热点工具函数
    验证过滤、排序、导出等工具函数
    """
    result = TestResult("热点工具函数测试")
    
    try:
        logger.info("\n" + "="*70)
        logger.info("测试 5: 热点工具函数")
        logger.info("="*70)
        
        # 创建测试数据
        hotspots = [
            Hotspot(
                title="高热度话题",
                source="来源A",
                heat_index=90,
                summary="高热度摘要",
                url="https://example.com/1",
                category="科技"
            ),
            Hotspot(
                title="中热度话题",
                source="来源B",
                heat_index=60,
                summary="中热度摘要",
                url="https://example.com/2",
                category="财经"
            ),
            Hotspot(
                title="低热度话题",
                source="来源C",
                heat_index=30,
                summary="低热度摘要",
                url="https://example.com/3",
                category="科技"
            )
        ]
        
        # 测试过滤
        filtered = filter_hotspots_by_heat(hotspots, min_heat=50)
        if len(filtered) != 2:
            result.mark_failed(f"过滤结果错误: 期望2个，实际{len(filtered)}个")
            return result
        
        # 测试排序
        sorted_hotspots = sort_hotspots_by_heat(hotspots, descending=True)
        if sorted_hotspots[0].heat_index != 90:
            result.mark_failed("排序结果错误")
            return result
        
        # 测试导出
        output_path = Path("output/hotspots/test_export.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        export_hotspots_to_json(hotspots, str(output_path))
        
        if not output_path.exists():
            result.mark_failed("导出文件不存在")
            return result
        
        # 验证导出内容
        with open(output_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        if len(exported_data.get("hotspots", [])) != 3:
            result.mark_failed("导出数据不完整")
            return result
        
        result.mark_passed("热点工具函数正常", {
            "filtered_count": len(filtered),
            "sorted_first_heat": sorted_hotspots[0].heat_index,
            "export_path": str(output_path)
        })
        
        logger.info("✅ 热点工具函数测试通过")
        
    except Exception as e:
        result.mark_failed(f"测试异常: {str(e)}")
        logger.error(f"❌ 热点工具函数测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return result


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🧪 热点获取智能体测试套件")
    print("="*70)
    print("\n测试内容：")
    print("  1. RSS 新闻源获取")
    print("  2. 热度验证")
    print("  3. 详细内容获取")
    print("  4. 热点数据模型")
    print("  5. 热点工具函数")
    print("\n" + "="*70)
    
    results = []
    
    try:
        # 初始化 Agent（仅用于需要 Agent 的测试）
        logger.info("\n初始化测试环境...")
        chat_client = create_deepseek_client(debug=False)
        mcp_manager = MCPConfigManager("config/mcp_servers.json")
        tool_configs = mcp_manager.get_tool_configs_for_agent('hotspot')
        agent = await create_hotspot_agent_async(chat_client, tool_configs)
        logger.info("✅ 测试环境初始化完成\n")
        
        # 运行需要 Agent 的测试
        results.append(await test_rss_feed_retrieval(agent))
        results.append(await test_heat_validation(agent))
        results.append(await test_detailed_content_retrieval(agent))
        
    except Exception as e:
        logger.error(f"❌ 初始化测试环境失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # 运行不需要 Agent 的测试
    results.append(await test_hotspot_data_model())
    results.append(await test_hotspot_utilities())
    
    # 生成测试报告
    print("\n" + "="*70)
    print("📊 测试报告")
    print("="*70)
    
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    
    print(f"\n总测试数: {total_count}")
    print(f"通过: {passed_count}")
    print(f"失败: {total_count - passed_count}")
    print(f"通过率: {passed_count/total_count*100:.1f}%")
    
    print("\n详细结果：")
    print("-"*70)
    
    for i, result in enumerate(results, 1):
        status = "✅ 通过" if result.passed else "❌ 失败"
        print(f"\n{i}. {result.test_name}: {status}")
        print(f"   耗时: {result.duration():.2f}秒")
        print(f"   信息: {result.message}")
        
        if result.details:
            print(f"   详情:")
            for key, value in result.details.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"     - {key}: {value[:100]}...")
                else:
                    print(f"     - {key}: {value}")
    
    # 保存测试报告
    report_path = Path("output/hotspots/test_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "test_time": datetime.now().isoformat(),
        "total_tests": total_count,
        "passed": passed_count,
        "failed": total_count - passed_count,
        "pass_rate": passed_count/total_count*100,
        "results": [r.to_dict() for r in results]
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print(f"✅ 测试报告已保存: {report_path}")
    print("="*70)
    
    return passed_count == total_count


async def main():
    """主函数"""
    # 设置 Windows 控制台编码
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    success = await run_all_tests()
    
    if success:
        print("\n✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
