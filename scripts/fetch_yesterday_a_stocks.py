#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取A股“昨天”的交易数据（仅昨日，按股票逐只获取并入库，存在则更新）
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import DailyData, StockInfo
from data_collection.tushare_client import TushareClient
from utils.config_loader import init_config


def main():
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()

    # Tushare配置
    tushare_cfg = config_loader.api_config.get('tushare', {})
    token = tushare_cfg.get('token')
    if not token:
        raise ValueError("Tushare token未配置")

    # 保守提速：关闭 daily_basic，统一限速
    ts_client = TushareClient(token=token, request_interval=1.2, enable_daily_basic=False)

    # 目标日期：昨天（自然日）。如需“自动回退到最近交易日”，可后续增强。
    target_date = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    # 获取所有A股
    with db_manager.get_session() as session:
        a_stocks = [(s.symbol, s.name) for s in session.query(StockInfo).filter_by(market='CN').all()]

    success, fail, no_data = 0, 0, 0
    total_records = 0

    print("\n" + "=" * 60)
    print("开始获取A股昨日交易数据")
    print(f"股票数量: {len(a_stocks)} 只")
    print(f"目标日期: {target_date.strftime('%Y-%m-%d')}")
    print("=" * 60 + "\n")

    t0 = time.time()

    for i, (symbol, name) in enumerate(a_stocks, 1):
        try:
            print(f"[{i}/{len(a_stocks)}] 获取 {symbol} - {name} 昨日数据...", end=' ')

            rows = ts_client.get_daily_data(
                symbol=symbol,
                start_date=target_date,
                end_date=target_date,
            )

            if rows:
                # 仅保留等于 target_date 的记录（保险）
                rows = [r for r in rows if r['trade_date'].date() == target_date.date()]

                if rows:
                    with db_manager.get_session() as session:
                        new_cnt, upd_cnt = 0, 0
                        for data in rows:
                            existing = session.query(DailyData).filter_by(
                                symbol=symbol,
                                trade_date=data['trade_date']
                            ).first()
                            if existing:
                                for k, v in data.items():
                                    if k not in ['symbol', 'trade_date', 'id', 'created_at']:
                                        setattr(existing, k, v)
                                upd_cnt += 1
                            else:
                                session.add(DailyData(**data))
                                new_cnt += 1
                        session.commit()
                    total_records += len(rows)
                    success += 1
                    if new_cnt and upd_cnt:
                        print(f"✅ 新增 {new_cnt} 条，更新 {upd_cnt} 条")
                    elif new_cnt:
                        print(f"✅ 新增 {new_cnt} 条")
                    else:
                        print(f"✅ 更新 {upd_cnt} 条")
                else:
                    print("⚠️ 昨日无数据（可能非交易日或停牌）")
                    no_data += 1
            else:
                print("⚠️ 昨日无数据（可能非交易日或停牌）")
                no_data += 1

        except Exception as e:
            print(f"❌ 错误: {e}")
            fail += 1
            time.sleep(1.5)

    t1 = time.time()
    elapse = t1 - t0

    print("\n" + "=" * 60)
    print("A股昨日数据获取完成！")
    print(f"成功: {success}/{len(a_stocks)} ({(success/len(a_stocks))*100:.1f}%)")
    print(f"无数据: {no_data}/{len(a_stocks)} ({(no_data/len(a_stocks))*100:.1f}%)")
    print(f"失败: {fail}/{len(a_stocks)} ({(fail/len(a_stocks))*100:.1f}%)")
    print(f"总记录: {total_records}")
    print(f"总用时: {elapse/60:.1f} 分钟 (≈ {elapse/len(a_stocks):.2f} 秒/股)")
    print("=" * 60)

    # 显示数据库中该市场的最新交易日期
    if total_records > 0:
        with db_manager.get_session() as session:
            from sqlalchemy import desc
            latest_date = session.query(DailyData.trade_date).\
                filter(DailyData.symbol.like('%.SH') | DailyData.symbol.like('%.SZ')).\
                order_by(desc(DailyData.trade_date)).first()
            if latest_date:
                print(f"\n📅 数据库中最新交易日期: {latest_date[0]}")
                print("=" * 60)


if __name__ == '__main__':
    main()

