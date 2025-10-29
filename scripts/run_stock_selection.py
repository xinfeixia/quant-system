"""
运行选股分析
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
from database.models import StockInfo, DailyData, TechnicalIndicator, StockSelection
from analysis.scoring_engine import ScoringEngine
from loguru import logger


def analyze_stock(symbol, name):
    """
    分析单只股票
    
    Args:
        symbol: 股票代码
        name: 股票名称
        
    Returns:
        dict: 评分结果
    """
    try:
        db_manager = get_db_manager()
        
        # 获取历史数据和技术指标
        with db_manager.get_session() as session:
            # 获取最近60天的数据
            daily_data = session.query(DailyData).filter_by(
                symbol=symbol
            ).order_by(DailyData.trade_date.desc()).limit(60).all()
            
            if not daily_data or len(daily_data) < 20:
                logger.warning(f"{symbol} 数据不足（少于20天）")
                return None
            
            # 反转顺序（从旧到新）
            daily_data = list(reversed(daily_data))
            
            # 获取技术指标
            indicators = session.query(TechnicalIndicator).filter_by(
                symbol=symbol
            ).order_by(TechnicalIndicator.trade_date.desc()).limit(60).all()
            
            indicators = list(reversed(indicators))
            indicator_dict = {ind.trade_date: ind for ind in indicators}
            
            # 构建DataFrame
            data = []
            for d in daily_data:
                ind = indicator_dict.get(d.trade_date)
                
                row = {
                    'date': d.trade_date,
                    'open': d.open,
                    'high': d.high,
                    'low': d.low,
                    'close': d.close,
                    'volume': d.volume
                }
                
                if ind:
                    row.update({
                        'ma5': ind.ma5,
                        'ma10': ind.ma10,
                        'ma20': ind.ma20,
                        'ma60': ind.ma60,
                        'macd': ind.macd,
                        'macd_signal': ind.macd_signal,
                        'macd_hist': ind.macd_hist,
                        'rsi': ind.rsi,
                        'kdj_k': ind.kdj_k,
                        'kdj_d': ind.kdj_d,
                        'kdj_j': ind.kdj_j,
                        'boll_upper': ind.boll_upper,
                        'boll_middle': ind.boll_middle,
                        'boll_lower': ind.boll_lower,
                        'volume_ma5': ind.volume_ma5,
                        'volume_ma10': ind.volume_ma10,
                    })
                
                data.append(row)
            
            df = pd.DataFrame(data)
            df.set_index('date', inplace=True)
        
        # 计算评分
        engine = ScoringEngine(df)
        scores = engine.calculate_total_score()
        
        # 添加股票信息
        scores['symbol'] = symbol
        scores['name'] = name
        scores['latest_price'] = float(df.iloc[-1]['close'])
        scores['latest_date'] = df.index[-1]
        
        return scores
        
    except Exception as e:
        logger.error(f"分析 {symbol} 失败: {e}")
        return None


def run_stock_selection(market='HK', min_score=50, top_n=50, hk_connect_only=False):
    """
    运行选股分析

    Args:
        market: 市场代码
        min_score: 最低分数
        top_n: 返回前N只股票
        hk_connect_only: 是否只选港股通标的（仅对HK市场有效）
    """
    try:
        logger.info(f"开始选股分析 - 市场:{market}, 最低分:{min_score}, Top:{top_n}, 港股通:{hk_connect_only}")

        db_manager = get_db_manager()

        # 获取股票列表
        stock_list = []
        with db_manager.get_session() as session:
            # 构建查询条件
            query = session.query(StockInfo).filter_by(
                market=market,
                is_active=True
            )

            # 如果是港股且只选港股通标的
            if market == 'HK' and hk_connect_only:
                query = query.filter_by(is_hk_connect=True)

            stocks = query.all()

            for stock in stocks:
                stock_list.append({
                    'symbol': stock.symbol,
                    'name': stock.name
                })

        logger.info(f"找到 {len(stock_list)} 只股票")
        
        # 分析所有股票
        results = []
        for i, stock_info in enumerate(stock_list, 1):
            symbol = stock_info['symbol']
            name = stock_info['name']
            
            logger.info(f"[{i}/{len(stock_list)}] 分析 {symbol} - {name}")
            
            scores = analyze_stock(symbol, name)
            
            if scores and scores['total_score'] >= min_score:
                results.append(scores)
        
        # 按总分排序
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 取前N只
        top_stocks = results[:top_n]
        
        logger.info(f"选股完成！共 {len(results)} 只股票达到最低分，返回Top {len(top_stocks)}")
        
        # 保存到数据库
        save_selection_results(top_stocks, market)
        
        # 显示结果
        display_results(top_stocks)
        
        return top_stocks
        
    except Exception as e:
        logger.error(f"选股分析失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def save_selection_results(results, market):
    """保存选股结果到数据库"""
    try:
        db_manager = get_db_manager()
        
        with db_manager.get_session() as session:
            # 删除旧的选股结果
            session.query(StockSelection).filter_by(market=market).delete()
            
            # 保存新结果
            for i, result in enumerate(results, 1):
                selection = StockSelection(
                    symbol=result['symbol'],
                    name=result['name'],
                    market=market,
                    total_score=result['total_score'],
                    technical_score=result['technical_score'],
                    volume_score=result['volume_score'],
                    trend_score=result['trend_score'],
                    pattern_score=result['pattern_score'],
                    latest_price=result['latest_price'],
                    rank=i,
                    selection_date=datetime.now().date(),
                    created_at=datetime.now()
                )
                session.add(selection)
        
        logger.info(f"保存 {len(results)} 条选股结果到数据库")
        
    except Exception as e:
        logger.error(f"保存选股结果失败: {e}")
        raise


def display_results(results):
    """显示选股结果"""
    print("\n" + "=" * 100)
    print("📊 选股结果")
    print("=" * 100)
    print(f"{'排名':<6s} {'代码':<12s} {'名称':<20s} {'总分':>6s} {'技术':>6s} {'量价':>6s} {'趋势':>6s} {'形态':>6s} {'最新价':>10s}")
    print("-" * 100)
    
    for i, result in enumerate(results, 1):
        print(f"{i:<6d} {result['symbol']:<12s} {result['name']:<20s} "
              f"{result['total_score']:>6.1f} "
              f"{result['technical_score']:>6.1f} "
              f"{result['volume_score']:>6.1f} "
              f"{result['trend_score']:>6.1f} "
              f"{result['pattern_score']:>6.1f} "
              f"{result['latest_price']:>10.2f}")
    
    print("=" * 100)
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='运行选股分析',
        epilog='''
示例:
  # 选出港股Top 50
  python run_stock_selection.py --market HK --top 50
  
  # 选出分数>=60的股票
  python run_stock_selection.py --market HK --min-score 60
  
  # 选出Top 100
  python run_stock_selection.py --market HK --top 100
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--market', type=str, default='HK',
                       choices=['HK', 'US', 'CN'],
                       help='市场代码')
    parser.add_argument('--min-score', type=float, default=50,
                       help='最低分数（默认50）')
    parser.add_argument('--top', type=int, default=50,
                       help='返回前N只股票（默认50）')
    parser.add_argument('--hk-connect-only', action='store_true',
                       help='只选港股通标的（仅对HK市场有效）')
    
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
        logger.info("运行选股分析")
        logger.info("=" * 60)
        
        # 初始化数据库
        db_manager = init_database(config)
        
        # 运行选股
        results = run_stock_selection(
            market=args.market,
            min_score=args.min_score,
            top_n=args.top,
            hk_connect_only=args.hk_connect_only
        )
        
        logger.info("=" * 60)
        logger.info("选股分析完成！")
        logger.info("=" * 60)
        
        print("\n💡 下一步:")
        print(f"  1. 查看Web界面: http://localhost:5000/api/selections?market={args.market}")
        print(f"  2. 查看K线图: http://localhost:5000/kline")
        print()
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

