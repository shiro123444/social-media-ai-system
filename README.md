# 社交媒体 AI 工作流

> 让新媒体运营从找选题中解放出来

一个基于 Microsoft Agent Framework 的智能内容生产系统。通过多智能体协作，实现从热点追踪到内容生成的全流程自动化。

## 项目简介

这是一个基于 Microsoft Agent Framework 的智能内容生产系统。我们用多智能体协作的方式，实现了从热点追踪到内容生成的全流程自动化。

**系统分三步走**：
1. **热点追踪** - 通过 MCP 协议接入 Daily Hot 工具，自动抓取 B站、微博、知乎等 15+ 平台的实时热榜
2. **深度分析** - 用 think-tool 让 AI 深度分析热点，按类别分类、找出趋势、推荐值得创作的话题
3. **内容生成** - 针对微信公众号、微博、B站三个平台的不同特点，自动生成适配的文案

**实际效果**：
- ⚡ 整个流程 1 分钟跑完
- 💰 成本不到 1 毛钱
- 📈 效率比人工提升 80% 以上

**技术亮点**：
- 🔧 **Agent Framework Sequential 工作流** - 每个 Agent 专注做一件事，可维护性和扩展性强
- 🔌 **原生支持 MCP 协议** - 接入新工具只需几行代码
- 👀 **DevUI 可视化界面** - 实时看到每个 Agent 的执行过程，调试效率高

## 能干什么

这个项目主要做三件事：

1. **抓热点** - 从 B 站、微博、知乎等平台获取实时热榜
2. **分析趋势** - 用 AI 分析哪些话题值得写，怎么写
3. **生成内容** - 自动生成适合不同平台的文案

目前支持微信公众号、微博、B 站三个平台，每个平台的内容风格和长度都不一样。

## 为什么做这个

做新媒体运营最头疼的就是每天找选题。这个系统的想法很简单：让 AI 帮你盯着各大平台的热榜，分析出值得写的话题，然后直接生成初稿。你只需要在初稿基础上修改润色就行了。

当然，AI 生成的内容不能直接用，但至少能帮你：
- 快速了解今天有什么热点
- 知道哪些话题热度高
- 有个初稿可以改，不用从零开始

## 为什么选 Microsoft Agent Framework

说实话，一开始我也纠结过用什么框架。目前选择挺多的：LangChain、AutoGen、CrewAI... 但最后选了 Agent Framework，主要是这几个原因：

### 1. 工作流模式及其灵活

Agent Framework 支持好几种编排模式：
- **Sequential（顺序）** - 像流水线一样，一个接一个执行，适合我这种"抓热点→分析→生成内容"的场景
- **Parallel（并行）** - 多个 Agent 同时跑，适合需要同时处理多个任务的情况
- **Fan-out/Fan-in** - 一个任务分发给多个 Agent 处理，然后汇总结果
- **Graph-based（图）** - 自定义复杂的执行流程，可以有条件分支、循环等

我现在用的是 Sequential，但如果以后想同时生成多个平台的内容，可以直接改成 Parallel，不用重写代码。这种扩展性很重要。

### 2. MCP 集成是原生的

Agent Framework 对 MCP (Model Context Protocol) 的支持是内置的。MCP 是个很新的协议，让 AI 能方便地调用各种工具。我用的 Daily Hot MCP 就是个例子，它能抓取 15+ 个平台的热榜。

用 Agent Framework 接入 MCP 工具很简单：

```python
from agent_framework import MCPStdioTool

async with MCPStdioTool(
    name="daily-hot",
    command="uvx",
    args=["daily-hot-mcp@latest"]
) as tool:
    # 直接用，不用写一堆适配代码
    result = await tool.call("get_bilibili_hot")
```

其他框架要接 MCP 还得自己写适配层，麻烦。

### 3. DevUI 

Agent Framework 自带一个 Web UI（DevUI），可以实时看到：
- 每个 Agent 在干什么
- 工具调用的参数和结果
- 整个工作流的执行过程
- 每一步的输出

这对调试太有用了。以前用其他框架，出了问题只能看日志，现在直接在浏览器里就能看到哪一步出问题了。

而且 DevUI 还兼容 OpenAI API，意味着你可以用任何支持 OpenAI 格式的客户端来调用你的工作流。

### 4. 微软出品，文档齐全

虽然这个框架还比较新（2024 年才开源），但文档写得很清楚，示例代码也多。遇到问题基本都能在文档里找到答案。

而且微软在 AI 这块投入很大，Agent Framework 应该会持续维护。不像有些开源项目，作者突然不更新了，你就尴尬了。

### 5. 支持多种 AI 模型

Agent Framework 不绑定特定的 AI 模型。你可以用：
- OpenAI GPT-4
- Azure OpenAI
- DeepSeek（我在用的）
- 任何兼容 OpenAI API 的模型

我选 DeepSeek 是因为便宜（），效果也不错。如果以后想换模型，改几行配置就行。

### 说点实话

当然，Agent Framework 也不是完美的：

- **还比较新** - 有些功能还在完善，偶尔会遇到小 bug
- **Python 版本要求高** - 必须 3.10+，有些老项目升级麻烦
- **学习曲线** - 概念比较多（Executor、WorkflowContext、handler 等），刚开始有点懵

但总体来说，对于我这种需要编排多个 AI Agent 的场景，Agent Framework 是目前最合适的选择。

## 技术栈

- **Agent Framework** - 微软的多智能体框架，用来编排工作流
- **MCP (Model Context Protocol)** - 用来接入各种工具，比如热榜 API
- **DeepSeek API** - 便宜好用的国产大模型
- **Daily Hot MCP** - 一个开源的热榜聚合工具

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env`，填入你的 DeepSeek API Key：

```env
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

没有 DeepSeek API Key？去 [platform.deepseek.com](https://platform.deepseek.com) 注册一个，新用户有免费额度。

### 3. 启动 MCP 服务器

这个服务器负责抓取热榜数据：

```bash
cd daily-hot-mcp
python -m daily_hot_mcp
```

看到 `Server running on http://localhost:8000` 就说明启动成功了。

### 4. 运行工作流

打开另一个终端，启动 DevUI：

```bash
python start_devui.ps1
```

然后浏览器访问 `http://localhost:9000`，选择 "social_media_workflow"，输入：

```
获取今天 B 站的热点，生成微信公众号文章
```

等几十秒，就能看到完整的工作流程和生成的内容了。

## 工作流程

整个系统分三步：

### 1. 热点获取 (Hotspot Executor)

调用 Daily Hot MCP 获取热榜数据。支持的平台有：
- B 站热门视频
- 微博热搜
- 知乎热榜
- 抖音热点
- 百度热搜
- 36氪科技新闻
- 等等...

### 2. 深度分析 (Analysis Executor)

拿到热点数据后，AI 会：
- 按类别分类（科技、娱乐、社会、财经、体育）
- 找出共同话题和趋势
- 推荐最值得写的内容
- 给出创作建议

这一步用了 think-tool，让 AI 有更多时间"思考"，分析质量会更好。

### 3. 内容生成 (Content Executor)

根据分析结果生成文案。不同平台有不同的要求：

- **微信公众号**: 2000-3000 字深度文章，专业性强
- **微博**: 500-1000 字，简洁有力，带话题标签
- **B 站**: 800-1500 字视频脚本，口语化，有互动

## 项目结构

```
social-media-ai-system/
├── agents/
│   └── social_media_workflow/      # 工作流定义
│       └── __init__.py             # 三个 Executor 都在这里
├── daily-hot-mcp/                  # 热榜数据源
├── config/
│   ├── platform_guidelines.json    # 各平台的内容规范
│   └── style_presets.json          # 内容风格预设
├── .env                            # API Key 配置
├── start_devui.ps1                 # 启动脚本
└── README.md
```

核心代码都在 `agents/social_media_workflow/__init__.py`，大概 600 行，包含三个 Executor 的实现。

## 遇到的坑

### 1. DeepSeek API 兼容性

Agent Framework 默认用 OpenAI 的格式，但 DeepSeek 不支持多模态消息。解决办法是写了个适配器，把所有消息转成纯文本。

### 2. TextContent 序列化问题

DevUI 在序列化消息时会报错 `object.__setattr__` 的问题。原因是 Agent Framework 的 `TextContent` 对象不能直接序列化。解决办法是提取文本内容，用字符串传递。

### 3. MCP 工具生命周期

MCP 工具需要手动管理连接，不能在 Executor 初始化时就连接，要在 handler 里用 `async with` 管理。

详细的踩坑记录在 `Learn.md` 里。

## 小红书发布功能

本来想做自动发布到小红书的功能，用的是 xhs_mcp_server 这个工具。测试下来发现：

- ✅ 能连上，能获取工具列表
- ✅ Cookie 登录正常
- ❌ 发布时找不到上传按钮（新版本页面结构可能变了）

目前的解决方案是**半自动化**：
1. 工作流生成小红书文案
2. 你复制文案到小红书 App
3. 手动选图发布

这样反而更好，因为：
- 可以最后检查内容质量
- 可以选更合适的图片
- 避免自动化发布的账号风险

配置方法看 `docs/XIAOHONGSHU_SETUP.md`。

## 实际效果

测试了几次，效果还不错：

- **热点获取**: 1-2 秒，能拿到 15 条左右的热点
- **分析处理**: 20-30 秒，会按类别分类，找出趋势
- **内容生成**: 30-40 秒，生成三个平台的内容
- **总耗时**: 大概 1 分钟

生成的内容质量：
- 标题还行，有吸引力
- 内容结构清晰，但需要润色
- 数据和事实基本准确（因为是基于真实热点）
- 建议当初稿用，不要直接发

## 后续计划

- [ ] 支持更多平台（抖音、快手、视频号）
- [ ] 添加图片推荐功能
- [ ] 优化内容生成质量
- [ ] 支持定时任务（每天自动跑一次）
- [ ] 添加内容审核功能

## 注意事项

1. **仅供学习研究** - 不要用于商业用途
2. **内容需审核** - AI 生成的内容必须人工审核后再发布
3. **遵守平台规则** - 不要频繁调用 API，避免被限流
4. **保护 API Key** - 不要把 `.env` 文件提交到 Git

## 相关资源

- [Agent Framework 文档](https://github.com/microsoft/agent-framework)
- [MCP 协议](https://modelcontextprotocol.io/)
- [DeepSeek API](https://platform.deepseek.com)
- [Daily Hot MCP](https://github.com/fatwang2/daily-hot-mcp)

## 核心价值

这个项目的核心价值不是"AI 能写文章"，而是把新媒体运营中最耗时的找选题、分析趋势、多平台适配这些重复性工作自动化了。

人只需要专注于最后的审核和润色，就像 GitHub Copilot 不是替代程序员，而是让程序员写代码更快一样。我们要做的是内容创作者的 Copilot。

## 团队成员

| 姓名 | 学校 | 专业 | 角色 | 联系方式 |
|------|------|------|------|----------|
| 范延哲 | 武汉商学院 | 人工智能 | 队长 | 15071203491 |
| 何旭 | 武汉商学院 | 人工智能 | 成员 | 19232749731 |
| 郑显龙 | 武汉商学院 | 大数据科学与技术 | 成员 | 18995717223 |

## 问题反馈

遇到问题可以：
1. 查看 `Learn.md` 里的踩坑记录
2. 查看 `docs/` 目录下的文档
3. 提 Issue
4. 联系团队成员

## 演示视频
https://www.bilibili.com/video/BV1tksbzCE9M/

## License

MIT License - 随便用，但后果自负。

---

**武汉商学院 智汇AI协会 出品** 🎓
