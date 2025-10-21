# 项目经验总结

## 0. DevUI TextContent 序列化问题 - 真正的根本原因

### 0.1 问题表现
```
Error converting agent update: Object of type TextContent is not JSON serializable
Location: agent_framework_devui._mapper.py:303
```

### 0.2 真正的根本原因（多个）

#### 原因 1：`ChatMessage(text=...)` 会创建 TextContent

**关键发现**：
```python
# ❌ 错误：会在 contents 中创建 TextContent 对象
msg = ChatMessage(role=Role.ASSISTANT, text="Hello")
print(msg.contents)  # [TextContent(text="Hello")]

# ✅ 正确：使用 contents=[] 并手动设置 _text
msg = ChatMessage(role=Role.ASSISTANT, contents=[])
object.__setattr__(msg, '_text', "Hello")
print(msg.contents)  # []
```

**影响位置**：
- `agents/social_media_workflow/__init__.py` 的 `TextOnlyConversation` executor
- 任何创建 `ChatMessage` 的地方

#### 原因 2：`_parse_text_from_choice()` 返回什么类型很关键

#### 调用链路
```
_create_chat_response_update(chunk)
  └─> 调用 _parse_text_from_choice(choice)
       └─> 父类返回: TextContent(text=..., raw_representation=choice)
       └─> 父类使用: if text_content := self._parse_text_from_choice(choice):
                        delta.contents.append(text_content)  # ❌ 添加到 contents
```

#### 错误的修复尝试

**❌ 尝试 1**：在 `_parse_text_from_choice()` 中返回纯字符串
```python
def _parse_text_from_choice(self, choice):
    text_content = super()._parse_text_from_choice(choice)
    return text_content.text  # ❌ 返回字符串
```
**结果**：字符串被添加到 `delta.contents`，仍然无法序列化！

**❌ 尝试 2**：在 `_create_chat_response_update()` 后清空 `delta.contents`
```python
if chat_response_update.delta.contents:
    chat_response_update.delta.contents = []  # ❌ 太晚了
```
**结果**：DevUI 在父类方法返回之前就序列化了，清空无效！

#### ✅ 正确的解决方案

**🔑 关键：让 `_parse_text_from_choice()` 返回 `None`**

```python
def _parse_text_from_choice(self, choice):
    # 🚫 直接返回 None，阻止父类添加任何内容
    return None
```

**后果**：父类的 `if text_content := ...` 判断为 False，不会添加任何内容到 `delta.contents`

**补充**：手动从 `chunk` 提取文本并设置到 `delta._text`

```python
def _create_chat_response_update(self, chunk):
    chat_response_update = super()._create_chat_response_update(chunk)
    
    # 手动提取文本（因为 _parse_text_from_choice 返回 None）
    if hasattr(chunk, 'choices') and chunk.choices:
        choice = chunk.choices[0]
        if hasattr(choice.delta, 'content'):
            object.__setattr__(chat_response_update.delta, '_text', choice.delta.content)
    
    # 确保 delta.contents 为空
    chat_response_update.delta.contents = []
    
    return chat_response_update
```

### 0.3 问题分析过程（历史）

#### 第一层：DeepSeek API 兼容性
- Agent Framework 使用多模态数组格式：`content: [{"type": "text", "text": "..."}]`
- DeepSeek API 只接受字符串：`content: "..."`
- **解决**：重写 `_openai_chat_message_parser()`

#### 第二层：DevUI 序列化 ChatMessage
- DevUI 在 agent 执行过程中序列化 `ChatMessage`
- 如果 `ChatMessage.contents` 包含 `TextContent` 对象会报错
- **解决**：重写 `_create_chat_response()` 和 `_create_chat_response_update()`

#### 第三层：根本原因
- **问题**：即使重写了响应创建方法，`TextContent` 对象仍然被创建
- **原因**：父类的 `_parse_text_from_choice()` 方法返回 `TextContent` 对象
- **后果**：这个对象进入系统的各个角落，包括 `AgentRunResponseUpdate`

### 0.3 根本解决方案

**🔑 关键：在源头阻止 `TextContent` 对象的创建**

需要重写 `_parse_text_from_choice()` 方法，它是 `TextContent` 对象创建的源头：

```python
class DeepSeekChatClient(OpenAIChatClient):
    def _parse_text_from_choice(self, choice):
        """
        从 choice 提取文本时返回纯字符串，而不是 TextContent 对象
        这是最根本的修复点！
        """
        # 调用父类方法（可能返回 TextContent 对象）
        text_content = super()._parse_text_from_choice(choice)
        
        # 如果是 TextContent 对象，提取纯文本
        if text_content and hasattr(text_content, 'text'):
            return text_content.text  # ✅ 返回字符串
        
        return text_content
    
    def _create_chat_response(self, response, chat_options):
        """清理 ChatMessage.contents 中的 TextContent"""
        chat_response = super()._create_chat_response(response, chat_options)
        
        if hasattr(chat_response, 'messages') and chat_response.messages:
            for msg in chat_response.messages:
                if hasattr(msg, 'contents') and msg.contents:
                    # 清空 contents，只保留 text 属性
                    msg.contents = []
                    # 确保有 text 属性
                    if msg.text:
                        object.__setattr__(msg, '_text', msg.text)
        
        return chat_response
    
    def _create_chat_response_update(self, chunk):
        """清理流式响应中的 TextContent"""
        chat_response_update = super()._create_chat_response_update(chunk)
        
        # 同样的清理逻辑
        if hasattr(chat_response_update, 'messages') and chat_response_update.messages:
            for msg in chat_response_update.messages:
                if hasattr(msg, 'contents') and msg.contents:
                    msg.contents = []
                    if msg.text:
                        object.__setattr__(msg, '_text', msg.text)
        
        # 清理 delta.contents
        if hasattr(chat_response_update, 'delta') and chat_response_update.delta:
            if hasattr(chat_response_update.delta, 'contents'):
                chat_response_update.delta.contents = []
        
        return chat_response_update
```

### 0.4 为什么这样有效

1. **`_parse_text_from_choice()`**: 在 `_create_chat_response()` 内部被调用，是 `TextContent` 创建的源头
2. **返回纯字符串**: 避免 `TextContent` 对象进入 `ChatMessage.contents`
3. **双重保护**: 即使父类创建了 `TextContent`，我们也在 `_create_chat_response()` 中清理

### 0.5 关键教训

✅ **问题定位要准确**
- 不要只看表面症状（序列化错误）
- 要追溯到对象创建的源头

✅ **修复要在源头**
- 在 `_parse_text_from_choice()` 阻止 `TextContent` 创建
- 比在下游各处清理更有效

✅ **理解框架机制**
- `_create_chat_response()` 调用 `_parse_text_from_choice()`
- `_parse_text_from_choice()` 返回什么，`contents` 就包含什么

✅ **流式响应的陷阱**
- 流式响应用 `_create_chat_response_update()`
- 需要同时修复流式和非流式两条路径

### 调试经验

1. **独立测试有效**
   - `simple_test_textcontent.py` 通过
   - 说明 `DeepSeekChatClient` 本身没问题

2. **DevUI 仍然失败**
   - 说明问题不在直接调用路径
   - 而是在 DevUI 内部的序列化路径

3. **追踪调用链**
   - DevUI → `_mapper.py:303` → `_convert_agent_update()`
   - → `update.contents` → 包含 `TextContent`
   - → `TextContent` 从哪来？→ `_parse_text_from_choice()`

---

## 1. Workflow Context Manager 错误诊断 (2025-10-21)

### 问题表现
```
Workflow execution error: Failed to enter context manager.
时间: 16:43:52
```

### 问题分析

当执行 `workflow.run(user_query)` 时抛出此错误，这表示在进入 context manager 时发生异常。

**可能的原因**：
1. MCP 工具连接在异步上下文中失败
2. SequentialBuilder.build() 返回的工作流对象有 context manager 问题
3. 工作流执行中的异步资源泄漏

### 修复方案

#### 方案 1：添加资源清理机制 ✅
在 `SequentialWorkflowCoordinator` 中添加：
- `cleanup()` 方法：关闭所有 MCP 工具
- `__aenter__` 和 `__aexit__` 方法：支持异步上下文管理
- 在 `run_workflow()` 的 finally 块中调用清理

#### 方案 2：改进错误诊断 ✅
添加详细的诊断日志：
- `build_workflow()` 中检查 SequentialBuilder 的可用方法
- 在 `run_workflow()` 中捕捉并报告具体的 context manager 错误
- 记录工作流对象类型和可用方法

#### 方案 3：追踪工具生命周期 ✅
- 在 `_create_hotspot_agent()` 中将创建的工具添加到 `self.mcp_tools` 列表
- 在 `cleanup()` 中逐个关闭所有工具
- 确保异步资源被正确释放

### 实施要点

**关键修改**：
1. `workflow_coordinator_sequential.py`：
   - 添加 `self.mcp_tools = []` 追踪工具
   - 添加 `cleanup()` 方法关闭工具
   - 在 `run_workflow()` 的 finally 块中调用清理
   - 在 `_create_hotspot_agent()` 中追踪创建的工具

2. `run_workflow_sequential.py`：
   - 在 main() 中使用 try-finally 确保资源清理
   - 添加详细的错误日志

3. `tests/test_context_manager_fix.py`：
   - 创建诊断脚本测试 SequentialBuilder
   - 测试 MCP 工具 context manager 支持
   - 验证工作流构建和执行

### 关键教训

✅ **异步资源管理**
- 异步工具必须使用 finally 或 context manager 确保清理
- 即使工作流执行失败，资源也要被释放

✅ **诊断的重要性**
- 添加详细的类型检查和方法检查
- 记录对象的结构信息便于调试

✅ **工具生命周期追踪**
- 集中管理工具的创建和销毁
- 避免工具泄漏

---

## 2. DevUI vs 直接运行格式问题诊断 (2025-10-21 16:55)

### 问题发现

当用户说"不使用DevUI可以正常运行，但使用DevUI就会因为格式不对齐报错"时，我们进行了对比测试：

**直接运行**：✅ 成功
```
python test_direct_workflow.py
成功: True
执行时间: 213.79秒
生成内容: wechat, weibo, bilibili
```

**DevUI 运行**：❌ 失败
```
Workflow execution error: Failed to enter context manager.
时间: 16:43:52
```

### 根本原因

两种运行方式的差异：

| 维度 | 直接运行 | DevUI 运行 |
|------|--------|---------|
| 调用方式 | 直接调用工作流 | DevUI 包装为 Agent |
| 消息格式 | 无要求 | 需要严格的序列化格式 |
| TextContent | 可以包含对象 | 必须清空内容数组 |
| 序列化 | 不需要 | JSON 序列化要求 |

### DevUI 期望的消息格式

**关键发现**：DevUI 期望 `ChatMessage` 满足：
```python
# ✅ 正确
msg = ChatMessage(role=Role.ASSISTANT, contents=[])  # 空数组！
object.__setattr__(msg, '_text', "content")

# ❌ 错误（会导致 TextContent 在 contents 中）
msg = ChatMessage(role=Role.ASSISTANT, text="content")
```

### 修复方案（多层次）

#### 1. 客户端层（DeepSeekChatClient）
- `_parse_text_from_choice()` 直接返回字符串（不创建 TextContent）
- `_create_chat_response()` 清空所有 `msg.contents`
- `_create_chat_response_update()` 清空 `delta.contents`

#### 2. Executor 层（TextOnlyConversation）
- 创建消息时使用 `ChatMessage(contents=[])`
- 用 `object.__setattr__()` 设置 `_text` 属性
- 不使用 `ChatMessage(text=...)` 初始化

#### 3. 协调器层（SequentialWorkflowCoordinator）
- 追踪工具生命周期
- 在 finally 块中清理资源
- 捕捉并报告异常

### 关键学习

✅ **问题的关键**
- Agent Framework 为支持多模态自动创建 TextContent 对象
- DevUI 序列化时无法处理这些对象
- 必须在源头（ChatClient）阻止 TextContent 创建

✅ **修复的精妙之处**
- `_parse_text_from_choice()` 完全绕过父类，直接返回字符串
- 在响应处理方法中统一清理，而不是在各处分散处理
- 使用 `object.__setattr__()` 直接修改只读属性

✅ **验证方法**
- 直接运行验证工作流逻辑
- DevUI 运行验证序列化兼容性
- 分层修复确保没有遗漏

---

## 3. DevUI 中 MCP 工具的同步/异步问题 (2025-10-21 17:25)

### 问题表现

DevUI 启动成功，但执行 workflow 时报错：
```
Workflow execution error: Failed to enter context manager.
```

### 根本原因

**同步/异步环境不匹配**：

1. **DevUI 模块加载** = 同步环境
   - DevUI 使用 `import agents.social_media_workflow` 加载模块
   - 这是一个**同步操作**，不能使用 `await`

2. **MCP 工具连接** = 异步操作
   ```python
   tool = MCPStreamableHTTPTool(url="...")
   await tool.connect()  # ❌ 在同步环境中无法调用
   ```

3. **Context Manager 失败**
   - 工具创建了但没有连接（半初始化状态）
   - Workflow 执行时尝试进入工具的 context manager
   - 因为工具未连接，context manager 失败

### 为什么直接运行可以工作？

直接运行（`test_direct_workflow.py`）使用异步环境：

```python
async def main():
    # ✅ 在异步函数中可以连接工具
    coordinator = SequentialWorkflowCoordinator(...)
    await coordinator.initialize_agents()  # 内部会 await tool.connect()
    result = await coordinator.run_workflow(query)
```

### 解决方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| 1. 不使用 MCP 工具 | 简单，DevUI 可用 | 无法调用外部工具 | 测试 workflow 结构 |
| 2. 使用模拟函数 | DevUI 可用，有工具能力 | 数据不真实 | 开发和演示 |
| 3. 动态创建工具 | 真实工具，DevUI 可用 | 实现复杂 | 生产环境 |
| 4. 只用直接运行 | 完整功能 | 无 DevUI 界面 | 生产部署 |

### ✅ 成功的解决方案

**方案 1：在 Workflow Executor 中动态创建 MCP 工具**（已实施）

```python
# agents/social_media_workflow/__init__.py
class MCPHotspotExecutor(Executor):
    """在 workflow 执行时动态创建和连接 MCP 工具"""
    
    @handler
    async def fetch_hotspots(self, messages: list[ChatMessage], 
                            ctx: WorkflowContext[list[ChatMessage]]) -> None:
        # ✅ 关键：使用 async with 在异步环境中创建和连接
        async with MCPStreamableHTTPTool(
            name="daily-hot-mcp",
            url=self.mcp_url,
            load_tools=True
        ) as mcp_tool:
            # 创建临时 agent 使用 MCP 工具
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

**效果**：
- ✅ DevUI 可以正常启动和运行
- ✅ Workflow 结构完整
- ✅ **可以调用真实的 MCP 工具**
- ✅ **获取真实的热点数据**
- ✅ 工具在 async with 中自动连接和断开

### 未来改进方向

**方案 3**：实现动态工具加载

```python
class DynamicMCPExecutor(Executor):
    """在 workflow 执行时动态创建和连接 MCP 工具"""
    
    @handler
    async def run(self, messages, ctx):
        # 在异步环境中创建工具
        tool = MCPStreamableHTTPTool(...)
        await tool.connect()
        
        # 使用工具
        result = await tool.call_function(...)
        
        # 清理
        await tool.close()
```

### 关键教训

✅ **理解环境限制**
- DevUI 模块加载 = 同步
- MCP 工具连接 = 异步
- 两者不兼容

✅ **选择合适的方案**
- 开发/测试：使用 DevUI（无 MCP）
- 生产部署：使用直接运行（有 MCP）

✅ **文档化限制**
- 在代码中明确说明为什么不能使用某些功能
- 提供替代方案

---

## 4. DevUI 修复方法的重要纠正 (2025-10-21 17:00)

### ❌ 我的错误做法

当 DevUI 运行时出现 "TextContent is not JSON serializable" 错误，我错误地采用了：

1. **重写 `_parse_text_from_choice()` 返回字符串**
   - ❌ 框架期望返回 `TextContent | None`，不是字符串
   - ❌ 字符串被添加到 `contents` 列表会破坏框架类型

2. **清空 `contents` 列表并设置 `_text`**
   - ❌ DevUI 的 `MessageMapper._convert_agent_update()` 检查：
     ```python
     if not hasattr(update, "contents") or not update.contents:
         return events  # 返回空列表！用户看不到输出
     ```
   - ❌ DevUI 依赖 `contents` 中的 `Content` 对象生成事件

### ✅ 正确的做法

**原则**：保持 `contents` 中的 `TextContent` 对象，让 DevUI 正常处理

1. **不要重写 `_parse_text_from_choice()`**
   ```python
   def _parse_text_from_choice(self, choice):
       # 直接调用父类，让它创建 TextContent
       return super()._parse_text_from_choice(choice)
   ```

2. **不要清空 `contents`**
   - 让 `TextContent` 对象保持在 `contents` 中
   - DevUI 通过 `content_mappers` 将其映射为事件

3. **只处理特殊情况：FunctionResult 序列化**
   ```python
   def _create_chat_response(self, response, chat_options):
       chat_response = super()._create_chat_response(response, chat_options)
       
       # 只处理 FunctionResult 的 result 字段
       if hasattr(chat_response, 'messages') and chat_response.messages:
           for msg in chat_response.messages:
               if hasattr(msg, 'contents') and msg.contents:
                   for content in msg.contents:
                       # FunctionResult 的 result 字段需要转换为字符串
                       if 'FunctionResult' in type(content).__name__:
                           result_text = self._content_to_string(content.result)
                           object.__setattr__(content, 'result', result_text)
       
       return chat_response
   ```

### 关键洞察

DevUI 期望的数据流：

```
TextContent 对象
    ↓（在 contents 中）
DevUI 的 MessageMapper._convert_agent_update()
    ↓
content_mappers 映射
    ↓
OpenAI Responses API 事件
    ↓
DevUI 前端显示
```

**不应该**：
- 在中间清空 `contents`（会导致返回空事件列表）
- 用字符串替换 `TextContent`（DevUI 无法识别）
- 试图避免 `TextContent` 对象（DevUI 需要它们）

### 真正的问题

`TextContent is not JSON serializable` 错误的真实原因可能是：
1. 在某个特定的序列化路径中出现
2. 不是所有 `TextContent` 都无法序列化（它实现了 `SerializationMixin`）
3. 可能是在 DevUI 的某个特殊操作中触发

**解决方法**：
- 保持标准的 `ChatMessage` 结构
- 使用标准的 `ChatMessage(role=..., text="...")` 构造
- 让框架和 DevUI 正常处理

### 实施改进

1. **DeepSeekChatClient**：
   - ✅ 不重写 `_parse_text_from_choice()`
   - ✅ 不清空 `contents`
   - ✅ 只处理 `FunctionResult.result` 的序列化

2. **工作流协调器**：
   - ✅ 保持消息的原始结构
   - ✅ 不修改 `contents` 列表

3. **Executor**：
   - ✅ 使用标准 `ChatMessage(text="...")` 构造
   - ✅ 让框架自动创建 `TextContent`

### 关键教训

✅ **理解框架的设计意图**
- DevUI 不是 bug，它的设计是正确的
- `TextContent` 在 `contents` 中是正常的设计

✅ **不要试图绕过框架**
- 清空 `contents` 会破坏 DevUI 的事件生成
- 返回错误的类型会破坏框架的类型期望

✅ **调查真正的问题源头**
- 序列化错误的真实原因可能在其他地方
- 应该在 DevUI 的 `MessageMapper` 层面添加错误处理
- 不是所有问题都能通过修改数据结构解决

