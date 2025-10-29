#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库状态
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import init_config

def check_database_status():
    """检查数据库状态"""

    # 加载配置获取数据库路径
    config_dir = str(project_root / 'config')
    config_loader = init_config(config_dir=config_dir)
    db_config = config_loader.config.get('database', {})
    db_path = db_config.get('sqlite', {}).get('path', 'data/longport_quant.db')

    print(f"使用数据库: {db_path}")
    print()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("数据库状态检查")
    print("=" * 60)
    print()
    
    # 1. A股最新交易数据
    print("1. A股最新交易数据:")
    cursor.execute("""
        SELECT MAX(d.trade_date) as latest_date,
               COUNT(DISTINCT d.symbol) as stock_count,
               COUNT(*) as total_records
        FROM daily_data d
        JOIN stock_info s ON d.symbol = s.symbol
        WHERE s.market='CN'
    """)
    result = cursor.fetchone()
    print(f"   最新日期: {result[0]}")
    print(f"   股票数量: {result[1]}")
    print(f"   总记录数: {result[2]}")
    print()

    # 2. 港股最新交易数据
    print("2. 港股最新交易数据:")
    cursor.execute("""
        SELECT MAX(d.trade_date) as latest_date,
               COUNT(DISTINCT d.symbol) as stock_count,
               COUNT(*) as total_records
        FROM daily_data d
        JOIN stock_info s ON d.symbol = s.symbol
        WHERE s.market='HK'
    """)
    result = cursor.fetchone()
    print(f"   最新日期: {result[0]}")
    print(f"   股票数量: {result[1]}")
    print(f"   总记录数: {result[2]}")
    print()
    
    # 3. A股最新技术指标
    print("3. A股最新技术指标:")
    cursor.execute("""
        SELECT MAX(trade_date) as latest_date, 
               COUNT(DISTINCT symbol) as stock_count,
               COUNT(*) as total_records
        FROM technical_indicators 
        WHERE symbol LIKE '%.SH' OR symbol LIKE '%.SZ'
    """)
    result = cursor.fetchone()
    print(f"   最新日期: {result[0]}")
    print(f"   股票数量: {result[1]}")
    print(f"   总记录数: {result[2]}")
    print()
    
    # 4. 港股最新技术指标
    print("4. 港股最新技术指标:")
    cursor.execute("""
        SELECT MAX(trade_date) as latest_date, 
               COUNT(DISTINCT symbol) as stock_count,
               COUNT(*) as total_records
        FROM technical_indicators 
        WHERE symbol LIKE '%.HK'
    """)
    result = cursor.fetchone()
    print(f"   最新日期: {result[0]}")
    print(f"   股票数量: {result[1]}")
    print(f"   总记录数: {result[2]}")
    print()
    
    # 5. 最近5天A股数据记录数
    print("5. 最近5天A股数据记录数:")
    cursor.execute("""
        SELECT d.trade_date, COUNT(*) as count
        FROM daily_data d
        JOIN stock_info s ON d.symbol = s.symbol
        WHERE s.market='CN'
        GROUP BY d.trade_date
        ORDER BY d.trade_date DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]:,} 条")
    print()

    # 6. 最近5天港股数据记录数
    print("6. 最近5天港股数据记录数:")
    cursor.execute("""
        SELECT d.trade_date, COUNT(*) as count
        FROM daily_data d
        JOIN stock_info s ON d.symbol = s.symbol
        WHERE s.market='HK'
        GROUP BY d.trade_date
        ORDER BY d.trade_date DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]:,} 条")
    print()
    
    # 7. 最近5天A股技术指标记录数
    print("7. 最近5天A股技术指标记录数:")
    cursor.execute("""
        SELECT trade_date, COUNT(*) as count 
        FROM technical_indicators 
        WHERE symbol LIKE '%.SH' OR symbol LIKE '%.SZ'
        GROUP BY trade_date 
        ORDER BY trade_date DESC 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]:,} 条")
    print()
    
    # 8. 最近5天港股技术指标记录数
    print("8. 最近5天港股技术指标记录数:")
    cursor.execute("""
        SELECT trade_date, COUNT(*) as count 
        FROM technical_indicators 
        WHERE symbol LIKE '%.HK'
        GROUP BY trade_date 
        ORDER BY trade_date DESC 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]:,} 条")
    print()
    
    # 9. 交易信号统计
    print("9. 交易信号统计:")
    cursor.execute("""
        SELECT ts.signal_date, s.market, ts.signal_type, COUNT(*) as count
        FROM trading_signals ts
        JOIN stock_info s ON ts.symbol = s.symbol
        GROUP BY ts.signal_date, s.market, ts.signal_type
        ORDER BY ts.signal_date DESC, s.market, ts.signal_type
        LIMIT 10
    """)
    print(f"   {'日期':<12} {'市场':<6} {'信号类型':<10} {'数量':<8}")
    print("   " + "-" * 40)
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} {row[1]:<6} {row[2]:<10} {row[3]:,}")
    print()
    
    # 10. 数据完整性检查
    print("10. 数据完整性检查:")

    # 检查是否有交易数据但没有技术指标的情况
    cursor.execute("""
        SELECT COUNT(DISTINCT d.symbol)
        FROM daily_data d
        JOIN stock_info s ON d.symbol = s.symbol
        LEFT JOIN technical_indicators t
        ON d.symbol = t.symbol AND d.trade_date = t.trade_date
        WHERE s.market='CN'
        AND d.trade_date = (
            SELECT MAX(d2.trade_date)
            FROM daily_data d2
            JOIN stock_info s2 ON d2.symbol = s2.symbol
            WHERE s2.market='CN'
        )
        AND t.symbol IS NULL
    """)
    cn_missing = cursor.fetchone()[0]
    print(f"   A股缺少技术指标的股票数: {cn_missing}")

    cursor.execute("""
        SELECT COUNT(DISTINCT d.symbol)
        FROM daily_data d
        JOIN stock_info s ON d.symbol = s.symbol
        LEFT JOIN technical_indicators t
        ON d.symbol = t.symbol AND d.trade_date = t.trade_date
        WHERE s.market='HK'
        AND d.trade_date = (
            SELECT MAX(d2.trade_date)
            FROM daily_data d2
            JOIN stock_info s2 ON d2.symbol = s2.symbol
            WHERE s2.market='HK'
        )
        AND t.symbol IS NULL
    """)
    hk_missing = cursor.fetchone()[0]
    print(f"   港股缺少技术指标的股票数: {hk_missing}")
    print()
    
    print("=" * 60)
    print("检查完成！")
    print("=" * 60)
    
    conn.close()

if __name__ == '__main__':
    check_database_status()

