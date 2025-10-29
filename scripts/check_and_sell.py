#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查港股持仓的卖出信号并自动执行卖出
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import Position, DailyData, TechnicalIndicator
from trading.auto_sell_monitor import AutoSellMonitor
from trading.engine_factory import create_trading_engine, get_trading_engine
from data_collection.longport_client import init_longport_client, get_longport_client
from utils.config_loader import init_config
from loguru import logger

def get_current_positions(db_manager):
    """获取当前所有港股持仓"""
    with db_manager.get_session() as session:
        positions = session.query(Position).filter(
            Position.quantity > 0,
            Position.market == 'HK'
        ).all()
        
        result = []
        for pos in positions:
            # 获取最新价格
            latest_data = session.query(DailyData).filter(
                DailyData.symbol == pos.symbol
            ).order_by(DailyData.trade_date.desc()).first()
            
            current_price = latest_data.close if latest_data else None
            
            result.append({
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'avg_price': pos.avg_price,
                'current_price': current_price,
                'market_value': pos.quantity * current_price if current_price else 0,
                'cost': pos.quantity * pos.avg_price,
                'pnl': (current_price - pos.avg_price) * pos.quantity if current_price else 0,
                'pnl_pct': (current_price - pos.avg_price) / pos.avg_price * 100 if current_price and pos.avg_price else 0
            })
        
        return result

def main():
    """主函数"""
    print(f"\n{'='*80}")
    print(f"检查港股持仓卖出信号并自动执行")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # 初始化配置和数据库
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()

    # 初始化交易引擎
    trading_mode = config_loader.config.get('trading', {}).get('mode', 'local_paper')

    if trading_mode in ['longport_paper', 'longport_live']:
        # 初始化 LongPort 客户端
        init_longport_client(config_loader.api_config)
        longport_client = get_longport_client()
        engine = create_trading_engine(config_loader.config, db_manager, longport_client)
    else:
        # 本地模拟交易
        engine = create_trading_engine(config_loader.config, db_manager)
    
    # 获取当前持仓
    positions = get_current_positions(db_manager)
    
    if not positions:
        print("✅ 当前没有港股持仓")
        return
    
    print(f"📊 当前持仓: {len(positions)} 只\n")
    print(f"{'代码':<12}{'数量':<10}{'成本价':<10}{'现价':<10}{'盈亏':<12}{'盈亏率':<10}")
    print(f"{'-'*80}")
    
    for pos in positions:
        pnl_str = f"{pos['pnl']:+.2f}" if pos['pnl'] else "N/A"
        pnl_pct_str = f"{pos['pnl_pct']:+.2f}%" if pos['current_price'] else "N/A"
        current_price_str = f"{pos['current_price']:.2f}" if pos['current_price'] else "N/A"
        
        print(f"{pos['symbol']:<12}{pos['quantity']:<10}{pos['avg_price']:<10.2f}{current_price_str:<10}{pnl_str:<12}{pnl_pct_str:<10}")
    
    print(f"\n{'='*80}")
    print(f"🔍 检查卖出信号...")
    print(f"{'='*80}\n")
    
    # 配置卖出策略
    strategy_config = config_loader.config.get('auto_sell', {
        'stop_loss': {
            'enabled': True,
            'stop_loss_pct': -0.05  # 止损 -5%
        },
        'take_profit': {
            'enabled': True,
            'take_profit_pct': 0.15  # 止盈 +15%
        },
        'fixed_hold': {
            'enabled': False,
            'hold_days': 10
        },
        'trailing_stop': {
            'enabled': False,
            'trailing_stop_pct': 0.05
        },
        'technical': {
            'enabled': True,
            'rsi_overbought': 70,
            'macd_death_cross': True
        }
    })
    
    # 创建监控器并检查持仓
    monitor = AutoSellMonitor(db_manager, strategy_config)
    sell_signals = monitor.check_positions()
    
    if not sell_signals:
        print("✅ 没有触发卖出条件的持仓\n")
        print("策略配置:")
        print(f"  - 止损: {strategy_config['stop_loss']['stop_loss_pct']*100:.1f}%")
        print(f"  - 止盈: {strategy_config['take_profit']['take_profit_pct']*100:.1f}%")
        print(f"  - 技术指标: RSI超买({strategy_config['technical']['rsi_overbought']}), MACD死叉")
        return
    
    print(f"🔔 发现 {len(sell_signals)} 个卖出信号:\n")
    
    for i, signal in enumerate(sell_signals, 1):
        print(f"{i}. {signal['symbol']}")
        print(f"   数量: {signal['quantity']}")
        print(f"   成本价: {signal['avg_price']:.2f}")
        print(f"   现价: {signal['current_price']:.2f}")
        print(f"   盈亏: {signal['pnl_pct']:+.2f}%")
        print(f"   原因: {', '.join(signal['reasons'])}")
        print()
    
    # 询问是否执行
    print(f"{'='*80}")
    response = input("是否执行卖出操作? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n❌ 已取消卖出操作")
        return
    
    print(f"\n{'='*80}")
    print(f"💼 开始执行卖出操作...")
    print(f"{'='*80}\n")

    # 使用已初始化的交易引擎
    print(f"使用交易引擎: {engine.__class__.__name__}\n")
    
    success_count = 0
    fail_count = 0
    
    for signal in sell_signals:
        symbol = signal['symbol']
        quantity = signal['quantity']
        price = signal['current_price']
        
        try:
            print(f"卖出 {symbol}: {quantity} 股 @ {price:.2f}...", end=' ')
            
            # 执行卖出
            result = engine.place_order(
                symbol=symbol,
                side='SELL',
                order_type='LIMIT',
                price=float(price),
                quantity=quantity,
                strategy_tag='auto_sell'
            )
            
            print(f"✅ 成功")
            print(f"   订单ID: {result.get('order_id', 'N/A')}")
            print(f"   状态: {result.get('status', 'N/A')}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            fail_count += 1
    
    print(f"\n{'='*80}")
    print(f"📊 执行结果")
    print(f"{'='*80}")
    print(f"成功: {success_count}/{len(sell_signals)}")
    print(f"失败: {fail_count}/{len(sell_signals)}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()

