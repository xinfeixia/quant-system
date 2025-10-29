#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询暗盘资金流向
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from database.models import StockInfo
from utils.config_loader import init_config
from loguru import logger


def find_stock(keyword):
    """
    根据关键词查找股票
    
    Args:
        keyword: 股票名称关键词
    """
    config = init_config()
    db = DatabaseManager(config)
    
    with db.get_session() as session:
        # 模糊查询股票名称
        stocks = session.query(StockInfo).filter(
            StockInfo.name.like(f'%{keyword}%')
        ).all()

        if not stocks:
            print(f"\n❌ 未找到包含 '{keyword}' 的股票")
            return None

        # 转换为字典列表，避免session关闭后无法访问
        stock_list = []
        for stock in stocks:
            stock_list.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'market': stock.market
            })

        print(f"\n找到 {len(stock_list)} 只股票：")
        print("-" * 80)
        for stock in stock_list:
            print(f"{stock['symbol']:<15} {stock['name']:<30} {stock['market']}")
        print("-" * 80)

        return stock_list


def get_grey_market_data(symbol):
    """
    获取暗盘数据
    
    Args:
        symbol: 股票代码
    """
    config = init_config()
    
    try:
        from longport.openapi import QuoteContext, Config
        
        # 初始化配置
        lp_config = Config(
            app_key=config['longport']['app_key'],
            app_secret=config['longport']['app_secret'],
            access_token=config['longport']['access_token']
        )
        
        # 创建行情上下文
        ctx = QuoteContext(lp_config)
        
        print(f"\n正在查询 {symbol} 的暗盘数据...")
        
        # 尝试获取实时报价（包含暗盘信息）
        try:
            quote = ctx.quote([symbol])
            if quote:
                print(f"\n✅ 获取到实时行情：")
                for q in quote:
                    print(f"  股票代码: {q.symbol}")
                    print(f"  最新价: {q.last_done}")
                    print(f"  成交量: {q.volume}")
                    print(f"  成交额: {q.turnover}")
                    
                    # 检查是否有暗盘相关字段
                    if hasattr(q, 'grey_market_price'):
                        print(f"  暗盘价: {q.grey_market_price}")
                    if hasattr(q, 'grey_market_volume'):
                        print(f"  暗盘成交量: {q.grey_market_volume}")
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
        
        # 尝试获取资金流向数据
        try:
            # LongPort可能有资金流向接口
            print(f"\n⚠️ LongPort API暗盘数据接口说明：")
            print("  暗盘数据通常只在新股上市前的暗盘交易时段提供")
            print("  对于已上市股票，暗盘数据不适用")
            print("  建议使用以下方式获取资金流向：")
            print("  1. 查看分时成交明细（大单流入流出）")
            print("  2. 查看资金流向指标（主力资金、散户资金）")
            print("  3. 使用我们的资金流入监控系统")
        except Exception as e:
            logger.error(f"查询失败: {e}")
        
        ctx.close()
        
    except ImportError:
        print("\n❌ LongPort SDK未安装")
        print("请运行: pip install longport")
    except Exception as e:
        logger.error(f"获取暗盘数据失败: {e}")
        print(f"\n❌ 获取暗盘数据失败: {e}")


def get_capital_flow(symbol):
    """
    获取资金流向数据（替代暗盘数据）
    
    Args:
        symbol: 股票代码
    """
    config = init_config()
    db = DatabaseManager(config)
    
    print(f"\n📊 查询 {symbol} 的资金流向数据...")
    
    with db.get_session() as session:
        from database.models import MoneyFlowAlert
        from datetime import datetime, timedelta
        
        # 查询最近的资金流入告警
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        alerts = session.query(MoneyFlowAlert).filter(
            MoneyFlowAlert.symbol == symbol,
            MoneyFlowAlert.alert_datetime >= week_ago
        ).order_by(MoneyFlowAlert.alert_datetime.desc()).limit(10).all()
        
        if alerts:
            print(f"\n✅ 找到 {len(alerts)} 条资金流入告警：")
            print("-" * 100)
            print(f"{'时间':<20} {'价格':<10} {'成交量倍数':<15} {'成交额倍数':<15} {'价格变动':<10}")
            print("-" * 100)
            for alert in alerts:
                print(f"{str(alert.alert_datetime):<20} "
                      f"{alert.current_price:<10.2f} "
                      f"{alert.volume_ratio:<15.2f} "
                      f"{alert.turnover_ratio:<15.2f} "
                      f"{alert.price_change_pct:>9.2f}%")
            print("-" * 100)
        else:
            print(f"\n⚠️ 最近7天没有资金流入告警")
        
        # 查询今天的分钟数据，分析资金流向
        from database.models import MinuteData
        from datetime import datetime as dt

        today_start = dt.combine(today, dt.min.time())

        minute_data = session.query(MinuteData).filter(
            MinuteData.symbol == symbol,
            MinuteData.trade_datetime >= today_start
        ).order_by(MinuteData.trade_datetime.desc()).limit(100).all()
        
        if minute_data:
            print(f"\n✅ 今天有 {len(minute_data)} 条分钟数据")
            
            # 计算资金流向
            total_volume = sum([m.volume for m in minute_data if m.volume])
            avg_volume = total_volume / len(minute_data) if minute_data else 0
            
            # 统计放量分钟数
            high_volume_count = sum([1 for m in minute_data if m.volume and m.volume > avg_volume * 1.5])
            
            print(f"  平均每分钟成交量: {avg_volume:,.0f}")
            print(f"  放量分钟数: {high_volume_count} / {len(minute_data)}")
            
            if high_volume_count > len(minute_data) * 0.3:
                print(f"\n  💰 资金流向: 流入（放量明显）")
            elif high_volume_count < len(minute_data) * 0.1:
                print(f"\n  💸 资金流向: 流出（缩量明显）")
            else:
                print(f"\n  ➡️ 资金流向: 平衡")
        else:
            print(f"\n⚠️ 今天还没有分钟数据")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='查询暗盘资金流向')
    parser.add_argument('--keyword', type=str, help='股票名称关键词')
    parser.add_argument('--symbol', type=str, help='股票代码')
    
    args = parser.parse_args()
    
    if args.keyword:
        stocks = find_stock(args.keyword)
        if stocks and len(stocks) == 1:
            symbol = stocks[0]['symbol']
            print(f"\n将查询 {symbol} 的资金流向数据...")
            get_capital_flow(symbol)
        elif stocks and len(stocks) > 1:
            print(f"\n请使用 --symbol 参数指定具体的股票代码")
    elif args.symbol:
        get_capital_flow(args.symbol)
    else:
        print("请使用 --keyword 或 --symbol 参数")
        print("示例: python scripts/check_grey_market.py --keyword 中文在线")

