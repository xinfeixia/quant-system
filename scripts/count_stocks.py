"""
快速查询股票数量
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from sqlalchemy import func


def main():
    """主函数"""
    try:
        # 加载配置
        config_loader = init_config()
        config = config_loader.config
        
        # 初始化数据库
        init_database(config)
        db_manager = get_db_manager()
        
        print("\n" + "=" * 60)
        print("📊 股票数量统计")
        print("=" * 60 + "\n")
        
        with db_manager.get_session() as session:
            # 统计各市场股票数量
            markets = ['HK', 'US', 'CN']
            total = 0
            
            for market in markets:
                count = session.query(StockInfo).filter_by(
                    market=market,
                    is_active=True
                ).count()
                
                if count > 0:
                    # 统计有数据的股票
                    stocks_with_data = session.query(StockInfo).filter(
                        StockInfo.market == market,
                        StockInfo.is_active == True,
                        StockInfo.symbol.in_(
                            session.query(DailyData.symbol).distinct()
                        )
                    ).count()
                    
                    print(f"  {market:4s} 市场: {count:3d} 只股票 (有数据: {stocks_with_data} 只)")
                    total += count
            
            print(f"\n  {'总计':4s}      : {total:3d} 只股票")
            
            # 统计数据条数
            data_count = session.query(func.count(DailyData.id)).scalar()
            print(f"\n  历史数据: {data_count:,} 条")
            
            if total > 0 and data_count > 0:
                avg = data_count // total
                print(f"  平均每只: {avg} 条数据")
        
        print("\n" + "=" * 60 + "\n")
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

