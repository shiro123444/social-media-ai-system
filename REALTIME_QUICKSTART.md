# 🚀 实时热点新闻系统 - 快速启动指南

## 系统架构

```
实时热点新闻系统
├── 网络新闻抓取智能体 (Fetch MCP)
├── 搜索趋势分析智能体 (Brave Search MCP)
├── 社交媒体监控智能体 (Twitter/Weibo API)
├── 数据聚合智能体 (数据处理)
└── 内容生成智能体 (内容创作)
```

## 快速开始

### 1. 基础版本（无需额外配置）

```bash
# 直接运行，使用模拟数据
python realtime_news_system.py
```

这会启动一个演示版本，展示多智能体协作流程。

### 2. 完整版本（需要 API 配置）

#### 步骤 1: 配置 AI 模型 API

在 `.env` 文件中添加：

```env
# 使用 DeepSeek (推荐)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 或使用 OpenAI
# OPENAI_API_KEY=your_openai_api_key
```

#### 步骤 2: 安装 MCP 工具（可选）

```bash
# 安装 uv (Python 包管理器)
pip install uv

# 安装 Fetch MCP (网页抓取)
uvx mcp-server-fetch

# 安装 Brave Search MCP (搜索引擎)
npm install -g @modelcontextprotocol/server-brave-search
```

#### 步骤 3: 配置 MCP 服务器（可选）

复制配置文件：
```bash
copy .kiro\settings\mcp.json.example .kiro\settings\mcp.json
```

编辑 `mcp.json`，添加你的 API 密钥。

#### 步骤 4: 运行系统

```bash
python realtime_news_system.py
```

## 功能演示

### 在 DevUI 中尝试

访问 http://localhost:8080，输入以下命令：

1. **获取热点新闻**
   ```
   获取科技领域的最新热点新闻
   ```

2. **分析搜索趋势**
   ```
   分析今日百度搜索趋势
   ```

3. **监控社交媒体**
   ```
   监控微博上的热门话题
   ```

4. **计算热度指数**
   ```
   计算"人工智能"话题的热度指数
   ```

5. **生成内容**
   ```
   为"新能源汽车"话题生成微信公众号文章方案
   ```

## 多智能体工作流

系统会自动协调5个智能体完成任务：

```
用户输入
    ↓
中央协调器
    ↓
┌───┴───┬───────┬───────┐
│       │       │       │
新闻    搜索    社交    
抓取    趋势    媒体    
↓       ↓       ↓       
└───┬───┴───────┴───────┘
    ↓
数据聚合
    ↓
内容生成
    ↓
输出结果
```

## 集成真实 MCP 工具

### Fetch MCP (网页抓取)

```python
from agent_framework import MCPStdioTool

async with MCPStdioTool(
    name="fetch",
    command="uvx",
    args=["mcp-server-fetch"]
) as fetch_tool:
    agent = ChatAgent(
        name="新闻抓取",
        tools=[fetch_tool]
    )
```

### Brave Search MCP (搜索引擎)

```python
async with MCPStdioTool(
    name="brave-search",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-brave-search"]
) as search_tool:
    agent = ChatAgent(
        name="搜索分析",
        tools=[search_tool]
    )
```

## 自定义配置

### 添加新闻源

编辑 `realtime_news_system.py`，修改 `fetch_news_from_web` 函数：

```python
def fetch_news_from_web(self, source: str = "综合") -> str:
    # 添加你的新闻源
    news_sources = {
        "科技": ["36氪", "IT之家", "极客公园"],
        "财经": ["财新网", "第一财经", "华尔街见闻"],
        # 添加更多...
    }
```

### 调整热度算法

修改 `calculate_hotness` 函数中的权重：

```python
# 搜索量权重 (40%)
score += news_item['search_volume'] * 0.4

# 社交媒体讨论量 (30%)
score += news_item['social_mentions'] * 0.3

# 调整为你需要的权重...
```

## 定时任务

添加定时抓取功能：

```python
import schedule

def fetch_news_job():
    """每小时抓取一次"""
    asyncio.run(workflow.run("获取最新热点"))

schedule.every(1).hours.do(fetch_news_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 数据持久化

保存热点数据到文件：

```python
import json
from datetime import datetime

def save_hotspot(data):
    filename = f"hotspots_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

## 常见问题

### Q: 如何获取真实的实时数据？

A: 需要配置相应的 API：
- Brave Search API: https://brave.com/search/api/
- 微博 API: https://open.weibo.com/
- Twitter API: https://developer.twitter.com/

### Q: MCP 工具安装失败？

A: 确保已安装：
- Python 3.10+
- Node.js 18+ (用于 npm)
- uv 包管理器

### Q: 如何添加更多智能体？

A: 在 `create_agents_with_mcp` 方法中添加新的智能体：

```python
new_agent = ChatAgent(
    name="新智能体",
    chat_client=self.chat_client,
    instructions="...",
    tools=[your_tools]
)
```

## 下一步

1. ✅ 运行基础演示
2. ⬜ 配置 API 密钥
3. ⬜ 集成真实 MCP 工具
4. ⬜ 添加数据持久化
5. ⬜ 实现定时任务
6. ⬜ 对接真实平台 API

## 参考资源

- [MCP 集成指南](MCP_INTEGRATION_GUIDE.md)
- [Agent Framework 文档](https://github.com/microsoft/agent-framework)
- [项目 README](README.md)

---

开始构建你的实时热点新闻系统吧！🚀