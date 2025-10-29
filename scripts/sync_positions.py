#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 LongPort 模拟账户的真实持仓到数据库
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import Position
from data_collection.longport_client import init_longport_client, get_longport_client
from utils.config_loader import init_config
from loguru import logger

def get_longport_positions(trade_ctx):
    """从 LongPort 获取真实持仓"""
    try:
        response = trade_ctx.stock_positions()
        # stock_positions() 返回的是 StockPositionsResponse 对象
        # response.channels 是一个列表，每个 channel 有 positions 属性
        all_positions = []
        if hasattr(response, 'channels') and response.channels:
            for channel in response.channels:
                if hasattr(channel, 'positions') and channel.positions:
                    all_positions.extend(channel.positions)
        return all_positions
    except Exception as e:
        logger.error(f"获取 LongPort 持仓失败: {e}")
        return []

def get_db_positions(db_manager):
    """从数据库获取持仓记录"""
    with db_manager.get_session() as session:
        positions = session.query(Position).filter(
            Position.quantity > 0,
            Position.market == 'HK'
        ).all()
        
        result = []
        for pos in positions:
            result.append({
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'avg_price': pos.avg_price,
                'market': pos.market
            })
        return result

def sync_positions(db_manager, longport_positions):
    """同步持仓到数据库"""
    with db_manager.get_session() as session:
        # 获取所有港股持仓
        db_positions = session.query(Position).filter(
            Position.market == 'HK'
        ).all()

        # 创建 LongPort 持仓字典
        lp_pos_dict = {}
        for pos in longport_positions:
            symbol = pos.symbol
            lp_pos_dict[symbol] = {
                'quantity': int(pos.quantity),  # 转换为 int
                'avg_price': float(pos.cost_price)  # 转换为 float
            }

        # 更新数据库持仓
        updated = 0
        cleared = 0
        added = 0

        # 更新或清零现有持仓
        for db_pos in db_positions:
            symbol = db_pos.symbol

            if symbol in lp_pos_dict:
                # 更新持仓数量和成本价
                lp_data = lp_pos_dict[symbol]
                if db_pos.quantity != lp_data['quantity'] or abs(db_pos.avg_price - lp_data['avg_price']) > 0.01:
                    logger.info(f"更新 {symbol}: {db_pos.quantity} -> {lp_data['quantity']}, {db_pos.avg_price:.2f} -> {lp_data['avg_price']:.2f}")
                    db_pos.quantity = lp_data['quantity']
                    db_pos.avg_price = lp_data['avg_price']
                    updated += 1
            else:
                # LongPort 中没有此持仓，清零
                if db_pos.quantity > 0:
                    logger.info(f"清零 {symbol}: {db_pos.quantity} -> 0")
                    db_pos.quantity = 0
                    cleared += 1

        # 添加数据库中不存在的新持仓
        db_symbols = {pos.symbol for pos in db_positions}
        for symbol, lp_data in lp_pos_dict.items():
            if symbol not in db_symbols:
                logger.info(f"新增 {symbol}: {lp_data['quantity']} 股 @ {lp_data['avg_price']:.2f}")
                new_pos = Position(
                    symbol=symbol,
                    market='HK',
                    quantity=lp_data['quantity'],
                    avg_price=lp_data['avg_price']
                )
                session.add(new_pos)
                added += 1

        session.commit()
        return updated, cleared, added

def main():
    """主函数"""
    print(f"\n{'='*80}")
    print(f"同步 LongPort 模拟账户持仓")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # 初始化配置和数据库
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 初始化 LongPort 客户端
    init_longport_client(config_loader.api_config)
    longport_client = get_longport_client()
    trade_ctx = longport_client.get_trade_context()
    
    print("📊 数据库中的持仓记录:\n")
    db_positions = get_db_positions(db_manager)
    
    if db_positions:
        print(f"{'代码':<12}{'数量':<10}{'成本价':<10}{'市场':<10}")
        print(f"{'-'*50}")
        for pos in db_positions:
            print(f"{pos['symbol']:<12}{pos['quantity']:<10}{pos['avg_price']:<10.2f}{pos['market']:<10}")
    else:
        print("  (无持仓)")
    
    print(f"\n{'='*80}")
    print("🔄 从 LongPort 获取真实持仓...\n")
    
    longport_positions = get_longport_positions(trade_ctx)
    
    if longport_positions:
        print(f"{'代码':<12}{'名称':<20}{'数量':<10}{'成本价':<10}")
        print(f"{'-'*60}")
        for pos in longport_positions:
            symbol_name = pos.symbol_name if hasattr(pos, 'symbol_name') else ''
            print(f"{pos.symbol:<12}{symbol_name:<20}{pos.quantity:<10}{pos.cost_price:<10.2f}")
    else:
        print("  (无持仓)")

    print(f"\n{'='*80}")
    print("🔄 同步持仓到数据库...\n")

    updated, cleared, added = sync_positions(db_manager, longport_positions)

    print(f"✅ 同步完成:")
    print(f"  - 新增: {added} 条")
    print(f"  - 更新: {updated} 条")
    print(f"  - 清零: {cleared} 条")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()

