"""
使用Tushare获取A股历史数据
避免长桥API频率限制
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from data_collection.tushare_client import init_tushare_client, get_tushare_client
from utils.config_loader import init_config
from loguru import logger


def fetch_stock_data(symbol: str, name: str, days: int = 365):
    """
    获取单只股票的历史数据
    
    Args:
        symbol: 股票代码
        name: 股票名称
        days: 获取天数
        
    Returns:
        保存的数据条数
    """
    try:
        logger.info(f"开始获取 {symbol} - {name} 的历史数据...")
        
        client = get_tushare_client()
        db_manager = get_db_manager()
        
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 转换为datetime
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.min.time())
        
        # 获取历史数据
        daily_data_list = client.get_daily_data(symbol, start_datetime, end_datetime)
        
        if not daily_data_list:
            logger.warning(f"{symbol} 没有历史数据")
            return 0
        
        logger.info(f"获取到 {len(daily_data_list)} 条数据")
        
        # 保存到数据库
        saved_count = 0
        
        with db_manager.get_session() as session:
            for data in daily_data_list:
                # 检查是否已存在
                existing = session.query(DailyData).filter_by(
                    symbol=symbol,
                    trade_date=data['trade_date']
                ).first()
                
                if existing:
                    continue
                
                # 创建新记录
                daily_data = DailyData(
                    symbol=data['symbol'],
                    trade_date=data['trade_date'],
                    open=data['open'],
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    volume=data['volume'],
                    turnover=data['turnover'],
                    created_at=data['created_at']
                )
                
                session.add(daily_data)
                saved_count += 1
            
            session.commit()
        
        logger.info(f"✅ {symbol} - {name}: 保存 {saved_count} 条新数据")
        return saved_count
        
    except Exception as e:
        logger.error(f"❌ {symbol} - {name}: 获取失败 - {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description='使用Tushare获取A股历史数据')
    parser.add_argument('--days', type=int, default=365,
                       help='获取天数（默认365天）')
    parser.add_argument('--start-from', type=int, default=0,
                       help='从第几只股票开始（默认0）')
    parser.add_argument('--limit', type=int, default=0,
                       help='限制获取数量（默认0=全部）')
    parser.add_argument('--test', action='store_true',
                       help='测试模式，只获取1只股票')
    
    args = parser.parse_args()
    
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    
    # 检查Tushare配置
    if 'tushare' not in config_loader.api_config:
        print("\n❌ 错误: 配置文件中缺少 Tushare 配置")
        print("请在 config/api_config.yaml 中添加 Tushare token")
        return
    
    # 初始化Tushare客户端
    try:
        init_tushare_client(config_loader.api_config['tushare'])
        client = get_tushare_client()
        
        # 测试连接
        if not client.test_connection():
            print("\n❌ Tushare连接失败，请检查token是否正确")
            return
            
    except Exception as e:
        print(f"\n❌ Tushare初始化失败: {e}")
        return
    
    print("\n" + "="*60)
    print("使用Tushare获取A股历史数据")
    print("="*60)
    print(f"获取天数: {args.days}")
    if args.test:
        print("模式: 测试模式（仅1只股票）")
    else:
        print(f"开始位置: 第{args.start_from + 1}只")
        if args.limit > 0:
            print(f"获取数量: {args.limit}只")
    print("="*60 + "\n")
    
    # 获取A股列表
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        cn_stocks_query = session.query(StockInfo).filter_by(market='CN').order_by(StockInfo.symbol).all()
        cn_stocks = [{'symbol': s.symbol, 'name': s.name} for s in cn_stocks_query]
    
    # 测试模式
    if args.test:
        cn_stocks = cn_stocks[:1]
    else:
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
        
        saved = fetch_stock_data(
            symbol=stock['symbol'],
            name=stock['name'],
            days=args.days
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
        print(f"已用时: {elapsed:.1f}秒, 预计剩余: {remaining:.1f}秒")
    
    # 最终统计
    total_time = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("获取完成！")
    print("="*60)
    print(f"✅ 成功: {success_count}/{total_stocks}")
    print(f"❌ 失败: {fail_count}/{total_stocks}")
    print(f"💾 总保存: {total_saved} 条数据")
    print(f"⏱️  总用时: {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)")
    if total_stocks > 0:
        print(f"⚡ 平均: {total_time/total_stocks:.1f} 秒/股票")
    print("="*60 + "\n")
    
    if success_count == total_stocks:
        print("🎉 所有A股历史数据获取完成！\n")
        print("💡 下一步:")
        print("   1. 计算技术指标:")
        print("      python scripts/calculate_indicators.py --batch --market CN")
        print("   2. 运行选股:")
        print("      python scripts/run_stock_selection.py --market CN --top 50")
        print("   3. 查看结果:")
        print("      http://localhost:5000/selections?market=CN")
        print()


if __name__ == '__main__':
    main()

