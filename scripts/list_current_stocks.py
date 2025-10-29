"""
查看当前数据库中的股票列表
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo
from utils.config_loader import init_config, get_config_loader


def list_stocks_by_market():
    """按市场列出股票"""
    # 初始化
    init_config()
    config_loader = get_config_loader()
    init_database(config_loader.config)
    
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 按市场分组统计
        markets = ['HK', 'US', 'CN']
        
        for market in markets:
            stocks = session.query(StockInfo).filter_by(market=market).order_by(StockInfo.symbol).all()
            
            print(f"\n{'='*80}")
            print(f"{market}股 - 共 {len(stocks)} 只")
            print(f"{'='*80}")
            
            if market == 'CN':
                # A股详细列出
                for i, stock in enumerate(stocks, 1):
                    print(f"{i:3d}. {stock.symbol:<12} {stock.name:<15} {stock.exchange}")
            else:
                # 港股和美股只显示数量
                print(f"共 {len(stocks)} 只股票")
                if len(stocks) <= 20:
                    for i, stock in enumerate(stocks, 1):
                        print(f"{i:3d}. {stock.symbol:<12} {stock.name:<15} {stock.exchange}")


if __name__ == '__main__':
    list_stocks_by_market()

