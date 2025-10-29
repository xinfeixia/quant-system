#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看交易信号
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from database.models import TradingSignal
from utils.config_loader import init_config


def main():
    """主函数"""
    print("\n" + "="*100)
    print("交易信号查询")
    print("="*100 + "\n")
    
    # 初始化配置和数据库
    config_loader = init_config()
    db = DatabaseManager(config_loader.config)
    
    with db.get_session() as session:
        # 查询今天的信号
        today = datetime.now().date()
        today_signals = session.query(TradingSignal).filter(
            TradingSignal.signal_date == today
        ).order_by(TradingSignal.created_at.desc()).all()
        
        print(f"📅 今天的交易信号 ({today}):")
        print("-" * 100)
        
        if today_signals:
            print(f"共 {len(today_signals)} 个信号\n")
            
            # 按类型分组
            buy_signals = [s for s in today_signals if s.signal_type == 'BUY']
            sell_signals = [s for s in today_signals if s.signal_type == 'SELL']
            
            if buy_signals:
                print(f"\n🟢 买入信号 ({len(buy_signals)} 个):")
                print("-" * 100)
                print(f"{'序号':<6} {'股票代码':<12} {'信号强度':<10} {'信号价格':<12} {'来源':<20} {'是否执行':<10} {'创建时间':<20}")
                print("-" * 100)
                
                for idx, signal in enumerate(buy_signals, 1):
                    executed = "✅ 已执行" if signal.is_executed else "⏳ 待执行"
                    print(f"{idx:<6} {signal.symbol:<12} {signal.signal_strength:<10.2f} "
                          f"${signal.signal_price:<11.2f} {signal.source:<20} {executed:<10} "
                          f"{signal.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    if signal.reason:
                        print(f"       原因: {signal.reason}")
                    print()
            
            if sell_signals:
                print(f"\n🔴 卖出信号 ({len(sell_signals)} 个):")
                print("-" * 100)
                print(f"{'序号':<6} {'股票代码':<12} {'信号强度':<10} {'信号价格':<12} {'来源':<20} {'是否执行':<10} {'创建时间':<20}")
                print("-" * 100)
                
                for idx, signal in enumerate(sell_signals, 1):
                    executed = "✅ 已执行" if signal.is_executed else "⏳ 待执行"
                    print(f"{idx:<6} {signal.symbol:<12} {signal.signal_strength:<10.2f} "
                          f"${signal.signal_price:<11.2f} {signal.source:<20} {executed:<10} "
                          f"{signal.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    if signal.reason:
                        print(f"       原因: {signal.reason}")
                    print()
        else:
            print("❌ 今天还没有交易信号\n")
        
        # 查询最近7天的信号统计
        print("\n" + "="*100)
        print("📊 最近7天信号统计:")
        print("-" * 100)
        
        seven_days_ago = today - timedelta(days=7)
        recent_signals = session.query(TradingSignal).filter(
            TradingSignal.signal_date >= seven_days_ago
        ).all()
        
        if recent_signals:
            total = len(recent_signals)
            buy_count = len([s for s in recent_signals if s.signal_type == 'BUY'])
            sell_count = len([s for s in recent_signals if s.signal_type == 'SELL'])
            executed_count = len([s for s in recent_signals if s.is_executed])
            pending_count = total - executed_count
            
            print(f"总信号数: {total}")
            print(f"  - 买入信号: {buy_count}")
            print(f"  - 卖出信号: {sell_count}")
            print(f"  - 已执行: {executed_count}")
            print(f"  - 待执行: {pending_count}")
            
            # 按来源统计
            sources = {}
            for signal in recent_signals:
                source = signal.source or 'unknown'
                sources[source] = sources.get(source, 0) + 1
            
            print(f"\n按来源统计:")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {source}: {count}")
        else:
            print("❌ 最近7天没有交易信号\n")
        
        # 查询待执行的信号
        print("\n" + "="*100)
        print("⏳ 待执行的信号:")
        print("-" * 100)
        
        pending_signals = session.query(TradingSignal).filter(
            TradingSignal.is_executed == False
        ).order_by(TradingSignal.created_at.desc()).all()
        
        if pending_signals:
            print(f"共 {len(pending_signals)} 个待执行信号\n")
            print(f"{'序号':<6} {'类型':<8} {'股票代码':<12} {'信号强度':<10} {'信号价格':<12} {'信号日期':<12} {'创建时间':<20}")
            print("-" * 100)
            
            for idx, signal in enumerate(pending_signals, 1):
                signal_type = "🟢 买入" if signal.signal_type == 'BUY' else "🔴 卖出"
                print(f"{idx:<6} {signal_type:<8} {signal.symbol:<12} {signal.signal_strength:<10.2f} "
                      f"${signal.signal_price:<11.2f} {str(signal.signal_date):<12} "
                      f"{signal.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("✅ 没有待执行的信号\n")
    
    print("="*100 + "\n")


if __name__ == '__main__':
    main()

