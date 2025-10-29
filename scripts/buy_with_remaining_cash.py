#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用剩余资金买入指定股票
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import Position, DailyData, StockInfo
from trading.engine_factory import create_trading_engine, get_trading_engine
from data_collection.longport_client import init_longport_client
from utils.config_loader import init_config
from loguru import logger


def get_current_price(session, symbol):
    """获取当前价格"""
    latest_data = session.query(DailyData).filter(
        DailyData.symbol == symbol
    ).order_by(DailyData.trade_date.desc()).first()
    
    return latest_data.close if latest_data else None


def get_stock_name(session, symbol):
    """获取股票名称"""
    stock = session.query(StockInfo).filter_by(symbol=symbol).first()
    return stock.name if stock else "未知"


def calculate_quantity(price, amount, lot_size):
    """
    计算买入数量
    
    Args:
        price: 股票价格
        amount: 投资金额
        lot_size: 每手股数
    
    Returns:
        买入数量（整手）
    """
    # 计算可以买多少股
    shares = int(amount / price)
    
    # 向下取整到整手
    lots = shares // lot_size
    quantity = lots * lot_size
    
    return quantity


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='使用剩余资金买入指定股票')
    parser.add_argument('--symbol', type=str, required=True, help='股票代码，如0012.HK')
    parser.add_argument('--amount', type=float, required=True, help='可用资金')
    parser.add_argument('--lot-size', type=int, default=100, help='每手股数')
    parser.add_argument('--dry-run', action='store_true', help='模拟模式')
    args = parser.parse_args()
    
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 初始化交易引擎
    trading_mode = config_loader.config.get('trading', {}).get('mode', 'local_paper')
    if trading_mode == 'longport_paper' or trading_mode == 'longport_live':
        longport_client = init_longport_client(config_loader.api_config)
        create_trading_engine(config_loader.config, db_manager, longport_client)
    else:
        create_trading_engine(config_loader.config, db_manager)
    
    symbol = args.symbol
    available_cash = args.amount
    lot_size = args.lot_size
    
    print(f"\n{'='*100}")
    print(f"使用剩余资金买入股票")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"交易模式: {trading_mode}")
    print(f"{'='*100}\n")
    
    with db_manager.get_session() as session:
        # 获取股票信息
        name = get_stock_name(session, symbol)
        price = get_current_price(session, symbol)
        
        if not price:
            print(f"❌ 无法获取 {symbol} 的价格数据\n")
            return
        
        # 计算可买数量
        quantity = calculate_quantity(price, available_cash, lot_size)
        
        if quantity == 0:
            print(f"股票: {symbol} - {name}")
            print(f"当前价格: ¥{price:.2f}")
            print(f"可用资金: ¥{available_cash:,.2f}")
            print(f"每手股数: {lot_size}股")
            print(f"每手金额: ¥{price * lot_size:,.2f}")
            print(f"\n❌ 资金不足，无法购买1手 {symbol}")
            print(f"   需要至少: ¥{price * lot_size:,.2f}")
            print(f"   当前资金: ¥{available_cash:,.2f}")
            print(f"   还差: ¥{price * lot_size - available_cash:,.2f}\n")
            return
        
        amount = quantity * price
        
        # 显示买入计划
        print(f"📋 买入计划")
        print(f"{'='*100}")
        print(f"股票代码: {symbol}")
        print(f"股票名称: {name}")
        print(f"当前价格: ¥{price:.2f}")
        print(f"可用资金: ¥{available_cash:,.2f}")
        print(f"每手股数: {lot_size}股")
        print(f"买入数量: {quantity:,}股 ({quantity // lot_size}手)")
        print(f"投资金额: ¥{amount:,.2f}")
        print(f"剩余资金: ¥{available_cash - amount:,.2f}")
        print(f"{'='*100}\n")
        
        if args.dry_run:
            print("⚠️  模拟模式：不执行实际买入操作\n")
            return
        
        # 确认
        confirm = input("确认执行买入操作？(yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("❌ 已取消买入操作\n")
            return
        
        # 执行买入
        print(f"\n{'='*100}")
        print("🚀 开始执行买入操作...")
        print(f"{'='*100}\n")
        
        engine = get_trading_engine()
        
        try:
            print(f"买入 {symbol} - {name} ({quantity:,} 股) @ ¥{price:.2f}...", end=' ')
            
            result = engine.place_order(
                symbol=symbol,
                side='BUY',
                order_type='LIMIT',
                price=price,
                quantity=quantity,
                strategy_tag='remaining_cash_buy'
            )
            
            print(f"✅ 成功")
            logger.info(f"买入成功: {symbol}, 数量: {quantity}, 价格: {price}, 结果: {result}")
            
            # 更新或创建持仓
            position = session.query(Position).filter_by(symbol=symbol).first()
            if position:
                # 更新持仓成本
                old_cost = position.avg_price * position.quantity
                new_cost = price * quantity
                total_quantity = position.quantity + quantity
                position.avg_price = (old_cost + new_cost) / total_quantity
                position.quantity = total_quantity
            else:
                # 创建新持仓
                position = Position(
                    symbol=symbol,
                    market='HK',
                    quantity=quantity,
                    avg_price=price
                )
                session.add(position)
            
            session.commit()
            
            print(f"\n{'='*100}")
            print(f"✅ 买入成功！")
            print(f"{'='*100}")
            print(f"订单ID: {result.get('external_order_id', 'N/A')}")
            print(f"持仓更新: {position.quantity:,} 股 @ ¥{position.avg_price:.2f}")
            print(f"持仓市值: ¥{position.quantity * position.avg_price:,.2f}")
            print(f"{'='*100}\n")
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            logger.error(f"买入失败: {symbol}, 错误: {e}")


if __name__ == '__main__':
    main()

