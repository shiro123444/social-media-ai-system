"""
新媒体运营 AI 系统 - DeepSeek 版本
使用 DeepSeek API 的完整功能演示
"""
import asyncio
import os
from dotenv import load_dotenv
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from agent_framework.devui import serve

# 加载环境变量
load_dotenv()

def create_deepseek_client():
    """创建 DeepSeek 客户端"""
    # DeepSeek API 兼容 OpenAI 接口
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    if not api_key:
        print("⚠️  警告: 未设置 DEEPSEEK_API_KEY")
        print("请在 .env 文件中设置:")
        print("DEEPSEEK_API_KEY=your_api_key_here")
        print("DEEPSEEK_BASE_URL=https://api.deepseek.com")
        print("DEEPSEEK_MODEL=deepseek-chat")
        print()
        return None
    
    # 使用 OpenAIChatClient，但配置为 DeepSeek 的端点
    client = OpenAIChatClient(
        model=model,
        api_key=api_key,
        base_url=base_url
    )
    
    print(f"✅ 成功连接到 DeepSeek API")
    print(f"📍 Base URL: {base_url}")
    print(f"🤖 Model: {model}")
    print()
    
    return client

def create_social_media_agent(chat_client):
    """创建新媒体运营智能体"""
    
    # 工具函数定义
    def get_hot_topics(platform: str = "综合") -> str:
        """获取热点话题"""
        topics = {
            "综合": ["人工智能技术突破", "新能源汽车发展", "短视频创作趋势"],
            "科技": ["AI大模型应用", "量子计算进展", "芯片技术创新"],
            "财经": ["数字货币监管", "新能源投资", "消费市场复苏"],
            "娱乐": ["热门影视剧", "明星动态", "综艺节目"]
        }
        
        selected_topics = topics.get(platform, topics["综合"])
        return f"""
🔥 {platform}平台当前热点话题：

1. {selected_topics[0]} - 热度指数: 95
   关键词: AI, 技术创新, 应用场景
   
2. {selected_topics[1]} - 热度指数: 88
   关键词: 绿色能源, 市场趋势, 政策支持
   
3. {selected_topics[2]} - 热度指数: 82
   关键词: 内容创作, 用户增长, 变现模式

💡 建议: 这些话题具有较高的传播潜力，适合多平台推广
        """
    
    def generate_wechat_article(topic: str, style: str = "专业") -> str:
        """生成微信公众号文章大纲"""
        styles = {
            "专业": "深度分析，数据支撑",
            "轻松": "通俗易懂，贴近生活",
            "幽默": "风趣幽默，引人入胜"
        }
        
        return f"""
📝 微信公众号文章方案

标题: 《{topic}：深度解析与未来展望》

风格定位: {styles.get(style, "专业")}

文章大纲:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 引言 (200字)
   - 引出话题，说明重要性
   - 抛出核心问题，引发思考

📊 现状分析 (500字)
   - 市场数据和趋势
   - 行业现状和痛点
   - 典型案例分析

🔍 深度解读 (800字)
   - 技术原理和创新点
   - 应用场景和价值
   - 发展机遇和挑战

🚀 未来展望 (400字)
   - 发展趋势预测
   - 对行业的影响
   - 给读者的启发

💬 结语 (100字)
   - 总结核心观点
   - 互动引导

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

预计字数: 2000-2500字
目标受众: 科技爱好者、行业从业者
阅读时长: 8-10分钟

📌 SEO 关键词: {topic}, 技术创新, 行业趋势
🏷️  推荐标签: #{topic} #深度分析 #行业洞察
        """
    
    def generate_weibo_post(topic: str, tone: str = "正式") -> str:
        """生成微博内容"""
        emojis = {
            "正式": "📊🔍💡",
            "活泼": "🔥✨🎉",
            "专业": "📈💼🎯"
        }
        
        selected_emojis = emojis.get(tone, "📊🔍💡")
        
        return f"""
📱 微博内容方案

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#{topic}# 最新动态！{selected_emojis[0]}

这个趋势值得关注 {selected_emojis[1]}

✨ 核心要点：
• [关键发现1]
• [关键发现2]  
• [关键发现3]

📊 数据支撑：
根据最新报告显示，[相关数据]

🚀 未来影响：
预计将在[领域]产生重大影响

{selected_emojis[2]} 你怎么看？欢迎评论区讨论！

#热点追踪# #科技前沿# #行业洞察#

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

字数: 约140字（符合微博限制）
互动建议: 提问引导、投票、转发抽奖
最佳发布时间: 12:00-13:00 或 20:00-22:00
        """
    
    def generate_video_script(topic: str, duration: int = 60) -> str:
        """生成短视频脚本"""
        return f"""
🎬 短视频脚本方案

主题: {topic}
时长: {duration}秒
平台: 抖音/快手

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 开场 (0-5秒)
画面: 震撼视觉效果
文案: "你知道{topic}吗？"
音效: 吸引注意力的音乐

📖 内容展开 (5-45秒)

第一部分 (5-20秒)
画面: 数据可视化动画
文案: "最新数据显示..."
要点: 核心信息1

第二部分 (20-35秒)
画面: 实际应用场景
文案: "这意味着什么？"
要点: 核心信息2

第三部分 (35-45秒)
画面: 未来展望画面
文案: "未来将会..."
要点: 核心信息3

🎬 结尾 (45-60秒)
画面: 品牌露出
文案: "关注我，了解更多"
引导: 点赞、评论、关注

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎨 视觉风格: 现代科技感
🎵 背景音乐: 节奏感强的电子音乐
📝 字幕: 大字体，高对比度
🏷️  话题标签: #{topic} #知识分享 #干货

💡 拍摄建议:
- 使用稳定器保证画面稳定
- 光线充足，画面清晰
- 快节奏剪辑，保持观众注意力
        """
    
    def analyze_content_style(content: str) -> str:
        """分析内容风格"""
        return f"""
📊 内容风格分析报告

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 语言风格分析:
   • 专业度: ⭐⭐⭐⭐⭐
   • 可读性: ⭐⭐⭐⭐
   • 吸引力: ⭐⭐⭐⭐

✅ 目标受众匹配:
   • 年龄段: 25-40岁
   • 教育水平: 本科及以上
   • 兴趣偏好: 科技、商业、创新

✅ 情感色彩:
   • 基调: 积极正面
   • 态度: 客观理性
   • 感染力: 较强

✅ 传播潜力:
   • 话题热度: 高
   • 分享意愿: 中高
   • 预计阅读量: 5000+

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 优化建议:

1. 增加互动元素
   - 添加问答环节
   - 设置投票调查
   - 引导用户评论

2. 强化视觉呈现
   - 添加信息图表
   - 使用配图增强吸引力
   - 优化排版布局

3. 提升传播效果
   - 结合时事热点
   - 优化标题吸引力
   - 选择最佳发布时间

4. 内容深度优化
   - 增加数据支撑
   - 补充案例分析
   - 提供实用建议
        """
    
    def suggest_images(topic: str, platform: str = "微信") -> str:
        """建议配图方案"""
        platform_specs = {
            "微信": "900x500px (头图), 1080x1080px (正文)",
            "微博": "690x920px (竖图), 1080x608px (横图)",
            "小红书": "1080x1080px (方图), 3:4 (竖图)",
            "抖音": "1080x1920px (竖屏视频封面)"
        }
        
        return f"""
🎨 {topic} 配图方案

平台: {platform}
尺寸规格: {platform_specs.get(platform, "通用尺寸")}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🖼️  主图设计:
   风格: 现代科技感
   色调: 蓝色系为主，白色和灰色为辅
   元素: 科技线条、数据图表、未来感图形

📊 图表设计:
   类型: 柱状图、折线图、饼图
   风格: 扁平化、简洁明了
   配色: 渐变色，视觉冲击力强

🎯 图标设计:
   风格: 线性图标
   主题: 与{topic}相关的行业符号
   大小: 统一规格，整齐排列

🌈 配色方案:
   主色: #2E5BFF (科技蓝)
   辅色: #FFFFFF (纯白)
   点缀: #00D4FF (亮蓝)
   背景: #F5F7FA (浅灰)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 设计建议:

1. 头图设计
   - 突出主题关键词
   - 使用视觉层次感
   - 保持品牌一致性

2. 正文配图
   - 每500字配一张图
   - 图文相关性强
   - 提升阅读体验

3. 图表使用
   - 数据可视化
   - 简化复杂信息
   - 增强说服力

4. 版权注意
   - 使用正版图库
   - 标注图片来源
   - 避免侵权风险

🔧 推荐工具:
   • Canva - 在线设计
   • Figma - 专业设计
   • Unsplash - 免费图库
   • iconfont - 图标资源
        """
    
    # 创建智能体
    agent = ChatAgent(
        name="新媒体运营 AI 助手 (DeepSeek驱动)",
        chat_client=chat_client,
        instructions="""
🤖 你好！我是基于 DeepSeek 大模型的新媒体运营 AI 助手！

我可以帮助你：

🔥 热点发现与分析
   - 获取各平台热点话题
   - 分析热点传播潜力
   - 提供话题选择建议

✍️ 多平台内容创作
   - 微信公众号长文章
   - 微博短文和话题
   - 短视频脚本和分镜
   - 小红书图文笔记

🎨 视觉设计建议
   - 配图方案设计
   - 色彩搭配建议
   - 视觉元素推荐

📊 内容风格分析
   - 语言风格评估
   - 受众匹配分析
   - 传播效果预测

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 快速开始 - 试试这些命令：

1. "获取科技领域的热点话题"
2. "为人工智能话题生成微信文章大纲"
3. "创作一条关于新能源汽车的微博"
4. "生成60秒短视频脚本，主题是数字化转型"
5. "分析这段内容的风格特点"
6. "推荐小红书平台的配图方案"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 特色功能：
• 基于 DeepSeek 大模型，响应快速
• 支持多平台内容适配
• 提供专业的创作建议
• 完全中文优化

让我们开始创作吧！有任何问题随时问我 😊
        """,
        tools=[
            get_hot_topics,
            generate_wechat_article,
            generate_weibo_post,
            generate_video_script,
            analyze_content_style,
            suggest_images
        ]
    )
    
    return agent

async def test_deepseek_connection(chat_client):
    """测试 DeepSeek 连接"""
    if not chat_client:
        return False
    
    try:
        print("🔄 测试 DeepSeek API 连接...")
        
        # 创建一个简单的测试智能体
        test_agent = ChatAgent(
            name="测试",
            chat_client=chat_client,
            instructions="你是一个测试助手，请简短回复。"
        )
        
        # 发送测试消息
        response = await test_agent.run("你好，请回复'连接成功'")
        print(f"✅ DeepSeek API 测试成功！")
        print(f"📝 响应: {response}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek API 连接失败: {e}")
        print()
        return False

async def main():
    """主函数"""
    print("=" * 50)
    print("🎯 新媒体运营 AI 系统 - DeepSeek 版本")
    print("=" * 50)
    print()
    
    # 创建 DeepSeek 客户端
    chat_client = create_deepseek_client()
    
    if not chat_client:
        print("💡 提示: 请先配置 DeepSeek API 密钥")
        print()
        print("步骤:")
        print("1. 访问 https://platform.deepseek.com/ 注册账号")
        print("2. 获取 API Key")
        print("3. 在 .env 文件中设置:")
        print("   DEEPSEEK_API_KEY=your_api_key_here")
        print("   DEEPSEEK_BASE_URL=https://api.deepseek.com")
        print("   DEEPSEEK_MODEL=deepseek-chat")
        print()
        print("⚠️  将使用模拟模式启动（功能受限）")
        print()
        
        # 使用模拟模式
        from simple_demo import create_mock_agent
        demo_agent = create_mock_agent()
    else:
        # 测试连接
        connection_ok = await test_deepseek_connection(chat_client)
        
        if not connection_ok:
            print("⚠️  API 连接测试失败，将使用模拟模式")
            from simple_demo import create_mock_agent
            demo_agent = create_mock_agent()
        else:
            # 创建完整功能的智能体
            demo_agent = create_social_media_agent(chat_client)
    
    # 启动 DevUI
    print("🌐 启动 DevUI 界面...")
    print("📍 访问地址: http://localhost:8080")
    print("💡 在界面中与 AI 助手交互")
    print()
    
    serve(
        entities=[demo_agent],
        host="localhost",
        port=8080,
        auto_open=True
    )

if __name__ == "__main__":
    asyncio.run(main())