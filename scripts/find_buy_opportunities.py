#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寻找建仓机会 - 结合选股评分和买入信号
"""

import sys
from pathlib import Path
from datetime import datetime, date

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockSelection, DailyData, TechnicalIndicator, StockInfo, Position
from utils.config_loader import init_config
from analysis.trading_signals import TradingSignalAnalyzer
from loguru import logger


def get_stock_data_with_indicators(session, symbol, days=60):
    """获取股票数据和技术指标"""
    # 获取日线数据
    daily_data = session.query(DailyData).filter(
        DailyData.symbol == symbol
    ).order_by(DailyData.trade_date.desc()).limit(days).all()
    
    if not daily_data:
        return None
    
    # 获取技术指标
    indicators = session.query(TechnicalIndicator).filter(
        TechnicalIndicator.symbol == symbol
    ).order_by(TechnicalIndicator.trade_date.desc()).limit(days).all()
    
    if not indicators:
        return None
    
    # 合并数据
    kline_data = []
    for data in reversed(daily_data):
        indicator = next((ind for ind in indicators if ind.trade_date == data.trade_date), None)
        if indicator:
            kline_data.append({
                'date': data.trade_date,
                'open': data.open,
                'high': data.high,
                'low': data.low,
                'close': data.close,
                'volume': data.volume,
                'ma5': indicator.ma5,
                'ma10': indicator.ma10,
                'ma20': indicator.ma20,
                'ma60': indicator.ma60,
                'macd': indicator.macd,
                'signal': indicator.macd_signal,  # TradingSignalAnalyzer expects 'signal' not 'macd_signal'
                'macd_hist': indicator.macd_hist,
                'rsi': indicator.rsi,
                'kdj_k': indicator.kdj_k,
                'kdj_d': indicator.kdj_d,
                'kdj_j': indicator.kdj_j,
                'boll_upper': indicator.boll_upper,
                'boll_middle': indicator.boll_middle,
                'boll_lower': indicator.boll_lower,
            })
    
    return kline_data


def check_if_already_holding(session, symbol):
    """检查是否已持仓"""
    position = session.query(Position).filter(
        Position.symbol == symbol,
        Position.quantity > 0
    ).first()
    return position is not None


def find_buy_opportunities(market='HK', min_score=70, min_signal_strength=40, top_n=20, hk_connect_only=False):
    """
    寻找建仓机会

    Args:
        market: 市场代码
        min_score: 最低选股分数
        min_signal_strength: 最低信号强度
        top_n: 返回前N个机会
        hk_connect_only: 是否只选港股通标的（仅对HK市场有效）
    """
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()

    opportunities = []

    with db_manager.get_session() as session:
        # 获取高分选股结果
        query = session.query(StockSelection).filter(
            StockSelection.market == market,
            StockSelection.total_score >= min_score,
            StockSelection.selection_date == date.today()
        )

        # 如果是港股且只选港股通标的
        if market == 'HK' and hk_connect_only:
            query = query.join(StockInfo, StockSelection.symbol == StockInfo.symbol).filter(
                StockInfo.is_hk_connect == True
            )

        selections = query.order_by(StockSelection.total_score.desc()).limit(100).all()
        
        logger.info(f"找到 {len(selections)} 只高分股票 (>={min_score}分)")
        
        for selection in selections:
            symbol = selection.symbol
            
            # 检查是否已持仓
            if check_if_already_holding(session, symbol):
                logger.debug(f"{symbol} 已持仓，跳过")
                continue
            
            # 获取数据和指标
            kline_data = get_stock_data_with_indicators(session, symbol)
            if not kline_data:
                logger.debug(f"{symbol} 无数据，跳过")
                continue
            
            # 分析买入信号
            analyzer = TradingSignalAnalyzer(kline_data)
            buy_signal = analyzer.generate_buy_signals()
            
            if buy_signal['signal'] == 'HOLD':
                continue
            
            # 计算信号强度
            signal_strength = buy_signal['strength']
            
            if signal_strength < min_signal_strength:
                continue
            
            # 获取最新价格
            latest_price = kline_data[-1]['close']
            
            opportunities.append({
                'symbol': symbol,
                'name': selection.name,
                'total_score': selection.total_score,
                'technical_score': selection.technical_score,
                'volume_score': selection.volume_score,
                'trend_score': selection.trend_score,
                'pattern_score': selection.pattern_score,
                'latest_price': latest_price,
                'signal': buy_signal['signal'],
                'signal_strength': signal_strength,
                'reasons': buy_signal['reasons'],
                'rsi': kline_data[-1].get('rsi'),
                'macd': kline_data[-1].get('macd'),
                'kdj_k': kline_data[-1].get('kdj_k'),
            })
        
        # 按综合评分排序（选股分数 + 信号强度）
        opportunities.sort(key=lambda x: (x['total_score'] + x['signal_strength'] * 0.5), reverse=True)
        
        return opportunities[:top_n]


def display_opportunities(opportunities):
    """显示建仓机会"""
    if not opportunities:
        print("\n❌ 未找到符合条件的建仓机会")
        return
    
    print(f"\n{'='*120}")
    print(f"🎯 建仓机会分析 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*120}\n")
    
    for i, opp in enumerate(opportunities, 1):
        symbol = opp['symbol']
        name = opp['name']
        total_score = opp['total_score']
        latest_price = opp['latest_price']
        signal = opp['signal']
        signal_strength = opp['signal_strength']
        reasons = opp['reasons']
        
        # 信号标识
        if signal == 'STRONG_BUY':
            signal_icon = '🟢🟢'
        elif signal == 'BUY':
            signal_icon = '🟢'
        else:
            signal_icon = '🟡'
        
        print(f"{i}. {symbol} - {name}")
        print(f"   {'='*116}")
        print(f"   综合评分: {total_score}分 (技术:{opp['technical_score']} | 量价:{opp['volume_score']} | 趋势:{opp['trend_score']} | 形态:{opp['pattern_score']})")
        print(f"   最新价格: ¥{latest_price:.2f}")
        print(f"   买入信号: {signal_icon} {signal} (强度: {signal_strength})")
        print(f"   买入理由: {', '.join(reasons)}")
        
        # 显示关键技术指标
        ind_str = []
        if opp['rsi']:
            ind_str.append(f"RSI:{opp['rsi']:.1f}")
        if opp['macd']:
            ind_str.append(f"MACD:{opp['macd']:.2f}")
        if opp['kdj_k']:
            ind_str.append(f"KDJ_K:{opp['kdj_k']:.1f}")
        
        if ind_str:
            print(f"   技术指标: {' | '.join(ind_str)}")
        
        print()
    
    print(f"{'='*120}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='寻找建仓机会')
    parser.add_argument('--market', type=str, default='HK', choices=['HK', 'CN', 'US'], help='市场')
    parser.add_argument('--min-score', type=int, default=70, help='最低选股分数')
    parser.add_argument('--min-signal', type=int, default=40, help='最低信号强度')
    parser.add_argument('--top', type=int, default=20, help='显示前N个机会')
    parser.add_argument('--hk-connect-only', action='store_true', help='只选港股通标的（仅对HK市场有效）')
    args = parser.parse_args()

    logger.info(f"开始寻找{args.market}市场建仓机会...")
    logger.info(f"筛选条件: 选股分数>={args.min_score}, 信号强度>={args.min_signal}")
    if args.market == 'HK' and args.hk_connect_only:
        logger.info("只选择港股通标的")

    opportunities = find_buy_opportunities(
        market=args.market,
        min_score=args.min_score,
        min_signal_strength=args.min_signal,
        top_n=args.top,
        hk_connect_only=args.hk_connect_only
    )

    display_opportunities(opportunities)

    logger.info(f"找到 {len(opportunities)} 个建仓机会")


if __name__ == '__main__':
    main()

