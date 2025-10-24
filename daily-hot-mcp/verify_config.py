#!/usr/bin/env python3
"""验证配置文件"""
import json

config = json.load(open('scheduler_config.json'))
print(f'✅ 配置文件有效')
print(f'✅ 数据源数量: {len(config["sources"])}')
print(f'✅ 数据源列表:')
for s in config['sources']:
    status = "✅" if s.get("enabled", True) else "❌"
    print(f'  {status} {s["name"]} ({s["interval_minutes"]}分钟)')
