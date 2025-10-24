#!/usr/bin/env python3
"""
检查所有工具的缓存覆盖情况
"""

import os
import re
from pathlib import Path

def check_tool_cache(file_path):
    """检查单个工具文件是否实现了缓存"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否导入了 cache
    has_cache_import = 'from daily_hot_mcp.utils import' in content and 'cache' in content
    
    # 检查是否使用了 cache.get
    has_cache_get = 'cache.get(' in content
    
    # 检查是否使用了 cache.set
    has_cache_set = 'cache.set(' in content
    
    # 提取工具名称
    tool_name_match = re.search(r'name="([^"]+)"', content)
    tool_name = tool_name_match.group(1) if tool_name_match else Path(file_path).stem
    
    return {
        'file': Path(file_path).name,
        'tool_name': tool_name,
        'has_cache_import': has_cache_import,
        'has_cache_get': has_cache_get,
        'has_cache_set': has_cache_set,
        'has_full_cache': has_cache_import and has_cache_get and has_cache_set
    }

def main():
    tools_dir = Path(__file__).parent / 'daily_hot_mcp' / 'tools'
    
    results = []
    for py_file in tools_dir.glob('*.py'):
        if py_file.name.startswith('__'):
            continue
        
        result = check_tool_cache(py_file)
        results.append(result)
    
    # 统计
    total = len(results)
    with_cache = sum(1 for r in results if r['has_full_cache'])
    without_cache = total - with_cache
    
    print("=" * 80)
    print("工具缓存覆盖情况检查报告")
    print("=" * 80)
    print(f"\n总计工具数: {total}")
    print(f"已实现缓存: {with_cache} ({with_cache/total*100:.1f}%)")
    print(f"未实现缓存: {without_cache} ({without_cache/total*100:.1f}%)")
    print("\n" + "=" * 80)
    
    # 已实现缓存的工具
    print("\n✅ 已实现缓存的工具:")
    print("-" * 80)
    for r in sorted(results, key=lambda x: x['tool_name']):
        if r['has_full_cache']:
            print(f"  • {r['tool_name']:<30} ({r['file']})")
    
    # 未实现缓存的工具
    if without_cache > 0:
        print("\n❌ 未实现缓存的工具:")
        print("-" * 80)
        for r in sorted(results, key=lambda x: x['tool_name']):
            if not r['has_full_cache']:
                status = []
                if not r['has_cache_import']:
                    status.append("缺少导入")
                if not r['has_cache_get']:
                    status.append("缺少读取")
                if not r['has_cache_set']:
                    status.append("缺少写入")
                print(f"  • {r['tool_name']:<30} ({', '.join(status)})")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
