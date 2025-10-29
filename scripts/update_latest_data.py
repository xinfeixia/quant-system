"""
更新最新交易数据
获取今天/最新的股票数据
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from data_collection.longport_client import init_longport_client, get_longport_client
from loguru import logger


def get_latest_data_date(symbol):
    """
    获取股票最新数据日期
    
    Args:
        symbol: 股票代码
        
    Returns:
        date: 最新数据日期，如果没有数据返回None
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        latest = session.query(DailyData).filter_by(
            symbol=symbol
        ).order_by(
            DailyData.trade_date.desc()
        ).first()
        
        return latest.trade_date if latest else None


def update_stock_latest_data(symbol, name, days=7):
    """
    更新单只股票的最新数据

    Args:
        symbol: 股票代码
        name: 股票名称
        days: 获取最近几天的数据

    Returns:
        int: 新增数据条数
    """
    try:
        # 获取最新数据日期
        latest_date = get_latest_data_date(symbol)

        if latest_date:
            logger.info(f"{symbol} - {name}: 最新数据日期 {latest_date}")
        else:
            logger.info(f"{symbol} - {name}: 没有历史数据，获取最近{days}天数据")

        # 获取最新K线数据
        client = get_longport_client()

        kline_data = client.get_candlesticks(
            symbol,
            'day',
            count=days
        )
        
        if not kline_data:
            logger.warning(f"{symbol} - {name}: 未获取到数据")
            return 0
        
        # 过滤出新数据
        new_data = []
        for candle in kline_data:
            trade_date = candle.timestamp.date()

            # 如果有最新日期，只保存比它新的数据
            if latest_date is None or trade_date > latest_date:
                new_data.append(candle)
        
        if not new_data:
            logger.info(f"{symbol} - {name}: 数据已是最新")
            return 0
        
        # 保存新数据
        db_manager = get_db_manager()

        with db_manager.get_session() as session:
            for candle in new_data:
                trade_date = candle.timestamp.date()

                # 检查是否已存在
                exists = session.query(DailyData).filter_by(
                    symbol=symbol,
                    trade_date=trade_date
                ).first()

                if exists:
                    continue

                # 创建新记录
                daily_data = DailyData(
                    symbol=symbol,
                    trade_date=trade_date,
                    open=float(candle.open),
                    high=float(candle.high),
                    low=float(candle.low),
                    close=float(candle.close),
                    volume=float(candle.volume),
                    turnover=float(candle.turnover)
                )

                session.add(daily_data)

            session.commit()
        
        logger.info(f"✅ {symbol} - {name}: 新增 {len(new_data)} 条数据")
        return len(new_data)
        
    except Exception as e:
        logger.error(f"❌ {symbol} - {name}: 更新失败 - {e}")
        return 0


def update_all_latest_data(market='HK', days=7):
    """
    更新所有股票的最新数据

    Args:
        market: 市场代码
        days: 获取最近几天的数据
    """

    # 获取股票列表
    db_manager = get_db_manager()

    with db_manager.get_session() as session:
        stocks = session.query(StockInfo).filter_by(market=market).all()

        if not stocks:
            logger.warning(f"没有找到 {market} 市场的股票")
            return

        # 提取股票信息到列表，避免session关闭后访问
        stock_list = [(stock.symbol, stock.name) for stock in stocks]

    # 在session外部处理
    logger.info(f"开始更新 {len(stock_list)} 只股票的最新数据...")

    total_new = 0
    success_count = 0

    for i, (symbol, name) in enumerate(stock_list, 1):
        logger.info(f"[{i}/{len(stock_list)}] 更新 {symbol} - {name}")

        new_count = update_stock_latest_data(symbol, name, days)

        if new_count > 0:
            total_new += new_count
            success_count += 1

    print("\n" + "=" * 60)
    print("✅ 更新完成！")
    print("=" * 60)
    print(f"总股票数: {len(stock_list)}")
    print(f"有更新的股票: {success_count}")
    print(f"新增数据条数: {total_new}")
    print("=" * 60 + "\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='更新最新交易数据')
    parser.add_argument('--market', default='HK', help='市场代码 (HK/US/CN)')
    parser.add_argument('--symbol', help='指定股票代码（可选）')
    parser.add_argument('--days', type=int, default=7, help='获取最近几天的数据（默认7天）')
    
    args = parser.parse_args()
    
    # 初始化配置和数据库
    config_loader = init_config()
    config = config_loader.config
    db_manager = init_database(config)

    # 初始化LongPort客户端
    init_longport_client(config_loader.api_config)
    
    print("\n" + "=" * 60)
    print("📊 更新最新交易数据")
    print("=" * 60)
    print(f"市场: {args.market}")
    print(f"获取天数: {args.days}")
    if args.symbol:
        print(f"股票代码: {args.symbol}")
    print("=" * 60 + "\n")
    
    if args.symbol:
        # 更新单只股票
        with db_manager.get_session() as session:
            stock = session.query(StockInfo).filter_by(symbol=args.symbol).first()

            if not stock:
                logger.error(f"股票 {args.symbol} 不存在")
                sys.exit(1)

            # 提取数据到变量
            symbol = stock.symbol
            name = stock.name

        # 在session外部调用
        new_count = update_stock_latest_data(symbol, name, args.days)

        print("\n" + "=" * 60)
        print("✅ 更新完成！")
        print("=" * 60)
        print(f"股票: {symbol} - {name}")
        print(f"新增数据: {new_count} 条")
        print("=" * 60 + "\n")
    else:
        # 更新所有股票
        update_all_latest_data(args.market, args.days)
    
    # 更新完成后，计算技术指标
    print("💡 提示: 数据更新完成后，建议运行以下命令计算技术指标：")
    if args.symbol:
        print(f"  python scripts/calculate_indicators.py --symbol {args.symbol}")
    else:
        print(f"  python scripts/calculate_indicators.py --batch --market {args.market}")


if __name__ == '__main__':
    main()

