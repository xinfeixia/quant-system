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
from sqlalchemy import func
from database.models import DailyData, StockInfo, TechnicalIndicator
from datetime import datetime, timedelta
from utils.config_loader import init_config

def check_hk_data_status():
    """检查港股数据状态"""
    config_dir = str(project_root / 'config')
    config_loader = init_config(config_dir=config_dir)
    init_database(config_loader.config)
    db_manager = get_db_manager()

    with db_manager.get_session() as session:
    
        # 1. 港股总数
        hk_stocks = session.query(StockInfo).filter(StockInfo.market == 'HK').count()
        print(f"📊 港股总数: {hk_stocks}")
        print()
        
        # 2. 检查前20只港股的数据天数
        print("=" * 80)
        print("前20只知名港股的历史数据天数:")
        print("=" * 80)
        
        famous_stocks = [
            '9988.HK', '0700.HK', '3690.HK', '1810.HK', '0388.HK',
            '9618.HK', '2318.HK', '1398.HK', '0939.HK', '3988.HK',
            '0941.HK', '1299.HK', '0005.HK', '0011.HK', '0001.HK',
            '0002.HK', '0003.HK', '0006.HK', '0012.HK', '0016.HK'
        ]
        
        for symbol in famous_stocks:
            stock = session.query(StockInfo).filter(StockInfo.symbol == symbol).first()
            if stock:
                data_count = session.query(DailyData).filter(DailyData.symbol == symbol).count()
                
                # 获取最新和最早的数据日期
                latest = session.query(DailyData).filter(DailyData.symbol == symbol).order_by(DailyData.trade_date.desc()).first()
                earliest = session.query(DailyData).filter(DailyData.symbol == symbol).order_by(DailyData.trade_date.asc()).first()
                
                latest_date = latest.trade_date if latest else None
                earliest_date = earliest.trade_date if earliest else None
                
                print(f"{symbol:12} {stock.name:20} 数据天数: {data_count:4}天  "
                      f"最早: {earliest_date}  最新: {latest_date}")
        
        print()
        
        # 3. 检查技术指标数据
        print("=" * 80)
        print("前20只知名港股的技术指标数据:")
        print("=" * 80)
        
        for symbol in famous_stocks:
            stock = session.query(StockInfo).filter(StockInfo.symbol == symbol).first()
            if stock:
                indicator_count = session.query(TechnicalIndicator).filter(
                    TechnicalIndicator.symbol == symbol
                ).count()
                
                # 获取最新的技术指标
                latest_indicator = session.query(TechnicalIndicator).filter(
                    TechnicalIndicator.symbol == symbol
                ).order_by(TechnicalIndicator.trade_date.desc()).first()
                
                if latest_indicator:
                    rsi_str = f"{latest_indicator.rsi:.2f}" if latest_indicator.rsi else "N/A"
                    print(f"{symbol:12} {stock.name:20} 指标数: {indicator_count:4}条  "
                          f"最新: {latest_indicator.trade_date}  "
                          f"RSI: {rsi_str}")
                else:
                    print(f"{symbol:12} {stock.name:20} ❌ 无技术指标数据")
        
        print()
        
        # 4. 统计数据分布
        print("=" * 80)
        print("港股历史数据分布统计:")
        print("=" * 80)
        
        data_distribution = session.query(
            func.count(DailyData.id).label('days'),
            func.count(func.distinct(DailyData.symbol)).label('stocks')
        ).join(
            StockInfo, StockInfo.symbol == DailyData.symbol
        ).filter(
            StockInfo.market == 'HK'
        ).group_by(
            DailyData.symbol
        ).subquery()
        
        ranges = [
            (0, 10, "0-10天"),
            (11, 30, "11-30天"),
            (31, 60, "31-60天"),
            (61, 120, "61-120天"),
            (121, 200, "121-200天"),
            (201, 999999, "200天以上")
        ]
        
        for min_days, max_days, label in ranges:
            count = session.query(StockInfo.symbol).join(
                DailyData, StockInfo.symbol == DailyData.symbol
            ).filter(
                StockInfo.market == 'HK'
            ).group_by(
                StockInfo.symbol
            ).having(
                func.count(DailyData.id) >= min_days,
                func.count(DailyData.id) <= max_days
            ).count()
            
            percentage = (count / hk_stocks * 100) if hk_stocks > 0 else 0
            print(f"{label:15} {count:5}只  ({percentage:5.1f}%)")
        
        print()
        
        # 5. 检查今天的数据
        print("=" * 80)
        print("今天(2025-10-22)的港股数据:")
        print("=" * 80)
        
        today = datetime(2025, 10, 22).date()
        today_count = session.query(DailyData).join(
            StockInfo, StockInfo.symbol == DailyData.symbol
        ).filter(
            StockInfo.market == 'HK',
            DailyData.trade_date == today
        ).count()
        
        print(f"今天有数据的港股数量: {today_count}只")
        
        # 检查几只知名股票今天的数据
        print("\n知名港股今天的数据:")
        for symbol in famous_stocks[:10]:
            today_data = session.query(DailyData).filter(
                DailyData.symbol == symbol,
                DailyData.trade_date == today
            ).first()
            
            stock = session.query(StockInfo).filter(StockInfo.symbol == symbol).first()
            if today_data:
                print(f"✅ {symbol:12} {stock.name if stock else '':20} "
                      f"收盘: {today_data.close:.2f}  涨跌幅: {today_data.change_percent:.2f}%")
            else:
                print(f"❌ {symbol:12} {stock.name if stock else '':20} 无今日数据")

if __name__ == '__main__':
    check_hk_data_status()

