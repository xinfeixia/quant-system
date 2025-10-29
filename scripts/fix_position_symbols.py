#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正持仓表中的股票代码格式
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import Position, StockInfo
from utils.config_loader import init_config
from loguru import logger


def normalize_hk_symbol(symbol):
    """标准化港股代码格式为5位数字.HK"""
    if not symbol.endswith('.HK'):
        return symbol
    
    code = symbol.replace('.HK', '')
    # 补齐为5位数字
    normalized_code = code.zfill(5)
    return f"{normalized_code}.HK"


def main():
    """主函数"""
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 获取所有持仓
        positions = session.query(Position).all()
        
        print(f"\n检查 {len(positions)} 个持仓的股票代码格式...\n")
        
        updated_count = 0
        for pos in positions:
            old_symbol = pos.symbol
            new_symbol = normalize_hk_symbol(old_symbol)
            
            if old_symbol != new_symbol:
                # 检查新代码是否在StockInfo中存在
                stock_info = session.query(StockInfo).filter_by(symbol=new_symbol).first()
                
                if stock_info:
                    print(f"✅ 更新: {old_symbol} -> {new_symbol} ({stock_info.name})")
                    pos.symbol = new_symbol
                    updated_count += 1
                else:
                    print(f"⚠️  跳过: {old_symbol} -> {new_symbol} (数据库中不存在)")
            else:
                stock_info = session.query(StockInfo).filter_by(symbol=old_symbol).first()
                if stock_info:
                    print(f"✓  正确: {old_symbol} ({stock_info.name})")
                else:
                    print(f"⚠️  警告: {old_symbol} (数据库中不存在)")
        
        if updated_count > 0:
            session.commit()
            print(f"\n✅ 成功更新 {updated_count} 个持仓的股票代码")
        else:
            print(f"\n✓  所有持仓代码格式正确")


if __name__ == '__main__':
    main()

