"""
计算技术指标脚本
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData, TechnicalIndicator
from analysis.technical_indicators import TechnicalIndicators
from loguru import logger


def calculate_stock_indicators(symbol, save_to_db=True):
    """
    计算单只股票的技术指标
    
    Args:
        symbol: 股票代码
        save_to_db: 是否保存到数据库
        
    Returns:
        DataFrame with indicators
    """
    try:
        logger.info(f"开始计算 {symbol} 的技术指标...")
        
        db_manager = get_db_manager()
        
        # 获取历史数据
        with db_manager.get_session() as session:
            daily_data = session.query(DailyData).filter_by(
                symbol=symbol
            ).order_by(DailyData.trade_date).all()
            
            if not daily_data:
                logger.warning(f"{symbol} 没有历史数据")
                return None
            
            # 转换为DataFrame
            data = []
            for d in daily_data:
                data.append({
                    'trade_date': d.trade_date,
                    'open': d.open,
                    'high': d.high,
                    'low': d.low,
                    'close': d.close,
                    'volume': d.volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('trade_date', inplace=True)
        
        logger.info(f"获取到 {len(df)} 条历史数据")
        
        # 计算技术指标
        ti = TechnicalIndicators(df)
        df_with_indicators = ti.calculate_all()
        
        logger.info(f"技术指标计算完成")
        
        # 保存到数据库
        if save_to_db:
            saved_count = 0
            with db_manager.get_session() as session:
                for date, row in df_with_indicators.iterrows():
                    # 检查是否已存在
                    existing = session.query(TechnicalIndicator).filter_by(
                        symbol=symbol,
                        trade_date=date
                    ).first()
                    
                    if existing:
                        # 更新
                        for col in df_with_indicators.columns:
                            if col not in ['open', 'high', 'low', 'close', 'volume']:
                                setattr(existing, col, row.get(col))
                    else:
                        # 插入
                        indicator = TechnicalIndicator(
                            symbol=symbol,
                            trade_date=date,
                            ma5=row.get('ma5'),
                            ma10=row.get('ma10'),
                            ma20=row.get('ma20'),
                            ma60=row.get('ma60'),
                            ema12=row.get('ema12'),
                            ema26=row.get('ema26'),
                            macd=row.get('macd'),
                            macd_signal=row.get('macd_signal'),
                            macd_hist=row.get('macd_hist'),
                            rsi=row.get('rsi'),
                            kdj_k=row.get('kdj_k'),
                            kdj_d=row.get('kdj_d'),
                            kdj_j=row.get('kdj_j'),
                            boll_upper=row.get('boll_upper'),
                            boll_middle=row.get('boll_middle'),
                            boll_lower=row.get('boll_lower'),
                            atr=row.get('atr'),
                            obv=row.get('obv'),
                            volume_ma5=row.get('volume_ma5'),
                            volume_ma10=row.get('volume_ma10'),
                            created_at=datetime.now()
                        )
                        session.add(indicator)
                        saved_count += 1
            
            logger.info(f"保存 {saved_count} 条技术指标到数据库")
        
        # 显示最新指标
        latest = ti.get_latest_indicators()
        logger.info(f"最新指标 ({df_with_indicators.index[-1]}):")
        logger.info(f"  MA5: {latest.get('ma5'):.2f}, MA10: {latest.get('ma10'):.2f}, MA20: {latest.get('ma20'):.2f}")
        logger.info(f"  MACD: {latest.get('macd'):.4f}, Signal: {latest.get('macd_signal'):.4f}")
        logger.info(f"  RSI: {latest.get('rsi'):.2f}")
        logger.info(f"  KDJ: K={latest.get('kdj_k'):.2f}, D={latest.get('kdj_d'):.2f}, J={latest.get('kdj_j'):.2f}")
        
        return df_with_indicators
        
    except Exception as e:
        logger.error(f"计算 {symbol} 技术指标失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_batch_indicators(market='HK', limit=None):
    """
    批量计算技术指标
    
    Args:
        market: 市场代码
        limit: 数量限制
    """
    try:
        logger.info(f"开始批量计算 {market} 市场的技术指标...")
        
        db_manager = get_db_manager()
        
        # 获取股票列表
        stock_list = []
        with db_manager.get_session() as session:
            query = session.query(StockInfo).filter_by(
                market=market,
                is_active=True
            )
            
            if limit:
                query = query.limit(limit)
            
            stocks = query.all()
            
            for stock in stocks:
                stock_list.append({
                    'symbol': stock.symbol,
                    'name': stock.name
                })
        
        if not stock_list:
            logger.warning(f"{market} 市场没有股票数据")
            return
        
        logger.info(f"找到 {len(stock_list)} 只股票")
        
        success_count = 0
        
        for i, stock_info in enumerate(stock_list, 1):
            symbol = stock_info['symbol']
            name = stock_info['name']
            
            logger.info(f"[{i}/{len(stock_list)}] 处理 {symbol} - {name}")
            
            result = calculate_stock_indicators(symbol, save_to_db=True)
            
            if result is not None:
                success_count += 1
        
        logger.info(f"批量计算完成！成功: {success_count}/{len(stock_list)}")
        
    except Exception as e:
        logger.error(f"批量计算技术指标失败: {e}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='计算技术指标',
        epilog='''
示例:
  # 计算单只股票
  python calculate_indicators.py --symbol 700.HK
  
  # 批量计算港股
  python calculate_indicators.py --batch --market HK
  
  # 批量计算指定数量
  python calculate_indicators.py --batch --market HK --limit 10
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--symbol', type=str, help='股票代码')
    parser.add_argument('--batch', action='store_true', help='批量模式')
    parser.add_argument('--market', type=str, default='HK',
                       choices=['HK', 'US', 'CN'],
                       help='市场代码（批量模式）')
    parser.add_argument('--limit', type=int, help='批量模式下的数量限制')
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        project_root = Path(__file__).parent.parent
        config_dir = str(project_root / 'config')
        config_loader = init_config(config_dir=config_dir)
        config = config_loader.config
        
        # 设置日志
        setup_logger(config)
        
        logger.info("=" * 60)
        logger.info("计算技术指标")
        logger.info("=" * 60)
        
        # 初始化数据库
        db_manager = init_database(config)
        
        # 执行计算
        if args.batch:
            # 批量模式
            calculate_batch_indicators(
                market=args.market,
                limit=args.limit
            )
        elif args.symbol:
            # 单只股票模式
            calculate_stock_indicators(args.symbol, save_to_db=True)
        else:
            logger.error("请指定 --symbol 或使用 --batch 模式")
            parser.print_help()
            sys.exit(1)
        
        logger.info("=" * 60)
        logger.info("技术指标计算完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

