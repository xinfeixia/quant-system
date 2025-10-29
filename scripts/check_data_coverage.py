#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查A股和港股的数据覆盖情况
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from database.models import StockInfo, DailyData
from sqlalchemy import func, and_
from utils.config_loader import ConfigLoader
from datetime import datetime, timedelta

def check_market_data_coverage(session, market):
    """检查市场数据覆盖情况"""
    print(f"\n{'='*100}")
    print(f"{market}市场数据覆盖情况")
    print(f"{'='*100}\n")
    
    # 获取该市场的股票总数
    total_stocks = session.query(StockInfo).filter(StockInfo.market == market).count()
    print(f"📊 {market}市场股票总数: {total_stocks:,} 只\n")
    
    # 统计每只股票的数据天数
    stock_data_stats = session.query(
        DailyData.symbol,
        StockInfo.name,
        func.count(DailyData.id).label('data_days'),
        func.min(DailyData.trade_date).label('first_date'),
        func.max(DailyData.trade_date).label('last_date')
    ).join(
        StockInfo, DailyData.symbol == StockInfo.symbol
    ).filter(
        StockInfo.market == market
    ).group_by(
        DailyData.symbol, StockInfo.name
    ).all()
    
    if not stock_data_stats:
        print(f"❌ {market}市场没有数据")
        return
    
    # 计算统计信息
    data_days_list = [s.data_days for s in stock_data_stats]
    avg_days = sum(data_days_list) / len(data_days_list)
    max_days = max(data_days_list)
    min_days = min(data_days_list)
    
    # 统计不同数据天数范围的股票数量
    ranges = [
        (0, 30, "0-30天"),
        (31, 60, "31-60天"),
        (61, 90, "61-90天"),
        (91, 180, "91-180天"),
        (181, 365, "181-365天"),
        (366, 999999, "365天以上")
    ]
    
    print(f"📈 数据统计:")
    print(f"  平均数据天数: {avg_days:.1f} 天")
    print(f"  最多数据天数: {max_days} 天")
    print(f"  最少数据天数: {min_days} 天")
    print(f"  有数据的股票: {len(stock_data_stats):,} 只")
    print(f"  无数据的股票: {total_stocks - len(stock_data_stats):,} 只\n")
    
    print(f"📊 数据天数分布:")
    print(f"{'-'*100}")
    print(f"{'范围':<15} {'股票数量':<15} {'占比':<15} {'百分比图'}")
    print(f"{'-'*100}")
    
    for min_range, max_range, label in ranges:
        count = sum(1 for days in data_days_list if min_range <= days <= max_range)
        percentage = count / len(stock_data_stats) * 100
        bar = '█' * int(percentage / 2)
        print(f"{label:<15} {count:<15,} {percentage:>6.1f}%      {bar}")
    
    print(f"{'-'*100}\n")
    
    # 显示数据最多的前10只股票
    print(f"📊 数据最多的前10只股票:")
    print(f"{'-'*100}")
    print(f"{'排名':<6} {'代码':<15} {'名称':<20} {'数据天数':<12} {'起始日期':<15} {'最新日期'}")
    print(f"{'-'*100}")
    
    sorted_stocks = sorted(stock_data_stats, key=lambda x: x.data_days, reverse=True)
    for i, stock in enumerate(sorted_stocks[:10], 1):
        print(f"{i:<6} {stock.symbol:<15} {stock.name:<20} {stock.data_days:<12} {stock.first_date} {stock.last_date}")
    
    print(f"{'-'*100}\n")
    
    # 显示数据最少的前10只股票
    print(f"📊 数据最少的前10只股票:")
    print(f"{'-'*100}")
    print(f"{'排名':<6} {'代码':<15} {'名称':<20} {'数据天数':<12} {'起始日期':<15} {'最新日期'}")
    print(f"{'-'*100}")
    
    for i, stock in enumerate(sorted_stocks[-10:], 1):
        print(f"{i:<6} {stock.symbol:<15} {stock.name:<20} {stock.data_days:<12} {stock.first_date} {stock.last_date}")
    
    print(f"{'-'*100}\n")
    
    # 检查最新数据日期
    latest_date = session.query(func.max(DailyData.trade_date)).join(
        StockInfo, DailyData.symbol == StockInfo.symbol
    ).filter(StockInfo.market == market).scalar()
    
    if latest_date:
        days_ago = (datetime.now().date() - latest_date).days
        print(f"📅 最新数据日期: {latest_date} ({days_ago}天前)")
        
        # 统计有最新数据的股票数量
        stocks_with_latest = session.query(func.count(func.distinct(DailyData.symbol))).join(
            StockInfo, DailyData.symbol == StockInfo.symbol
        ).filter(
            and_(
                StockInfo.market == market,
                DailyData.trade_date == latest_date
            )
        ).scalar()
        
        print(f"📊 有最新数据的股票: {stocks_with_latest:,} 只 ({stocks_with_latest/total_stocks*100:.1f}%)")
    
    print()

def main():
    """主函数"""
    print(f"\n{'='*100}")
    print(f"A股和港股数据覆盖情况检查")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}")
    
    # 初始化数据库
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    db = DatabaseManager(config)
    
    with db.get_session() as session:
        # 检查A股数据
        check_market_data_coverage(session, 'CN')
        
        # 检查港股数据
        check_market_data_coverage(session, 'HK')
    
    print(f"{'='*100}\n")

if __name__ == '__main__':
    main()

