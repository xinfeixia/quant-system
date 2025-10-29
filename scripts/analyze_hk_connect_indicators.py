#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股通标的技术指标分析
分析港股通标的股票的技术指标状态，找出优质标的
"""

import sys
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo, DailyData, TechnicalIndicator
from utils.config_loader import init_config
from loguru import logger


def analyze_hk_connect_indicators(min_price=1.0, max_price=1000.0, top_n=50):
    """
    分析港股通标的的技术指标
    
    Args:
        min_price: 最低价格筛选
        max_price: 最高价格筛选
        top_n: 显示前N只股票
    """
    # 初始化
    config_dir = str(project_root / 'config')
    config_loader = init_config(config_dir=config_dir)
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    print("\n" + "="*120)
    print("📊 港股通标的技术指标分析")
    print("="*120 + "\n")
    
    with db_manager.get_session() as session:
        # 获取所有港股通标的
        hk_connect_stocks = session.query(StockInfo).filter(
            StockInfo.market == 'HK',
            StockInfo.is_active == True,
            StockInfo.is_hk_connect == True
        ).all()
        
        total_count = len(hk_connect_stocks)
        print(f"📈 港股通标的总数: {total_count} 只\n")
        
        if total_count == 0:
            print("⚠️ 数据库中没有港股通标的数据")
            print("💡 请先运行: python longport-quant-system/scripts/update_hk_connect_flag.py")
            return
        
        # 分析每只股票的技术指标
        analysis_results = []
        
        print("正在分析技术指标...\n")
        
        for stock in hk_connect_stocks:
            try:
                # 获取最新交易数据
                latest_daily = session.query(DailyData).filter(
                    DailyData.symbol == stock.symbol
                ).order_by(DailyData.trade_date.desc()).first()
                
                if not latest_daily:
                    continue
                
                # 价格筛选
                if latest_daily.close < min_price or latest_daily.close > max_price:
                    continue
                
                # 获取最新技术指标
                latest_indicator = session.query(TechnicalIndicator).filter(
                    TechnicalIndicator.symbol == stock.symbol
                ).order_by(TechnicalIndicator.trade_date.desc()).first()
                
                if not latest_indicator:
                    continue
                
                # 计算综合评分
                score = 0
                signals = []
                
                # RSI分析 (30分)
                if latest_indicator.rsi:
                    if latest_indicator.rsi < 30:
                        score += 30
                        signals.append("RSI超卖")
                    elif latest_indicator.rsi < 40:
                        score += 20
                        signals.append("RSI偏低")
                    elif latest_indicator.rsi > 70:
                        score -= 20
                        signals.append("RSI超买")
                
                # MACD分析 (25分)
                if latest_indicator.macd and latest_indicator.macd_signal:
                    if latest_indicator.macd > latest_indicator.macd_signal:
                        # 获取前一天的MACD
                        prev_indicator = session.query(TechnicalIndicator).filter(
                            TechnicalIndicator.symbol == stock.symbol,
                            TechnicalIndicator.trade_date < latest_indicator.trade_date
                        ).order_by(TechnicalIndicator.trade_date.desc()).first()
                        
                        if prev_indicator and prev_indicator.macd and prev_indicator.macd_signal:
                            if prev_indicator.macd <= prev_indicator.macd_signal:
                                score += 25
                                signals.append("MACD金叉")
                            else:
                                score += 15
                                signals.append("MACD多头")
                
                # KDJ分析 (20分)
                if latest_indicator.kdj_k and latest_indicator.kdj_d:
                    if latest_indicator.kdj_k < 20:
                        score += 20
                        signals.append("KDJ超卖")
                    elif latest_indicator.kdj_k > latest_indicator.kdj_d:
                        score += 10
                        signals.append("KDJ金叉")
                
                # 均线分析 (25分)
                if all([latest_indicator.ma5, latest_indicator.ma10, latest_indicator.ma20]):
                    if (latest_indicator.ma5 > latest_indicator.ma10 > latest_indicator.ma20):
                        score += 25
                        signals.append("均线多头")
                    elif latest_daily.close > latest_indicator.ma5:
                        score += 15
                        signals.append("价格>MA5")
                
                # 布林带分析
                if all([latest_indicator.boll_upper, latest_indicator.boll_lower]):
                    boll_position = (latest_daily.close - latest_indicator.boll_lower) / \
                                  (latest_indicator.boll_upper - latest_indicator.boll_lower)
                    if boll_position < 0.2:
                        signals.append("接近下轨")
                    elif boll_position > 0.8:
                        signals.append("接近上轨")
                
                analysis_results.append({
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'price': latest_daily.close,
                    'change_pct': latest_daily.change_percent if hasattr(latest_daily, 'change_percent') else 0,
                    'volume': latest_daily.volume,
                    'rsi': latest_indicator.rsi,
                    'macd': latest_indicator.macd,
                    'kdj_k': latest_indicator.kdj_k,
                    'ma5': latest_indicator.ma5,
                    'ma10': latest_indicator.ma10,
                    'ma20': latest_indicator.ma20,
                    'score': score,
                    'signals': ', '.join(signals) if signals else '-',
                    'trade_date': latest_daily.trade_date
                })
                
            except Exception as e:
                logger.error(f"分析 {stock.symbol} 失败: {e}")
                continue
        
        # 按评分排序
        analysis_results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"✅ 成功分析 {len(analysis_results)} 只港股通标的\n")
        
        # 显示高分股票
        print("="*120)
        print(f"🌟 技术指标优质港股通标的 (Top {min(top_n, len(analysis_results))})")
        print("="*120)
        print(f"{'排名':<6} {'代码':<12} {'名称':<20} {'价格':<10} {'涨跌%':<8} {'RSI':<8} {'MACD':<10} {'KDJ_K':<8} {'评分':<6} {'信号'}")
        print("-"*120)
        
        for i, result in enumerate(analysis_results[:top_n], 1):
            rsi_str = f"{result['rsi']:.1f}" if result['rsi'] else "N/A"
            macd_str = f"{result['macd']:.3f}" if result['macd'] else "N/A"
            kdj_str = f"{result['kdj_k']:.1f}" if result['kdj_k'] else "N/A"
            change_str = f"{result['change_pct']:+.2f}%" if result['change_pct'] else "N/A"
            
            print(f"{i:<6} {result['symbol']:<12} {result['name']:<20} "
                  f"HK${result['price']:<9.2f} {change_str:<8} {rsi_str:<8} {macd_str:<10} "
                  f"{kdj_str:<8} {result['score']:<6} {result['signals']}")
        
        print("="*120 + "\n")
        
        # 统计分析
        print("="*120)
        print("📊 技术指标统计")
        print("="*120)
        
        # RSI分布
        rsi_oversold = sum(1 for r in analysis_results if r['rsi'] and r['rsi'] < 30)
        rsi_low = sum(1 for r in analysis_results if r['rsi'] and 30 <= r['rsi'] < 40)
        rsi_normal = sum(1 for r in analysis_results if r['rsi'] and 40 <= r['rsi'] <= 60)
        rsi_high = sum(1 for r in analysis_results if r['rsi'] and 60 < r['rsi'] <= 70)
        rsi_overbought = sum(1 for r in analysis_results if r['rsi'] and r['rsi'] > 70)
        
        print(f"\nRSI分布:")
        print(f"  超卖 (RSI<30):     {rsi_oversold:4} 只 ({rsi_oversold/len(analysis_results)*100:.1f}%)")
        print(f"  偏低 (30≤RSI<40):  {rsi_low:4} 只 ({rsi_low/len(analysis_results)*100:.1f}%)")
        print(f"  正常 (40≤RSI≤60):  {rsi_normal:4} 只 ({rsi_normal/len(analysis_results)*100:.1f}%)")
        print(f"  偏高 (60<RSI≤70):  {rsi_high:4} 只 ({rsi_high/len(analysis_results)*100:.1f}%)")
        print(f"  超买 (RSI>70):     {rsi_overbought:4} 只 ({rsi_overbought/len(analysis_results)*100:.1f}%)")
        
        # 评分分布
        high_score = sum(1 for r in analysis_results if r['score'] >= 60)
        medium_score = sum(1 for r in analysis_results if 30 <= r['score'] < 60)
        low_score = sum(1 for r in analysis_results if r['score'] < 30)
        
        print(f"\n综合评分分布:")
        print(f"  高分 (≥60分):      {high_score:4} 只 ({high_score/len(analysis_results)*100:.1f}%)")
        print(f"  中等 (30-59分):    {medium_score:4} 只 ({medium_score/len(analysis_results)*100:.1f}%)")
        print(f"  低分 (<30分):      {low_score:4} 只 ({low_score/len(analysis_results)*100:.1f}%)")
        
        print("\n" + "="*120 + "\n")
        
        # 显示低分股票（可能的卖出信号）
        print("="*120)
        print(f"⚠️ 技术指标较弱的港股通标的 (评分<0, 可能的卖出信号)")
        print("="*120)
        
        weak_stocks = [r for r in analysis_results if r['score'] < 0]
        if weak_stocks:
            print(f"{'排名':<6} {'代码':<12} {'名称':<20} {'价格':<10} {'涨跌%':<8} {'RSI':<8} {'评分':<6} {'信号'}")
            print("-"*120)
            
            for i, result in enumerate(weak_stocks[:20], 1):
                rsi_str = f"{result['rsi']:.1f}" if result['rsi'] else "N/A"
                change_str = f"{result['change_pct']:+.2f}%" if result['change_pct'] else "N/A"
                
                print(f"{i:<6} {result['symbol']:<12} {result['name']:<20} "
                      f"HK${result['price']:<9.2f} {change_str:<8} {rsi_str:<8} "
                      f"{result['score']:<6} {result['signals']}")
        else:
            print("✅ 没有评分为负的股票")
        
        print("="*120 + "\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='港股通标的技术指标分析')
    parser.add_argument('--min-price', type=float, default=1.0, help='最低价格筛选')
    parser.add_argument('--max-price', type=float, default=1000.0, help='最高价格筛选')
    parser.add_argument('--top', type=int, default=50, help='显示前N只股票')
    args = parser.parse_args()
    
    try:
        analyze_hk_connect_indicators(
            min_price=args.min_price,
            max_price=args.max_price,
            top_n=args.top
        )
    except Exception as e:
        logger.error(f"分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

