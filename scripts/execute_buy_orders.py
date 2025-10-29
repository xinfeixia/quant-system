#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行建仓买入操作
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


def calculate_quantity(price, amount, lot_size=100):
    """
    计算买入数量
    
    Args:
        price: 股票价格
        amount: 投资金额
        lot_size: 每手股数（港股通常是100或其他）
    
    Returns:
        买入数量（整手）
    """
    # 计算可以买多少股
    shares = int(amount / price)
    
    # 向下取整到整手
    lots = shares // lot_size
    quantity = lots * lot_size
    
    return quantity


def display_buy_plan(buy_plan, session):
    """显示买入计划"""
    print(f"\n{'='*120}")
    print(f"📋 建仓买入计划")
    print(f"{'='*120}\n")
    
    total_amount = 0
    
    for i, plan in enumerate(buy_plan, 1):
        symbol = plan['symbol']
        name = get_stock_name(session, symbol)
        quantity = plan['quantity']
        price = plan['price']
        amount = plan['amount']
        reason = plan['reason']
        score = plan.get('score', 0)
        signal_strength = plan.get('signal_strength', 0)
        
        total_amount += amount
        
        print(f"{i}. {symbol} - {name}")
        print(f"   买入数量: {quantity:,} 股")
        print(f"   买入价格: ¥{price:.2f}")
        print(f"   投资金额: ¥{amount:,.2f}")
        print(f"   综合评分: {score}分 | 信号强度: {signal_strength}")
        print(f"   买入理由: {reason}")
        print()
    
    print(f"{'='*120}")
    print(f"预计总投资: ¥{total_amount:,.2f}")
    print(f"{'='*120}\n")


def execute_buy_orders(buy_plan, db_manager, dry_run=False):
    """执行买入订单"""
    if dry_run:
        print("⚠️  模拟模式：不执行实际买入操作\n")
        return 0
    
    # 确认是否执行
    print(f"{'='*120}")
    confirm = input(f"确认执行买入操作？(yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ 已取消买入操作\n")
        return 0
    
    # 执行买入
    print(f"\n{'='*120}")
    print("🚀 开始执行买入操作...")
    print(f"{'='*120}\n")
    
    engine = get_trading_engine()
    success_count = 0
    fail_count = 0
    
    with db_manager.get_session() as session:
        for plan in buy_plan:
            symbol = plan['symbol']
            quantity = plan['quantity']
            price = plan['price']
            name = get_stock_name(session, symbol)
            
            try:
                print(f"买入 {symbol} - {name} ({quantity:,} 股) @ ¥{price:.2f}...", end=' ')
                
                result = engine.place_order(
                    symbol=symbol,
                    side='BUY',
                    order_type='LIMIT',
                    price=price,
                    quantity=quantity,
                    strategy_tag='new_position'
                )
                
                print(f"✅ 成功")
                logger.info(f"买入成功: {symbol}, 数量: {quantity}, 价格: {price}, 结果: {result}")
                success_count += 1
                
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
                print(f"   持仓已更新: {position.quantity:,} 股 @ ¥{position.avg_price:.2f}")
                
            except Exception as e:
                print(f"❌ 失败: {e}")
                logger.error(f"买入失败: {symbol}, 错误: {e}")
                fail_count += 1
    
    print(f"\n{'='*120}")
    print(f"执行完成: 成功 {success_count}/{len(buy_plan)}, 失败 {fail_count}/{len(buy_plan)}")
    print(f"{'='*120}\n")
    
    return success_count


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='执行建仓买入操作')
    parser.add_argument('--dry-run', action='store_true', help='模拟模式，不执行实际买入')
    parser.add_argument('--auto', action='store_true', help='自动执行，不需要确认')
    parser.add_argument('--amount', type=float, default=100000, help='总投资金额（默认100000）')
    args = parser.parse_args()
    
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 初始化交易引擎
    trading_mode = config_loader.config.get('trading', {}).get('mode', 'local_paper')
    if trading_mode == 'longport_paper' or trading_mode == 'longport_live':
        # 需要初始化 LongPort 客户端
        longport_client = init_longport_client(config_loader.api_config)
        create_trading_engine(config_loader.config, db_manager, longport_client)
    else:
        # 本地模拟交易
        create_trading_engine(config_loader.config, db_manager)
    
    print(f"\n{'='*120}")
    print(f"建仓买入执行")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"交易模式: {trading_mode}")
    print(f"总投资金额: ¥{args.amount:,.2f}")
    print(f"{'='*120}")
    
    with db_manager.get_session() as session:
        # 定义买入计划（基于之前的分析）
        # 采用稳健型方案
        buy_plan = []
        
        total_amount = args.amount
        
        # 1. 恒基地产 - 40% (STRONG_BUY) - 每手1000股
        symbol_1 = '0012.HK'
        price_1 = get_current_price(session, symbol_1)
        if price_1:
            amount_1 = total_amount * 0.40
            quantity_1 = calculate_quantity(price_1, amount_1, lot_size=1000)
            if quantity_1 > 0:
                buy_plan.append({
                    'symbol': symbol_1,
                    'quantity': quantity_1,
                    'price': price_1,
                    'amount': quantity_1 * price_1,
                    'reason': 'STRONG_BUY信号，MACD金叉+KDJ金叉+均线多头',
                    'score': 79,
                    'signal_strength': 65
                })

        # 2. 太古股份B - 30% (最高评分) - 每手2500股
        symbol_2 = '0087.HK'
        price_2 = get_current_price(session, symbol_2)
        if price_2:
            amount_2 = total_amount * 0.30
            quantity_2 = calculate_quantity(price_2, amount_2, lot_size=2500)
            if quantity_2 > 0:
                buy_plan.append({
                    'symbol': symbol_2,
                    'quantity': quantity_2,
                    'price': price_2,
                    'amount': quantity_2 * price_2,
                    'reason': '综合评分最高(84分)，KDJ金叉+均线多头',
                    'score': 84,
                    'signal_strength': 40
                })

        # 3. 太古地产 - 30% (地产蓝筹) - 每手200股
        symbol_3 = '1972.HK'
        price_3 = get_current_price(session, symbol_3)
        if price_3:
            amount_3 = total_amount * 0.30
            quantity_3 = calculate_quantity(price_3, amount_3, lot_size=200)
            if quantity_3 > 0:
                buy_plan.append({
                    'symbol': symbol_3,
                    'quantity': quantity_3,
                    'price': price_3,
                    'amount': quantity_3 * price_3,
                    'reason': '地产蓝筹，KDJ金叉+均线多头，RSI适中',
                    'score': 76,
                    'signal_strength': 40
                })
        
        if not buy_plan:
            print("\n❌ 无法生成买入计划（可能是价格数据缺失）\n")
            return
        
        # 显示买入计划
        display_buy_plan(buy_plan, session)
        
        # 执行买入
        if args.auto:
            # 自动执行模式
            print(f"🤖 自动执行模式")
            execute_buy_orders(buy_plan, db_manager, dry_run=args.dry_run)
        else:
            execute_buy_orders(buy_plan, db_manager, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

