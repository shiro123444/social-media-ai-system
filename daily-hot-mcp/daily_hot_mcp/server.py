from fastmcp import FastMCP
from daily_hot_mcp.utils.logger import logger
from daily_hot_mcp.tools import all_tools
from daily_hot_mcp.scheduler import SchedulerManager

# 重命名变量，使其符合 mcp dev 命令的预期
server = FastMCP(name = "daily-hot-mcp")

for tool in all_tools:
    server.add_tool(tool)
    logger.info(f"Registered tool: {tool.name}")

# Initialize scheduler manager
scheduler_manager = SchedulerManager(tool_registry=all_tools)

def run_http(host: str, port: int, path: str, log_level: str):
    """Run Daily Hot MCP server in HTTP mode."""
    try:
        logger.info(f"Starting Daily Hot MCP server with HTTP transport (http://{host}:{port}{path})")
        
        # Start scheduler before server
        try:
            scheduler_manager.start()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            logger.warning("Server will continue without scheduler")
        
        server.run(
            transport="http",
            host=host,
            port=port,
            path=path,
            log_level=log_level
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        # Ensure scheduler stops on shutdown
        try:
            scheduler_manager.stop()
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")

def main():
    run_http("0.0.0.0", 8000, "/mcp", "INFO")

if __name__ == "__main__":
    main()