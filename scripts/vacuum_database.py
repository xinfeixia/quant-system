#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化数据库（VACUUM）
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from utils.config_loader import ConfigLoader
from loguru import logger

def main():
    """主函数"""
    print(f"\n{'='*100}")
    print(f"数据库优化工具 (VACUUM)")
    print(f"{'='*100}\n")
    
    # 初始化数据库
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    db = DatabaseManager(config)
    
    print("正在执行 VACUUM 命令...")
    print("这可能需要几分钟时间，请耐心等待...\n")
    
    try:
        # 获取原始数据库文件大小
        db_path = Path(config['database']['sqlite']['path'])
        original_size = db_path.stat().st_size / (1024 * 1024)  # MB
        
        # 执行VACUUM
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("VACUUM"))
            conn.commit()
        
        # 获取优化后的数据库文件大小
        new_size = db_path.stat().st_size / (1024 * 1024)  # MB
        saved_size = original_size - new_size
        
        print(f"✅ VACUUM 执行成功！")
        print(f"\n数据库大小变化：")
        print(f"  优化前: {original_size:.2f} MB")
        print(f"  优化后: {new_size:.2f} MB")
        print(f"  节省空间: {saved_size:.2f} MB ({saved_size/original_size*100:.1f}%)")
        
    except Exception as e:
        logger.error(f"VACUUM 执行失败: {e}")
        print(f"❌ VACUUM 执行失败: {e}")
    
    print(f"\n{'='*100}\n")

if __name__ == '__main__':
    main()

