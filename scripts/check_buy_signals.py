#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看买入信号和选股结果
"""

import sys
from pathlib import Path
from datetime import datetime, date

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import TradingSignal, StockSelection, StockInfo, DailyData, Position
from utils.config_loader import init_config
from sqlalchemy import desc


def check_trading_signals(db_manager):
    """检查未执行的买入信号"""
    with db_manager.get_session() as session:
        # 查询未执行的买入信号
        signals = session.query(TradingSignal, StockInfo).join(
            StockInfo, TradingSignal.symbol == StockInfo.symbol
        ).filter(
            TradingSignal.signal_type == 'BUY',
            TradingSignal.is_executed == False
        ).order_by(desc(TradingSignal.signal_date), desc(TradingSignal.signal_strength)).all()
        
        if not signals:
            print("\n📭 没有未执行的买入信号")
            return []
        
        print(f"\n{'='*100}")
        print(f"🔔 未执行的买入信号 ({len(signals)} 个)")
        print(f"{'='*100}")
        print(f"{'日期':<12} {'代码':<12} {'名称':<20} {'信号强度':<10} {'建议价格':<12} {'来源':<15} {'原因':<30}")
        print(f"{'-'*100}")
        
        signal_list = []
        for sig, stock in signals:
            signal_list.append({
                'date': sig.signal_date,
                'symbol': sig.symbol,
                'name': stock.name,
                'strength': sig.signal_strength,
                'price': sig.signal_price,
                'source': sig.source,
                'reason': sig.reason
            })
            
            print(f"{sig.signal_date.strftime('%Y-%m-%d'):<12} {sig.symbol:<12} {stock.name:<20} "
                  f"{sig.signal_strength:<10.2f} {sig.signal_price or 0:<12.2f} {sig.source or 'N/A':<15} "
                  f"{(sig.reason or 'N/A')[:30]:<30}")
        
        print(f"{'='*100}\n")
        return signal_list


def check_latest_selections(db_manager, market='HK', top_n=20):
    """检查最新的选股结果"""
    with db_manager.get_session() as session:
        # 获取最新选股日期
        latest_date = session.query(StockSelection.selection_date).order_by(
            desc(StockSelection.selection_date)
        ).first()
        
        if not latest_date:
            print(f"\n📭 没有{market}市场的选股结果")
            return []
        
        latest_date = latest_date[0]
        
        # 查询最新选股结果
        selections = session.query(StockSelection, StockInfo, DailyData).join(
            StockInfo, StockSelection.symbol == StockInfo.symbol
        ).outerjoin(
            DailyData, 
            (StockSelection.symbol == DailyData.symbol) & 
            (StockSelection.selection_date == DailyData.trade_date)
        ).filter(
            StockInfo.market == market,
            StockSelection.selection_date == latest_date
        ).order_by(desc(StockSelection.total_score)).limit(top_n).all()
        
        if not selections:
            print(f"\n📭 {latest_date} 没有{market}市场的选股结果")
            return []
        
        print(f"\n{'='*120}")
        print(f"📈 {market}市场最新选股结果 (日期: {latest_date})")
        print(f"{'='*120}")
        print(f"{'排名':<6} {'代码':<12} {'名称':<20} {'总分':<8} {'技术':<6} {'成交量':<8} {'趋势':<6} "
              f"{'形态':<6} {'最新价':<10} {'原因':<30}")
        print(f"{'-'*120}")
        
        selection_list = []
        for sel, stock, daily in selections:
            # 检查是否已持有
            pos = session.query(Position).filter_by(symbol=sel.symbol).first()
            has_position = pos and pos.quantity > 0
            
            selection_list.append({
                'rank': sel.rank,
                'symbol': sel.symbol,
                'name': stock.name,
                'total_score': sel.total_score,
                'technical_score': sel.technical_score,
                'volume_score': sel.volume_score,
                'trend_score': sel.trend_score,
                'pattern_score': sel.pattern_score,
                'latest_price': sel.latest_price or sel.current_price,
                'reason': sel.reason,
                'has_position': has_position
            })
            
            position_mark = "✓" if has_position else " "
            print(f"{sel.rank:<6} {sel.symbol:<12} {stock.name:<20} {sel.total_score:<8.1f} "
                  f"{sel.technical_score or 0:<6.1f} {sel.volume_score or 0:<8.1f} "
                  f"{sel.trend_score or 0:<6.1f} {sel.pattern_score or 0:<6.1f} "
                  f"{sel.latest_price or sel.current_price or 0:<10.2f} "
                  f"{(sel.reason or 'N/A')[:30]:<30} {position_mark}")
        
        print(f"{'='*120}")
        print(f"说明: ✓ = 已持有")
        print(f"{'='*120}\n")
        
        return selection_list


def check_all_positions(db_manager):
    """检查所有持仓"""
    with db_manager.get_session() as session:
        positions = session.query(Position, StockInfo).join(
            StockInfo, Position.symbol == StockInfo.symbol
        ).filter(Position.quantity > 0).all()
        
        if not positions:
            print("\n📭 当前没有任何持仓\n")
            return []
        
        print(f"\n{'='*100}")
        print(f"💼 当前所有持仓 ({len(positions)} 只)")
        print(f"{'='*100}")
        print(f"{'代码':<12} {'名称':<20} {'市场':<8} {'数量':<10} {'成本价':<12} {'最新价':<12} {'盈亏':<12} {'盈亏率':<10}")
        print(f"{'-'*100}")
        
        total_cost = 0
        total_value = 0
        position_list = []
        
        for pos, stock in positions:
            # 获取最新价格
            latest_data = session.query(DailyData).filter(
                DailyData.symbol == pos.symbol
            ).order_by(DailyData.trade_date.desc()).first()
            
            if latest_data:
                current_price = latest_data.close
                cost = pos.avg_price * pos.quantity
                value = current_price * pos.quantity
                pnl = value - cost
                pnl_pct = (pnl / cost * 100) if cost > 0 else 0
                
                total_cost += cost
                total_value += value
                
                position_list.append({
                    'symbol': pos.symbol,
                    'name': stock.name,
                    'market': pos.market,
                    'quantity': pos.quantity,
                    'avg_price': pos.avg_price,
                    'current_price': current_price,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
                
                pnl_str = f"{pnl:+.2f}" if pnl != 0 else "0.00"
                pnl_pct_str = f"{pnl_pct:+.2f}%" if pnl_pct != 0 else "0.00%"
                
                print(f"{pos.symbol:<12} {stock.name:<20} {pos.market:<8} {pos.quantity:<10} "
                      f"{pos.avg_price:<12.2f} {current_price:<12.2f} {pnl_str:<12} {pnl_pct_str:<10}")
            else:
                print(f"{pos.symbol:<12} {stock.name:<20} {pos.market:<8} {pos.quantity:<10} "
                      f"{pos.avg_price:<12.2f} {'N/A':<12} {'N/A':<12} {'N/A':<10}")
        
        if total_cost > 0:
            total_pnl = total_value - total_cost
            total_pnl_pct = (total_pnl / total_cost * 100)
            print(f"{'-'*100}")
            print(f"{'总计':<12} {'':<20} {'':<8} {'':<10} {total_cost:<12.2f} {total_value:<12.2f} "
                  f"{total_pnl:+.2f}{'':>6} {total_pnl_pct:+.2f}%")
        
        print(f"{'='*100}\n")
        return position_list


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='查看买入信号和选股结果')
    parser.add_argument('--market', default='HK', choices=['HK', 'CN', 'US'], help='市场')
    parser.add_argument('--top', type=int, default=20, help='显示前N个选股结果')
    args = parser.parse_args()
    
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    print(f"\n{'='*100}")
    print(f"买入信号和选股结果查询")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}")
    
    # 1. 检查所有持仓
    check_all_positions(db_manager)
    
    # 2. 检查未执行的买入信号
    check_trading_signals(db_manager)
    
    # 3. 检查最新选股结果
    check_latest_selections(db_manager, market=args.market, top_n=args.top)


if __name__ == '__main__':
    main()

