"""
启动 DevUI 可视化界面
用于展示小红书内容生产工作流
"""

import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    启动 DevUI 服务器
    """
    logger.info("=" * 80)
    logger.info("🚀 启动 Agent Framework DevUI")
    logger.info("=" * 80)
    
    # 检查环境变量
    logger.info("\n[1/3] 检查环境配置...")
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("❌ DEEPSEEK_API_KEY 未配置")
        logger.info("请在 .env 文件中添加: DEEPSEEK_API_KEY=your_api_key")
        return
    
    logger.info("✅ DeepSeek API Key 已配置")
    
    # 导入工作流
    logger.info("\n[2/3] 加载工作流...")
    
    try:
        from agents.social_media_workflow import workflow
        logger.info(f"✅ 工作流加载成功: {workflow.name}")
        logger.info(f"   描述: {workflow.description}")
    except Exception as e:
        logger.error(f"❌ 工作流加载失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return
    
    # 启动 DevUI
    logger.info("\n[3/3] 启动 DevUI 服务器...")
    
    try:
        from agent_framework_devui import serve
        
        logger.info("\n" + "=" * 80)
        logger.info("🖥️ DevUI 服务器信息")
        logger.info("=" * 80)
        logger.info("📍 URL: http://localhost:9000")
        logger.info("🔄 工作流: 小红书内容生产工作流")
        logger.info("")
        logger.info("📋 工作流步骤:")
        logger.info("   1. 🔥 热点获取 - 使用 daily-hot-mcp 获取最新热点")
        logger.info("   2. 📊 内容分析 - 使用 think-tool 深度分析")
        logger.info("   3. ✍️ 内容生成 - 生成小红书文案")
        logger.info("   4. 📤 内容发布 - 发布到小红书")
        logger.info("")
        logger.info("💡 使用说明:")
        logger.info("   1. 浏览器将自动打开 http://localhost:9000")
        logger.info("   2. 选择 'Xiaohongshu Hotspot Workflow'")
        logger.info("   3. 输入查询，如: '获取最新AI技术热点，生成小红书文案'")
        logger.info("   4. 点击运行，观察可视化执行过程")
        logger.info("")
        logger.info("⚠️ 注意事项:")
        logger.info("   - 确保 daily-hot-mcp 在 http://localhost:8000/mcp 运行")
        logger.info("   - 确保 xiaohongshu-mcp 在 http://localhost:18060/mcp 运行")
        logger.info("   - 确保配置了 XHS_DEFAULT_IMAGES 环境变量")
        logger.info("   - 工作流执行可能需要几分钟时间")
        logger.info("")
        logger.info("🛑 按 Ctrl+C 停止服务器")
        logger.info("=" * 80)
        
        # 启动服务器（使用 serve 函数）
        serve(
            entities=[workflow],
            host="127.0.0.1",
            port=9000,
            auto_open=True  # 自动打开浏览器
        )
        
    except KeyboardInterrupt:
        logger.info("\n\n👋 DevUI 服务器已停止")
        logger.info("感谢使用！")
    except Exception as e:
        logger.error(f"\n❌ DevUI 服务器启动失败: {e}")
        
        # 提供故障排除建议
        logger.info("\n🔧 故障排除建议:")
        logger.info("1. 检查端口 9000 是否被占用")
        logger.info("2. 确保 agent-framework-devui 已安装")
        logger.info("   pip install agent-framework-devui")
        logger.info("3. 检查工作流配置是否正确")
        logger.info("4. 查看详细错误信息:")
        
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
