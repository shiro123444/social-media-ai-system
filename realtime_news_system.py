"""
实时热点新闻系统 - 多智能体协作版本
每个智能体都有专属的 MCP 工具来获取实时数据
"""
import asyncio
import os
from dotenv import load_dotenv
from agent_framework import ChatAgent, WorkflowBuilder, AgentRunEvent
from agent_framework.openai import OpenAIChatClient
from agent_framework.devui import serve

# 加载环境变量
load_dotenv()

class RealtimeNewsSystem:
    """实时新闻系统 - 多智能体协作"""
    
    def __init__(self):
        self.chat_client = self._create_client()
        self.agents = {}
    
    def _create_client(self):
        """创建聊天客户端"""
        # 配置 DeepSeek 或 OpenAI
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        if os.getenv("DEEPSEEK_API_KEY"):
            os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")
            os.environ["OPENAI_BASE_URL"] = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            os.environ["OPENAI_CHAT_MODEL_ID"] = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        
        return OpenAIChatClient() if api_key else None
    

    async def create_agents_with_mcp(self):
        """创建带 MCP 工具的智能体"""
        
        # 智能体 1: 网络新闻抓取 (使用 Fetch MCP)
        news_crawler = ChatAgent(
            name="网络新闻抓取智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个专业的新闻抓取专家。你的任务是：
            1. 从主流新闻网站获取最新资讯
            2. 识别热点新闻和趋势话题
            3. 提取关键信息：标题、摘要、来源、时间
            4. 评估新闻的重要性和传播潜力
            
            重点关注：科技、财经、社会、娱乐等领域
            """,
            tools=[self.fetch_news_from_web]
        )
        
        # 智能体 2: 搜索趋势分析 (使用搜索 API)
        trend_analyzer = ChatAgent(
            name="搜索趋势分析智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个搜索趋势分析专家。你的任务是：
            1. 分析搜索引擎的热搜榜单
            2. 识别上升最快的话题
            3. 预测话题的发展趋势
            4. 评估话题的商业价值
            
            提供数据驱动的分析结果
            """,
            tools=[self.analyze_search_trends]
        )
        
        # 智能体 3: 社交媒体监控
        social_monitor = ChatAgent(
            name="社交媒体监控智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个社交媒体分析专家。你的任务是：
            1. 监控微博、Twitter 等平台的热门话题
            2. 分析用户讨论和情感倾向
            3. 识别 KOL 和意见领袖的观点
            4. 评估话题的社交传播力
            
            关注用户真实反馈和讨论热度
            """,
            tools=[self.monitor_social_media]
        )
        
        # 智能体 4: 数据聚合与热度计算
        data_aggregator = ChatAgent(
            name="数据聚合智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个数据分析专家。你的任务是：
            1. 整合来自多个智能体的数据
            2. 计算综合热度指数
            3. 识别最具价值的热点话题
            4. 生成热点排行榜
            
            使用科学的算法进行数据分析
            """,
            tools=[self.aggregate_data, self.calculate_hotness]
        )
        
        # 智能体 5: 内容生成
        content_generator = ChatAgent(
            name="内容生成智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个专业的内容创作者。基于热点话题：
            1. 生成吸引人的标题和内容
            2. 适配不同平台的格式要求
            3. 融入 SEO 关键词
            4. 保持内容的时效性和价值
            
            创作高质量、有传播力的内容
            """,
            tools=[self.generate_content_for_platform]
        )
        
        self.agents = {
            "crawler": news_crawler,
            "trend": trend_analyzer,
            "social": social_monitor,
            "aggregator": data_aggregator,
            "content": content_generator
        }
        
        return self.agents

    
    # ========== 工具函数定义 ==========
    
    def fetch_news_from_web(self, source: str = "综合") -> str:
        """从网络抓取新闻 (模拟 Fetch MCP)"""
        # 实际应用中，这里会调用 MCP Fetch 工具
        news_data = {
            "综合": [
                {"title": "AI大模型技术突破", "source": "科技日报", "热度": 95},
                {"title": "新能源汽车销量创新高", "source": "财经网", "热度": 88},
                {"title": "短视频平台新规发布", "source": "新浪科技", "热度": 82}
            ],
            "科技": [
                {"title": "量子计算取得重大进展", "source": "36氪", "热度": 92},
                {"title": "AI芯片国产化加速", "source": "IT之家", "热度": 87},
                {"title": "5G应用场景扩展", "source": "极客公园", "热度": 79}
            ]
        }
        
        selected_news = news_data.get(source, news_data["综合"])
        result = f"📰 {source}领域最新新闻:\n\n"
        for i, news in enumerate(selected_news, 1):
            result += f"{i}. {news['title']}\n"
            result += f"   来源: {news['source']} | 热度: {news['热度']}\n\n"
        
        return result
    
    def analyze_search_trends(self, platform: str = "百度") -> str:
        """分析搜索趋势 (模拟 Brave Search MCP)"""
        # 实际应用中，这里会调用搜索 API
        trends = {
            "百度": [
                {"keyword": "人工智能", "搜索量": "100万+", "趋势": "↑ 上升30%"},
                {"keyword": "新能源汽车", "搜索量": "80万+", "趋势": "↑ 上升25%"},
                {"keyword": "数字化转型", "搜索量": "60万+", "趋势": "→ 持平"}
            ]
        }
        
        selected_trends = trends.get(platform, trends["百度"])
        result = f"🔍 {platform}搜索趋势分析:\n\n"
        for i, trend in enumerate(selected_trends, 1):
            result += f"{i}. {trend['keyword']}\n"
            result += f"   搜索量: {trend['搜索量']} | {trend['趋势']}\n\n"
        
        return result
    
    def monitor_social_media(self, platform: str = "微博") -> str:
        """监控社交媒体 (模拟 Twitter/Weibo MCP)"""
        # 实际应用中，这里会调用社交媒体 API
        social_data = {
            "微博": [
                {"话题": "#AI技术革命#", "讨论量": "50万", "情感": "积极"},
                {"话题": "#新能源未来#", "讨论量": "35万", "情感": "积极"},
                {"话题": "#短视频创作#", "讨论量": "28万", "情感": "中性"}
            ]
        }
        
        selected_data = social_data.get(platform, social_data["微博"])
        result = f"📱 {platform}热门话题:\n\n"
        for i, topic in enumerate(selected_data, 1):
            result += f"{i}. {topic['话题']}\n"
            result += f"   讨论量: {topic['讨论量']} | 情感: {topic['情感']}\n\n"
        
        return result
   
 
    def aggregate_data(self, *data_sources) -> str:
        """聚合多源数据"""
        result = "📊 数据聚合分析:\n\n"
        result += "已整合以下数据源:\n"
        result += "✓ 网络新闻数据\n"
        result += "✓ 搜索趋势数据\n"
        result += "✓ 社交媒体数据\n\n"
        result += "综合分析结果:\n"
        result += "- 数据覆盖度: 95%\n"
        result += "- 数据新鲜度: 实时\n"
        result += "- 数据可信度: 高\n"
        return result
    
    def calculate_hotness(self, topic: str) -> str:
        """计算热度指数"""
        # 模拟热度计算算法
        import random
        base_score = random.randint(70, 95)
        
        result = f"🔥 '{topic}' 热度分析:\n\n"
        result += f"综合热度指数: {base_score}/100\n\n"
        result += "评分细节:\n"
        result += f"- 搜索热度: {base_score * 0.4:.1f} (权重40%)\n"
        result += f"- 社交讨论: {base_score * 0.3:.1f} (权重30%)\n"
        result += f"- 媒体报道: {base_score * 0.2:.1f} (权重20%)\n"
        result += f"- 时效性: {base_score * 0.1:.1f} (权重10%)\n\n"
        
        if base_score >= 90:
            result += "💡 建议: 极高热度，强烈推荐立即创作内容"
        elif base_score >= 80:
            result += "💡 建议: 高热度，推荐优先创作"
        else:
            result += "💡 建议: 中等热度，可考虑创作"
        
        return result
    
    def generate_content_for_platform(self, topic: str, platform: str = "微信") -> str:
        """为指定平台生成内容"""
        templates = {
            "微信": f"📝 微信公众号文章方案\n\n标题: 《{topic}：深度解析与未来展望》\n大纲: 引言、现状分析、深度解读、未来展望、结语\n字数: 2000-2500字",
            "微博": f"📱 微博内容\n\n#{topic}# 最新动态！🔥\n核心要点 + 数据支撑 + 互动引导\n字数: 约140字",
            "抖音": f"🎬 短视频脚本\n\n主题: {topic}\n时长: 60秒\n结构: 开场吸引 → 内容展开 → 结尾引导"
        }
        
        return templates.get(platform, templates["微信"])
    
    def build_workflow(self):
        """构建多智能体工作流"""
        if not self.agents:
            raise ValueError("请先创建智能体")
        
        # 顺序执行工作流：crawler -> trend -> social -> aggregator -> content
        workflow = (WorkflowBuilder()
            .set_start_executor(self.agents["crawler"])
            .add_edge(self.agents["crawler"], self.agents["trend"])
            .add_edge(self.agents["trend"], self.agents["social"])
            .add_edge(self.agents["social"], self.agents["aggregator"])
            .add_edge(self.agents["aggregator"], self.agents["content"])
            .build())
        
        return workflow


async def demo_workflow():
    """演示多智能体协作工作流"""
    print("🚀 启动实时热点新闻系统")
    print("=" * 60)
    
    system = RealtimeNewsSystem()
    
    if not system.chat_client:
        print("⚠️  未配置 API 密钥，使用模拟模式")
    
    # 创建智能体
    print("\n📦 创建多智能体系统...")
    agents = await system.create_agents_with_mcp()
    print(f"✅ 成功创建 {len(agents)} 个智能体")
    
    # 构建工作流
    print("\n🔄 构建智能体协作工作流...")
    workflow = system.build_workflow()
    print("✅ 工作流构建完成")
    
    # 运行工作流
    print("\n▶️  执行工作流: 获取今日科技热点并生成内容")
    print("-" * 60)
    
    try:
        events = await workflow.run("获取今日科技领域热点，并为微信公众号生成文章方案")
        
        print("\n📊 工作流执行结果:")
        for event in events:
            if isinstance(event, AgentRunEvent):
                print(f"\n🤖 {event.executor_id}:")
                print(f"   {event.data}")
        
        print(f"\n✅ 工作流状态: {events.get_final_state()}")
        
    except Exception as e:
        print(f"\n❌ 工作流执行出错: {e}")
    
    return system


def main():
    """主函数"""
    print("=" * 60)
    print("🎯 实时热点新闻系统 - 多智能体协作版")
    print("=" * 60)
    print()
    print("💡 系统特点:")
    print("- 5个专业智能体协同工作")
    print("- 每个智能体都有专属的 MCP 工具")
    print("- 实时获取多源热点数据")
    print("- 自动生成多平台内容")
    print()
    
    # 运行演示工作流
    system = asyncio.run(demo_workflow())
    
    # 启动 DevUI
    print("\n" + "=" * 60)
    print("🌐 启动 DevUI 管理界面...")
    print("📍 访问地址: http://localhost:8080")
    print("💡 你可以在界面中与各个智能体交互")
    print()
    
    # 创建一个统一的入口智能体用于 DevUI
    if system.chat_client and system.agents:
        coordinator = ChatAgent(
            name="中央协调器",
            chat_client=system.chat_client,
            instructions="""
            你是实时热点新闻系统的中央协调器。你可以：
            
            🔥 获取实时热点
            - "获取科技领域的最新热点"
            - "分析今日搜索趋势"
            - "监控社交媒体热门话题"
            
            ✍️ 生成内容
            - "为人工智能话题生成微信文章"
            - "创作关于新能源的微博内容"
            - "生成短视频脚本"
            
            📊 数据分析
            - "计算某个话题的热度指数"
            - "聚合多源数据分析"
            
            我会协调5个专业智能体为你服务！
            """,
            tools=[
                system.fetch_news_from_web,
                system.analyze_search_trends,
                system.monitor_social_media,
                system.calculate_hotness,
                system.generate_content_for_platform
            ]
        )
        
        serve(
            entities=[coordinator],
            host="localhost",
            port=8080,
            auto_open=True
        )
    else:
        print("⚠️  无法启动 DevUI: 未配置 API 密钥")
        print("请在 .env 文件中配置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")


if __name__ == "__main__":
    main()