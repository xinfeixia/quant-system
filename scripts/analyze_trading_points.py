"""
分析股票的买卖点
"""
import sys
from pathlib import Path
import argparse
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData, TechnicalIndicator
from analysis.trading_signals import TradingSignalAnalyzer
from loguru import logger


def analyze_stock_trading_points(symbol):
    """
    分析单只股票的买卖点
    
    Args:
        symbol: 股票代码
        
    Returns:
        dict: 分析结果
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 获取股票信息
        stock = session.query(StockInfo).filter_by(symbol=symbol).first()
        if not stock:
            logger.error(f"股票 {symbol} 不存在")
            return None
        
        # 获取K线数据和技术指标
        query = session.query(
            DailyData, TechnicalIndicator
        ).outerjoin(
            TechnicalIndicator,
            (DailyData.symbol == TechnicalIndicator.symbol) &
            (DailyData.trade_date == TechnicalIndicator.trade_date)
        ).filter(
            DailyData.symbol == symbol
        ).order_by(
            DailyData.trade_date
        )
        
        results = query.all()
        
        if not results:
            logger.error(f"股票 {symbol} 没有数据")
            return None
        
        # 转换为字典列表
        kline_data = []
        for daily, indicator in results:
            data = {
                'date': daily.trade_date.strftime('%Y-%m-%d'),
                'open': daily.open,
                'high': daily.high,
                'low': daily.low,
                'close': daily.close,
                'volume': daily.volume
            }
            
            if indicator:
                data.update({
                    'ma5': indicator.ma5,
                    'ma10': indicator.ma10,
                    'ma20': indicator.ma20,
                    'ma60': indicator.ma60,
                    'macd': indicator.macd,
                    'signal': indicator.macd_signal,
                    'rsi': indicator.rsi,
                    'kdj_k': indicator.kdj_k,
                    'kdj_d': indicator.kdj_d,
                    'kdj_j': indicator.kdj_j,
                    'boll_upper': indicator.boll_upper,
                    'boll_middle': indicator.boll_middle,
                    'boll_lower': indicator.boll_lower,
                    'atr': indicator.atr
                })
            
            kline_data.append(data)
        
        # 创建分析器
        analyzer = TradingSignalAnalyzer(kline_data)
        
        # 生成分析结果
        result = {
            'symbol': symbol,
            'name': stock.name,
            'current_price': kline_data[-1]['close'],
            'buy_signals': analyzer.generate_buy_signals(),
            'sell_signals': analyzer.generate_sell_signals(),
            'support_resistance': analyzer.calculate_support_resistance(),
            'target_prices': analyzer.calculate_target_prices(),
            'best_historical_trades': analyzer.find_best_historical_trades()
        }
        
        return result


def display_analysis_result(result):
    """
    显示分析结果
    
    Args:
        result: 分析结果字典
    """
    print("\n" + "=" * 80)
    print(f"📊 {result['symbol']} - {result['name']} 买卖点分析")
    print("=" * 80)
    
    print(f"\n💰 当前价格: {result['current_price']:.2f}")
    
    # 买入信号
    print("\n" + "-" * 80)
    print("📈 买入信号分析")
    print("-" * 80)
    buy = result['buy_signals']
    signal_emoji = {
        'STRONG_BUY': '🟢🟢🟢',
        'BUY': '🟢🟢',
        'WEAK_BUY': '🟢',
        'HOLD': '⚪'
    }
    print(f"信号: {signal_emoji.get(buy['signal'], '⚪')} {buy['signal']}")
    print(f"强度: {buy['strength']}/100")
    if buy['reasons']:
        print("原因:")
        for reason in buy['reasons']:
            print(f"  ✓ {reason}")
    
    # 卖出信号
    print("\n" + "-" * 80)
    print("📉 卖出信号分析")
    print("-" * 80)
    sell = result['sell_signals']
    signal_emoji_sell = {
        'STRONG_SELL': '🔴🔴🔴',
        'SELL': '🔴🔴',
        'WEAK_SELL': '🔴',
        'HOLD': '⚪'
    }
    print(f"信号: {signal_emoji_sell.get(sell['signal'], '⚪')} {sell['signal']}")
    print(f"强度: {sell['strength']}/100")
    if sell['reasons']:
        print("原因:")
        for reason in sell['reasons']:
            print(f"  ✓ {reason}")
    
    # 目标价和止损价
    print("\n" + "-" * 80)
    print("🎯 目标价和止损价")
    print("-" * 80)
    targets = result['target_prices']
    if targets:
        print(f"当前价格: {targets['current_price']:.2f}")
        print(f"止损价格: {targets['stop_loss']:.2f} ({targets['stop_loss_pct']:+.2f}%)")
        print(f"目标价1:  {targets['target1']:.2f} ({targets['target1_pct']:+.2f}%) - 风险收益比 1:{targets['risk_reward_ratio1']:.2f}")
        print(f"目标价2:  {targets['target2']:.2f} ({targets['target2_pct']:+.2f}%) - 风险收益比 1:{targets['risk_reward_ratio2']:.2f}")
    
    # 支撑位和阻力位
    print("\n" + "-" * 80)
    print("📊 支撑位和阻力位")
    print("-" * 80)
    sr = result['support_resistance']
    if sr['support']:
        print("支撑位:")
        for s in sr['support'][:3]:
            print(f"  {s['price']:.2f} ({s['period']}日低点, 距离当前 {s['distance']:.2f}%)")
    if sr['resistance']:
        print("阻力位:")
        for r in sr['resistance'][:3]:
            print(f"  {r['price']:.2f} ({r['period']}日高点, 距离当前 {r['distance']:.2f}%)")
    
    # 历史最佳交易
    print("\n" + "-" * 80)
    print("🏆 历史最佳交易机会（过去90天）")
    print("-" * 80)
    trades = result['best_historical_trades']
    if trades:
        print(f"{'买入日期':<12} {'买入价':<10} {'卖出日期':<12} {'卖出价':<10} {'收益率':<10} {'持仓天数'}")
        print("-" * 80)
        for trade in trades[:5]:
            print(f"{trade['buy_date']:<12} {trade['buy_price']:<10.2f} "
                  f"{trade['sell_date']:<12} {trade['sell_price']:<10.2f} "
                  f"{trade['profit_pct']:>8.2f}% {trade['holding_days']:>8}天")
    else:
        print("未找到明显的交易机会")
    
    # 综合建议
    print("\n" + "=" * 80)
    print("💡 综合建议")
    print("=" * 80)
    
    if buy['strength'] > sell['strength']:
        if buy['strength'] >= 60:
            print("🟢 强烈建议买入")
        elif buy['strength'] >= 40:
            print("🟢 建议买入")
        else:
            print("🟡 可以考虑买入")
        
        if targets:
            print(f"\n建议操作:")
            print(f"  买入价格: {targets['current_price']:.2f} 附近")
            print(f"  止损价格: {targets['stop_loss']:.2f}")
            print(f"  目标价1:  {targets['target1']:.2f} (短期)")
            print(f"  目标价2:  {targets['target2']:.2f} (中期)")
    elif sell['strength'] > buy['strength']:
        if sell['strength'] >= 60:
            print("🔴 强烈建议卖出")
        elif sell['strength'] >= 40:
            print("🔴 建议卖出")
        else:
            print("🟡 可以考虑卖出")
    else:
        print("⚪ 建议持有观望")
    
    print("=" * 80 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='分析股票买卖点')
    parser.add_argument('--symbol', '-s', required=True, help='股票代码')
    
    args = parser.parse_args()
    
    # 初始化
    config_loader = init_config()
    config = config_loader.config
    db_manager = init_database(config)
    
    # 分析
    result = analyze_stock_trading_points(args.symbol)
    
    if result:
        display_analysis_result(result)
    else:
        logger.error("分析失败")
        sys.exit(1)


if __name__ == '__main__':
    main()

