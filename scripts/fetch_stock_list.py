"""
获取股票列表脚本
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from database import init_database, get_db_manager
from database.models import StockInfo
from data_collection.longport_client import init_longport_client, get_longport_client
from loguru import logger


def add_stock_manually(symbols, market='HK'):
    """
    手动添加股票列表

    Args:
        symbols: 股票代码列表
        market: 市场代码
    """
    try:
        logger.info(f"开始添加 {len(symbols)} 只股票...")

        client = get_longport_client()
        db_manager = get_db_manager()
        saved_count = 0

        with db_manager.get_session() as session:
            for symbol in symbols:
                # 检查是否已存在
                existing = session.query(StockInfo).filter_by(symbol=symbol).first()

                if existing:
                    logger.info(f"股票已存在: {symbol} - {existing.name}")
                    continue

                # 获取股票详细信息
                try:
                    static_info = client.get_static_info([symbol])
                    if static_info and len(static_info) > 0:
                        info = static_info[0]

                        # 创建股票信息
                        stock = StockInfo(
                            symbol=symbol,
                            name=info.name_cn if hasattr(info, 'name_cn') else info.name_en,
                            name_en=info.name_en if hasattr(info, 'name_en') else '',
                            market=market,
                            exchange=info.exchange if hasattr(info, 'exchange') else '',
                            currency=info.currency if hasattr(info, 'currency') else '',
                            lot_size=info.lot_size if hasattr(info, 'lot_size') else 100,
                            is_active=True,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )

                        session.add(stock)
                        saved_count += 1
                        logger.info(f"✓ 添加股票: {symbol} - {stock.name}")
                    else:
                        logger.warning(f"✗ 无法获取股票信息: {symbol}")

                except Exception as e:
                    logger.warning(f"✗ 获取股票 {symbol} 详细信息失败: {e}")
                    continue

        logger.info(f"成功添加 {saved_count} 只股票到数据库")
        return saved_count

    except Exception as e:
        logger.error(f"添加股票失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def fetch_stock_list(market='HK'):
    """
    获取股票列表（从自选股）

    Args:
        market: 市场代码（HK/US/CN）
    """
    try:
        logger.info(f"开始获取 {market} 市场的股票列表...")

        # 获取长桥客户端
        client = get_longport_client()

        # 获取自选股列表
        watch_list = client.get_watch_list()

        if not watch_list:
            logger.warning("自选股列表为空")
            logger.info("提示：您可以使用 --symbols 参数手动添加股票")
            return 0

        logger.info(f"获取到 {len(watch_list)} 个自选股分组")

        # 收集所有股票代码
        all_symbols = []
        for watch_group in watch_list:
            if hasattr(watch_group, 'securities'):
                for security in watch_group.securities:
                    all_symbols.append(security.symbol)

        logger.info(f"共找到 {len(all_symbols)} 只股票")

        if all_symbols:
            return add_stock_manually(all_symbols, market)
        else:
            logger.warning("未找到任何股票")
            return 0

    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='获取股票列表',
        epilog='''
示例:
  # 从自选股获取
  python fetch_stock_list.py --market HK

  # 手动添加港股
  python fetch_stock_list.py --symbols 700.HK 9988.HK 0001.HK --market HK

  # 手动添加美股
  python fetch_stock_list.py --symbols AAPL.US TSLA.US MSFT.US --market US
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--market', type=str, default='HK',
                       choices=['HK', 'US', 'CN'],
                       help='市场代码（HK/US/CN）')
    parser.add_argument('--symbols', type=str, nargs='+',
                       help='股票代码列表（如 700.HK 9988.HK）')

    args = parser.parse_args()
    
    try:
        # 加载配置
        config_loader = init_config()
        config = config_loader.config
        api_config = config_loader.api_config
        
        # 设置日志
        setup_logger(config)
        
        logger.info("=" * 60)
        logger.info(f"获取 {args.market} 市场股票列表")
        logger.info("=" * 60)
        
        # 初始化数据库
        db_manager = init_database(config)
        db_manager.create_tables()
        
        # 初始化长桥客户端
        init_longport_client(api_config)

        # 执行操作
        if args.symbols:
            # 手动添加股票
            saved = add_stock_manually(args.symbols, args.market)
            logger.info("=" * 60)
            logger.info(f"成功添加 {saved} 只股票！")
            logger.info("=" * 60)
        else:
            # 从自选股获取
            saved = fetch_stock_list(args.market)
            logger.info("=" * 60)
            if saved > 0:
                logger.info(f"成功获取 {saved} 只股票！")
            else:
                logger.info("提示：使用 --symbols 参数手动添加股票")
                logger.info("示例：python fetch_stock_list.py --symbols 700.HK 9988.HK --market HK")
            logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

