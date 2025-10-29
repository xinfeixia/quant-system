#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看数据库表结构
"""

import sqlite3

def show_table_structure():
    """查看数据库表结构"""
    
    conn = sqlite3.connect('data/longport_quant.db')
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("=" * 80)
    print("数据库表结构")
    print("=" * 80)
    print()
    
    for table in tables:
        table_name = table[0]
        print(f"表名: {table_name}")
        print("-" * 80)
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"{'列名':<30} {'类型':<15} {'非空':<8} {'默认值':<15}")
        print("-" * 80)
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            not_null = "是" if col[3] else "否"
            default_val = col[4] if col[4] else ""
            print(f"{col_name:<30} {col_type:<15} {not_null:<8} {str(default_val):<15}")
        
        # 获取记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\n总记录数: {count:,}")
        print()
        print()
    
    conn.close()

if __name__ == '__main__':
    show_table_structure()

