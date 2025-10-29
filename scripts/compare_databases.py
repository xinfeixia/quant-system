#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较两个数据库的内容
"""

import sqlite3
from pathlib import Path

def check_database(db_path, db_name):
    """检查数据库内容"""
    
    print(f"\n{'=' * 80}")
    print(f"{db_name}")
    print(f"路径: {db_path}")
    print(f"{'=' * 80}\n")
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在")
        return
    
    file_size = Path(db_path).stat().st_size
    print(f"文件大小: {file_size:,} 字节 ({file_size / 1024 / 1024:.2f} MB)\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # A股最新交易数据
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
    print(f"   总记录数: {result[2]:,}")
    print()
    
    # 港股最新交易数据
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
    print(f"   总记录数: {result[2]:,}")
    print()
    
    # A股最新技术指标
    print("3. A股最新技术指标:")
    cursor.execute("""
        SELECT MAX(trade_date) as latest_date, 
               COUNT(DISTINCT symbol) as stock_count
        FROM technical_indicators 
        WHERE symbol LIKE '%.SH' OR symbol LIKE '%.SZ'
    """)
    result = cursor.fetchone()
    print(f"   最新日期: {result[0]}")
    print(f"   股票数量: {result[1]}")
    print()
    
    # 港股最新技术指标
    print("4. 港股最新技术指标:")
    cursor.execute("""
        SELECT MAX(trade_date) as latest_date, 
               COUNT(DISTINCT symbol) as stock_count
        FROM technical_indicators 
        WHERE symbol LIKE '%.HK'
    """)
    result = cursor.fetchone()
    print(f"   最新日期: {result[0]}")
    print(f"   股票数量: {result[1]}")
    print()
    
    # 最近3天的数据记录数
    print("5. 最近3天A股数据记录数:")
    cursor.execute("""
        SELECT d.trade_date, COUNT(*) as count 
        FROM daily_data d
        JOIN stock_info s ON d.symbol = s.symbol
        WHERE s.market='CN' 
        GROUP BY d.trade_date 
        ORDER BY d.trade_date DESC 
        LIMIT 3
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]:,} 条")
    print()
    
    print("6. 最近3天港股数据记录数:")
    cursor.execute("""
        SELECT d.trade_date, COUNT(*) as count 
        FROM daily_data d
        JOIN stock_info s ON d.symbol = s.symbol
        WHERE s.market='HK' 
        GROUP BY d.trade_date 
        ORDER BY d.trade_date DESC 
        LIMIT 3
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]:,} 条")
    print()
    
    # 交易信号统计
    print("7. 交易信号统计:")
    cursor.execute("""
        SELECT COUNT(*) as total_signals
        FROM trading_signals
    """)
    result = cursor.fetchone()
    print(f"   总信号数: {result[0]:,}")
    
    cursor.execute("""
        SELECT ts.signal_date, s.market, ts.signal_type, COUNT(*) as count 
        FROM trading_signals ts
        JOIN stock_info s ON ts.symbol = s.symbol
        GROUP BY ts.signal_date, s.market, ts.signal_type 
        ORDER BY ts.signal_date DESC, s.market, ts.signal_type 
        LIMIT 5
    """)
    print(f"   最近的信号:")
    for row in cursor.fetchall():
        print(f"   {row[0]} {row[1]} {row[2]}: {row[3]:,} 条")
    print()
    
    conn.close()

def main():
    """主函数"""
    
    print("\n" + "=" * 80)
    print("数据库对比分析")
    print("=" * 80)
    
    # 数据库1: D:\xiaohongshu\data\longport_quant.db
    db1_path = r"D:\xiaohongshu\data\longport_quant.db"
    check_database(db1_path, "数据库1 (当前使用)")
    
    # 数据库2: D:\xiaohongshu\longport-quant-system\data\longport_quant.db
    db2_path = r"D:\xiaohongshu\longport-quant-system\data\longport_quant.db"
    check_database(db2_path, "数据库2 (项目目录)")
    
    print("\n" + "=" * 80)
    print("对比完成！")
    print("=" * 80)
    print("\n建议:")
    print("1. 数据库2 (352.60 MB) 比数据库1 (94.26 MB) 大得多")
    print("2. 需要检查哪个数据库包含最新的数据")
    print("3. 建议统一使用一个数据库，避免数据不一致")
    print()

if __name__ == '__main__':
    main()

