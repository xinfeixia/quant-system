"""
检查数据获取情况
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from sqlalchemy import func
from loguru import logger


def check_data_status():
    """检查数据获取状态"""
    try:
        db_manager = get_db_manager()
        
        print("=" * 80)
        print("📊 数据获取情况检查")
        print("=" * 80)
        print()
        
        with db_manager.get_session() as session:
            # 1. 检查股票数量
            print("📈 股票数量统计:")
            print("-" * 80)
            
            markets = ['HK', 'US', 'CN']
            total_stocks = 0
            
            for market in markets:
                count = session.query(StockInfo).filter_by(
                    market=market,
                    is_active=True
                ).count()
                if count > 0:
                    print(f"  {market:4s} 市场: {count:3d} 只股票")
                    total_stocks += count
            
            print(f"  {'总计':4s}      : {total_stocks:3d} 只股票")
            print()
            
            if total_stocks == 0:
                print("⚠️  没有股票数据！请先运行 fetch_stock_list.py")
                return
            
            # 2. 检查每只股票的数据情况
            print("📊 历史数据统计:")
            print("-" * 80)
            print(f"{'代码':<12s} {'名称':<20s} {'数据条数':>8s} {'最早日期':>12s} {'最新日期':>12s}")
            print("-" * 80)
            
            stocks = session.query(StockInfo).filter_by(is_active=True).all()
            
            stocks_with_data = 0
            stocks_without_data = 0
            total_records = 0
            
            for stock in stocks:
                # 查询该股票的数据条数
                data_count = session.query(DailyData).filter_by(
                    symbol=stock.symbol
                ).count()
                
                if data_count > 0:
                    # 获取最早和最新日期
                    earliest = session.query(func.min(DailyData.trade_date)).filter_by(
                        symbol=stock.symbol
                    ).scalar()
                    
                    latest = session.query(func.max(DailyData.trade_date)).filter_by(
                        symbol=stock.symbol
                    ).scalar()
                    
                    print(f"{stock.symbol:<12s} {stock.name:<20s} {data_count:>8d} {str(earliest):>12s} {str(latest):>12s}")
                    stocks_with_data += 1
                    total_records += data_count
                else:
                    print(f"{stock.symbol:<12s} {stock.name:<20s} {'无数据':>8s} {'-':>12s} {'-':>12s}")
                    stocks_without_data += 1
            
            print("-" * 80)
            print()
            
            # 3. 总结
            print("📋 数据总结:")
            print("-" * 80)
            print(f"  总股票数量: {total_stocks} 只")
            print(f"  有数据股票: {stocks_with_data} 只 ✅")
            print(f"  无数据股票: {stocks_without_data} 只 ⚠️")
            print(f"  总数据条数: {total_records} 条")
            
            if total_records > 0:
                print(f"  平均每只股票: {total_records // stocks_with_data if stocks_with_data > 0 else 0} 条数据")
            
            print()
            
            # 4. 建议
            if stocks_without_data > 0:
                print("💡 建议:")
                print("-" * 80)
                print(f"  还有 {stocks_without_data} 只股票没有历史数据")
                print(f"  运行以下命令获取数据:")
                print(f"  python scripts/fetch_historical_data.py --batch --market HK --limit {stocks_without_data}")
                print()
            else:
                print("✅ 所有股票都已获取历史数据！")
                print()
                print("🚀 下一步建议:")
                print("-" * 80)
                print("  1. 开发技术指标计算模块")
                print("  2. 创建K线图表可视化")
                print("  3. 实现选股评分系统")
                print()
            
            print("=" * 80)
            
    except Exception as e:
        logger.error(f"检查数据失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    try:
        # 加载配置
        config_loader = init_config()
        config = config_loader.config
        
        # 设置日志（只输出到控制台）
        from loguru import logger
        logger.remove()
        logger.add(sys.stdout, level="ERROR")
        
        # 初始化数据库
        db_manager = init_database(config)
        
        # 检查数据
        check_data_status()
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

