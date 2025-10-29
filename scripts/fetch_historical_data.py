"""
获取历史数据脚本
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import time

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from data_collection.longport_client import init_longport_client, get_longport_client
from loguru import logger


def fetch_stock_history(symbol, days=365, period='day'):
    """
    获取单只股票的历史数据
    
    Args:
        symbol: 股票代码（如 700.HK）
        days: 获取天数
        period: K线周期（day/week/month）
    """
    try:
        logger.info(f"开始获取 {symbol} 的历史数据...")
        
        # 获取长桥客户端
        client = get_longport_client()
        
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 获取历史K线
        candlesticks = client.get_history_candlesticks(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        if not candlesticks:
            logger.warning(f"{symbol} 没有历史数据")
            return 0
        
        logger.info(f"获取到 {len(candlesticks)} 条K线数据")
        
        # 保存到数据库
        db_manager = get_db_manager()
        saved_count = 0
        
        with db_manager.get_session() as session:
            for candle in candlesticks:
                # 检查是否已存在
                existing = session.query(DailyData).filter_by(
                    symbol=symbol,
                    trade_date=candle.timestamp.date()
                ).first()
                
                if existing:
                    # 更新数据
                    existing.open = candle.open
                    existing.high = candle.high
                    existing.low = candle.low
                    existing.close = candle.close
                    existing.volume = candle.volume
                    existing.turnover = candle.turnover
                else:
                    # 插入新数据
                    daily_data = DailyData(
                        symbol=symbol,
                        trade_date=candle.timestamp.date(),
                        open=candle.open,
                        high=candle.high,
                        low=candle.low,
                        close=candle.close,
                        volume=candle.volume,
                        turnover=candle.turnover,
                        created_at=datetime.now()
                    )
                    session.add(daily_data)
                    saved_count += 1
        
        logger.info(f"成功保存 {saved_count} 条新数据到数据库")
        return saved_count
        
    except Exception as e:
        logger.error(f"获取 {symbol} 历史数据失败: {e}")
        return 0


def fetch_batch_history(market='HK', limit=10, days=365):
    """
    批量获取股票历史数据

    Args:
        market: 市场代码（HK/US/CN）
        limit: 获取数量限制
        days: 获取天数
    """
    try:
        logger.info(f"开始批量获取 {market} 市场的历史数据...")

        db_manager = get_db_manager()

        # 获取股票列表（提取需要的字段，避免会话问题）
        stock_list = []
        with db_manager.get_session() as session:
            stocks = session.query(StockInfo).filter_by(
                market=market,
                is_active=True
            ).limit(limit).all()

            # 提取股票信息到字典列表
            for stock in stocks:
                stock_list.append({
                    'symbol': stock.symbol,
                    'name': stock.name
                })

        if not stock_list:
            logger.warning(f"{market} 市场没有股票数据，请先运行 fetch_stock_list.py")
            return

        logger.info(f"找到 {len(stock_list)} 只股票，开始获取历史数据...")

        total_saved = 0
        success_count = 0

        for i, stock_info in enumerate(stock_list, 1):
            symbol = stock_info['symbol']
            name = stock_info['name']
            logger.info(f"[{i}/{len(stock_list)}] 处理 {symbol} - {name}")

            try:
                saved = fetch_stock_history(symbol, days=days)
                total_saved += saved
                success_count += 1

                # 避免请求过快
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"处理 {symbol} 失败: {e}")
                continue

        logger.info(f"批量获取完成！成功: {success_count}/{len(stock_list)}, 总共保存: {total_saved} 条数据")

    except Exception as e:
        logger.error(f"批量获取历史数据失败: {e}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='获取股票历史数据')
    parser.add_argument('--symbol', type=str, help='股票代码（如 700.HK）')
    parser.add_argument('--market', type=str, default='HK', 
                       choices=['HK', 'US', 'CN'],
                       help='市场代码（批量模式）')
    parser.add_argument('--days', type=int, default=365, 
                       help='获取天数（默认365天）')
    parser.add_argument('--batch', action='store_true', 
                       help='批量模式')
    parser.add_argument('--limit', type=int, default=10, 
                       help='批量模式下的数量限制（默认10）')
    parser.add_argument('--period', type=str, default='day',
                       choices=['day', 'week', 'month'],
                       help='K线周期（默认day）')
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        config_loader = init_config()
        config = config_loader.config
        api_config = config_loader.api_config
        
        # 设置日志
        setup_logger(config)
        
        logger.info("=" * 60)
        logger.info("获取股票历史数据")
        logger.info("=" * 60)
        
        # 初始化数据库
        db_manager = init_database(config)
        db_manager.create_tables()
        
        # 初始化长桥客户端
        init_longport_client(api_config)
        
        # 执行获取
        if args.batch:
            # 批量模式
            fetch_batch_history(
                market=args.market,
                limit=args.limit,
                days=args.days
            )
        elif args.symbol:
            # 单只股票模式
            fetch_stock_history(
                symbol=args.symbol,
                days=args.days,
                period=args.period
            )
        else:
            logger.error("请指定 --symbol 或使用 --batch 模式")
            parser.print_help()
            sys.exit(1)
        
        logger.info("=" * 60)
        logger.info("历史数据获取完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

