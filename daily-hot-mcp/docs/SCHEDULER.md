# Scheduler Documentation

## Overview

The scheduler is a background service that automatically fetches data from configured sources and populates the cache before user requests. This significantly improves response times by ensuring cached data is always fresh and available.

## How It Works

### Cache Prewarming Flow

```
1. Scheduler starts when MCP server starts
2. Reads configuration from scheduler_config.json
3. Schedules periodic tasks for each enabled source
4. Tasks run in background threads at configured intervals
5. Each task calls the corresponding tool function
6. Tool function fetches data and stores in cache (via existing cache mechanism)
7. User requests read from pre-warmed cache → Fast responses!
```

### Key Benefits

- **Fast Response Times**: All requests benefit from cached data
- **No Code Changes**: Existing tools work without modification
- **Configurable**: Control which sources to fetch and how often
- **Resilient**: Source failures don't affect other sources or the MCP server

## Configuration

### Configuration File Location

The scheduler looks for configuration in the following locations (in order):

1. Environment variable: `SCHEDULER_CONFIG_PATH`
2. Current directory: `./scheduler_config.json`
3. Project directory: `./daily_hot_mcp/scheduler_config.json`
4. User config: `~/.config/daily-hot-mcp/scheduler_config.json`

### Configuration Format

```json
{
  "default_interval_minutes": 25,
  "sources": [
    {
      "name": "weibo_hot",
      "tool_name": "get-weibo-hot",
      "enabled": true,
      "interval_minutes": 15
    },
    {
      "name": "bilibili_rank_all",
      "tool_name": "get-bilibili-rank",
      "enabled": true,
      "interval_minutes": 25,
      "tool_params": {
        "rank_type": 0
      }
    }
  ]
}
```

### Configuration Options

#### Global Settings

- `default_interval_minutes` (optional): Default fetch interval for sources without explicit interval (default: 25)

#### Source Configuration

Each source in the `sources` array supports:

- `name` (required): Unique identifier for this source
- `tool_name` (required): Name of the MCP tool to call (e.g., "get-weibo-hot")
- `enabled` (optional): Whether to schedule this source (default: true)
- `interval_minutes` (optional): How often to fetch data in minutes (default: uses global default)
- `tool_params` (optional): Parameters to pass to the tool function (default: {})

### Recommended Intervals

Choose intervals based on:
- **Data freshness requirements**: How quickly content changes
- **API rate limits**: Respect external service limits
- **Cache TTL**: Default cache expires after 30 minutes

Recommended intervals:
- **High-frequency sources** (Weibo, Douyin, Toutiao): 15-20 minutes
- **Medium-frequency sources** (Bilibili, Zhihu, Xiaohongshu): 20-25 minutes
- **Low-frequency sources** (Tech news, forums): 30 minutes

**Important**: Keep intervals at least 5 minutes shorter than cache TTL (30 min) to prevent cache expiration.

## Getting Started

### 1. Create Configuration File

Copy the example configuration:

```bash
cp scheduler_config.example.json scheduler_config.json
```

### 2. Customize Configuration

Edit `scheduler_config.json` to:
- Enable/disable specific sources
- Adjust fetch intervals
- Configure tool parameters

### 3. Start the Server

The scheduler starts automatically with the MCP server:

```bash
python -m daily_hot_mcp
```

You should see log messages like:

```
INFO - SchedulerManager initialized
INFO - Loading scheduler config from: scheduler_config.json
INFO - Loaded 28 source configurations
INFO - Scheduling 28 enabled sources
INFO - Added job warm_weibo_hot with interval 15 minutes
INFO - Scheduler started successfully
```

## Monitoring

### Log Messages

The scheduler logs important events:

- **Startup**: Configuration loading and job scheduling
- **Successful fetches**: `[source_name] Cache warmed successfully (X items, Y.YYs)`
- **Failed fetches**: `[source_name] Failed to warm cache: error message`
- **Shutdown**: Graceful shutdown messages

### Checking Status

Monitor scheduler activity through logs:

```bash
# View recent scheduler activity
tail -f /path/to/logs

# Search for specific source
grep "weibo_hot" /path/to/logs

# Check for errors
grep "ERROR" /path/to/logs | grep "scheduler"
```

## Troubleshooting

### Scheduler Not Starting

**Symptom**: No scheduler log messages on server startup

**Possible causes**:
1. Configuration file not found
2. Invalid JSON in configuration file
3. No sources configured

**Solutions**:
- Check log for "Loading scheduler config from: ..." message
- Validate JSON syntax in configuration file
- Ensure at least one source is enabled

### Source Not Fetching

**Symptom**: Specific source not appearing in logs

**Possible causes**:
1. Source disabled in configuration
2. Tool name incorrect
3. Tool parameters invalid

**Solutions**:
- Check `enabled: true` in configuration
- Verify tool name matches exactly (case-sensitive)
- Check tool parameters match tool function signature

### High Memory Usage

**Symptom**: Server memory usage increasing over time

**Possible causes**:
1. Too many sources scheduled
2. Intervals too short
3. Large response data

**Solutions**:
- Disable less important sources
- Increase fetch intervals
- Monitor cache directory size

### API Rate Limiting

**Symptom**: Frequent fetch failures for specific source

**Possible causes**:
1. Fetch interval too short
2. External API rate limits

**Solutions**:
- Increase interval for affected source
- Check external API documentation for rate limits
- Consider disabling source temporarily

## Advanced Usage

### Environment-Specific Configuration

Use environment variables to switch configurations:

```bash
# Development
export SCHEDULER_CONFIG_PATH=./scheduler_config.dev.json

# Production
export SCHEDULER_CONFIG_PATH=./scheduler_config.prod.json
```

### Disabling Scheduler

To run MCP server without scheduler:

1. **Option 1**: Disable all sources in configuration
```json
{
  "sources": []
}
```

2. **Option 2**: Remove configuration file (scheduler won't start)

3. **Option 3**: Comment out scheduler initialization in `server.py`

### Hot Reloading Configuration

Currently, configuration changes require server restart. Future versions may support hot reloading via `scheduler_manager.reload_config()`.

## Performance Considerations

### Resource Usage

- **Memory**: ~10-20MB overhead for scheduler
- **CPU**: Minimal when idle, brief spikes during fetches
- **Network**: Controlled by fetch intervals
- **Disk**: Cache files in `/tmp/mcp_daily_news/cache/`

### Scaling

The scheduler can handle:
- **30+ sources** simultaneously
- **10 concurrent fetches** (thread pool size)
- **Intervals as short as 5 minutes** (not recommended)

### Best Practices

1. **Start conservative**: Enable fewer sources initially
2. **Monitor performance**: Watch logs for slow fetches
3. **Adjust intervals**: Increase if seeing issues
4. **Disable unused sources**: Reduce unnecessary work
5. **Respect rate limits**: Follow external API guidelines

## FAQ

**Q: Will scheduler failures crash the MCP server?**  
A: No. Scheduler errors are isolated and logged. The MCP server continues running.

**Q: What happens if a fetch takes longer than the interval?**  
A: APScheduler prevents overlapping executions. The next fetch waits until the current one completes.

**Q: Can I schedule the same tool multiple times with different parameters?**  
A: Yes! Use different `name` values for each configuration.

**Q: How do I know if caching is working?**  
A: Check response times. First request after server start may be slow, subsequent requests should be fast.

**Q: Can I use this with custom tools?**  
A: Yes! Add your custom tools to the registry and configure them in `scheduler_config.json`.

## Support

For issues or questions:
1. Check logs for error messages
2. Review this documentation
3. Check example configuration
4. Open an issue on GitHub
