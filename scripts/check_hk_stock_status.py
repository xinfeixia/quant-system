#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查港股数据状态
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo, DailyData
from utils.config_loader import init_config
from sqlalchemy import func

def main():
    """检查港股数据状态"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 获取所有港股
        hk_stocks = session.query(StockInfo).filter_by(market='HK').all()
        
        print(f"\n{'='*60}")
        print(f"港股数据状态")
        print(f"{'='*60}")
        
        stocks_with_data = []
        stocks_without_data = []
        total_records = 0
        
        for stock in hk_stocks:
            # 查询该股票的数据条数
            count = session.query(func.count(DailyData.id)).filter_by(symbol=stock.symbol).scalar()
            
            if count > 0:
                stocks_with_data.append((stock.symbol, stock.name, count))
                total_records += count
            else:
                stocks_without_data.append((stock.symbol, stock.name))
        
        print(f"港股总数: {len(hk_stocks)} 只")
        print(f"有数据: {len(stocks_with_data)} 只")
        print(f"无数据: {len(stocks_without_data)} 只")
        print(f"总数据条数: {total_records:,} 条")
        if stocks_with_data:
            print(f"平均每股: {total_records // len(stocks_with_data)} 条")
        print(f"{'='*60}")
        
        if stocks_without_data:
            print(f"\n无数据的港股 ({len(stocks_without_data)} 只)：\n")
            for symbol, name in stocks_without_data:
                print(f"❌ {symbol} - {name}")
        
        if stocks_with_data:
            print(f"\n有数据的港股 (前20只)：\n")
            for symbol, name, count in stocks_with_data[:20]:
                print(f"✅ {symbol} - {name}: {count} 条数据")

if __name__ == '__main__':
    main()

