#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成详细的买入计划
包括买入价格区间、止损止盈点位等
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from database.models import StockInfo, DailyData, TechnicalIndicator, StockSelection
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from loguru import logger
from utils.config_loader import ConfigLoader

def get_stock_details(db: DatabaseManager, symbol: str, market: str):
    """获取股票详细信息"""
    with db.get_session() as session:
        # 获取股票基本信息
        stock = session.query(StockInfo).filter(
            and_(
                StockInfo.symbol == symbol,
                StockInfo.market == market
            )
        ).first()

        if not stock:
            return None

        # 获取最新日线数据
        latest_daily = session.query(DailyData).filter(
            DailyData.symbol == symbol
        ).order_by(desc(DailyData.trade_date)).first()

        # 获取最新技术指标
        latest_indicator = session.query(TechnicalIndicator).filter(
            TechnicalIndicator.symbol == symbol
        ).order_by(desc(TechnicalIndicator.trade_date)).first()

        # 获取选股评分
        latest_selection = session.query(StockSelection).filter(
            and_(
                StockSelection.symbol == symbol,
                StockSelection.market == market
            )
        ).order_by(desc(StockSelection.selection_date)).first()

        # 提取数据到字典，避免detached问题
        result = {
            'stock_name': stock.name if stock else None,
            'current_price': latest_daily.close if latest_daily else None,
            'rsi': latest_indicator.rsi if latest_indicator else None,
            'ma5': latest_indicator.ma5 if latest_indicator else None,
            'ma20': latest_indicator.ma20 if latest_indicator else None,
            'boll_lower': latest_indicator.boll_lower if latest_indicator else None,
            'boll_upper': latest_indicator.boll_upper if latest_indicator else None,
            'boll_middle': latest_indicator.boll_middle if latest_indicator else None,
        }

        return result

def calculate_buy_plan(details, signal_strength):
    """计算买入计划"""
    if not details or not details['current_price']:
        return None

    current_price = details['current_price']
    boll_lower = details['boll_lower']
    boll_upper = details['boll_upper']
    ma20 = details['ma20']
    rsi = details['rsi']
    
    # 计算买入价格区间
    # 如果接近布林带下轨，可以在下轨附近买入
    if boll_lower:
        buy_price_low = boll_lower * 0.98  # 下轨下方2%
        buy_price_high = boll_lower * 1.02  # 下轨上方2%
    else:
        buy_price_low = current_price * 0.97
        buy_price_high = current_price * 1.01

    # 如果当前价格低于买入区间，调整买入区间
    if current_price < buy_price_low:
        buy_price_low = current_price * 0.99
        buy_price_high = current_price * 1.02

    # 计算止损位
    # 优先使用布林带下轨，其次使用MA20
    if boll_lower:
        stop_loss = boll_lower * 0.95
    elif ma20:
        stop_loss = ma20 * 0.95
    else:
        stop_loss = current_price * 0.92
    
    # 确保止损不超过8-10%
    max_stop_loss = current_price * 0.90
    if stop_loss < max_stop_loss:
        stop_loss = max_stop_loss
    
    # 计算止盈位
    # 根据信号强度设置不同的止盈目标
    if signal_strength >= 70:
        # 强烈买入：目标20-25%
        take_profit_1 = current_price * 1.15  # 第一目标15%
        take_profit_2 = current_price * 1.25  # 第二目标25%
    elif signal_strength >= 60:
        # 买入：目标15-20%
        take_profit_1 = current_price * 1.12
        take_profit_2 = current_price * 1.20
    else:
        # 一般买入：目标10-15%
        take_profit_1 = current_price * 1.10
        take_profit_2 = current_price * 1.15
    
    # 如果有布林带上轨，作为参考
    if boll_upper:
        # 如果布林带上轨在止盈目标之间，使用它作为第一目标
        if take_profit_1 < boll_upper < take_profit_2:
            take_profit_1 = boll_upper

    return {
        'current_price': current_price,
        'buy_price_low': buy_price_low,
        'buy_price_high': buy_price_high,
        'stop_loss': stop_loss,
        'take_profit_1': take_profit_1,
        'take_profit_2': take_profit_2,
        'stop_loss_pct': (stop_loss - current_price) / current_price * 100,
        'take_profit_1_pct': (take_profit_1 - current_price) / current_price * 100,
        'take_profit_2_pct': (take_profit_2 - current_price) / current_price * 100,
        'rsi': rsi if rsi else 0,
        'ma5': details['ma5'] if details['ma5'] else 0,
        'ma20': ma20 if ma20 else 0,
        'boll_lower': boll_lower if boll_lower else 0,
        'boll_upper': boll_upper if boll_upper else 0,
    }

def generate_buy_plan(market: str, stocks: list):
    """生成买入计划"""
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    db = DatabaseManager(config)
    
    print(f"\n{'='*120}")
    print(f"📋 {market}市场买入计划")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*120}\n")
    
    for i, stock_info in enumerate(stocks, 1):
        symbol = stock_info['symbol']
        name = stock_info['name']
        signal_strength = stock_info['signal_strength']
        signal_type = stock_info['signal_type']
        buy_reason = stock_info['buy_reason']
        
        details = get_stock_details(db, symbol, market)
        if not details:
            logger.warning(f"未找到 {symbol} 的数据")
            continue
        
        plan = calculate_buy_plan(details, signal_strength)
        if not plan:
            logger.warning(f"无法为 {symbol} 生成买入计划")
            continue
        
        print(f"{'='*120}")
        print(f"【{i}】{symbol} - {name}")
        print(f"{'='*120}")
        print(f"📊 信号强度: {signal_strength} ({signal_type})")
        print(f"💡 买入理由: {buy_reason}")
        print(f"\n💰 价格信息:")
        print(f"   当前价格: {plan['current_price']:.2f}")
        print(f"   MA5:      {plan['ma5']:.2f}")
        print(f"   MA20:     {plan['ma20']:.2f}")
        print(f"   布林下轨: {plan['boll_lower']:.2f}")
        print(f"   布林上轨: {plan['boll_upper']:.2f}")
        print(f"   RSI:      {plan['rsi']:.1f}")
        
        print(f"\n🎯 买入计划:")
        print(f"   ✅ 买入价格区间: {plan['buy_price_low']:.2f} - {plan['buy_price_high']:.2f}")
        print(f"   ❌ 止损价位:     {plan['stop_loss']:.2f} ({plan['stop_loss_pct']:.1f}%)")
        print(f"   🎁 第一目标:     {plan['take_profit_1']:.2f} (+{plan['take_profit_1_pct']:.1f}%)")
        print(f"   🎁 第二目标:     {plan['take_profit_2']:.2f} (+{plan['take_profit_2_pct']:.1f}%)")
        
        print(f"\n📝 操作建议:")
        if plan['current_price'] <= plan['buy_price_high']:
            print(f"   ✅ 当前价格在买入区间内，可以考虑买入")
        else:
            print(f"   ⏳ 当前价格略高，建议等待回调至 {plan['buy_price_high']:.2f} 以下")
        
        # 根据RSI给出建议
        if plan['rsi'] < 30:
            print(f"   ✅ RSI超卖({plan['rsi']:.1f})，反弹潜力大")
        elif plan['rsi'] < 40:
            print(f"   ✅ RSI偏低({plan['rsi']:.1f})，适合买入")
        
        # 仓位建议
        if signal_strength >= 70:
            position = "25-30%"
        elif signal_strength >= 60:
            position = "20-25%"
        elif signal_strength >= 55:
            position = "15-20%"
        else:
            position = "10-15%"
        
        print(f"   💼 建议仓位: {position}")
        print(f"\n")

def main():
    """主函数"""
    # A股推荐买入
    cn_stocks = [
        {
            'symbol': '300122.SZ',
            'name': '智飞生物',
            'signal_strength': 70,
            'signal_type': 'STRONG_BUY',
            'buy_reason': 'MACD金叉, RSI偏低(37.1), KDJ金叉, 接近布林带下轨'
        },
        {
            'symbol': '300070.SZ',
            'name': '碧水源',
            'signal_strength': 70,
            'signal_type': 'STRONG_BUY',
            'buy_reason': 'MACD金叉, RSI偏低(37.5), KDJ金叉, 接近布林带下轨'
        },
        {
            'symbol': '000014.SZ',
            'name': '沙河股份',
            'signal_strength': 65,
            'signal_type': 'STRONG_BUY',
            'buy_reason': 'MACD金叉, KDJ金叉, 均线多头排列'
        },
        {
            'symbol': '002205.SZ',
            'name': '国统股份',
            'signal_strength': 65,
            'signal_type': 'STRONG_BUY',
            'buy_reason': 'MACD金叉, KDJ金叉, 均线多头排列'
        },
        {
            'symbol': '000001.SZ',
            'name': '平安银行',
            'signal_strength': 60,
            'signal_type': 'STRONG_BUY',
            'buy_reason': 'MACD金叉, KDJ金叉, 接近布林带下轨'
        },
    ]
    
    # 港股通推荐买入
    hk_stocks = [
        {
            'symbol': '1800.HK',
            'name': '中国交通建设',
            'signal_strength': 70,
            'signal_type': 'STRONG_BUY',
            'buy_reason': 'MACD金叉, RSI偏低(38.9), KDJ金叉, 接近布林带下轨'
        },
        {
            'symbol': '2068.HK',
            'name': '中铝国际',
            'signal_strength': 65,
            'signal_type': 'STRONG_BUY',
            'buy_reason': 'MACD金叉, KDJ金叉, 均线多头排列'
        },
        {
            'symbol': '2899.HK',
            'name': '紫金矿业',
            'signal_strength': 55,
            'signal_type': 'BUY',
            'buy_reason': 'RSI超卖(27.6), KDJ金叉, 接近布林带下轨'
        },
        {
            'symbol': '1698.HK',
            'name': '腾讯音乐-SW',
            'signal_strength': 55,
            'signal_type': 'BUY',
            'buy_reason': 'MACD金叉, RSI偏低(37.1), KDJ金叉'
        },
        {
            'symbol': '1785.HK',
            'name': '成都高速',
            'signal_strength': 50,
            'signal_type': 'BUY',
            'buy_reason': 'MACD金叉, RSI偏低(33.3), 接近布林带下轨'
        },
    ]
    
    # 生成A股买入计划
    generate_buy_plan('CN', cn_stocks)
    
    # 生成港股买入计划
    generate_buy_plan('HK', hk_stocks)
    
    print(f"{'='*120}")
    print(f"⚠️  风险提示")
    print(f"{'='*120}")
    print(f"1. 以上买入计划仅供参考，不构成投资建议")
    print(f"2. 请严格执行止损止盈纪律，避免情绪化交易")
    print(f"3. 建议分批买入，不要一次性满仓")
    print(f"4. 港股波动性较大，建议控制总仓位在50%以内")
    print(f"5. 市场有风险，投资需谨慎")
    print(f"{'='*120}\n")

if __name__ == '__main__':
    main()

