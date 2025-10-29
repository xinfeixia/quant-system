#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取港股今天的交易数据
"""

import sys
from pathlib import Path
import time
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import DailyData, StockInfo
from data_collection.longport_client import LongPortClient
from utils.config_loader import init_config
from sqlalchemy import func

def main():
    """获取港股今天的交易数据"""
    config_dir = str(project_root / 'config')
    config_loader = init_config(config_dir=config_dir)
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 初始化LongPort客户端
    longport_client = LongPortClient(config_loader.api_config)
    
    # 获取所有港股的symbol和name
    with db_manager.get_session() as session:
        hk_stocks = [(s.symbol, s.name) for s in session.query(StockInfo).filter_by(market='HK').all()]

    # 获取最近7天的数据（确保能获取到最近一个交易日）
    today = datetime.now()
    start_date = today - timedelta(days=7)

    success_count = 0
    fail_count = 0
    no_data_count = 0
    total_records = 0

    print(f"\n{'='*60}")
    print(f"开始获取港股最新交易数据")
    print(f"股票数量: {len(hk_stocks)} 只")
    print(f"日期范围: {start_date.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")

    latest_date = None

    for idx, (symbol, name) in enumerate(hk_stocks, 1):
        try:
            print(f"[{idx}/{len(hk_stocks)}] 获取 {symbol} - {name} 数据...", end=" ")

            # 使用LongPort API获取最近10天的K线数据
            candlesticks = longport_client.get_candlesticks(
                symbol=symbol,
                period='day',
                count=10  # 获取最近10天，确保包含最新交易日
            )

            if not candlesticks:
                print(f"⚠️  无数据")
                no_data_count += 1
                continue

            # 保存到数据库
            with db_manager.get_session() as session:
                # 删除这个时间段的旧数据
                session.query(DailyData).filter(
                    DailyData.symbol == symbol,
                    DailyData.trade_date >= start_date.date()
                ).delete()

                # 插入新数据
                for candle in candlesticks:
                    record = DailyData(
                        symbol=symbol,
                        trade_date=candle.timestamp.date(),
                        open=float(candle.open),
                        high=float(candle.high),
                        low=float(candle.low),
                        close=float(candle.close),
                        volume=int(candle.volume),
                        turnover=float(candle.turnover)
                    )
                    session.add(record)

                session.commit()

            record_count = len(candlesticks)
            total_records += record_count
            success_count += 1

            # 记录最新交易日期
            last_date = candlesticks[-1].timestamp.date()
            if latest_date is None or last_date > latest_date:
                latest_date = last_date

            print(f"✅ 新增 {record_count} 条数据")

            # 避免请求过快
            time.sleep(0.2)
            
        except Exception as e:
            print(f"❌ 失败: {str(e)}")
            fail_count += 1
            continue

    # 统计信息
    print(f"\n{'='*60}")
    print(f"数据获取完成！")
    print(f"{'='*60}")
    print(f"✅ 成功: {success_count}/{len(hk_stocks)} ({success_count/len(hk_stocks)*100:.1f}%)")
    print(f"⚠️  无数据: {no_data_count}/{len(hk_stocks)} ({no_data_count/len(hk_stocks)*100:.1f}%)")
    print(f"❌ 失败: {fail_count}/{len(hk_stocks)} ({fail_count/len(hk_stocks)*100:.1f}%)")
    print(f"📊 总数据: {total_records} 条")
    if latest_date:
        print(f"📅 最新交易日期: {latest_date}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()

