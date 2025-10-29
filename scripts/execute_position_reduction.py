#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行持仓减仓操作
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


def display_reduction_plan(reduction_plan, session):
    """显示减仓计划"""
    print(f"\n{'='*100}")
    print(f"📋 减仓计划")
    print(f"{'='*100}\n")
    
    total_value = 0
    
    for i, plan in enumerate(reduction_plan, 1):
        symbol = plan['symbol']
        name = get_stock_name(session, symbol)
        quantity = plan['quantity']
        price = plan['price']
        reason = plan['reason']
        
        value = quantity * price
        total_value += value
        
        print(f"{i}. {symbol} - {name}")
        print(f"   减仓数量: {quantity:,} 股")
        print(f"   卖出价格: ¥{price:.2f}")
        print(f"   预计金额: ¥{value:,.2f}")
        print(f"   减仓原因: {reason}")
        print()
    
    print(f"{'='*100}")
    print(f"预计总金额: ¥{total_value:,.2f}")
    print(f"{'='*100}\n")


def execute_reduction(reduction_plan, db_manager, dry_run=False):
    """执行减仓"""
    if dry_run:
        print("⚠️  模拟模式：不执行实际卖出操作\n")
        return 0
    
    # 确认是否执行
    print(f"{'='*100}")
    confirm = input(f"确认执行减仓操作？(yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ 已取消减仓操作\n")
        return 0
    
    # 执行卖出
    print(f"\n{'='*100}")
    print("🚀 开始执行减仓操作...")
    print(f"{'='*100}\n")
    
    engine = get_trading_engine()
    success_count = 0
    fail_count = 0
    
    with db_manager.get_session() as session:
        for plan in reduction_plan:
            symbol = plan['symbol']
            quantity = plan['quantity']
            price = plan['price']
            name = get_stock_name(session, symbol)
            
            try:
                print(f"卖出 {symbol} - {name} ({quantity:,} 股) @ ¥{price:.2f}...", end=' ')
                
                result = engine.place_order(
                    symbol=symbol,
                    side='SELL',
                    order_type='LIMIT',
                    price=price,
                    quantity=quantity,
                    strategy_tag='position_reduction'
                )
                
                print(f"✅ 成功")
                logger.info(f"减仓成功: {symbol}, 数量: {quantity}, 价格: {price}, 结果: {result}")
                success_count += 1
                
                # 更新持仓
                position = session.query(Position).filter_by(symbol=symbol).first()
                if position:
                    position.quantity -= quantity
                    session.commit()
                    print(f"   持仓已更新: 剩余 {position.quantity:,} 股")
                
            except Exception as e:
                print(f"❌ 失败: {e}")
                logger.error(f"减仓失败: {symbol}, 错误: {e}")
                fail_count += 1
    
    print(f"\n{'='*100}")
    print(f"执行完成: 成功 {success_count}/{len(reduction_plan)}, 失败 {fail_count}/{len(reduction_plan)}")
    print(f"{'='*100}\n")
    
    return success_count


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='执行持仓减仓操作')
    parser.add_argument('--dry-run', action='store_true', help='模拟模式，不执行实际卖出')
    parser.add_argument('--auto', action='store_true', help='自动执行，不需要确认')
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
    
    print(f"\n{'='*100}")
    print(f"持仓减仓执行")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"交易模式: {trading_mode}")
    print(f"{'='*100}")
    
    with db_manager.get_session() as session:
        # 定义减仓计划（基于之前的分析）
        reduction_plan = []
        
        # 1. 建设银行 - RSI 94.2 极度超买，减仓60%
        pos_939 = session.query(Position).filter_by(symbol='0939.HK').first()
        if pos_939 and pos_939.quantity > 0:
            price_939 = get_current_price(session, '0939.HK')
            if price_939:
                reduction_qty = int(pos_939.quantity * 0.6)  # 减仓60%
                reduction_plan.append({
                    'symbol': '0939.HK',
                    'quantity': reduction_qty,
                    'price': price_939,
                    'reason': 'RSI极度超买(94.2)，技术指标严重过热'
                })
        
        # 2. 昆仑能源 - RSI 79.7 超买，减仓50%
        pos_135 = session.query(Position).filter_by(symbol='0135.HK').first()
        if pos_135 and pos_135.quantity > 0:
            price_135 = get_current_price(session, '0135.HK')
            if price_135:
                reduction_qty = int(pos_135.quantity * 0.5)  # 减仓50%
                reduction_plan.append({
                    'symbol': '0135.HK',
                    'quantity': reduction_qty,
                    'price': price_135,
                    'reason': 'RSI超买(79.7)，KDJ超买，短期见顶'
                })
        
        if not reduction_plan:
            print("\n✅ 没有需要减仓的持仓\n")
            return
        
        # 显示减仓计划
        display_reduction_plan(reduction_plan, session)
        
        # 执行减仓
        if args.auto:
            # 自动执行模式
            print(f"🤖 自动执行模式")
            execute_reduction(reduction_plan, db_manager, dry_run=args.dry_run)
        else:
            execute_reduction(reduction_plan, db_manager, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

