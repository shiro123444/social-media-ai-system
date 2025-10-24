#!/usr/bin/env python3
"""
批量为工具添加缓存支持
"""

import re
from pathlib import Path

def add_cache_to_tool(file_path):
    """为单个工具文件添加缓存支持"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经有缓存
    if 'cache.get(' in content and 'cache.set(' in content:
        return False, "已有缓存"
    
    # 提取工具名称作为缓存键
    tool_name_match = re.search(r'name="([^"]+)"', content)
    if not tool_name_match:
        return False, "无法找到工具名称"
    
    tool_name = tool_name_match.group(1)
    cache_key = tool_name.replace('-', '_')
    
    # 1. 添加 cache 和 logger 导入
    if 'from daily_hot_mcp.utils import' in content:
        # 已有导入，添加 cache 和 logger
        content = re.sub(
            r'from daily_hot_mcp\.utils import ([^\n]+)',
            lambda m: f'from daily_hot_mcp.utils import {m.group(1)}, cache, logger' if 'cache' not in m.group(1) else m.group(0),
            content
        )
    else:
        # 没有导入，在第一个 import 后添加
        content = re.sub(
            r'(import [^\n]+\n)',
            r'\1from daily_hot_mcp.utils import cache, logger\n',
            content,
            count=1
        )
    
    # 2. 找到主函数并添加缓存读取逻辑
    # 查找函数定义
    func_pattern = r'(async def \w+_func\([^)]*\)[^:]*:\s*"""[^"]*""")'
    
    cache_read_code = f'''
    cache_key = "{cache_key}"
    
    # 尝试从缓存获取
    try:
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"从缓存获取{{cache_key}}数据")
            return cached_data
    except Exception as e:
        logger.warning(f"读取缓存失败: {{e}}")
    '''
    
    content = re.sub(
        func_pattern,
        r'\1' + cache_read_code,
        content
    )
    
    # 3. 在 return results 前添加缓存写入逻辑
    cache_write_code = '''
    # 缓存结果
    try:
        cache.set(cache_key, results)
        logger.info(f"获取{cache_key}数据成功，共{len(results)}条")
    except Exception as e:
        logger.warning(f"写入缓存失败: {e}")
    '''
    
    # 查找最后的 return results 或 return results[:N]
    content = re.sub(
        r'(\n\s+)(return results(?:\[:[0-9]+\])?)',
        cache_write_code + r'\1\2',
        content
    )
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True, "成功添加缓存"

def main():
    tools_dir = Path(__file__).parent / 'daily_hot_mcp' / 'tools'
    
    # 需要添加缓存的工具列表（排除已有缓存的）
    skip_files = {
        '__init__.py',
        'bilibili.py',  # 已有缓存
        'zhihu.py',     # 已有缓存
        'weibo.py',     # 已有缓存
        'baidu.py',     # 已有缓存
        'toutiao.py',   # 已有缓存
        'douyin.py',    # 已有缓存
        'xiaohongshu.py', # 已有缓存
        'kuaishou.py',  # 已有缓存
        'hupu.py',      # 已有缓存
    }
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    print("=" * 80)
    print("批量添加缓存支持")
    print("=" * 80)
    
    for py_file in sorted(tools_dir.glob('*.py')):
        if py_file.name in skip_files:
            skip_count += 1
            continue
        
        success, message = add_cache_to_tool(py_file)
        
        if success:
            print(f"✅ {py_file.name:<30} - {message}")
            success_count += 1
        else:
            print(f"⏭️  {py_file.name:<30} - {message}")
            if "已有缓存" not in message:
                fail_count += 1
    
    print("\n" + "=" * 80)
    print(f"总计: {success_count + skip_count + fail_count} 个文件")
    print(f"成功添加: {success_count}")
    print(f"跳过: {skip_count}")
    print(f"失败: {fail_count}")
    print("=" * 80)

if __name__ == '__main__':
    main()
