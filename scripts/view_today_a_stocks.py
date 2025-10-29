#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看今天（最近交易日）的A股交易数据
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import DailyData, StockInfo
from utils.config_loader import init_config
from sqlalchemy import func, desc

def main():
    """查看今天的A股交易数据"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 获取最新交易日期
        latest_date = session.query(func.max(DailyData.trade_date)).filter(
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ'))
        ).scalar()
        
        if not latest_date:
            print("❌ 数据库中没有A股数据")
            return
        
        print(f"\n{'='*80}")
        print(f"📅 最新交易日期: {latest_date}")
        print(f"{'='*80}\n")
        
        # 统计当日数据
        total_count = session.query(DailyData).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ'))
        ).count()
        
        print(f"📊 当日交易股票数量: {total_count} 只\n")
        
        # 获取涨幅榜前20
        print(f"{'='*80}")
        print(f"📈 涨幅榜 TOP 20")
        print(f"{'='*80}")
        print(f"{'排名':<6}{'代码':<12}{'名称':<20}{'收盘价':<10}{'涨跌幅':<10}{'成交量(万手)':<15}")
        print(f"{'-'*80}")
        
        top_gainers = session.query(DailyData, StockInfo).join(
            StockInfo, DailyData.symbol == StockInfo.symbol
        ).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ')),
            DailyData.change_pct.isnot(None)
        ).order_by(desc(DailyData.change_pct)).limit(20).all()
        
        for i, (data, stock) in enumerate(top_gainers, 1):
            volume_wan = data.volume / 10000 if data.volume else 0
            print(f"{i:<6}{data.symbol:<12}{stock.name:<20}{data.close:<10.2f}{data.change_pct:>9.2f}%{volume_wan:>14.0f}")
        
        # 获取跌幅榜前20
        print(f"\n{'='*80}")
        print(f"📉 跌幅榜 TOP 20")
        print(f"{'='*80}")
        print(f"{'排名':<6}{'代码':<12}{'名称':<20}{'收盘价':<10}{'涨跌幅':<10}{'成交量(万手)':<15}")
        print(f"{'-'*80}")
        
        top_losers = session.query(DailyData, StockInfo).join(
            StockInfo, DailyData.symbol == StockInfo.symbol
        ).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ')),
            DailyData.change_pct.isnot(None)
        ).order_by(DailyData.change_pct).limit(20).all()
        
        for i, (data, stock) in enumerate(top_losers, 1):
            volume_wan = data.volume / 10000 if data.volume else 0
            print(f"{i:<6}{data.symbol:<12}{stock.name:<20}{data.close:<10.2f}{data.change_pct:>9.2f}%{volume_wan:>14.0f}")
        
        # 获取成交量榜前20
        print(f"\n{'='*80}")
        print(f"💰 成交量榜 TOP 20")
        print(f"{'='*80}")
        print(f"{'排名':<6}{'代码':<12}{'名称':<20}{'收盘价':<10}{'涨跌幅':<10}{'成交量(万手)':<15}")
        print(f"{'-'*80}")
        
        top_volume = session.query(DailyData, StockInfo).join(
            StockInfo, DailyData.symbol == StockInfo.symbol
        ).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ')),
            DailyData.volume.isnot(None)
        ).order_by(desc(DailyData.volume)).limit(20).all()
        
        for i, (data, stock) in enumerate(top_volume, 1):
            volume_wan = data.volume / 10000 if data.volume else 0
            change_pct = data.change_pct if data.change_pct else 0
            print(f"{i:<6}{data.symbol:<12}{stock.name:<20}{data.close:<10.2f}{change_pct:>9.2f}%{volume_wan:>14.0f}")
        
        # 市场统计
        print(f"\n{'='*80}")
        print(f"📊 市场统计")
        print(f"{'='*80}")
        
        # 涨跌统计
        up_count = session.query(DailyData).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ')),
            DailyData.change_pct > 0
        ).count()
        
        down_count = session.query(DailyData).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ')),
            DailyData.change_pct < 0
        ).count()
        
        flat_count = session.query(DailyData).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ')),
            DailyData.change_pct == 0
        ).count()
        
        print(f"上涨: {up_count} 只 ({up_count/total_count*100:.1f}%)")
        print(f"下跌: {down_count} 只 ({down_count/total_count*100:.1f}%)")
        print(f"平盘: {flat_count} 只 ({flat_count/total_count*100:.1f}%)")
        
        # 涨停跌停统计
        limit_up = session.query(DailyData).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ')),
            DailyData.change_pct >= 9.9
        ).count()
        
        limit_down = session.query(DailyData).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ')),
            DailyData.change_pct <= -9.9
        ).count()
        
        print(f"涨停: {limit_up} 只")
        print(f"跌停: {limit_down} 只")
        
        # 平均涨跌幅
        avg_change = session.query(func.avg(DailyData.change_pct)).filter(
            DailyData.trade_date == latest_date,
            (DailyData.symbol.like('%.SH')) | (DailyData.symbol.like('%.SZ')),
            DailyData.change_pct.isnot(None)
        ).scalar()
        
        print(f"平均涨跌幅: {avg_change:.2f}%")
        
        print(f"{'='*80}\n")

if __name__ == '__main__':
    main()

