#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查港股持仓的卖出信号并执行卖出操作
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
from data_collection.longport_client import init_longport_client
from utils.config_loader import init_config
from loguru import logger


def get_hk_positions(db_manager):
    """获取港股持仓（返回字典列表）"""
    with db_manager.get_session() as session:
        positions = session.query(Position).filter(
            Position.quantity > 0,
            Position.market == 'HK'
        ).all()

        # 转换为字典列表，避免 DetachedInstanceError
        position_list = []
        for pos in positions:
            position_list.append({
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'avg_price': pos.avg_price,
                'market': pos.market,
                'updated_at': pos.updated_at
            })

        return position_list


def display_positions(positions, db_manager):
    """显示持仓信息"""
    if not positions:
        print("\n📭 当前没有港股持仓")
        return

    print(f"\n{'='*80}")
    print(f"💼 当前港股持仓 ({len(positions)} 只)")
    print(f"{'='*80}")
    print(f"{'股票代码':<12} {'数量':<10} {'成本价':<12} {'最新价':<12} {'盈亏':<12} {'盈亏率':<10}")
    print(f"{'-'*80}")

    total_cost = 0
    total_value = 0

    with db_manager.get_session() as session:
        for pos in positions:
            # 获取最新价格
            latest_data = session.query(DailyData).filter(
                DailyData.symbol == pos['symbol']
            ).order_by(DailyData.trade_date.desc()).first()

            if latest_data:
                current_price = latest_data.close
                cost = pos['avg_price'] * pos['quantity']
                value = current_price * pos['quantity']
                pnl = value - cost
                pnl_pct = (pnl / cost * 100) if cost > 0 else 0

                total_cost += cost
                total_value += value

                pnl_str = f"{pnl:+.2f}" if pnl != 0 else "0.00"
                pnl_pct_str = f"{pnl_pct:+.2f}%" if pnl_pct != 0 else "0.00%"

                print(f"{pos['symbol']:<12} {pos['quantity']:<10} {pos['avg_price']:<12.2f} {current_price:<12.2f} {pnl_str:<12} {pnl_pct_str:<10}")
            else:
                print(f"{pos['symbol']:<12} {pos['quantity']:<10} {pos['avg_price']:<12.2f} {'N/A':<12} {'N/A':<12} {'N/A':<10}")

    if total_cost > 0:
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100)
        print(f"{'-'*80}")
        print(f"{'总计':<12} {'':<10} {total_cost:<12.2f} {total_value:<12.2f} {total_pnl:+.2f}{'':>6} {total_pnl_pct:+.2f}%")

    print(f"{'='*80}\n")


def check_sell_signals(db_manager, strategy_config):
    """检查卖出信号"""
    monitor = AutoSellMonitor(db_manager, strategy_config)
    sell_signals = monitor.check_positions()
    return sell_signals


def execute_sell_orders(sell_signals, db_manager, dry_run=False):
    """执行卖出订单"""
    if not sell_signals:
        print("✅ 没有触发卖出条件的持仓\n")
        return 0
    
    print(f"\n{'='*80}")
    print(f"🔔 检测到 {len(sell_signals)} 个卖出信号")
    print(f"{'='*80}\n")
    
    for i, signal in enumerate(sell_signals, 1):
        print(f"{i}. {signal['symbol']}")
        print(f"   数量: {signal['quantity']}")
        print(f"   成本价: {signal['avg_price']:.2f}")
        print(f"   当前价: {signal['current_price']:.2f}")
        print(f"   盈亏率: {signal['pnl_pct']:+.2f}%")
        print(f"   卖出原因: {', '.join(signal['reasons'])}")
        print()
    
    if dry_run:
        print("⚠️  模拟模式：不执行实际卖出操作\n")
        return 0
    
    # 确认是否执行
    print(f"{'='*80}")
    confirm = input(f"是否执行卖出操作？(yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ 已取消卖出操作\n")
        return 0
    
    # 执行卖出
    print(f"\n{'='*80}")
    print("🚀 开始执行卖出操作...")
    print(f"{'='*80}\n")
    
    engine = get_trading_engine()
    success_count = 0
    fail_count = 0
    
    for signal in sell_signals:
        try:
            print(f"卖出 {signal['symbol']} ({signal['quantity']} 股) @ {signal['current_price']:.2f}...", end=' ')
            
            result = engine.place_order(
                symbol=signal['symbol'],
                side='SELL',
                order_type='LIMIT',
                price=signal['current_price'],
                quantity=signal['quantity'],
                strategy_tag='auto_sell'
            )
            
            print(f"✅ 成功")
            logger.info(f"卖出成功: {signal['symbol']}, 结果: {result}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            logger.error(f"卖出失败: {signal['symbol']}, 错误: {e}")
            fail_count += 1
    
    print(f"\n{'='*80}")
    print(f"执行完成: 成功 {success_count}/{len(sell_signals)}, 失败 {fail_count}/{len(sell_signals)}")
    print(f"{'='*80}\n")
    
    return success_count


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='检查港股持仓的卖出信号并执行卖出操作')
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

    print(f"\n{'='*80}")
    print(f"港股持仓卖出信号检查")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"交易模式: {trading_mode}")
    print(f"{'='*80}")
    
    # 获取持仓
    positions = get_hk_positions(db_manager)
    
    # 显示持仓
    display_positions(positions, db_manager)
    
    if not positions:
        return
    
    # 卖出策略配置
    strategy_config = {
        'stop_loss': {
            'enabled': True,
            'stop_loss_pct': -0.08  # 止损 -8%
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
            'enabled': True,
            'trailing_stop_pct': 0.08  # 从最高价回撤8%
        },
        'technical': {
            'enabled': True,
            'rsi_overbought': 75,  # RSI超买阈值
            'macd_death_cross': True  # MACD死叉
        }
    }
    
    print("📋 卖出策略配置:")
    print(f"  - 止损: {strategy_config['stop_loss']['stop_loss_pct']*100:.0f}%")
    print(f"  - 止盈: {strategy_config['take_profit']['take_profit_pct']*100:.0f}%")
    print(f"  - 移动止损: 从最高价回撤 {strategy_config['trailing_stop']['trailing_stop_pct']*100:.0f}%")
    print(f"  - 技术指标: RSI > {strategy_config['technical']['rsi_overbought']}, MACD死叉")
    print()
    
    # 检查卖出信号
    sell_signals = check_sell_signals(db_manager, strategy_config)
    
    # 执行卖出
    if args.auto:
        # 自动执行模式，不需要确认
        if sell_signals:
            print(f"🤖 自动执行模式")
            engine = get_trading_engine()
            success_count = 0
            
            for signal in sell_signals:
                try:
                    result = engine.place_order(
                        symbol=signal['symbol'],
                        side='SELL',
                        order_type='LIMIT',
                        price=signal['current_price'],
                        quantity=signal['quantity'],
                        strategy_tag='auto_sell'
                    )
                    print(f"✅ 卖出 {signal['symbol']}: {result}")
                    success_count += 1
                except Exception as e:
                    print(f"❌ 卖出 {signal['symbol']} 失败: {e}")
            
            print(f"\n执行完成: 成功 {success_count}/{len(sell_signals)}")
    else:
        execute_sell_orders(sell_signals, db_manager, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

