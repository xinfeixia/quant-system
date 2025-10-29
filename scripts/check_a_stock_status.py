#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查A股数据状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager, init_database
from database.models import StockInfo, DailyData
from utils.config_loader import init_config
from sqlalchemy import func

def check_status():
    """检查A股数据状态"""
    
    # 初始化配置和数据库
    config_loader = init_config()
    config = config_loader.config
    init_database(config)
    
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 统计A股数量
        total_stocks = session.query(StockInfo).filter_by(market='CN').count()
        
        # 统计有数据的A股
        stocks_with_data = session.query(
            func.count(func.distinct(DailyData.symbol))
        ).join(
            StockInfo, DailyData.symbol == StockInfo.symbol
        ).filter(
            StockInfo.market == 'CN'
        ).scalar()
        
        # 统计总数据条数
        total_data = session.query(func.count(DailyData.id)).join(
            StockInfo, DailyData.symbol == StockInfo.symbol
        ).filter(
            StockInfo.market == 'CN'
        ).scalar()
        
        print(f"\n{'='*60}")
        print(f"A股数据状态")
        print(f"{'='*60}")
        print(f"A股总数: {total_stocks} 只")
        print(f"有数据: {stocks_with_data} 只")
        print(f"无数据: {total_stocks - stocks_with_data} 只")
        print(f"总数据条数: {total_data:,} 条")
        print(f"平均每股: {total_data / stocks_with_data:.0f} 条" if stocks_with_data > 0 else "平均每股: 0 条")
        print(f"{'='*60}\n")
        
        # 列出最近添加的股票
        print("最近添加的35只股票数据情况：\n")
        
        recent_symbols = [
            '601818.SH', '601998.SH', '600837.SH', '000166.SZ', '601377.SH',
            '600019.SH', '000709.SZ', '600010.SH', '601600.SH', '600362.SH',
            '000878.SZ', '600383.SH', '601933.SH', '002024.SZ', '600729.SH',
            '600660.SH', '600741.SH', '002050.SZ', '601111.SH', '600029.SH',
            '600115.SH', '600089.SH', '000400.SZ', '002074.SZ', '600352.SH',
            '000157.SZ', '002008.SZ', '000401.SZ', '600801.SH', '000538.SZ',
            '600436.SH', '300027.SZ', '300413.SZ', '600588.SH', '300033.SZ'
        ]
        
        for symbol in recent_symbols:
            stock = session.query(StockInfo).filter_by(symbol=symbol).first()
            if stock:
                data_count = session.query(func.count(DailyData.id)).filter_by(symbol=symbol).scalar()
                status = "✅" if data_count > 0 else "❌"
                print(f"{status} {symbol} - {stock.name}: {data_count} 条数据")
            else:
                print(f"⚠️  {symbol} - 不存在")

if __name__ == '__main__':
    check_status()

