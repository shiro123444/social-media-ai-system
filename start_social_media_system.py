"""
新媒体运营 AI 系统 - DevUI 启动脚本
基于 Microsoft Agent Framework 构建的多智能体协作系统
"""
import asyncio
import os
from typing import List, Dict, Any
from datetime import datetime
from agent_framework import ChatAgent, WorkflowBuilder, AgentRunEvent
from agent_framework.openai import OpenAIChatClient
from agent_framework.devui import serve

# 设置环境变量 (请替换为你的实际 API 密钥)
os.environ.setdefault("OPENAI_API_KEY", "your-openai-api-key-here")

class SocialMediaAISystem:
    """新媒体运营 AI 系统主类"""
    
    def __init__(self):
        self.chat_client = OpenAIChatClient()
        self.agents = self._create_agents()
        self.workflow = self._build_workflow()
    
    def _create_agents(self) -> Dict[str, ChatAgent]:
        """创建所有智能体"""
        
        # 1. 热点抓取智能体
        hotspot_agent = ChatAgent(
            name="热点抓取智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个专业的热点信息分析师。你的任务是：
            1. 分析当前网络热点和趋势
            2. 评估热点的传播潜力和商业价值
            3. 提取关键词和相关话题
            4. 判断热点的适用平台和受众群体
            
            请以专业、客观的态度分析热点信息，并提供可操作的建议。
            """,
            tools=[self.get_trending_topics, self.analyze_hotspot_potential]
        )
        
        # 2. 内容生成智能体
        content_agent = ChatAgent(
            name="内容生成智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个专业的新媒体内容创作专家。根据热点信息和目标平台：
            1. 创作吸引人的标题和内容
            2. 适配不同平台的格式要求
            3. 融入 SEO 关键词和话题标签
            4. 保持内容的原创性和价值
            
            支持的平台：微信公众号、微博、抖音、小红书、B站
            """,
            tools=[self.generate_wechat_article, self.generate_weibo_post, 
                  self.generate_video_script]
        )
        
        # 3. 风格控制智能体
        style_agent = ChatAgent(
            name="风格控制智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个品牌内容风格顾问。你需要：
            1. 确保内容符合品牌调性和价值观
            2. 调整语言风格适应目标受众
            3. 过滤敏感或不当内容
            4. 优化内容的情感表达和传播效果
            
            始终保持专业、负责任的态度，确保内容质量。
            """,
            tools=[self.analyze_content_style, self.adjust_brand_tone]
        )
        
        # 4. 配图智能体
        image_agent = ChatAgent(
            name="配图智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个专业的视觉设计师。根据文字内容：
            1. 分析内容主题和情感色彩
            2. 设计合适的视觉元素和构图
            3. 生成详细的图片描述和关键词
            4. 确保视觉风格与品牌形象一致
            
            注重视觉冲击力和传播效果。
            """,
            tools=[self.generate_image_description, self.suggest_visual_elements]
        )
        
        # 5. 发布管理智能体
        publish_agent = ChatAgent(
            name="发布管理智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个专业的新媒体运营管理员。负责：
            1. 检查内容格式和平台适配性
            2. 安排最佳发布时间和策略
            3. 管理发布队列和优先级
            4. 监控发布状态和异常处理
            
            确保内容能够高效、准确地发布到各个平台。
            """,
            tools=[self.format_for_platform, self.schedule_publication]
        )
        
        # 6. 数据分析智能体
        analytics_agent = ChatAgent(
            name="数据分析智能体",
            chat_client=self.chat_client,
            instructions="""
            你是一个专业的数据分析师。你需要：
            1. 收集和分析各平台的内容表现数据
            2. 识别成功内容的特征和规律
            3. 提供数据驱动的优化建议
            4. 预测内容趋势和传播效果
            
            用数据说话，提供客观、准确的分析报告。
            """,
            tools=[self.collect_platform_metrics, self.analyze_content_performance]
        )
        
        return {
            "hotspot": hotspot_agent,
            "content": content_agent,
            "style": style_agent,
            "image": image_agent,
            "publish": publish_agent,
            "analytics": analytics_agent
        }
    
    def _build_workflow(self):
        """构建智能体工作流"""
        return (WorkflowBuilder()
            .set_start_executor(self.agents["hotspot"])
            .add_edge(self.agents["hotspot"], self.agents["content"])
            .add_edge(self.agents["content"], self.agents["style"])
            .add_edge(self.agents["style"], self.agents["image"])
            .add_edge(self.agents["image"], self.agents["publish"])
            .add_edge(self.agents["publish"], self.agents["analytics"])
            .build())
    
    # 工具函数定义
    def get_trending_topics(self, platform: str = "综合") -> str:
        """获取热点话题 (模拟数据)"""
        mock_topics = [
            "人工智能技术突破",
            "新能源汽车市场动态", 
            "短视频创作趋势",
            "数字化转型案例",
            "可持续发展理念"
        ]
        return f"当前{platform}平台热点：" + "、".join(mock_topics[:3])
    
    def analyze_hotspot_potential(self, topic: str) -> str:
        """分析热点潜力"""
        return f"热点'{topic}'分析：传播潜力高，适合多平台推广，建议重点关注年轻用户群体。"
    
    def generate_wechat_article(self, topic: str, style: str = "专业") -> str:
        """生成微信公众号文章"""
        return f"微信文章标题：《{topic}：深度解析与未来展望》\n内容概要：专业分析{topic}的发展趋势..."
    
    def generate_weibo_post(self, topic: str) -> str:
        """生成微博内容"""
        return f"微博内容：#{topic}# 最新动态！这个趋势值得关注 👀 [链接] #热点追踪#"
    
    def generate_video_script(self, topic: str) -> str:
        """生成视频脚本"""
        return f"视频脚本：开场白 - 大家好，今天聊聊{topic}... [详细分镜和文案]"
    
    def analyze_content_style(self, content: str) -> str:
        """分析内容风格"""
        return f"内容风格分析：语调专业，适合目标受众，建议增加互动元素。"
    
    def adjust_brand_tone(self, content: str, brand_style: str) -> str:
        """调整品牌调性"""
        return f"已根据{brand_style}风格调整内容，更符合品牌形象。"
    
    def generate_image_description(self, content: str) -> str:
        """生成图片描述"""
        return f"配图建议：现代简约风格，主色调蓝色，包含科技元素和数据可视化图表。"
    
    def suggest_visual_elements(self, theme: str) -> str:
        """建议视觉元素"""
        return f"视觉元素：图标、图表、背景纹理，整体风格现代专业。"
    
    def format_for_platform(self, content: str, platform: str) -> str:
        """格式化平台内容"""
        return f"已为{platform}平台格式化内容，符合平台规范。"
    
    def schedule_publication(self, content: str, time: str) -> str:
        """安排发布"""
        return f"已安排在{time}发布内容，预计覆盖用户数：10000+"
    
    def collect_platform_metrics(self, platform: str) -> str:
        """收集平台数据"""
        return f"{platform}平台数据：阅读量 5000+，点赞 200+，转发 50+"
    
    def analyze_content_performance(self, content_id: str) -> str:
        """分析内容表现"""
        return f"内容{content_id}表现良好，互动率 8.5%，建议复制成功要素。"
    
    async def run_complete_workflow(self, initial_prompt: str):
        """运行完整工作流"""
        print(f"🚀 启动新媒体运营 AI 系统")
        print(f"📝 输入任务: {initial_prompt}")
        print("=" * 60)
        
        events = await self.workflow.run(initial_prompt)
        
        print("\n📊 工作流执行结果:")
        for event in events:
            if isinstance(event, AgentRunEvent):
                print(f"🤖 {event.executor_id}: {event.data}")
        
        print(f"\n✅ 工作流状态: {events.get_final_state()}")
        return events.get_outputs()

def create_demo_system():
    """创建演示系统"""
    system = SocialMediaAISystem()
    
    # 创建一个简单的演示智能体用于 DevUI
    demo_agent = ChatAgent(
        name="新媒体运营 AI 助手",
        chat_client=OpenAIChatClient(),
        instructions="""
        你是一个新媒体运营 AI 助手，专门帮助用户：
        
        🔥 热点发现：分析当前网络热点和趋势
        ✍️ 内容创作：生成适合不同平台的优质内容  
        🎨 视觉设计：提供配图和视觉元素建议
        📱 平台管理：协助多平台内容发布和管理
        📊 数据分析：分析内容表现和优化建议
        
        请告诉我你想要做什么，我会为你提供专业的建议和帮助！
        
        示例问题：
        - "帮我分析一下人工智能相关的热点话题"
        - "为微信公众号写一篇关于数字化转型的文章"
        - "这个内容适合在哪些平台发布？"
        """,
        tools=[
            system.get_trending_topics,
            system.generate_wechat_article,
            system.generate_weibo_post,
            system.analyze_content_style
        ]
    )
    
    return demo_agent, system

async def main():
    """主函数"""
    print("🎯 新媒体运营 AI 系统")
    print("基于 Microsoft Agent Framework 构建")
    print("=" * 50)
    
    # 创建演示系统
    demo_agent, system = create_demo_system()
    
    # 可选：运行一个完整的工作流演示
    print("\n🔄 运行工作流演示...")
    try:
        results = await system.run_complete_workflow(
            "分析人工智能在新媒体运营中的应用趋势，并为微信公众号创作相关内容"
        )
        print(f"\n🎉 演示完成！生成了 {len(results)} 个输出结果")
    except Exception as e:
        print(f"⚠️ 演示运行需要有效的 OpenAI API 密钥: {e}")
    
    # 启动 DevUI
    print(f"\n🌐 启动 DevUI 界面...")
    print("📍 访问地址: http://localhost:8080")
    print("💡 你可以在界面中与智能体交互，测试各种功能")
    
    # 启动 DevUI 服务
    serve(
        entities=[demo_agent],
        host="localhost",
        port=8080,
        auto_open=True
    )

if __name__ == "__main__":
    asyncio.run(main())