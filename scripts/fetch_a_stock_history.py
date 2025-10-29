#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充A股历史数据
为所有数据不足的A股补充历史K线数据
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from data_collection.tushare_client import TushareClient
from loguru import logger
from sqlalchemy import func


def get_stocks_need_data(min_days=60):
    """
    获取需要补充数据的A股列表
    
    Args:
        min_days: 最少需要的数据天数
        
    Returns:
        list: 需要补充数据的股票列表
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 获取所有A股
        all_stocks = session.query(StockInfo).filter(
            StockInfo.market == 'CN',
            StockInfo.is_active == True
        ).all()
        
        stocks_need_data = []
        
        for stock in all_stocks:
            # 查询该股票的数据条数
            count = session.query(func.count(DailyData.id)).filter(
                DailyData.symbol == stock.symbol
            ).scalar()
            
            if count < min_days:
                stocks_need_data.append({
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'current_count': count
                })
        
        return stocks_need_data


def fetch_stock_history_tushare(symbol, name, days=120, tushare_token=None):
    """
    使用Tushare获取单只股票的历史数据

    Args:
        symbol: 股票代码（如 600000.SH）
        name: 股票名称
        days: 获取天数
        tushare_token: Tushare API Token

    Returns:
        int: 保存的数据条数
    """
    try:
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 获取历史数据
        if not tushare_token:
            logger.error("Tushare token未配置")
            return 0

        client = TushareClient(token=tushare_token)
        data_list = client.get_daily_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )

        if not data_list:
            logger.warning(f"{symbol} - {name} 没有历史数据")
            return 0

        # 保存到数据库
        db_manager = get_db_manager()
        saved_count = 0
        updated_count = 0

        with db_manager.get_session() as session:
            for data in data_list:
                trade_date = data['trade_date']

                # 检查是否已存在
                existing = session.query(DailyData).filter_by(
                    symbol=symbol,
                    trade_date=trade_date
                ).first()

                if existing:
                    # 更新数据
                    existing.open = data['open']
                    existing.high = data['high']
                    existing.low = data['low']
                    existing.close = data['close']
                    existing.volume = data['volume']
                    existing.turnover = data['turnover']
                    updated_count += 1
                else:
                    # 插入新数据
                    daily_data = DailyData(
                        symbol=symbol,
                        trade_date=trade_date,
                        open=data['open'],
                        high=data['high'],
                        low=data['low'],
                        close=data['close'],
                        volume=data['volume'],
                        turnover=data['turnover'],
                        created_at=datetime.now()
                    )
                    session.add(daily_data)
                    saved_count += 1

            session.commit()

        logger.info(f"{symbol} - {name}: 新增 {saved_count} 条, 更新 {updated_count} 条")
        return saved_count
        
    except Exception as e:
        logger.error(f"获取 {symbol} - {name} 历史数据失败: {e}")
        return 0


def fetch_all_a_stock_history(days=120, min_days=60, batch_size=100, auto_confirm=False, tushare_token=None):
    """
    批量补充所有A股的历史数据

    Args:
        days: 获取天数
        min_days: 最少需要的数据天数
        batch_size: 每批处理的股票数量
        auto_confirm: 是否自动确认，不等待用户输入
        tushare_token: Tushare API Token
    """
    try:
        logger.info("=" * 80)
        logger.info(f"开始补充A股历史数据 - 获取{days}天数据")
        logger.info("=" * 80)

        if not tushare_token:
            logger.error("❌ Tushare token未配置，请在api_config.yaml中配置tushare.token")
            return

        # 获取需要补充数据的股票
        stocks_need_data = get_stocks_need_data(min_days=min_days)

        if not stocks_need_data:
            logger.info("✅ 所有A股数据都已充足，无需补充")
            return

        total_stocks = len(stocks_need_data)
        logger.info(f"\n📊 统计信息:")
        logger.info(f"  需要补充数据的股票: {total_stocks} 只")
        logger.info(f"  目标数据天数: {days} 天")
        logger.info(f"  最少数据天数: {min_days} 天")

        # 显示前10只需要补充的股票
        logger.info(f"\n前10只需要补充数据的股票:")
        for i, stock in enumerate(stocks_need_data[:10], 1):
            logger.info(f"  {i}. {stock['symbol']} - {stock['name']} (当前: {stock['current_count']}条)")

        # 确认是否继续
        if not auto_confirm:
            print(f"\n⚠️  将为 {total_stocks} 只A股补充历史数据，预计耗时: {total_stocks * 0.6 / 60:.1f} 分钟")
            confirm = input("是否继续？(y/n): ")
            if confirm.lower() != 'y':
                logger.info("用户取消操作")
                return
        else:
            logger.info(f"\n⚠️  将为 {total_stocks} 只A股补充历史数据，预计耗时: {total_stocks * 0.6 / 60:.1f} 分钟")
            logger.info("自动确认模式，开始执行...")
        
        # 开始批量获取
        total_saved = 0
        success_count = 0
        failed_count = 0
        
        start_time = time.time()
        
        for i, stock_info in enumerate(stocks_need_data, 1):
            symbol = stock_info['symbol']
            name = stock_info['name']
            current_count = stock_info['current_count']
            
            logger.info(f"\n[{i}/{total_stocks}] 处理 {symbol} - {name} (当前: {current_count}条)")

            try:
                saved = fetch_stock_history_tushare(symbol, name, days=days, tushare_token=tushare_token)
                total_saved += saved
                
                if saved > 0:
                    success_count += 1
                else:
                    failed_count += 1
                
                # Tushare限制：每分钟最多200次请求，这里设置为0.6秒/次（100次/分钟）
                time.sleep(0.6)
                
                # 每100只股票显示一次进度
                if i % batch_size == 0:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / i
                    remaining = (total_stocks - i) * avg_time
                    logger.info(f"\n📊 进度报告:")
                    logger.info(f"  已处理: {i}/{total_stocks} ({i/total_stocks*100:.1f}%)")
                    logger.info(f"  成功: {success_count}, 失败: {failed_count}")
                    logger.info(f"  新增数据: {total_saved} 条")
                    logger.info(f"  已用时: {elapsed/60:.1f} 分钟")
                    logger.info(f"  预计剩余: {remaining/60:.1f} 分钟")
                
            except Exception as e:
                logger.error(f"处理 {symbol} - {name} 失败: {e}")
                failed_count += 1
                continue
        
        # 最终统计
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 80)
        logger.info("✅ A股历史数据补充完成！")
        logger.info("=" * 80)
        logger.info(f"\n📊 最终统计:")
        logger.info(f"  总股票数: {total_stocks}")
        logger.info(f"  成功: {success_count} ({success_count/total_stocks*100:.1f}%)")
        logger.info(f"  失败: {failed_count} ({failed_count/total_stocks*100:.1f}%)")
        logger.info(f"  新增数据: {total_saved} 条")
        logger.info(f"  总用时: {elapsed/60:.1f} 分钟")
        logger.info(f"  平均速度: {elapsed/total_stocks:.2f} 秒/股")
        
    except Exception as e:
        logger.error(f"批量补充历史数据失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='补充A股历史数据')
    parser.add_argument('--days', type=int, default=120, help='获取天数（默认120天）')
    parser.add_argument('--min-days', type=int, default=60, help='最少需要的数据天数（默认60天）')
    parser.add_argument('--batch-size', type=int, default=100, help='每批处理的股票数量（默认100）')
    parser.add_argument('--auto-confirm', action='store_true', help='自动确认，不等待用户输入')

    args = parser.parse_args()

    try:
        # 加载配置
        config_loader = init_config()
        config = config_loader.config
        api_config = config_loader.api_config

        # 设置日志
        setup_logger(config)

        # 初始化数据库
        init_database(config)

        # 获取Tushare token
        tushare_token = api_config.get('tushare', {}).get('token')
        if not tushare_token:
            logger.error("❌ Tushare token未配置，请在config/api_config.yaml中配置tushare.token")
            sys.exit(1)

        # 执行补充
        fetch_all_a_stock_history(
            days=args.days,
            min_days=args.min_days,
            batch_size=args.batch_size,
            auto_confirm=args.auto_confirm,
            tushare_token=tushare_token
        )
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

