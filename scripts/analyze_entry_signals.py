#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析建仓信号
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from database.models import StockSelection, TechnicalIndicator, DailyData
from datetime import datetime, timedelta
from loguru import logger
from utils.config_loader import init_config


def analyze_entry_signals(min_score=75, market='HK'):
    """
    分析建仓信号

    Args:
        min_score: 最低评分
        market: 市场（HK/CN）
    """
    config = init_config()
    db = DatabaseManager(config)
    
    with db.get_session() as session:
        # 获取最新的选股结果
        latest_date = session.query(StockSelection.selection_date).filter(
            StockSelection.market == market
        ).order_by(StockSelection.selection_date.desc()).first()
        
        if not latest_date:
            logger.error(f"没有找到{market}市场的选股结果")
            return
        
        latest_date = latest_date[0]
        logger.info(f"分析日期: {latest_date}")
        
        # 获取高分股票
        selections = session.query(StockSelection).filter(
            StockSelection.market == market,
            StockSelection.selection_date == latest_date,
            StockSelection.total_score >= min_score
        ).order_by(StockSelection.total_score.desc()).all()
        
        logger.info(f"找到 {len(selections)} 只评分≥{min_score}的股票")
        
        # 分析每只股票
        buy_signals = []
        
        for sel in selections:
            symbol = sel.symbol
            
            # 获取最新技术指标
            indicator = session.query(TechnicalIndicator).filter(
                TechnicalIndicator.symbol == symbol
            ).order_by(TechnicalIndicator.trade_date.desc()).first()
            
            if not indicator:
                continue
            
            # 获取最新价格
            daily = session.query(DailyData).filter(
                DailyData.symbol == symbol
            ).order_by(DailyData.trade_date.desc()).first()
            
            if not daily:
                continue
            
            # 分析建仓信号
            signals = []
            score = 0
            
            # 1. MACD金叉且DIF>0
            if indicator.macd and indicator.macd_signal and indicator.macd_hist:
                if indicator.macd > indicator.macd_signal and indicator.macd > 0:
                    signals.append("✅ MACD金叉向上")
                    score += 3
                elif indicator.macd > indicator.macd_signal:
                    signals.append("⚠️ MACD金叉但DIF<0")
                    score += 1
            
            # 2. RSI在合理区间
            if indicator.rsi:
                if 40 <= indicator.rsi <= 70:
                    signals.append(f"✅ RSI={indicator.rsi:.1f} (健康)")
                    score += 3
                elif 30 <= indicator.rsi < 40:
                    signals.append(f"⚠️ RSI={indicator.rsi:.1f} (偏低)")
                    score += 2
                elif indicator.rsi > 70:
                    signals.append(f"❌ RSI={indicator.rsi:.1f} (超买)")
                    score -= 2
            
            # 3. 价格在均线之上
            price = daily.close
            above_ma = []
            if indicator.ma5 and price > indicator.ma5:
                above_ma.append("MA5")
                score += 1
            if indicator.ma10 and price > indicator.ma10:
                above_ma.append("MA10")
                score += 1
            if indicator.ma20 and price > indicator.ma20:
                above_ma.append("MA20")
                score += 1
            
            if above_ma:
                signals.append(f"✅ 价格在{','.join(above_ma)}之上")
            
            # 4. KDJ金叉
            if indicator.kdj_k and indicator.kdj_d:
                if indicator.kdj_k > indicator.kdj_d and indicator.kdj_k < 80:
                    signals.append(f"✅ KDJ金叉 (K={indicator.kdj_k:.1f})")
                    score += 2
                elif indicator.kdj_k > 80:
                    signals.append(f"❌ KDJ超买 (K={indicator.kdj_k:.1f})")
                    score -= 1
            
            # 5. 布林带位置
            if indicator.boll_upper and indicator.boll_lower and indicator.boll_middle:
                if price > indicator.boll_middle:
                    signals.append("✅ 价格在布林中轨之上")
                    score += 1
                if price < indicator.boll_upper * 0.95:  # 未触及上轨
                    score += 1
            
            # 6. 成交量
            if indicator.volume_ma5 and daily.volume:
                if daily.volume > indicator.volume_ma5 * 1.2:
                    signals.append("✅ 成交量放大")
                    score += 2
            
            # 只保留得分>=4的股票（建仓信号）
            if score >= 4:
                buy_signals.append({
                    'symbol': symbol,
                    'name': sel.name,
                    'total_score': sel.total_score,
                    'signal_score': score,
                    'price': price,
                    'signals': signals,
                    'change_pct': daily.change_pct if daily.change_pct else 0
                })
        
        # 按信号得分排序
        buy_signals.sort(key=lambda x: (x['signal_score'], x['total_score']), reverse=True)
        
        # 输出结果
        print("\n" + "="*100)
        print("📊 建仓信号分析")
        print("="*100)
        print(f"分析日期: {latest_date}")
        print(f"筛选条件: 评分≥{min_score}分 且 建仓信号≥4分")
        print(f"找到 {len(buy_signals)} 只适合建仓的股票")
        print("="*100)
        
        if not buy_signals:
            print("\n❌ 暂无符合条件的建仓机会")
            print("\n💡 建议:")
            print("  1. 降低筛选条件 (--min-score 70)")
            print("  2. 等待更好的入场时机")
            print("  3. 关注资金流入监控系统的实时信号")
            return
        
        print(f"\n{'排名':<6}{'代码':<12}{'名称':<20}{'评分':<8}{'信号':<8}{'最新价':<10}{'涨跌幅':<10}")
        print("-"*100)
        
        for i, signal in enumerate(buy_signals[:20], 1):  # 只显示前20个
            print(f"{i:<6}{signal['symbol']:<12}{signal['name']:<20}"
                  f"{signal['total_score']:<8}{signal['signal_score']:<8}"
                  f"{signal['price']:<10.2f}{signal['change_pct']:>9.2f}%")
        
        print("="*100)
        
        # 详细分析前5名
        print("\n" + "="*100)
        print("🎯 Top 5 详细分析")
        print("="*100)
        
        for i, signal in enumerate(buy_signals[:5], 1):
            print(f"\n【{i}】{signal['name']} ({signal['symbol']})")
            print(f"  综合评分: {signal['total_score']}分")
            print(f"  建仓信号: {signal['signal_score']}分")
            print(f"  最新价格: ¥{signal['price']:.2f}")
            print(f"  今日涨跌: {signal['change_pct']:+.2f}%")
            print(f"  技术信号:")
            for sig in signal['signals']:
                print(f"    {sig}")
        
        print("\n" + "="*100)
        print("💡 建仓建议")
        print("="*100)
        print("1. 建议分批建仓，首次建仓30-50%")
        print("2. 设置止损位：-5%")
        print("3. 设置止盈位：+10%")
        print("4. 关注成交量变化，放量上涨可加仓")
        print("5. 如遇大盘调整，可适当降低仓位")
        print("="*100)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='分析建仓信号')
    parser.add_argument('--min-score', type=int, default=75, help='最低评分')
    parser.add_argument('--market', type=str, default='HK', choices=['HK', 'CN'], help='市场')
    
    args = parser.parse_args()
    
    analyze_entry_signals(min_score=args.min_score, market=args.market)

