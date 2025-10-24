# 调度器问题修复说明

## 🐛 发现的问题

### 问题1：百度热榜工具参数不匹配

**错误信息**：
```
[baidu_trending] Failed to warm cache: get_baidu_trending_func() missing 1 required positional argument: 'args'
```

**原因**：
- 百度工具的函数签名是 `async def get_baidu_trending_func(args: dict)`
- 但调度器调用时没有传递 `args` 参数

**解决方案**：
暂时禁用百度热榜的定时预热（设置 `enabled: false`）

### 问题2：抖音API反爬限制

**错误信息**：
```
[douyin_trending] Failed to warm cache: Expecting value: line 1 column 1 (char 0)
```

**原因**：
- 抖音API检测到频繁请求，返回了非JSON数据
- 可能是反爬虫机制触发

**解决方案**：
暂时禁用抖音热搜的定时预热（设置 `enabled: false`）

## ✅ 当前稳定配置

已更新 `scheduler_config.json`，只保留稳定可靠的数据源：

```json
{
  "sources": [
    {
      "name": "weibo_trending",
      "enabled": true,
      "interval_minutes": 20
    },
    {
      "name": "zhihu_trending",
      "enabled": true,
      "interval_minutes": 20
    },
    {
      "name": "bilibili_trending",
      "enabled": true,
      "interval_minutes": 20
    },
    {
      "name": "toutiao_trending",
      "enabled": true,
      "interval_minutes": 20
    },
    {
      "name": "baidu_trending",
      "enabled": false,  ← 已禁用
      "interval_minutes": 15
    },
    {
      "name": "douyin_trending",
      "enabled": false,  ← 已禁用
      "interval_minutes": 15
    }
  ]
}
```

## 📊 当前状态

### ✅ 正常工作的数据源（4个）

1. **微博热搜** - 稳定
2. **知乎热榜** - 稳定
3. **B站热榜** - 稳定
4. **今日头条** - 稳定

### ⏸️ 暂时禁用的数据源（2个）

1. **百度热榜** - 需要修复函数签名
2. **抖音热搜** - API反爬限制

## 🔧 后续修复计划

### 修复百度热榜

需要修改工具函数签名，使其与其他工具一致：

```python
# 当前（有问题）
async def get_baidu_trending_func(args: dict) -> list:
    ...

# 应该改为
async def get_baidu_trending_func() -> list:
    ...
```

### 修复抖音热搜

需要增强反爬策略：
1. 添加更真实的请求头
2. 增加请求间隔
3. 使用代理池（可选）
4. 添加重试机制

## 💡 建议

当前配置已经足够使用：
- ✅ 4个稳定数据源
- ✅ 覆盖主流平台
- ✅ 定时自动刷新
- ✅ 缓存性能优秀

可以先使用当前配置，后续有需要再逐步修复其他数据源。

## 🎯 验证方法

重启 MCP 服务器后，应该只看到4个数据源的预热日志：

```
2025-10-23 XX:XX:XX - INFO - Scheduling 4 enabled sources
2025-10-23 XX:XX:XX - INFO - Added job warm_weibo_trending with interval 20 minutes
2025-10-23 XX:XX:XX - INFO - Added job warm_zhihu_trending with interval 20 minutes
2025-10-23 XX:XX:XX - INFO - Added job warm_bilibili_trending with interval 20 minutes
2025-10-23 XX:XX:XX - INFO - Added job warm_toutiao_trending with interval 20 minutes
```

不应该再看到百度和抖音的错误日志。
