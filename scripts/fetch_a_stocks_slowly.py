"""
慢速获取A股历史数据 - 避免API频率限制
每只股票之间有较长延迟，确保不触发限制
"""
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from data_collection.longport_client import init_longport_client, get_longport_client
from utils.config_loader import init_config
from loguru import logger


def fetch_stock_slowly(symbol, name, days=365, delay_after=10):
    """
    慢速获取单只股票数据
    
    Args:
        symbol: 股票代码
        name: 股票名称
        days: 获取天数
        delay_after: 获取后延迟秒数
    """
    try:
        logger.info(f"开始获取 {symbol} - {name} 的历史数据...")
        
        client = get_longport_client()
        db_manager = get_db_manager()
        
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 获取历史K线
        try:
            candlesticks = client.get_history_candlesticks(
                symbol=symbol,
                period='day',
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            if '301607' in str(e):
                logger.warning(f"{symbol} - API频率限制，等待{delay_after}秒后重试...")
                time.sleep(delay_after)
                # 重试一次
                try:
                    candlesticks = client.get_history_candlesticks(
                        symbol=symbol,
                        period='day',
                        start_date=start_date,
                        end_date=end_date
                    )
                except Exception as e2:
                    logger.error(f"{symbol} - 重试失败: {e2}")
                    return 0
            else:
                raise
        
        if not candlesticks:
            logger.warning(f"{symbol} 没有历史数据")
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
                    turnover=float(candle.turnover) if hasattr(candle, 'turnover') else None,
                    created_at=datetime.now()
                )
                
                session.add(daily_data)
                saved_count += 1
            
            session.commit()
        
        logger.info(f"✅ {symbol} - {name}: 保存 {saved_count} 条新数据")
        
        # 延迟
        if delay_after > 0:
            logger.info(f"等待 {delay_after} 秒...")
            time.sleep(delay_after)
        
        return saved_count
        
    except Exception as e:
        logger.error(f"❌ {symbol} - {name}: 获取失败 - {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description='慢速获取A股历史数据')
    parser.add_argument('--days', type=int, default=365,
                       help='获取天数（默认365天）')
    parser.add_argument('--delay', type=int, default=15,
                       help='每只股票之间的延迟秒数（默认15秒）')
    parser.add_argument('--start-from', type=int, default=0,
                       help='从第几只股票开始（默认0，用于断点续传）')
    parser.add_argument('--limit', type=int, default=0,
                       help='限制获取数量（默认0=全部）')
    
    args = parser.parse_args()
    
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    init_longport_client(config_loader.api_config)
    
    db_manager = get_db_manager()
    
    print("\n" + "="*60)
    print("慢速获取A股历史数据")
    print("="*60)
    print(f"获取天数: {args.days}")
    print(f"延迟时间: {args.delay}秒/股票")
    print(f"开始位置: 第{args.start_from + 1}只")
    if args.limit > 0:
        print(f"获取数量: {args.limit}只")
    print("="*60 + "\n")
    
    # 获取A股列表（转换为字典列表避免session问题）
    with db_manager.get_session() as session:
        cn_stocks_query = session.query(StockInfo).filter_by(market='CN').order_by(StockInfo.symbol).all()
        cn_stocks = [{'symbol': s.symbol, 'name': s.name} for s in cn_stocks_query]

    # 应用起始位置和限制
    if args.start_from > 0:
        cn_stocks = cn_stocks[args.start_from:]

    if args.limit > 0:
        cn_stocks = cn_stocks[:args.limit]

    total_stocks = len(cn_stocks)
    print(f"📊 准备获取 {total_stocks} 只A股的历史数据\n")

    # 统计
    success_count = 0
    fail_count = 0
    total_saved = 0

    start_time = datetime.now()

    # 逐个获取
    for i, stock in enumerate(cn_stocks, 1):
        print(f"\n[{i}/{total_stocks}] {stock['symbol']} - {stock['name']}")
        print("-" * 60)

        saved = fetch_stock_slowly(
            symbol=stock['symbol'],
            name=stock['name'],
            days=args.days,
            delay_after=args.delay
        )
        
        if saved >= 0:
            success_count += 1
            total_saved += saved
        else:
            fail_count += 1
        
        # 显示进度
        elapsed = (datetime.now() - start_time).total_seconds()
        avg_time = elapsed / i if i > 0 else 0
        remaining = (total_stocks - i) * avg_time
        
        print(f"进度: {i}/{total_stocks} ({i*100//total_stocks}%)")
        print(f"成功: {success_count}, 失败: {fail_count}, 总保存: {total_saved}条")
        print(f"已用时: {elapsed/60:.1f}分钟, 预计剩余: {remaining/60:.1f}分钟")
    
    # 最终统计
    total_time = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("获取完成！")
    print("="*60)
    print(f"✅ 成功: {success_count}/{total_stocks}")
    print(f"❌ 失败: {fail_count}/{total_stocks}")
    print(f"💾 总保存: {total_saved} 条数据")
    print(f"⏱️  总用时: {total_time/60:.1f} 分钟")
    print(f"⚡ 平均: {total_time/total_stocks:.1f} 秒/股票")
    print("="*60 + "\n")
    
    # 如果有失败的，提示如何继续
    if fail_count > 0:
        print("💡 提示: 如需重试失败的股票，可以稍后再次运行此脚本")
    
    # 如果没有全部完成，提示如何继续
    if args.limit > 0 and args.limit < len(cn_stocks):
        next_start = args.start_from + args.limit
        print(f"💡 继续获取: python scripts/fetch_a_stocks_slowly.py --start-from {next_start} --limit {args.limit}")


if __name__ == '__main__':
    main()

