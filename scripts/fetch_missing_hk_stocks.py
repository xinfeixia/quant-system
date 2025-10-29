#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取缺失的港股历史数据
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
    """获取缺失的港股历史数据"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 初始化LongPort客户端
    longport_client = LongPortClient(api_config=config_loader.api_config)
    
    # 获取无数据的港股列表
    missing_symbols = []
    with db_manager.get_session() as session:
        hk_stocks = session.query(StockInfo).filter_by(market='HK').all()
        
        for stock in hk_stocks:
            count = session.query(func.count(DailyData.id)).filter_by(symbol=stock.symbol).scalar()
            if count == 0:
                missing_symbols.append((stock.symbol, stock.name))
    
    if not missing_symbols:
        print("所有港股都有数据！")
        return
    
    # 获取最近1年的数据
    end_date = datetime.now()
    start_date = datetime.now() - timedelta(days=365)
    
    success_count = 0
    fail_count = 0
    total_records = 0
    
    print(f"\n{'='*60}")
    print(f"开始获取缺失的港股历史数据")
    print(f"股票数量: {len(missing_symbols)} 只")
    print(f"时间范围: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    for i, (symbol, name) in enumerate(missing_symbols, 1):
        try:
            print(f"[{i}/{len(missing_symbols)}] 获取 {symbol} - {name} 数据...", end=' ')

            # 获取历史K线数据
            candlesticks = longport_client.get_history_candlesticks(
                symbol=symbol,
                period='day',
                start_date=start_date.date(),
                end_date=end_date.date()
            )

            if candlesticks and len(candlesticks) > 0:
                # 保存到数据库
                saved_count = 0
                with db_manager.get_session() as session:
                    # 删除旧数据
                    session.query(DailyData).filter_by(symbol=symbol).delete()

                    # 插入新数据
                    for candle in candlesticks:
                        daily_data = DailyData(
                            symbol=symbol,
                            trade_date=candle.timestamp.date(),
                            open=candle.open,
                            high=candle.high,
                            low=candle.low,
                            close=candle.close,
                            volume=candle.volume,
                            turnover=candle.turnover,
                            created_at=datetime.now()
                        )
                        session.add(daily_data)
                        saved_count += 1

                    session.commit()

                print(f"✅ 保存 {saved_count} 条数据")
                success_count += 1
                total_records += saved_count
            else:
                print(f"⚠️  无数据")
                fail_count += 1

            # 控制请求频率（避免触发限流）
            time.sleep(2)

        except Exception as e:
            print(f"❌ 错误: {e}")
            fail_count += 1
            time.sleep(3)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"\n{'='*60}")
    print(f"港股数据补充完成！")
    print(f"成功: {success_count}/{len(missing_symbols)} ({success_count/len(missing_symbols)*100:.1f}%)")
    print(f"失败: {fail_count}/{len(missing_symbols)} ({fail_count/len(missing_symbols)*100:.1f}%)")
    print(f"总数据: {total_records} 条")
    print(f"总用时: {elapsed/60:.1f} 分钟")
    print(f"平均速度: {elapsed/len(missing_symbols):.1f} 秒/股票")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

