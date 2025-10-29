#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析当前持仓，提供调整建议
"""

import sys
from pathlib import Path
from datetime import datetime, date

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import Position, DailyData, TechnicalIndicator, StockInfo
from utils.config_loader import init_config
from loguru import logger


def get_stock_name(session, symbol):
    """获取股票名称"""
    stock = session.query(StockInfo).filter_by(symbol=symbol).first()
    return stock.name if stock else "未知"


def get_latest_data(session, symbol):
    """获取最新交易数据"""
    return session.query(DailyData).filter(
        DailyData.symbol == symbol
    ).order_by(DailyData.trade_date.desc()).first()


def get_latest_indicators(session, symbol):
    """获取最新技术指标"""
    return session.query(TechnicalIndicator).filter(
        TechnicalIndicator.symbol == symbol
    ).order_by(TechnicalIndicator.trade_date.desc()).first()


def analyze_position(session, position):
    """分析单个持仓"""
    symbol = position.symbol
    quantity = position.quantity
    avg_price = position.avg_price
    
    # 获取股票名称
    name = get_stock_name(session, symbol)
    
    # 获取最新价格
    latest_data = get_latest_data(session, symbol)
    if not latest_data:
        return {
            'symbol': symbol,
            'name': name,
            'quantity': quantity,
            'avg_price': avg_price,
            'current_price': None,
            'pnl': None,
            'pnl_pct': None,
            'recommendation': '⚠️ 无数据',
            'reasons': ['无最新交易数据'],
            'signal_strength': 0
        }
    
    current_price = latest_data.close
    cost = avg_price * quantity
    value = current_price * quantity
    pnl = value - cost
    pnl_pct = (pnl / cost * 100) if cost > 0 else 0
    
    # 获取技术指标
    indicators = get_latest_indicators(session, symbol)
    
    # 分析建议
    recommendation = "持有"
    reasons = []
    signal_strength = 0  # 信号强度：正数=买入，负数=卖出
    
    # 1. 盈亏分析
    if pnl_pct <= -8:
        recommendation = "🔴 建议止损"
        reasons.append(f"亏损{pnl_pct:.1f}%，触发止损线(-8%)")
        signal_strength -= 60
    elif pnl_pct >= 15:
        recommendation = "🟢 建议止盈"
        reasons.append(f"盈利{pnl_pct:.1f}%，触发止盈线(+15%)")
        signal_strength -= 40
    elif pnl_pct >= 10:
        reasons.append(f"盈利{pnl_pct:.1f}%，接近止盈")
        signal_strength -= 20
    elif pnl_pct <= -5:
        reasons.append(f"亏损{pnl_pct:.1f}%，接近止损")
        signal_strength -= 30
    
    # 2. 技术指标分析
    if indicators:
        # RSI分析
        if indicators.rsi:
            if indicators.rsi > 75:
                recommendation = "🔴 建议减仓"
                reasons.append(f"RSI超买({indicators.rsi:.1f})")
                signal_strength -= 45
            elif indicators.rsi < 30:
                if pnl_pct < 0:
                    recommendation = "🟡 可考虑补仓"
                    reasons.append(f"RSI超卖({indicators.rsi:.1f})，可能反弹")
                    signal_strength += 40
                else:
                    reasons.append(f"RSI超卖({indicators.rsi:.1f})")
                    signal_strength += 20
            elif indicators.rsi > 65:
                reasons.append(f"RSI偏高({indicators.rsi:.1f})")
                signal_strength -= 20
            elif indicators.rsi < 35:
                reasons.append(f"RSI偏低({indicators.rsi:.1f})")
                signal_strength += 15
        
        # MACD分析
        if indicators.macd and indicators.macd_signal:
            macd_diff = indicators.macd - indicators.macd_signal
            if macd_diff < 0 and abs(macd_diff) > 0.1:
                recommendation = "🔴 建议减仓"
                reasons.append("MACD死叉")
                signal_strength -= 40
            elif macd_diff > 0 and macd_diff > 0.1:
                reasons.append("MACD金叉")
                signal_strength += 35
        
        # KDJ分析
        if indicators.kdj_k and indicators.kdj_d:
            if indicators.kdj_k > 80 and indicators.kdj_d > 80:
                reasons.append(f"KDJ超买(K:{indicators.kdj_k:.1f})")
                signal_strength -= 25
            elif indicators.kdj_k < 20 and indicators.kdj_d < 20:
                reasons.append(f"KDJ超卖(K:{indicators.kdj_k:.1f})")
                signal_strength += 25
            
            # KDJ金叉/死叉
            if indicators.kdj_k > indicators.kdj_d:
                if indicators.kdj_k < 50:  # 低位金叉
                    reasons.append("KDJ金叉")
                    signal_strength += 20
            else:
                if indicators.kdj_k > 50:  # 高位死叉
                    reasons.append("KDJ死叉")
                    signal_strength -= 20
        
        # 均线分析
        if indicators.ma5 and indicators.ma10 and indicators.ma20:
            if current_price < indicators.ma5 < indicators.ma10 < indicators.ma20:
                recommendation = "🔴 建议减仓"
                reasons.append("均线空头排列")
                signal_strength -= 35
            elif current_price > indicators.ma5 > indicators.ma10 > indicators.ma20:
                reasons.append("均线多头排列")
                signal_strength += 30
            elif current_price < indicators.ma20:
                reasons.append("跌破MA20")
                signal_strength -= 15
        
        # 布林带分析
        if indicators.boll_upper and indicators.boll_lower:
            boll_width = indicators.boll_upper - indicators.boll_lower
            if current_price >= indicators.boll_upper:
                reasons.append("触及布林带上轨")
                signal_strength -= 20
            elif current_price <= indicators.boll_lower:
                reasons.append("触及布林带下轨")
                signal_strength += 20
    
    # 3. 价格趋势分析
    change_pct = latest_data.change_pct if latest_data.change_pct else 0
    if change_pct <= -5:
        reasons.append(f"今日大跌{change_pct:.1f}%")
        signal_strength -= 15
    elif change_pct >= 5:
        reasons.append(f"今日大涨{change_pct:.1f}%")
        signal_strength += 10
    
    # 综合判断
    if signal_strength <= -60:
        recommendation = "🔴 强烈建议卖出"
    elif signal_strength <= -40:
        recommendation = "🔴 建议减仓"
    elif signal_strength <= -20:
        recommendation = "🟡 考虑减仓"
    elif signal_strength >= 40:
        recommendation = "🟢 可考虑加仓"
    elif signal_strength >= 20:
        recommendation = "🟢 持有观察"
    else:
        recommendation = "⚪ 继续持有"
    
    if not reasons:
        reasons.append("技术指标正常")
    
    return {
        'symbol': symbol,
        'name': name,
        'quantity': quantity,
        'avg_price': avg_price,
        'current_price': current_price,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'recommendation': recommendation,
        'reasons': reasons,
        'signal_strength': signal_strength,
        'indicators': {
            'rsi': indicators.rsi if indicators else None,
            'macd': indicators.macd if indicators else None,
            'kdj_k': indicators.kdj_k if indicators else None,
            'ma5': indicators.ma5 if indicators else None,
            'ma20': indicators.ma20 if indicators else None,
        } if indicators else None
    }


def display_analysis(analyses):
    """显示分析结果"""
    if not analyses:
        print("\n📭 当前没有持仓")
        return
    
    print(f"\n{'='*120}")
    print(f"💼 持仓分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*120}\n")
    
    # 按信号强度排序（从最需要卖出到最值得持有）
    sorted_analyses = sorted(analyses, key=lambda x: x['signal_strength'])
    
    total_cost = 0
    total_value = 0
    
    for i, analysis in enumerate(sorted_analyses, 1):
        symbol = analysis['symbol']
        name = analysis['name']
        quantity = analysis['quantity']
        avg_price = analysis['avg_price']
        current_price = analysis['current_price']
        pnl = analysis['pnl']
        pnl_pct = analysis['pnl_pct']
        recommendation = analysis['recommendation']
        reasons = analysis['reasons']
        signal_strength = analysis['signal_strength']
        
        print(f"{i}. {symbol} - {name}")
        print(f"   {'='*116}")
        
        if current_price is None:
            print(f"   ⚠️ 无最新数据")
            print()
            continue
        
        cost = avg_price * quantity
        value = current_price * quantity
        total_cost += cost
        total_value += value
        
        print(f"   持仓: {quantity:,} 股 | 成本: ¥{avg_price:.2f} | 现价: ¥{current_price:.2f}")
        
        pnl_symbol = "+" if pnl >= 0 else ""
        pnl_color = "🟢" if pnl >= 0 else "🔴"
        print(f"   盈亏: {pnl_color} {pnl_symbol}¥{pnl:,.2f} ({pnl_symbol}{pnl_pct:.2f}%) | 市值: ¥{value:,.2f}")
        
        print(f"   建议: {recommendation} (信号强度: {signal_strength:+d})")
        print(f"   原因: {', '.join(reasons)}")
        
        # 显示关键技术指标
        if analysis['indicators']:
            ind = analysis['indicators']
            ind_str = []
            if ind['rsi']:
                ind_str.append(f"RSI:{ind['rsi']:.1f}")
            if ind['macd']:
                ind_str.append(f"MACD:{ind['macd']:.2f}")
            if ind['kdj_k']:
                ind_str.append(f"KDJ_K:{ind['kdj_k']:.1f}")
            if ind['ma5'] and ind['ma20']:
                ind_str.append(f"MA5:{ind['ma5']:.2f}")
                ind_str.append(f"MA20:{ind['ma20']:.2f}")
            
            if ind_str:
                print(f"   指标: {' | '.join(ind_str)}")
        
        print()
    
    # 总计
    if total_cost > 0:
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100)
        
        print(f"{'='*120}")
        pnl_symbol = "+" if total_pnl >= 0 else ""
        pnl_color = "🟢" if total_pnl >= 0 else "🔴"
        print(f"📊 总计: 成本 ¥{total_cost:,.2f} | 市值 ¥{total_value:,.2f} | 盈亏 {pnl_color} {pnl_symbol}¥{total_pnl:,.2f} ({pnl_symbol}{total_pnl_pct:.2f}%)")
        print(f"{'='*120}\n")


def main():
    """主函数"""
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    logger.info("开始分析持仓...")
    
    with db_manager.get_session() as session:
        # 获取所有持仓（数量>0）
        positions = session.query(Position).filter(Position.quantity > 0).all()
        
        if not positions:
            print("\n📭 当前没有持仓")
            return
        
        # 分析每个持仓
        analyses = []
        for pos in positions:
            analysis = analyze_position(session, pos)
            analyses.append(analysis)
        
        # 显示分析结果
        display_analysis(analyses)


if __name__ == '__main__':
    main()

