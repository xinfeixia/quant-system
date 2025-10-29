"""
检查数据状态
快速查看各市场的数据完整性
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_database, get_db_manager
from database.models import StockInfo, DailyData, TechnicalIndicators, StockSelection
from utils.config_loader import init_config
from sqlalchemy import func


def check_market_data(market: str):
    """检查指定市场的数据状态"""
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 股票总数
        total_stocks = session.query(StockInfo).filter_by(market=market).count()
        
        # 有历史数据的股票数
        stocks_with_data = session.query(func.count(func.distinct(DailyData.symbol)))\
            .join(StockInfo, DailyData.symbol == StockInfo.symbol)\
            .filter(StockInfo.market == market)\
            .scalar()
        
        # 历史数据总条数
        total_daily_data = session.query(func.count(DailyData.id))\
            .join(StockInfo, DailyData.symbol == StockInfo.symbol)\
            .filter(StockInfo.market == market)\
            .scalar()
        
        # 有技术指标的股票数
        stocks_with_indicators = session.query(func.count(func.distinct(TechnicalIndicators.symbol)))\
            .join(StockInfo, TechnicalIndicators.symbol == StockInfo.symbol)\
            .filter(StockInfo.market == market)\
            .scalar()
        
        # 技术指标总条数
        total_indicators = session.query(func.count(TechnicalIndicators.id))\
            .join(StockInfo, TechnicalIndicators.symbol == StockInfo.symbol)\
            .filter(StockInfo.market == market)\
            .scalar()
        
        # 选股结果数
        selection_count = session.query(func.count(StockSelection.id))\
            .filter_by(market=market)\
            .scalar()
        
        # 最新选股时间
        latest_selection = session.query(func.max(StockSelection.created_at))\
            .filter_by(market=market)\
            .scalar()
        
        # 数据日期范围
        date_range = session.query(
            func.min(DailyData.trade_date),
            func.max(DailyData.trade_date)
        ).join(StockInfo, DailyData.symbol == StockInfo.symbol)\
         .filter(StockInfo.market == market)\
         .first()
        
        return {
            'total_stocks': total_stocks,
            'stocks_with_data': stocks_with_data,
            'total_daily_data': total_daily_data,
            'stocks_with_indicators': stocks_with_indicators,
            'total_indicators': total_indicators,
            'selection_count': selection_count,
            'latest_selection': latest_selection,
            'date_range': date_range
        }


def print_market_status(market: str, data: dict):
    """打印市场数据状态"""
    market_names = {
        'HK': '港股',
        'US': '美股',
        'CN': 'A股'
    }
    
    print(f"\n{'='*60}")
    print(f"{market_names.get(market, market)} 数据状态")
    print(f"{'='*60}")
    
    # 股票数据
    print(f"\n📊 股票数据:")
    print(f"  总股票数: {data['total_stocks']} 只")
    print(f"  有数据股票: {data['stocks_with_data']} 只 ({data['stocks_with_data']*100//data['total_stocks'] if data['total_stocks'] > 0 else 0}%)")
    print(f"  历史数据: {data['total_daily_data']:,} 条")
    
    if data['stocks_with_data'] > 0:
        avg_data = data['total_daily_data'] // data['stocks_with_data']
        print(f"  平均数据: {avg_data} 条/股票")
    
    # 日期范围
    if data['date_range'][0] and data['date_range'][1]:
        start_date = data['date_range'][0]
        end_date = data['date_range'][1]
        days = (end_date - start_date).days
        print(f"  日期范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} ({days}天)")
    
    # 技术指标
    print(f"\n📈 技术指标:")
    print(f"  有指标股票: {data['stocks_with_indicators']} 只")
    print(f"  指标数据: {data['total_indicators']:,} 条")
    
    if data['stocks_with_indicators'] > 0:
        avg_indicators = data['total_indicators'] // data['stocks_with_indicators']
        print(f"  平均指标: {avg_indicators} 条/股票")
    
    # 选股结果
    print(f"\n🎯 选股结果:")
    print(f"  选股数量: {data['selection_count']} 只")
    if data['latest_selection']:
        print(f"  最新时间: {data['latest_selection'].strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"  最新时间: 无")
    
    # 状态评估
    print(f"\n✅ 完整性评估:")
    
    # 历史数据完整性
    data_completeness = data['stocks_with_data'] * 100 // data['total_stocks'] if data['total_stocks'] > 0 else 0
    if data_completeness >= 90:
        print(f"  历史数据: ✅ 优秀 ({data_completeness}%)")
    elif data_completeness >= 70:
        print(f"  历史数据: ⚠️  良好 ({data_completeness}%)")
    else:
        print(f"  历史数据: ❌ 不足 ({data_completeness}%)")
    
    # 技术指标完整性
    indicator_completeness = data['stocks_with_indicators'] * 100 // data['total_stocks'] if data['total_stocks'] > 0 else 0
    if indicator_completeness >= 90:
        print(f"  技术指标: ✅ 优秀 ({indicator_completeness}%)")
    elif indicator_completeness >= 70:
        print(f"  技术指标: ⚠️  良好 ({indicator_completeness}%)")
    else:
        print(f"  技术指标: ❌ 不足 ({indicator_completeness}%)")
    
    # 选股结果
    if data['selection_count'] > 0:
        print(f"  选股结果: ✅ 已生成")
    else:
        print(f"  选股结果: ❌ 未生成")


def main():
    parser = argparse.ArgumentParser(description='检查数据状态')
    parser.add_argument('--market', type=str, choices=['HK', 'US', 'CN', 'ALL'],
                       default='ALL', help='市场代码（默认ALL=全部）')
    
    args = parser.parse_args()
    
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    
    print("\n" + "="*60)
    print("数据状态检查")
    print("="*60)
    
    markets = ['HK', 'US', 'CN'] if args.market == 'ALL' else [args.market]
    
    total_stats = {
        'total_stocks': 0,
        'stocks_with_data': 0,
        'total_daily_data': 0,
        'stocks_with_indicators': 0,
        'total_indicators': 0,
        'selection_count': 0
    }
    
    for market in markets:
        data = check_market_data(market)
        print_market_status(market, data)
        
        # 累计统计
        total_stats['total_stocks'] += data['total_stocks']
        total_stats['stocks_with_data'] += data['stocks_with_data']
        total_stats['total_daily_data'] += data['total_daily_data']
        total_stats['stocks_with_indicators'] += data['stocks_with_indicators']
        total_stats['total_indicators'] += data['total_indicators']
        total_stats['selection_count'] += data['selection_count']
    
    # 总计
    if len(markets) > 1:
        print(f"\n{'='*60}")
        print(f"总计")
        print(f"{'='*60}")
        print(f"\n📊 总体数据:")
        print(f"  总股票数: {total_stats['total_stocks']} 只")
        print(f"  有数据股票: {total_stats['stocks_with_data']} 只 ({total_stats['stocks_with_data']*100//total_stats['total_stocks'] if total_stats['total_stocks'] > 0 else 0}%)")
        print(f"  历史数据: {total_stats['total_daily_data']:,} 条")
        print(f"  技术指标: {total_stats['total_indicators']:,} 条")
        print(f"  选股结果: {total_stats['selection_count']} 只")
    
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    main()

