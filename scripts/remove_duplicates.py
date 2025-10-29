#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查并删除数据库中的重复数据
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from database.models import DailyData, TechnicalIndicator, StockSelection, TradingSignal
from sqlalchemy import func, and_
from utils.config_loader import ConfigLoader
from loguru import logger

def check_duplicates(session, model, group_fields, table_name):
    """检查重复数据"""
    print(f"\n{'='*100}")
    print(f"检查 {table_name} 表的重复数据...")
    print(f"{'='*100}")
    
    # 构建GROUP BY查询
    query = session.query(
        *group_fields,
        func.count().label('count'),
        func.min(model.id).label('min_id'),
        func.max(model.id).label('max_id')
    ).group_by(*group_fields).having(func.count() > 1)
    
    duplicates = query.all()
    
    if not duplicates:
        print(f"✅ {table_name} 表没有重复数据")
        return 0, []
    
    total_duplicates = sum(d.count - 1 for d in duplicates)
    print(f"⚠️  发现 {len(duplicates)} 组重复数据，共 {total_duplicates} 条重复记录")
    
    # 显示前10组重复数据的详情
    print(f"\n前10组重复数据详情：")
    print(f"{'-'*100}")
    for i, dup in enumerate(duplicates[:10], 1):
        field_values = [str(getattr(dup, field.name)) for field in group_fields]
        print(f"{i}. {' + '.join(field_values)}: {dup.count}条记录 (ID: {dup.min_id} - {dup.max_id})")
    
    if len(duplicates) > 10:
        print(f"... 还有 {len(duplicates) - 10} 组重复数据")
    
    return total_duplicates, duplicates

def remove_duplicates(session, model, group_fields, table_name):
    """删除重复数据，保留ID最大的记录"""
    print(f"\n开始删除 {table_name} 表的重复数据...")
    
    # 查找所有重复组
    query = session.query(
        *group_fields,
        func.count().label('count')
    ).group_by(*group_fields).having(func.count() > 1)
    
    duplicates = query.all()
    
    if not duplicates:
        print(f"✅ {table_name} 表没有重复数据需要删除")
        return 0
    
    deleted_count = 0
    
    for dup in duplicates:
        # 构建过滤条件
        filters = []
        for field in group_fields:
            field_value = getattr(dup, field.name)
            filters.append(field == field_value)
        
        # 查找这组重复数据的所有记录
        records = session.query(model).filter(and_(*filters)).order_by(model.id.desc()).all()
        
        # 保留第一条（ID最大的），删除其他
        if len(records) > 1:
            for record in records[1:]:
                session.delete(record)
                deleted_count += 1
    
    session.commit()
    print(f"✅ 成功删除 {deleted_count} 条重复记录")
    return deleted_count

def main():
    """主函数"""
    print(f"\n{'='*100}")
    print(f"数据库重复数据检查和清理工具")
    print(f"{'='*100}\n")
    
    # 初始化数据库
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    db = DatabaseManager(config)
    
    # 统计信息
    total_checked = 0
    total_deleted = 0
    
    with db.get_session() as session:
        # 1. 检查 DailyData 表
        table_name = "DailyData (日线数据)"
        group_fields = [DailyData.symbol, DailyData.trade_date]
        dup_count, _ = check_duplicates(session, DailyData, group_fields, table_name)
        total_checked += dup_count
        
        if dup_count > 0:
            deleted = remove_duplicates(session, DailyData, group_fields, table_name)
            total_deleted += deleted
        
        # 2. 检查 TechnicalIndicator 表
        table_name = "TechnicalIndicator (技术指标)"
        group_fields = [TechnicalIndicator.symbol, TechnicalIndicator.trade_date]
        dup_count, _ = check_duplicates(session, TechnicalIndicator, group_fields, table_name)
        total_checked += dup_count
        
        if dup_count > 0:
            deleted = remove_duplicates(session, TechnicalIndicator, group_fields, table_name)
            total_deleted += deleted
        
        # 3. 检查 StockSelection 表
        table_name = "StockSelection (选股结果)"
        group_fields = [StockSelection.symbol, StockSelection.selection_date]
        dup_count, _ = check_duplicates(session, StockSelection, group_fields, table_name)
        total_checked += dup_count
        
        if dup_count > 0:
            deleted = remove_duplicates(session, StockSelection, group_fields, table_name)
            total_deleted += deleted
        
        # 4. 检查 TradingSignal 表
        table_name = "TradingSignal (交易信号)"
        group_fields = [TradingSignal.symbol, TradingSignal.signal_date]
        dup_count, _ = check_duplicates(session, TradingSignal, group_fields, table_name)
        total_checked += dup_count
        
        if dup_count > 0:
            deleted = remove_duplicates(session, TradingSignal, group_fields, table_name)
            total_deleted += deleted
    
    # 显示总结
    print(f"\n{'='*100}")
    print(f"清理完成！")
    print(f"{'='*100}")
    print(f"总共发现重复记录: {total_checked} 条")
    print(f"成功删除重复记录: {total_deleted} 条")
    
    if total_deleted > 0:
        print(f"\n✅ 数据库已清理完成，建议运行 VACUUM 命令优化数据库")
        print(f"   可以使用以下命令：")
        print(f"   sqlite3 data/longport_quant.db 'VACUUM;'")
    else:
        print(f"\n✅ 数据库没有重复数据，无需清理")
    
    print(f"{'='*100}\n")

if __name__ == '__main__':
    main()

