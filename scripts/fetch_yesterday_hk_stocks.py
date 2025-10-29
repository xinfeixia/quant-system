#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取港股昨天的交易数据（仅昨日，按日K）
"""

import sys
from pathlib import Path
import time
from datetime import datetime, timedelta

# 将项目根目录加入路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import DailyData, StockInfo
from data_collection.longport_client import LongPortClient
from utils.config_loader import init_config


def main():
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()

    # 初始化 LongPort 客户端
    lp_client = LongPortClient(config_loader.api_config)

    # 读取港股清单
    with db_manager.get_session() as session:
        hk_stocks = [
            (s.symbol, s.name) for s in session.query(StockInfo).filter_by(market='HK').all()
        ]

    target_date = (datetime.now() - timedelta(days=1)).date()

    print(f"\n{'='*60}")
    print("开始获取港股昨日交易数据")
    print(f"目标日期: {target_date}")
    print(f"股票数量: {len(hk_stocks)} 只")
    print(f"{'='*60}\n")

    success = 0
    fail = 0
    zero = 0
    total = 0

    # 简单速率控制，避免过快
    sleep_secs = 0.15

    for i, (symbol, name) in enumerate(hk_stocks, 1):
        try:
            print(f"[{i}/{len(hk_stocks)}] {symbol} - {name} ...", end=' ')

            # 拉最近5个交易日，过滤出“昨日”那一根
            candles = lp_client.get_candlesticks(symbol=symbol, period='day', count=5)
            if not candles:
                print("⚠️ 无数据")
                zero += 1
                time.sleep(sleep_secs)
                continue

            # 过滤昨日
            selected = [c for c in candles if c.timestamp.date() == target_date]
            if not selected:
                print("⚠️ 昨日无K线（可能是非交易日或该股停牌）")
                zero += 1
                time.sleep(sleep_secs)
                continue

            c = selected[-1]

            # 写库：存在则更新，不存在则插入
            with db_manager.get_session() as session:
                existing = (
                    session.query(DailyData)
                    .filter_by(symbol=symbol, trade_date=c.timestamp.date())
                    .first()
                )

                if existing:
                    existing.open = float(c.open)
                    existing.high = float(c.high)
                    existing.low = float(c.low)
                    existing.close = float(c.close)
                    existing.volume = int(c.volume)
                    existing.turnover = float(c.turnover)
                else:
                    session.add(
                        DailyData(
                            symbol=symbol,
                            trade_date=c.timestamp.date(),
                            open=float(c.open),
                            high=float(c.high),
                            low=float(c.low),
                            close=float(c.close),
                            volume=int(c.volume),
                            turnover=float(c.turnover),
                        )
                    )
                session.commit()

            print("✅ OK")
            success += 1
            total += 1
            time.sleep(sleep_secs)
        except Exception as e:
            print(f"❌ 失败: {e}")
            fail += 1
            time.sleep(sleep_secs)

    print(f"\n{'='*60}")
    print("港股昨日数据获取完成！")
    print(f"成功: {success}/{len(hk_stocks)} ({(success/len(hk_stocks))*100:.1f}%)")
    print(f"无数据: {zero}/{len(hk_stocks)} ({(zero/len(hk_stocks))*100:.1f}%)")
    print(f"失败: {fail}/{len(hk_stocks)} ({(fail/len(hk_stocks))*100:.1f}%)")
    print(f"总记录变更: {total} 条")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

