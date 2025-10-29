"""
慢速获取美股历史数据（避免API限制）
"""
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from data_collection.longport_client import init_longport_client, get_longport_client
from loguru import logger


def fetch_stock_data(symbol, days=365):
    """获取单只股票的历史数据"""
    try:
        client = get_longport_client()
        db_manager = get_db_manager()
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取历史K线
        logger.info(f"获取 {symbol} 从 {start_date.date()} 到 {end_date.date()} 的数据...")
        
        candlesticks = client.get_candlesticks(
            symbol=symbol,
            period='Day',
            count=days,
            adjust_type='NoAdjust'
        )
        
        if not candlesticks:
            logger.warning(f"{symbol} 没有获取到数据")
            return 0
        
        logger.info(f"获取到 {len(candlesticks)} 条K线数据")
        
        # 保存到数据库
        saved_count = 0
        with db_manager.get_session() as session:
            for candle in candlesticks:
                # 检查是否已存在
                existing = session.query(DailyData).filter_by(
                    symbol=symbol,
                    trade_date=candle.timestamp.date()
                ).first()
                
                if existing:
                    continue
                
                # 创建新记录
                daily_data = DailyData(
                    symbol=symbol,
                    trade_date=candle.timestamp.date(),
                    open=float(candle.open),
                    high=float(candle.high),
                    low=float(candle.low),
                    close=float(candle.close),
                    volume=int(candle.volume),
                    turnover=float(candle.turnover)
                )
                session.add(daily_data)
                saved_count += 1
            
            session.commit()
        
        logger.info(f"✅ {symbol} 保存了 {saved_count} 条新数据")
        return saved_count
        
    except Exception as e:
        logger.error(f"❌ {symbol} 获取失败: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description='慢速获取美股历史数据')
    parser.add_argument('--days', type=int, default=365, help='获取多少天的数据')
    parser.add_argument('--batch-size', type=int, default=5, help='每批处理多少只股票')
    parser.add_argument('--batch-delay', type=int, default=60, help='每批之间延迟多少秒')
    parser.add_argument('--stock-delay', type=int, default=2, help='每只股票之间延迟多少秒')
    parser.add_argument('--start-from', type=int, default=0, help='从第几只股票开始')
    
    args = parser.parse_args()
    
    # 初始化
    config_loader = init_config()
    config = config_loader.config
    db_manager = init_database(config)
    init_longport_client(config_loader.api_config)
    
    print("\n" + "=" * 60)
    print("慢速获取美股历史数据")
    print("=" * 60)
    print(f"每批处理: {args.batch_size} 只股票")
    print(f"批次延迟: {args.batch_delay} 秒")
    print(f"股票延迟: {args.stock_delay} 秒")
    print(f"获取天数: {args.days} 天")
    print("=" * 60 + "\n")
    
    # 获取所有美股
    with db_manager.get_session() as session:
        us_stocks = session.query(StockInfo).filter_by(
            market='US',
            is_active=True
        ).all()
    
    total = len(us_stocks)
    print(f"找到 {total} 只美股\n")
    
    # 从指定位置开始
    us_stocks = us_stocks[args.start_from:]
    
    total_saved = 0
    total_failed = 0
    
    for i, stock in enumerate(us_stocks, args.start_from + 1):
        batch_num = (i - args.start_from - 1) // args.batch_size + 1
        in_batch_num = (i - args.start_from - 1) % args.batch_size + 1
        
        print(f"\n[批次 {batch_num}] [{in_batch_num}/{args.batch_size}] [{i}/{total}] {stock.symbol} - {stock.name}")
        
        # 获取数据
        saved = fetch_stock_data(stock.symbol, args.days)
        
        if saved > 0:
            total_saved += saved
        else:
            total_failed += 1
        
        # 延迟
        if i < total:  # 不是最后一只
            if in_batch_num == args.batch_size:
                # 批次结束，长延迟
                print(f"\n⏸️  批次完成，休息 {args.batch_delay} 秒...\n")
                time.sleep(args.batch_delay)
            else:
                # 批次内，短延迟
                time.sleep(args.stock_delay)
    
    print("\n" + "=" * 60)
    print("获取完成！")
    print(f"  处理股票: {len(us_stocks)} 只")
    print(f"  新增数据: {total_saved} 条")
    print(f"  失败股票: {total_failed} 只")
    print("=" * 60 + "\n")
    
    if total_saved > 0:
        print("💡 下一步:")
        print("  1. 计算技术指标: python scripts/calculate_indicators.py --batch --market US")
        print("  2. 运行选股分析: python scripts/run_stock_selection.py --market US --top 30\n")


if __name__ == '__main__':
    main()

