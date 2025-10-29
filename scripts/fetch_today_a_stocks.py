#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取A股今天的交易数据
"""

import sys
from pathlib import Path
import time
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import DailyData, StockInfo
from data_collection.tushare_client import TushareClient
from utils.config_loader import init_config
from sqlalchemy import func

def main():
    """获取A股今天的交易数据"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 获取Tushare配置
    tushare_config = config_loader.api_config.get('tushare', {})
    token = tushare_config.get('token')
    if not token:
        raise ValueError("Tushare token未配置")
    
    # 使用保守提速配置：关闭daily_basic，统一用客户端限速；去掉每只股票额外sleep
    tushare_client = TushareClient(token=token, request_interval=1.2, enable_daily_basic=False)

    # 获取所有A股的symbol和name
    with db_manager.get_session() as session:
        a_stocks = [(s.symbol, s.name) for s in session.query(StockInfo).filter_by(market='CN').all()]

    # 仅获取最近2天的数据（覆盖最近交易日即可）
    from datetime import timedelta
    today = datetime.now()
    start_date = today - timedelta(days=2)

    success_count = 0
    fail_count = 0
    no_data_count = 0
    total_records = 0

    print(f"\n{'='*60}")
    print(f"开始获取A股最新交易数据")
    print(f"股票数量: {len(a_stocks)} 只")
    print(f"日期范围: {start_date.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")

    start_time = time.time()

    for i, (symbol, name) in enumerate(a_stocks, 1):
        try:
            print(f"[{i}/{len(a_stocks)}] 获取 {symbol} - {name} 数据...", end=' ')

            # 获取最近7天的数据
            daily_data = tushare_client.get_daily_data(
                symbol=symbol,
                start_date=start_date,
                end_date=today
            )

            if daily_data and len(daily_data) > 0:
                # 保存到数据库
                with db_manager.get_session() as session:
                    new_count = 0
                    update_count = 0

                    for data in daily_data:
                        # 检查是否已存在该日期的数据
                        existing = session.query(DailyData).filter_by(
                            symbol=symbol,
                            trade_date=data['trade_date']
                        ).first()

                        if existing:
                            # 更新现有数据
                            for key, value in data.items():
                                if key not in ['symbol', 'trade_date', 'id', 'created_at']:
                                    setattr(existing, key, value)
                            update_count += 1
                        else:
                            # 插入新数据
                            new_data = DailyData(**data)
                            session.add(new_data)
                            new_count += 1

                    session.commit()

                    if new_count > 0 and update_count > 0:
                        print(f"✅ 新增 {new_count} 条，更新 {update_count} 条")
                    elif new_count > 0:
                        print(f"✅ 新增 {new_count} 条数据")
                    else:
                        print(f"✅ 更新 {update_count} 条数据")

                success_count += 1
                total_records += len(daily_data)
            else:
                print(f"⚠️  近期无交易数据（可能停牌）")
                no_data_count += 1
            
            # 控制请求频率（Tushare限制50次/分钟）
            # time.sleep(1.5)
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            fail_count += 1
            time.sleep(2)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"\n{'='*60}")
    print(f"A股最新数据获取完成！")
    print(f"成功: {success_count}/{len(a_stocks)} ({success_count/len(a_stocks)*100:.1f}%)")
    print(f"无数据: {no_data_count}/{len(a_stocks)} ({no_data_count/len(a_stocks)*100:.1f}%)")
    print(f"失败: {fail_count}/{len(a_stocks)} ({fail_count/len(a_stocks)*100:.1f}%)")
    print(f"总数据: {total_records} 条")
    print(f"总用时: {elapsed/60:.1f} 分钟")
    print(f"平均速度: {elapsed/len(a_stocks):.1f} 秒/股票")
    print(f"{'='*60}")

    # 显示最新数据日期
    if total_records > 0:
        with db_manager.get_session() as session:
            latest_date = session.query(DailyData.trade_date).filter(
                DailyData.symbol.like('%.SH') | DailyData.symbol.like('%.SZ')
            ).order_by(DailyData.trade_date.desc()).first()
            if latest_date:
                print(f"\n📅 数据库中最新交易日期: {latest_date[0]}")
                print(f"{'='*60}")

if __name__ == '__main__':
    main()

