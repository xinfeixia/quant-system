#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成A股买卖信号
基于技术指标分析生成交易信号
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo, DailyData, TechnicalIndicator, TradingSignal
from analysis.trading_signals import TradingSignalAnalyzer
from utils.config_loader import init_config
from loguru import logger


def get_stock_data_with_indicators(session, symbol, days=60):
    """
    获取股票数据和技术指标
    
    Args:
        session: 数据库会话
        symbol: 股票代码
        days: 获取天数
        
    Returns:
        list: K线数据列表，包含技术指标
    """
    # 获取最近N天的数据
    daily_data = session.query(DailyData).filter(
        DailyData.symbol == symbol
    ).order_by(DailyData.trade_date.desc()).limit(days).all()
    
    if not daily_data:
        return []
    
    # 反转为时间正序
    daily_data = list(reversed(daily_data))
    
    # 获取技术指标
    indicators_data = session.query(TechnicalIndicator).filter(
        TechnicalIndicator.symbol == symbol
    ).order_by(TechnicalIndicator.trade_date.desc()).limit(days).all()
    
    # 创建指标字典，方便查找
    indicators_dict = {ind.trade_date: ind for ind in indicators_data}
    
    # 合并数据
    kline_data = []
    for daily in daily_data:
        ind = indicators_dict.get(daily.trade_date)
        
        data_point = {
            'date': daily.trade_date,
            'open': daily.open,
            'high': daily.high,
            'low': daily.low,
            'close': daily.close,
            'volume': daily.volume,
        }
        
        # 添加技术指标
        if ind:
            data_point.update({
                'ma5': ind.ma5,
                'ma10': ind.ma10,
                'ma20': ind.ma20,
                'ma60': ind.ma60,
                'ema12': ind.ema12,
                'ema26': ind.ema26,
                'macd': ind.macd,
                'signal': ind.macd_signal,
                'macd_hist': ind.macd_hist,
                'rsi': ind.rsi,
                'kdj_k': ind.kdj_k,
                'kdj_d': ind.kdj_d,
                'kdj_j': ind.kdj_j,
                'boll_upper': ind.boll_upper,
                'boll_middle': ind.boll_middle,
                'boll_lower': ind.boll_lower,
                'atr': ind.atr,
                'obv': ind.obv,
            })
        
        kline_data.append(data_point)
    
    return kline_data


def generate_signals_for_all_stocks(db_manager, market='CN', min_strength=40, save_to_db=False):
    """
    为所有股票生成买卖信号
    
    Args:
        db_manager: 数据库管理器
        market: 市场代码 (CN/HK/US)
        min_strength: 最小信号强度
        save_to_db: 是否保存到数据库
        
    Returns:
        dict: 买入和卖出信号列表
    """
    buy_signals = []
    sell_signals = []
    
    with db_manager.get_session() as session:
        # 获取所有股票
        stocks = session.query(StockInfo).filter_by(market=market).all()
        total = len(stocks)
        
        logger.info(f"开始分析 {total} 只{market}市场股票...")
        
        for idx, stock in enumerate(stocks, 1):
            if idx % 100 == 0:
                logger.info(f"进度: [{idx}/{total}] {stock.symbol} {stock.name}")
            
            try:
                # 获取数据
                kline_data = get_stock_data_with_indicators(session, stock.symbol, days=60)
                
                if len(kline_data) < 30:
                    continue
                
                # 创建分析器
                analyzer = TradingSignalAnalyzer(kline_data)
                
                # 生成买入信号
                buy_signal = analyzer.generate_buy_signals()
                if buy_signal['strength'] >= min_strength:
                    buy_signals.append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'signal': buy_signal['signal'],
                        'strength': buy_signal['strength'],
                        'reasons': buy_signal['reasons'],
                        'price': buy_signal['current_price']
                    })
                
                # 生成卖出信号
                sell_signal = analyzer.generate_sell_signals()
                if sell_signal['strength'] >= min_strength:
                    sell_signals.append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'signal': sell_signal['signal'],
                        'strength': sell_signal['strength'],
                        'reasons': sell_signal['reasons'],
                        'price': sell_signal['current_price']
                    })
                    
            except Exception as e:
                logger.error(f"分析 {stock.symbol} 失败: {e}")
                continue
        
        # 按强度排序
        buy_signals.sort(key=lambda x: x['strength'], reverse=True)
        sell_signals.sort(key=lambda x: x['strength'], reverse=True)
        
        # 保存到数据库
        if save_to_db:
            save_signals_to_db(session, buy_signals, sell_signals)
    
    return {
        'buy_signals': buy_signals,
        'sell_signals': sell_signals
    }


def save_signals_to_db(session, buy_signals, sell_signals):
    """
    将信号保存到数据库
    
    Args:
        session: 数据库会话
        buy_signals: 买入信号列表
        sell_signals: 卖出信号列表
    """
    today = date.today()
    saved_count = 0
    
    # 保存买入信号
    for sig in buy_signals:
        # 检查是否已存在
        existing = session.query(TradingSignal).filter(
            TradingSignal.symbol == sig['symbol'],
            TradingSignal.signal_date == today,
            TradingSignal.signal_type == 'BUY',
            TradingSignal.is_executed == False
        ).first()
        
        if not existing:
            signal = TradingSignal(
                symbol=sig['symbol'],
                signal_date=today,
                signal_type='BUY',
                signal_strength=sig['strength'] / 100.0,  # 转换为0-1
                signal_price=sig['price'],
                source='trading_signal_analyzer',
                reason=', '.join(sig['reasons'])
            )
            session.add(signal)
            saved_count += 1
    
    # 保存卖出信号
    for sig in sell_signals:
        # 检查是否已存在
        existing = session.query(TradingSignal).filter(
            TradingSignal.symbol == sig['symbol'],
            TradingSignal.signal_date == today,
            TradingSignal.signal_type == 'SELL',
            TradingSignal.is_executed == False
        ).first()
        
        if not existing:
            signal = TradingSignal(
                symbol=sig['symbol'],
                signal_date=today,
                signal_type='SELL',
                signal_strength=sig['strength'] / 100.0,  # 转换为0-1
                signal_price=sig['price'],
                source='trading_signal_analyzer',
                reason=', '.join(sig['reasons'])
            )
            session.add(signal)
            saved_count += 1
    
    session.commit()
    logger.info(f"已保存 {saved_count} 个信号到数据库")


def print_signals_report(signals_data):
    """
    打印信号报告
    
    Args:
        signals_data: 信号数据字典
    """
    buy_signals = signals_data['buy_signals']
    sell_signals = signals_data['sell_signals']
    
    print(f"\n{'='*120}")
    print(f"📊 A股交易信号分析报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*120}\n")
    
    # 买入信号
    if buy_signals:
        print(f"{'='*120}")
        print(f"🟢 买入信号 ({len(buy_signals)} 只)")
        print(f"{'='*120}")
        print(f"{'排名':<6} {'代码':<12} {'名称':<20} {'信号':<15} {'强度':<8} {'当前价':<10} {'原因':<40}")
        print(f"{'-'*120}")
        
        for idx, sig in enumerate(buy_signals[:50], 1):  # 只显示前50个
            print(f"{idx:<6} {sig['symbol']:<12} {sig['name']:<20} {sig['signal']:<15} "
                  f"{sig['strength']:<8} {sig['price']:<10.2f} {', '.join(sig['reasons']):<40}")
        
        print(f"{'='*120}\n")
    else:
        print("📭 没有符合条件的买入信号\n")
    
    # 卖出信号
    if sell_signals:
        print(f"{'='*120}")
        print(f"🔴 卖出信号 ({len(sell_signals)} 只)")
        print(f"{'='*120}")
        print(f"{'排名':<6} {'代码':<12} {'名称':<20} {'信号':<15} {'强度':<8} {'当前价':<10} {'原因':<40}")
        print(f"{'-'*120}")
        
        for idx, sig in enumerate(sell_signals[:50], 1):  # 只显示前50个
            print(f"{idx:<6} {sig['symbol']:<12} {sig['name']:<20} {sig['signal']:<15} "
                  f"{sig['strength']:<8} {sig['price']:<10.2f} {', '.join(sig['reasons']):<40}")
        
        print(f"{'='*120}\n")
    else:
        print("📭 没有符合条件的卖出信号\n")
    
    # 统计信息
    print(f"{'='*120}")
    print(f"📈 统计信息")
    print(f"{'='*120}")
    print(f"总买入信号: {len(buy_signals)} 只")
    print(f"  - 强烈买入 (STRONG_BUY): {sum(1 for s in buy_signals if s['signal'] == 'STRONG_BUY')} 只")
    print(f"  - 买入 (BUY): {sum(1 for s in buy_signals if s['signal'] == 'BUY')} 只")
    print(f"  - 弱买入 (WEAK_BUY): {sum(1 for s in buy_signals if s['signal'] == 'WEAK_BUY')} 只")
    print(f"\n总卖出信号: {len(sell_signals)} 只")
    print(f"  - 强烈卖出 (STRONG_SELL): {sum(1 for s in sell_signals if s['signal'] == 'STRONG_SELL')} 只")
    print(f"  - 卖出 (SELL): {sum(1 for s in sell_signals if s['signal'] == 'SELL')} 只")
    print(f"  - 弱卖出 (WEAK_SELL): {sum(1 for s in sell_signals if s['signal'] == 'WEAK_SELL')} 只")
    print(f"{'='*120}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='批量生成A股买卖信号')
    parser.add_argument('--market', default='CN', choices=['CN', 'HK', 'US'], help='市场代码')
    parser.add_argument('--min-strength', type=int, default=40, help='最小信号强度 (0-100)')
    parser.add_argument('--save-db', action='store_true', help='保存信号到数据库')
    args = parser.parse_args()

    # 初始化
    config_dir = str(project_root / 'config')
    config_loader = init_config(config_dir=config_dir)
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    logger.info(f"开始生成{args.market}市场交易信号...")
    logger.info(f"最小信号强度: {args.min_strength}")
    logger.info(f"保存到数据库: {args.save_db}")
    
    # 生成信号
    signals_data = generate_signals_for_all_stocks(
        db_manager, 
        market=args.market,
        min_strength=args.min_strength,
        save_to_db=args.save_db
    )
    
    # 打印报告
    print_signals_report(signals_data)
    
    logger.info("交易信号生成完成！")


if __name__ == '__main__':
    main()

