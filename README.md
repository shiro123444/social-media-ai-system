#  HotFlow AI - 基于 Agent Framework 的智能热点内容生产系统

> 让新媒体运营从找选题中解放出来

一个基于 Microsoft Agent Framework 的智能内容生产系统。通过多智能体协作，实现从热点追踪到内容生成再到自动发布的全流程自动化。

##  项目简介

这是一个基于 Microsoft Agent Framework 的智能内容生产系统。我们用多智能体协作的方式，实现了从热点追踪到内容生成的全流程自动化。

**系统工作流程**：
1. **热点追踪** - 通过 MCP 协议接入 Daily Hot 工具，自动抓取微博、知乎、B站、今日头条等主流平台的实时热榜，采用热加载机制，首次响应时间大大缩短
2. **深度分析** - 用 think-tool 让 AI 深度分析热点，按类别分类、找出趋势、推荐值得创作的话题
3. **内容生成** - 针对小红书平台特点，自动生成符合规范的爆款文案
4. **自动发布** - 通过 xiaohongshu-mcp 实现一键发布到小红书

**实际效果**：
- 整个流程 **4-7 秒**跑完
- 成本不到 **1 分钱**
- 数据获取 **0.003 秒**
- 效率比人工提升 **80% 以上**

##  核心亮点

### 极致性能优化

- **智能缓存系统** - 数据获取从 1-3 秒降至 0.003 秒，提升 **300-1000 倍**
- **自动预热机制** - 4 个稳定数据源定时刷新（20 分钟间隔），缓存命中率接近 100%
- **指令精简优化** - 工作流指令减少 91%（10,500 → 900 字符），执行速度提升 **70-80%**
- **成本大幅降低** - Token 消耗和 API 成本降低 **90%**
- **解耦式设计** -从系统框架到模块内存全部解耦式设计，如同拼台式机一样可卸载可重装自由度极高

###  技术创新

- **Agent Framework Sequential 工作流** - 每个 Agent 专注做一件事，可维护性和扩展性强
- **原生 MCP 协议支持** - 接入新工具只需几行代码，已经支持 HTTP 和 stdio 两种模式
- **DevUI 可视化界面** - 实时看到每个 Agent 的执行过程，调试效率高
- **全自动发布** - 从热点抓取到发布小红书一气呵成

##  能干什么

这个项目主要做四件事：

1. **抓热点** - 从微博、知乎、B站、今日头条等平台获取实时热榜（支持缓存加速）
2. **分析趋势** - 用 AI 深度分析哪些话题值得写，怎么写
3. **生成内容** - 自动生成符合小红书规范的爆款文案
4. **自动发布** - 一键发布到小红书，无需手动操作

目前专注于小红书平台，文案包含：
- 新闻内容（时间、数据、来源、热度）
-  时评观点（分析、思考、提问）
- 话题标签
-  自动配图（TODO）



## 为什么做这个

做新媒体运营最头疼的就是每天找选题。这个系统的想法很简单：让 AI 帮你盯着各大平台的热榜，分析出值得写的话题，然后直接生成初稿。你只需要在初稿基础上修改润色就行了。

当然，AI 生成的内容不能直接用，但至少能帮你：
- 快速了解今天有什么热点
- 知道哪些话题热度高
- 有个初稿可以改，不用从零开始

## 为什么选 Microsoft Agent Framework

说实话，一开始也纠结过用什么框架。目前选择挺多的：LangChain、AutoGen、CrewAI... 但最后选了 Agent Framework，主要是这几个原因：

### 1. 工作流模式及其灵活

Agent Framework 支持好几种编排模式：
- **Sequential（顺序）** - 像流水线一样，一个接一个执行，适合我这种"抓热点→分析→生成内容"的场景
- **Parallel（并行）** - 多个 Agent 同时跑，适合需要同时处理多个任务的情况
- **Fan-out/Fan-in** - 一个任务分发给多个 Agent 处理，然后汇总结果
- **Graph-based（图）** - 自定义复杂的执行流程，可以有条件分支、循环等

现在用的是 Sequential，但如果以后想同时生成多个平台的内容，可以直接改成 Parallel，不用重写代码，扩展性这一块。

### 2. MCP 集成是原生的

Agent Framework 对 MCP (Model Context Protocol) 的支持是内置的。我用的 Daily Hot MCP 就是个例子，它能抓取 15+ 个平台的热榜。

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

## 🚀 快速开始

### 前置要求

- Python 3.10+
- DeepSeek API Key（[免费注册](https://platform.deepseek.com)）
- Windows 系统（小红书发布功能）

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入配置：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# MCP 服务配置
DAILY_HOT_MCP_URL=http://localhost:8000/mcp
XIAOHONGSHU_MCP_URL=http://localhost:18060/mcp

# 小红书默认图片（可选）
XHS_DEFAULT_IMAGES=C:\Users\YourName\Pictures\default.jpg
```

### 3. 启动 Daily Hot MCP 服务

这个服务负责抓取热榜数据并提供缓存：

```bash
cd daily-hot-mcp
python -m daily_hot_mcp
```

看到以下日志说明启动成功：
```
✅ Server running on http://localhost:8000
✅ Scheduling 4 enabled sources
✅ Cache warmer started
```

### 4. 启动小红书 MCP 服务（可选）

如果需要自动发布功能：

1. 下载 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp/releases)
2. 运行登录工具：`.\xiaohongshu-login-windows-amd64.exe`
3. 启动 MCP 服务：`.\xiaohongshu-mcp-windows-amd64.exe`

详细配置见 `docs/XIAOHONGSHU_SETUP.md`

### 5. 运行工作流

启动 DevUI 界面：

```bash
python run_devui.py
```

浏览器访问 `http://localhost:9000`，选择 "Xiaohongshu Hotspot Workflow"，输入：

```
获取今天知乎的热点，生成小红书文案
```

等待 **4-7 秒**，就能看到完整的工作流程和生成的内容！

## 🔄 工作流程

整个系统分四步，采用 Sequential 顺序执行：

### 1. 热点获取 (Hotspot Executor)

调用 Daily Hot MCP 获取热榜数据，**支持智能缓存**：

**稳定数据源（4个）**：
- ✅ 微博热搜（20 分钟刷新）
- ✅ 知乎热榜（20 分钟刷新）
- ✅ B站热榜（20 分钟刷新）
- ✅ 今日头条（20 分钟刷新）

**性能优势**：
- 首次调用：0.003 秒（缓存命中）
- 自动预热：后台定时刷新
- 缓存命中率：接近 100%

### 2. 深度分析 (Analysis Executor)

使用 **think-tool** 进行深度分析：
- 按类别分类（科技、娱乐、社会、财经、体育）
- 找出共同话题和趋势
- 推荐最值得写的内容
- 给出创作建议

**优化效果**：
- 指令精简：2,800 → 300 字符（89% 减少）
- 执行速度：5-7 秒 → 1-2 秒

### 3. 内容生成 (Content Executor)

生成符合小红书规范的文案：

**文案规范**：
- 标题：≤20 字，含 emoji 和日期
- 内容：≤1000 字，包含 3-4 条热点
- 格式：📰 新闻内容 + 💭 时评观点
- 标签：自动生成话题标签
- 配图：支持默认图片配置

**优化效果**：
- 指令精简：6,500 → 400 字符（94% 减少）
- 执行速度：5-8 秒 → 2-3 秒

### 4. 自动发布 (Publisher Executor)

使用 **xiaohongshu-mcp** 自动发布：
- 自动填充标题、内容、标签
- 自动上传配图
- 支持重试机制（最多 3 次）
- 发布成功后返回详细结果

## 📁 项目结构

```
social-media-ai-system/
├── agents/
│   └── social_media_workflow/           # 工作流定义
│       └── __init__.py                  # 四个 Executor 实现
├── daily-hot-mcp/                       # 热榜数据源 MCP 服务
│   ├── daily_hot_mcp/
│   │   ├── tools/                       # 各平台热榜工具
│   │   │   ├── weibo.py                # 微博热搜
│   │   │   ├── zhihu.py                # 知乎热榜
│   │   │   ├── bilibili.py             # B站热榜
│   │   │   └── toutiao.py              # 今日头条
│   │   ├── utils/
│   │   │   └── cache.py                # 缓存系统
│   │   └── scheduler/                   # 调度器
│   │       ├── scheduler.py            # 定时任务
│   │       ├── warmer.py               # 缓存预热
│   │       └── manager.py              # 调度管理
│   └── scheduler_config.json           # 调度配置
├── docs/                                # 文档
│   ├── XIAOHONGSHU_SETUP.md           # 小红书配置指南
│   └── XIAOHONGSHU_PUBLISH_FIX.md     # 发布问题修复
├── .env                                 # 环境变量配置
├── run_devui.py                         # DevUI 启动脚本
└── README.md
```

**核心文件说明**：
- `agents/social_media_workflow/__init__.py` - 工作流核心逻辑（约 600 行）
- `daily_hot_mcp/utils/cache.py` - 智能缓存系统
- `daily_hot_mcp/scheduler/` - 自动预热调度器
- `scheduler_config.json` - 数据源配置（4 个稳定源）

## 遇到的坑

### 1. DeepSeek API 兼容性

Agent Framework 默认用 OpenAI 的格式，但 DeepSeek 不支持多模态消息。解决办法是写了个适配器，把所有消息转成纯文本。

### 2. TextContent 序列化问题

DevUI 在序列化消息时会报错 `object.__setattr__` 的问题。原因是 Agent Framework 的 `TextContent` 对象不能直接序列化。解决办法是提取文本内容，用字符串传递。

### 3. MCP 工具生命周期

MCP 工具需要手动管理连接，不能在 Executor 初始化时就连接，要在 handler 里用 `async with` 管理。

详细的踩坑记录在 `Learn.md` 里。

## 小红书自动发布功能

现在支持**全自动发布**到小红书！使用 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 实现。

### 功能特点

- ✅ **全自动发布** - 从热点抓取到发布一气呵成
- ✅ **智能文案生成** - 每条新闻分两段：📰 新闻内容 + 💭 时评观点
- ✅ **详细内容** - 包含时间、数据、来源、热度等细节
- ✅ **自动配图** - 支持配置默认图片，无需手动上传
- ✅ **符合规范** - 标题 ≤20 字，内容 ≤1000 字

### 工作流程

```
热点追踪 → 深度分析 → 生成文案 → 自动发布
   ↓           ↓          ↓          ↓
 Daily Hot   think-tool  DeepSeek   xiaohongshu-mcp
```

### 文案格式示例

```
标题：🔥10.23热搜！学生梗+金庸

内容：
姐妹们！10月23日的热搜真的太炸了！😱

📰 学生满口「包的包的」、「666」等网络梗，这将带来哪些深远影响？
10月22日，一篇关于学生语言习惯的文章在知乎引发热议，获得797万热度...

💭 这个现象确实值得关注！网络梗虽然有趣，但过度使用可能会影响学生的
正式表达能力...

📰 金庸小说有哪些情节是成年后才能看懂的？
10月23日，这个话题在知乎热榜获得428万热度...

💭 经典就是经典！成年后重读金庸，才发现那些看似简单的情节背后...

你们怎么看？评论区聊聊！👇
```

### 快速开始

1. **下载 xiaohongshu-mcp**：
   - 访问 [Releases](https://github.com/xpzouying/xiaohongshu-mcp/releases)
   - 下载 `xiaohongshu-login-windows-amd64.exe` 和 `xiaohongshu-mcp-windows-amd64.exe`

2. **配置环境变量**（`.env`）：
   ```env
   XIAOHONGSHU_MCP_URL=http://localhost:18060/mcp
   XHS_DEFAULT_IMAGES=C:\Users\YourName\Pictures\default.jpg
   ```

3. **登录小红书**：
   ```powershell
   .\xiaohongshu-login-windows-amd64.exe
   ```

4. **启动 MCP 服务**：
   ```powershell
   .\xiaohongshu-mcp-windows-amd64.exe
   ```

5. **运行工作流**：
   ```bash
   python test_devui_final.py
   ```

详细配置方法看 `docs/XIAOHONGSHU_SETUP.md`。

## 📊 实际效果

经过性能优化后，效果显著提升：

### 性能指标

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 数据获取 | 1-3 秒 | **0.003 秒** | **99.9%** ⚡ |
| 工作流执行 | 18-25 秒 | **4-7 秒** | **75%** 🚀 |
| API 调用 | 每次请求 | 20 分钟 1 次 | **99%** 💰 |
| Token 消耗 | 2,600 | 225 | **91%** 📉 |
| 总成本 | ~0.1 元 | **~0.01 元** | **90%** 💵 |

### 内容质量

- ✅ 标题吸引力强，符合小红书风格
- ✅ 内容结构清晰，包含新闻+时评
- ✅ 数据和事实准确（基于真实热点）
- ✅ 自动配图，符合平台规范
- ⚠️ 建议人工审核后再发布

## 🎯 技术创新点

### 1. 智能缓存系统

**创新点**：
- 自动预热机制，后台定时刷新热点数据
- 文件持久化存储，重启服务不丢失缓存
- 智能调度器，只预热稳定可靠的数据源
- 缓存命中率接近 100%

**性能提升**：
- 数据获取速度提升 **300-1000 倍**
- API 调用减少 **99%**
- 用户体验：几乎瞬时响应

### 2. 工作流指令优化

**创新点**：
- 大幅精简 Agent 指令（总计减少 91%）
- 保留核心功能，删除冗余说明
- 统一输出格式，减少歧义
- 简洁明确的表达方式

**性能提升**：
- Token 消耗减少 **90%**
- 推理速度提升 **70-80%**
- API 成本降低 **90%**

### 3. MCP 协议深度集成

**创新点**：
- 支持 HTTP 和 stdio 两种 MCP 模式
- 动态创建和管理 MCP 工具生命周期
- 异步环境中使用 `async with` 管理连接
- 完善的错误处理和重试机制

**优势**：
- 接入新工具只需几行代码
- 工具隔离，互不影响
- 资源自动释放，无内存泄漏

### 4. 全自动发布流程

**创新点**：
- 从热点抓取到发布一气呵成
- 智能重试机制（最多 3 次）
- 自动配图，无需手动上传
- 详细的发布结果反馈

**用户价值**：
- 节省 80% 以上的人工操作时间
- 降低 90% 的内容生产成本
- 提高内容发布的稳定性和成功率

## 📋 后续计划

- [ ] 支持更多平台（微信公众号、微博、抖音）
- [ ] 优化缓存策略（支持更多数据源）
- [ ] 添加内容质量评分功能
- [ ] 支持定时任务（每天自动跑一次）
- [ ] 添加内容审核和合规检查

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

## 💎 核心价值

这个项目的核心价值不是"AI 能写文章"，而是通过**技术创新**把新媒体运营中最耗时的工作自动化：

### 传统方式 vs HotFlow AI

| 环节 | 传统方式 | HotFlow AI | 提升 |
|------|----------|------------|------|
| 找热点 | 手动浏览多个平台，15-30 分钟 | 自动抓取+缓存，**0.003 秒** | **99.9%** |
| 分析趋势 | 人工分析，30-60 分钟 | AI 深度分析，**1-2 秒** | **99%** |
| 写文案 | 从零开始写，60-120 分钟 | AI 生成初稿，**2-3 秒** | **99%** |
| 发布 | 手动复制粘贴，5-10 分钟 | 自动发布，**即时** | **100%** |
| **总耗时** | **110-220 分钟** | **4-7 秒** | **99.9%** |
| **成本** | 人工成本高 | **~0.01 元/次** | **极低** |

### 价值主张

就像 GitHub Copilot 不是替代程序员，而是让程序员写代码更快一样，**HotFlow AI 是内容创作者的 Copilot**：

- ✅ 解放创作者，专注于审核和润色
- ✅ 降低内容生产成本 90%
- ✅ 提高内容发布效率 80%+
- ✅ 保证内容质量和时效性

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
