"""
新媒体运营 AI 系统 - 简化演示版本
不需要 OpenAI API 密钥的基础演示
"""
import asyncio
from agent_framework.devui import serve
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient

def create_mock_agent():
    """创建模拟智能体用于演示"""
    
    # 模拟工具函数
    def get_hot_topics() -> str:
        """获取热点话题"""
        return """
        当前热点话题：
        1. 🔥 人工智能技术突破 - 热度指数: 95
        2. 🚗 新能源汽车发展 - 热度指数: 88  
        3. 📱 短视频创作趋势 - 热度指数: 82
        4. 💼 数字化转型案例 - 热度指数: 76
        5. 🌱 可持续发展理念 - 热度指数: 71
        """
    
    def generate_content(topic: str, platform: str = "微信公众号") -> str:
        """生成内容"""
        if platform == "微信公众号":
            return f"""
            📝 微信公众号文章方案：
            
            标题：《{topic}：深度解析与未来展望》
            
            大纲：
            1. 引言：{topic}的重要性
            2. 现状分析：市场趋势和数据
            3. 深度解读：技术原理和应用
            4. 未来展望：发展方向和机遇
            5. 结语：对读者的启发和建议
            
            预计字数：2000-2500字
            目标受众：科技爱好者、行业从业者
            """
        elif platform == "微博":
            return f"""
            📱 微博内容方案：
            
            #{topic}# 最新动态！🔥
            
            这个趋势值得关注 👀 
            ✨ 核心要点：[简要说明]
            📊 数据支撑：[关键数据]  
            🚀 未来影响：[发展预测]
            
            #热点追踪# #科技前沿# #行业洞察#
            """
        else:
            return f"为{platform}平台生成的{topic}相关内容"
    
    def analyze_style(content: str) -> str:
        """分析内容风格"""
        return """
        📊 内容风格分析报告：
        
        ✅ 语言风格：专业且易懂
        ✅ 目标受众：匹配度高
        ✅ 情感色彩：积极正面
        ✅ 传播潜力：预计较高
        
        💡 优化建议：
        - 增加互动元素（问答、投票）
        - 添加视觉化数据图表
        - 结合时事热点提升关注度
        """
    
    def suggest_images(topic: str) -> str:
        """建议配图"""
        return f"""
        🎨 {topic} 配图建议：
        
        🖼️ 主图：现代科技风格，蓝色调
        📊 图表：数据可视化，清晰易读
        🎯 图标：相关行业符号，简洁明了
        🌈 色彩：主色蓝色，辅色白色和灰色
        
        📐 尺寸建议：
        - 微信头图：900x500px
        - 微博配图：690x920px  
        - 小红书：1080x1080px
        """
    
    # 创建智能体（不需要真实的 OpenAI 客户端）
    try:
        # 尝试创建真实客户端
        chat_client = OpenAIChatClient()
    except:
        # 如果失败，使用 None（演示模式）
        chat_client = None
    
    agent = ChatAgent(
        name="新媒体运营 AI 助手 (演示版)",
        chat_client=chat_client,
        instructions="""
        🤖 我是新媒体运营 AI 助手！
        
        我可以帮助你：
        🔥 发现和分析热点话题
        ✍️ 生成多平台内容方案  
        🎨 提供视觉设计建议
        📊 分析内容风格和效果
        
        💡 试试这些命令：
        - "获取当前热点话题"
        - "为人工智能话题生成微信文章"
        - "分析这段内容的风格"
        - "推荐配图方案"
        
        注意：这是演示版本，部分功能为模拟数据。
        """,
        tools=[get_hot_topics, generate_content, analyze_style, suggest_images]
    )
    
    return agent

def main():
    """启动演示系统"""
    print("🎯 新媒体运营 AI 系统 - 演示版")
    print("=" * 40)
    print("📍 启动 DevUI 界面...")
    print("🌐 访问地址: http://localhost:8080")
    print("💡 在界面中输入问题，体验 AI 助手功能")
    print()
    print("🔧 演示功能：")
    print("- 热点话题分析")
    print("- 多平台内容生成")  
    print("- 内容风格分析")
    print("- 配图建议")
    print()
    
    # 创建演示智能体
    demo_agent = create_mock_agent()
    
    # 启动 DevUI
    serve(
        entities=[demo_agent],
        host="localhost", 
        port=8080,
        auto_open=True
    )

if __name__ == "__main__":
    main()