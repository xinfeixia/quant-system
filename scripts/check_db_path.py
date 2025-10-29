#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库路径
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import init_config
from database import init_database, get_db_manager

def main():
    """检查数据库路径"""
    
    print("=" * 80)
    print("数据库路径检查")
    print("=" * 80)
    print()
    
    # 当前工作目录
    print(f"1. 当前工作目录: {os.getcwd()}")
    print()
    
    # 项目根目录
    print(f"2. 项目根目录: {project_root}")
    print()
    
    # 加载配置
    config_dir = str(project_root / 'config')
    config_loader = init_config(config_dir=config_dir)
    
    # 配置文件中的数据库路径
    db_config = config_loader.config.get('database', {})
    db_path_in_config = db_config.get('sqlite', {}).get('path', 'data/longport_quant.db')
    print(f"3. 配置文件中的数据库路径: {db_path_in_config}")
    print()
    
    # 初始化数据库
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 实际使用的数据库路径
    actual_db_url = str(db_manager.engine.url)
    print(f"4. 实际数据库URL: {actual_db_url}")
    print()
    
    # 解析实际路径
    if actual_db_url.startswith('sqlite:///'):
        actual_db_path = actual_db_url.replace('sqlite:///', '')
        print(f"5. 实际数据库路径: {actual_db_path}")
        
        # 转换为绝对路径
        abs_db_path = os.path.abspath(actual_db_path)
        print(f"6. 绝对路径: {abs_db_path}")
        print()
        
        # 检查文件是否存在
        if os.path.exists(abs_db_path):
            file_size = os.path.getsize(abs_db_path)
            print(f"7. 数据库文件存在: ✅")
            print(f"   文件大小: {file_size:,} 字节 ({file_size / 1024 / 1024:.2f} MB)")
        else:
            print(f"7. 数据库文件存在: ❌")
        print()
    
    # 检查其他可能的数据库文件位置
    print("8. 检查其他可能的数据库文件位置:")
    possible_paths = [
        'data/longport_quant.db',
        'longport-quant-system/data/longport_quant.db',
        os.path.join(project_root, 'data/longport_quant.db'),
        os.path.join(os.getcwd(), 'data/longport_quant.db'),
    ]
    
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        exists = os.path.exists(abs_path)
        if exists:
            file_size = os.path.getsize(abs_path)
            print(f"   ✅ {abs_path}")
            print(f"      大小: {file_size:,} 字节 ({file_size / 1024 / 1024:.2f} MB)")
        else:
            print(f"   ❌ {abs_path}")
    print()
    
    print("=" * 80)
    print("检查完成！")
    print("=" * 80)

if __name__ == '__main__':
    main()

