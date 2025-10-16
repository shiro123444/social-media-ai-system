"""
启动 Agent Framework DevUI
"""
import asyncio
from agent_framework_devui import start_dev_ui

async def main():
    print("正在启动 DevUI...")
    await start_dev_ui(host="localhost", port=8000)

if __name__ == "__main__":
    asyncio.run(main())