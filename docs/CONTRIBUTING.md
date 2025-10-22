# 贡献指南

感谢以上成员对社交媒体 AI 工作流项目的关注！这份文档记录了我们在开发过程中遇到的问题、解决方案，以及团队成员的贡献。

## 团队成员

| 姓名  | 学校    | 专业       | 角色  | 主要贡献                               |
| --- | ----- | -------- | --- | ---------------------------------- |
| 范延哲 | 武汉商学院 | 人工智能     | 队长  | 项目架构设计、Agent Framework 集成、MCP 工具接入 |
| 何旭  | 武汉商学院 | 人工智能     | 成员  | 内容生成优化、多平台适配、文档编写                  |
| 郑显龙 | 武汉商学院 | 大数据科学与技术 | 成员  | 数据分析、热点追踪、测试与调试                    |

## 开发历程

### 项目起源

做新媒体运营最头疼的就是每天找选题。我们想：这些重复性的工作，为什么不能让 AI 来做？于是就有了这个项目。

最初的想法很简单：
1. 自动抓取各大平台的热榜
2. AI 分析哪些话题值得写
3. 自动生成适合不同平台的文案

但实现起来遇到了很多坑...

## 遇到的主要问题与解决方案

### 1. DeepSeek API 兼容性问题

**问题描述**：
Agent Framework 默认使用 OpenAI 的多模态消息格式：
```python
content: [{"type": "text", "text": "..."}]
```

但 DeepSeek API 只接受纯字符串格式：
```python
content: "..."
```

**解决方案**：
创建了 `DeepSeekChatClient` 适配器（`utils/deepseek_adapter.py`），重写了消息解析方法：

```python
class DeepSeekChatClient(OpenAIChatClient):
    def _openai_chat_message_parser(self, message):
        """将多模态消息转换为纯文本"""
        if isinstance(message.content, list):
            # 提取所有文本内容
            text_parts = [
                item.get("text", "") 
                for item in message.content 
                if item.get("type") == "text"
            ]
            message.content = " ".join(text_parts)
        return message
```

**贡献者**：范延哲  
**时间**：2025-10-20  
**影响**：解决了 DeepSeek API 调用失败的问题，让项目可以使用便宜的国产模型

---

### 2. DevUI TextContent 序列化问题

**问题描述**：
在 DevUI 中运行工作流时报错：
```
Error converting agent update: Object of type TextContent is not JSON serializable
```

**根本原因**：
1. Agent Framework 为支持多模态，会自动创建 `TextContent` 对象
2. DevUI 在序列化消息时无法处理这些对象
3. 问题出在 `_parse_text_from_choice()` 方法，它是 `TextContent` 创建的源头

**解决方案**：
在 `DeepSeekChatClient` 中重写了三个关键方法：

```python
def _parse_text_from_choice(self, choice):
    """直接返回 None，阻止父类创建 TextContent"""
    return None

def _create_chat_response_update(self, chunk):
    """手动提取文本并设置到 _text 属性"""
    chat_response_update = super()._create_chat_response_update(chunk)
    
    # 手动提取文本
    if hasattr(chunk, 'choices') and chunk.choices:
        choice = chunk.choices[0]
        if hasattr(choice.delta, 'content'):
            object.__setattr__(
                chat_response_update.delta, 
                '_text', 
                choice.delta.content
            )
    
    # 确保 contents 为空
    chat_response_update.delta.contents = []
    return chat_response_update
```

**关键洞察**：
- 必须在源头（`_parse_text_from_choice`）阻止 `TextContent` 创建
- 使用 `object.__setattr__()` 直接修改只读属性
- 同时处理流式和非流式两条路径

**贡献者**：范延哲、何旭  
**时间**：2025-10-21  
**影响**：解决了 DevUI 无法运行的问题，让可视化调试成为可能

---

### 3. MCP 工具生命周期管理

**问题描述**：
在 DevUI 中运行工作流时报错：
```
Workflow execution error: Failed to enter context manager.
```

**根本原因**：
1. DevUI 模块加载是同步环境，不能使用 `await`
2. MCP 工具连接是异步操作，需要 `await tool.connect()`
3. 工具创建了但没有连接（半初始化状态），导致 context manager 失败

**解决方案**：
在 Workflow Executor 中动态创建和连接 MCP 工具：

```python
class MCPHotspotExecutor(Executor):
    @handler
    async def fetch_hotspots(self, messages, ctx):
        # 在异步环境中创建和连接工具
        async with MCPStreamableHTTPTool(
            name="daily-hot-mcp",
            url=self.mcp_url,
            load_tools=True
        ) as mcp_tool:
            # 创建临时 agent 使用工具
            temp_agent = self.client.create_agent(
                name="temp_hotspot_agent",
                instructions=HOTSPOT_INSTRUCTIONS,
                tools=[mcp_tool]
            )
            
            # 执行查询
            result = await temp_agent.run(query)
            
            # 发送结果到下游
            await ctx.send_message([ChatMessage(...)])
```

**关键洞察**：
- 不要在模块加载时创建 MCP 工具
- 使用 `async with` 确保工具正确连接和断开
- 在 handler 中动态创建工具，利用异步环境

**贡献者**：范延哲、郑显龙  
**时间**：2025-10-21  
**影响**：解决了 DevUI 中 MCP 工具无法使用的问题

---

### 4. 小红书自动发布问题

**问题描述**：
使用 xhs_mcp_server 自动发布到小红书时报错：
```
no such element: Unable to locate element: {"method":"css selector","selector":".upload-input"}
```

**根本原因**：
小红书更新了页面结构，xhs_mcp_server 使用的 CSS 选择器 `.upload-input` 已经失效。

**解决方案**：
改为半自动化方案：
1. 工作流生成小红书文案（JSON 格式）
2. 用户复制文案到小红书 App
3. 手动选图发布

**为什么这样更好**：
- ✅ 可以最后检查内容质量
- ✅ 可以选更合适的图片
- ✅ 避免自动化发布的账号风险
- ✅ 不依赖第三方工具的稳定性

**贡献者**：何旭、郑显龙  
**时间**：2025-10-21  
**影响**：虽然没有实现全自动发布，但找到了更实用的方案

---

### 5. 内容质量控制

**问题描述**：
AI 生成的内容有时候会"胡说八道"，编造不存在的热点。

**解决方案**：

1. **使用 think-tool**：
   ```python
   from agent_framework import MCPStdioTool
   
   async with MCPStdioTool(
       name="think-tool",
       command="uvx",
       args=["think-tool@latest"]
   ) as think_tool:
       # 让 AI 有更多时间"思考"
       analysis_agent = client.create_agent(
           name="analysis_agent",
           tools=[think_tool],
           instructions=ANALYSIS_INSTRUCTIONS
       )
   ```

2. **优化 Prompt**：
   - 强调"基于真实热点，不要编造"
   - 要求输出 JSON 格式，方便验证数据完整性
   - 提供具体的输出示例

3. **数据验证**：
   ```python
   # 验证 JSON 格式
   try:
       content_json = json.loads(content_text)
       title = content_json.get("title", "")
       content = content_json.get("content", "")
   except json.JSONDecodeError:
       logger.error("文案不是有效的 JSON 格式")
       return
   ```

**贡献者**：何旭、范延哲  
**时间**：2025-10-21  
**影响**：显著提升了生成内容的质量和可靠性

---

### 6. Git 大文件推送问题

**问题描述**：
推送到 GitCode 时报错：
```
Error: size of the file 'chromedriver.exe', is 18 MiB, 
which has exceeded the limited size (10 MiB)
```

**解决方案**：
1. 从 git 追踪中移除 chromedriver：
   ```bash
   git rm -r --cached chromedriver/
   ```

2. 更新 .gitignore：
   ```
   chromedriver/
   ```

3. 在 README 中添加安装说明：
   ```markdown
   ## ChromeDriver 安装
   
   npx @puppeteer/browsers install chromedriver@YOUR_CHROME_VERSION
   ```

**贡献者**：郑显龙  
**时间**：2025-10-21  
**影响**：解决了仓库推送问题，减小了仓库体积

---

## 技术选型的思考

### 为什么选 Microsoft Agent Framework？

我们对比了几个框架：

| 框架 | 优点 | 缺点 | 为什么没选 |
|------|------|------|-----------|
| LangChain | 生态丰富 | 太重，学习曲线陡 | 对我们的场景来说太复杂 |
| AutoGen | 微软出品 | 主要面向对话场景 | 不适合我们的流水线场景 |
| CrewAI | 简单易用 | 功能有限 | 扩展性不够 |
| Agent Framework | 灵活，MCP 原生支持 | 比较新，文档少 | ✅ 最适合我们 |

**最终选择 Agent Framework 的原因**：
1. 支持多种工作流模式（Sequential、Parallel、Graph）
2. 原生支持 MCP 协议
3. 自带 DevUI 可视化
4. 微软出品，持续维护

### 为什么选 DeepSeek？

| 模型        | 价格  | 效果  | 为什么选/不选 |
| --------- | --- | --- | ------- |
| CLAUDE4.5 | 贵   | 最好  | 成本太高    |
| GPT-5     | 便宜  | 一般  | 效果不够好   |
| DeepSeek  | 很便宜 | 不错  | ✅ 性价比最高 |

**实际成本**：
- 一次完整运行（抓热点+分析+生成内容）：不到 1 毛钱
- 每天运行 10 次：不到 1 块钱
- 一个月：不到 30 块钱

## 开发规范

### 代码风格

1. **使用类型注解**：
   ```python
   async def fetch_hotspots(
       self, 
       messages: list[ChatMessage], 
       ctx: WorkflowContext[list[ChatMessage]]
   ) -> None:
   ```

2. **添加详细的日志**：
   ```python
   logger.info(f"[{self.id}] 开始获取热点数据")
   logger.debug(f"[{self.id}] 查询: {query}")
   ```

3. **错误处理**：
   ```python
   try:
       result = await agent.run(query)
   except Exception as e:
       logger.error(f"执行失败: {e}")
       import traceback
       traceback.print_exc()
   ```

### 提交规范

使用语义化提交信息：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: 添加小红书内容生成功能
fix: 修复 DeepSeek API 兼容性问题
docs: 更新 README 添加团队信息
```

### 文档规范

1. **代码注释**：
   - 复杂逻辑必须添加注释
   - 说明"为什么"而不是"是什么"

2. **README 更新**：
   - 添加新功能时更新 README
   - 记录已知问题和限制

3. **Learn.md 记录**：
   - 遇到的坑和解决方案
   - 技术决策的思考过程

## 测试指南

### 本地测试

1. **测试 MCP 工具连接**：
   ```bash
   python test_xhs_direct.py
   ```

2. **测试完整工作流**：
   ```bash
   python test_devui_final.py
   ```

3. **测试 DevUI**：
   ```bash
   python start_devui.ps1
   # 访问 http://localhost:9000
   ```

### 调试技巧

1. **查看详细日志**：
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **使用 DevUI 可视化**：
   - 实时看到每个 Agent 的执行过程
   - 查看工具调用的参数和结果

3. **独立测试组件**：
   - 先测试 MCP 工具连接
   - 再测试 Agent 执行
   - 最后测试完整工作流

## 未来计划

### 短期（1-2 周）

- [ ] 优化内容生成质量
- [ ] 添加更多平台支持（抖音、快手）
- [ ] 改进错误处理和日志

### 中期（1-2 个月）

- [ ] 添加图片推荐功能
- [ ] 支持定时任务
- [ ] 添加内容审核功能

### 长期（3-6 个月）

- [ ] 支持多语言
- [ ] 添加用户反馈机制
- [ ] 优化性能和成本

## 如何贡献

1. **Fork 项目**
2. **创建分支**：`git checkout -b feature/your-feature`
3. **提交更改**：`git commit -m "feat: your feature"`
4. **推送分支**：`git push origin feature/your-feature`
5. **创建 Pull Request**

## 联系我们

- **范延哲**（队长）：15071203491
- **何旭**：19232749731
- **郑显龙**：18995717223

## 致谢

感谢以下开源项目：
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Daily Hot MCP](https://github.com/fatwang2/daily-hot-mcp)
- [DeepSeek](https://www.deepseek.com/)

---

**武汉商学院 AI 团队** 🎓  
**2025年10月**
