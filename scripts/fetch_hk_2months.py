#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量获取所有港股2个月的历史数据
使用 get_candlesticks (count模式) 避免 API 限制
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import init_config
from database import get_db_manager, init_database
from database.models import DailyData, StockInfo
from data_collection.longport_client import init_longport_client, get_longport_client
from loguru import logger


def fetch_stock_history(symbol, name, longport_client, db_manager):
    """获取单只股票的历史数据（2个月）"""
    try:
        # 使用 count 模式获取最近60天的数据（约2个月）
        candlesticks = longport_client.get_candlesticks(
            symbol=symbol,
            period='day',
            count=60  # 获取60天数据
        )
        
        if not candlesticks or len(candlesticks) == 0:
            return 0, 0, "无数据"
        
        # 保存到数据库
        with db_manager.get_session() as session:
            inserted = 0
            updated = 0
            
            for candle in candlesticks:
                trade_date = candle.timestamp.date()
                
                # 检查是否已存在
                existing = session.query(DailyData).filter_by(
                    symbol=symbol,
                    trade_date=trade_date
                ).first()
                
                if existing:
                    # 更新数据
                    existing.open = candle.open
                    existing.high = candle.high
                    existing.low = candle.low
                    existing.close = candle.close
                    existing.volume = candle.volume
                    existing.turnover = candle.turnover
                    updated += 1
                else:
                    # 插入新数据
                    daily_data = DailyData(
                        symbol=symbol,
                        trade_date=trade_date,
                        open=candle.open,
                        high=candle.high,
                        low=candle.low,
                        close=candle.close,
                        volume=candle.volume,
                        turnover=candle.turnover,
                        created_at=datetime.now()
                    )
                    session.add(daily_data)
                    inserted += 1
            
            session.commit()
        
        return inserted, updated, f"新增{inserted}条, 更新{updated}条"
        
    except Exception as e:
        logger.error(f"获取 {symbol} 数据失败: {e}")
        return 0, 0, f"错误: {str(e)[:50]}"


def main():
    """主函数"""
    print("\n" + "="*80)
    print("批量获取所有港股2个月历史数据")
    print("="*80)
    
    # 初始化配置和数据库
    logger.info("初始化配置与数据库...")
    config_dir = str(project_root / 'config')
    config_loader = init_config(config_dir=config_dir)
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 初始化长桥客户端
    init_longport_client(config_loader.api_config)
    longport_client = get_longport_client()
    
    # 获取所有活跃港股
    with db_manager.get_session() as session:
        hk_stocks = [(s.symbol, s.name) for s in session.query(StockInfo).filter_by(
            market='HK', 
            is_active=True
        ).all()]
    
    print(f"\n共 {len(hk_stocks)} 只港股需要获取数据")
    print(f"每只股票获取最近60天（约2个月）的数据\n")
    
    success_count = 0
    fail_count = 0
    total_inserted = 0
    total_updated = 0
    
    start_time = time.time()
    
    for i, (symbol, name) in enumerate(hk_stocks, 1):
        print(f"[{i}/{len(hk_stocks)}] {symbol} - {name}... ", end='', flush=True)
        
        inserted, updated, msg = fetch_stock_history(symbol, name, longport_client, db_manager)
        
        if inserted > 0 or updated > 0:
            print(f"✅ {msg}")
            success_count += 1
            total_inserted += inserted
            total_updated += updated
        else:
            print(f"⚠️  {msg}")
            fail_count += 1
        
        # 每10只股票显示一次进度
        if i % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(hk_stocks) - i) * avg_time
            print(f"\n📊 进度: {i}/{len(hk_stocks)} ({i*100//len(hk_stocks)}%), "
                  f"成功: {success_count}, 失败: {fail_count}, "
                  f"已用时: {elapsed/60:.1f}分钟, 预计剩余: {remaining/60:.1f}分钟\n")
        
        # 避免请求过快（每秒最多2个请求）
        time.sleep(0.6)
    
    # 最终统计
    elapsed = time.time() - start_time
    print("\n" + "="*80)
    print("数据获取完成！")
    print("="*80)
    print(f"总计: {len(hk_stocks)} 只港股")
    print(f"成功: {success_count} 只")
    print(f"失败: {fail_count} 只")
    print(f"新增数据: {total_inserted} 条")
    print(f"更新数据: {total_updated} 条")
    print(f"总用时: {elapsed/60:.1f} 分钟")
    print("="*80)


if __name__ == '__main__':
    main()

