# Think Tool 实现详解

## 概述

第二个智能体（内容分析智能体）使用的 **Structured Thinking Tool** 实际上是 `@modelcontextprotocol/server-sequential-thinking` MCP 服务器提供的工具。

## 源代码位置

- **GitHub 仓库**: https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking
- **NPM 包**: `@modelcontextprotocol/server-sequential-thinking`
- **主要文件**:
  - `index.ts` - MCP 服务器入口
  - `lib.ts` - 核心思考逻辑实现

## 核心实现原理

### 1. 数据结构

```typescript
interface ThoughtData {
  thought: string;              // 当前思考内容
  thoughtNumber: number;        // 当前思考步骤编号
  totalThoughts: number;        // 预计总思考步骤数
  nextThoughtNeeded: boolean;   // 是否需要继续思考
  isRevision?: boolean;         // 是否是修订
  revisesThought?: number;      // 修订哪个思考步骤
  branchFromThought?: number;   // 从哪个步骤分支
  branchId?: string;            // 分支标识符
  needsMoreThoughts?: boolean;  // 是否需要更多思考
}
```

### 2. 核心类：SequentialThinkingServer

```typescript
class SequentialThinkingServer {
  private thoughtHistory: ThoughtData[] = [];           // 思考历史记录
  private branches: Record<string, ThoughtData[]> = {}; // 分支记录
  private disableThoughtLogging: boolean;               // 是否禁用日志
  
  // 处理思考步骤
  processThought(input: unknown): Response
  
  // 验证输入数据
  validateThoughtData(input: unknown): ThoughtData
  
  // 格式化思考输出
  formatThought(thoughtData: ThoughtData): string
}
```

### 3. 工作流程

```
用户请求
    ↓
智能体开始思考
    ↓
调用 sequentialthinking 工具
    ↓
传入参数：
  - thought: "第一步：分析问题..."
  - thoughtNumber: 1
  - totalThoughts: 5
  - nextThoughtNeeded: true
    ↓
SequentialThinkingServer.processThought()
    ↓
1. 验证输入数据
2. 保存到 thoughtHistory
3. 如果是分支，保存到 branches
4. 格式化输出（带颜色和边框）
5. 返回状态信息
    ↓
智能体继续下一步思考
    ↓
重复直到 nextThoughtNeeded = false
```

## 思考过程可视化

工具会在控制台输出格式化的思考过程：

```
┌──────────────────────────────────────┐
│ 💭 Thought 1/5                       │
├──────────────────────────────────────┤
│ 首先识别热点的核心主题...            │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 💭 Thought 2/5                       │
├──────────────────────────────────────┤
│ 分析关键词和情感倾向...              │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 🔄 Revision 3/5 (revising thought 2) │
├──────────────────────────────────────┤
│ 重新考虑情感分析的角度...            │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ 🌿 Branch 4/6 (from thought 2, ID: A)│
├──────────────────────────────────────┤
│ 探索另一种分析路径...                │
└──────────────────────────────────────┘
```

## 关键特性

### 1. 动态调整思考步骤

```typescript
// 如果当前步骤超过预计总数，自动调整
if (validatedInput.thoughtNumber > validatedInput.totalThoughts) {
  validatedInput.totalThoughts = validatedInput.thoughtNumber;
}
```

### 2. 支持思考修订

```typescript
{
  thought: "重新考虑之前的分析...",
  thoughtNumber: 3,
  totalThoughts: 5,
  isRevision: true,
  revisesThought: 2,  // 修订第2步
  nextThoughtNeeded: true
}
```

### 3. 支持思考分支

```typescript
{
  thought: "探索另一种可能性...",
  thoughtNumber: 4,
  totalThoughts: 6,
  branchFromThought: 2,  // 从第2步分支
  branchId: "alternative-A",
  nextThoughtNeeded: true
}
```

### 4. 思考历史追踪

```typescript
// 返回的状态信息
{
  thoughtNumber: 3,
  totalThoughts: 5,
  nextThoughtNeeded: true,
  branches: ["alternative-A", "alternative-B"],
  thoughtHistoryLength: 8
}
```

## 在分析智能体中的应用

### 配置方式

在 `config/mcp_servers.json` 中配置：

```json
{
  "structured-thinking": {
    "isActive": true,
    "name": "structured-thinking",
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  }
}
```

### 使用示例

分析智能体在处理热点分析时的思考过程：

```
步骤 1: 问题定义
  → "识别热点的核心主题和关键信息"

步骤 2: 数据收集
  → "搜索相关学术背景和研究数据"

步骤 3: 内容分析
  → "提取关键词、分析情感倾向"

步骤 4: 趋势预测
  → "基于数据预测发展趋势"

步骤 5: 受众分析
  → "分析目标受众特征和行为"

步骤 6: 综合洞察
  → "生成数据驱动的分析报告"
```

## 为什么使用这个工具？

### 1. 结构化推理
- 将复杂分析任务分解为清晰的步骤
- 每一步都有明确的目标和输出

### 2. 可追溯性
- 记录完整的思考历史
- 便于调试和优化分析过程

### 3. 灵活性
- 支持动态调整思考步骤数
- 可以修订之前的思考
- 可以探索多个分析路径

### 4. 质量控制
- 强制智能体进行深度思考
- 避免简单的一次性回答
- 确保分析的全面性和深度

### 5. 透明度
- 用户可以看到完整的推理过程
- 增强对分析结果的信任

## 环境变量

```bash
# 禁用思考日志输出（生产环境）
DISABLE_THOUGHT_LOGGING=true
```

## 工具调用示例

### Python 代码中的调用

```python
# 智能体会自动调用这个工具
# 不需要手动编写调用代码

# 工具调用参数示例：
{
  "thought": "首先，我需要分析这个热点的核心主题...",
  "thoughtNumber": 1,
  "totalThoughts": 5,
  "nextThoughtNeeded": True
}

# 工具返回示例：
{
  "thoughtNumber": 1,
  "totalThoughts": 5,
  "nextThoughtNeeded": True,
  "branches": [],
  "thoughtHistoryLength": 1
}
```

## 与其他工具的协同

在分析智能体中，Structured Thinking 工具与其他工具协同工作：

```
Structured Thinking (思考框架)
    ↓
Semantic Scholar (学术搜索)
    ↓
Structured Thinking (分析学术资料)
    ↓
Chart Generator (生成可视化)
    ↓
Structured Thinking (综合洞察)
    ↓
输出最终分析报告
```

## 参考资源

- **GitHub**: https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking
- **NPM**: https://www.npmjs.com/package/@modelcontextprotocol/server-sequential-thinking
- **MCP 文档**: https://modelcontextprotocol.io
- **本地配置**: `social-media-ai-system/config/mcp_servers.json`
- **智能体实现**: `social-media-ai-system/agents/analysis_agent.py`

## 总结

`mcp_LIFw3vNPhS4KRORHku5hV_capture_thought` 是一个强大的结构化思考工具，它通过：

1. **记录思考历史** - 保存每一步的推理过程
2. **支持动态调整** - 可以增加或减少思考步骤
3. **允许修订和分支** - 可以重新思考或探索多个路径
4. **提供可视化输出** - 清晰展示思考过程
5. **确保深度分析** - 强制智能体进行系统化思考

这使得分析智能体能够像人类专家一样，进行有条理、可追溯、高质量的深度分析。
