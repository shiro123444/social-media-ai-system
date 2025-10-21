"""
最终测试：验证 DevUI 可以正常启动并使用 MCP 工具
"""
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("DevUI 最终测试")
    logger.info("=" * 80)
    
    try:
        logger.info("\n[1/2] 导入 DevUI 和 workflow...")
        from agent_framework.devui import serve
        from agents.social_media_workflow import workflow
        
        logger.info(f"✅ 导入成功")
        logger.info(f"   Workflow: {workflow.name if hasattr(workflow, 'name') else 'unnamed'}")
        
        logger.info("\n[2/2] 启动 DevUI...")
        logger.info("   URL: http://localhost:9000")
        logger.info("   按 Ctrl+C 停止")
        logger.info("")
        
        # 启动 DevUI
        serve(entities=[workflow], auto_open=False, port=9000)
        
    except KeyboardInterrupt:
        logger.info("\n\n✅ DevUI 已停止")
        return 0
    except Exception as e:
        logger.error(f"\n❌ 启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
