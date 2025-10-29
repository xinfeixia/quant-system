"""
清理重复的股票数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData, TechnicalIndicator, StockSelection
from loguru import logger


def clean_duplicate_stocks():
    """清理重复的股票数据"""
    # 初始化配置和数据库
    config_loader = init_config()
    config = config_loader.config
    db_manager = init_database(config)
    
    print("\n" + "=" * 60)
    print("清理重复股票数据")
    print("=" * 60)
    
    with db_manager.get_session() as session:
        # 查找所有股票
        all_stocks = session.query(StockInfo).all()
        
        # 按名称分组，找出重复的
        stock_dict = {}
        for stock in all_stocks:
            if stock.name not in stock_dict:
                stock_dict[stock.name] = []
            stock_dict[stock.name].append(stock)
        
        # 找出重复的股票
        duplicates = {name: stocks for name, stocks in stock_dict.items() if len(stocks) > 1}
        
        if not duplicates:
            print("✅ 没有发现重复的股票")
            return
        
        print(f"\n发现 {len(duplicates)} 组重复股票：\n")
        
        for name, stocks in duplicates.items():
            print(f"📊 {name}:")
            for stock in stocks:
                # 统计数据量
                daily_count = session.query(DailyData).filter_by(symbol=stock.symbol).count()
                indicator_count = session.query(TechnicalIndicator).filter_by(symbol=stock.symbol).count()
                print(f"  - {stock.symbol}: 日线数据 {daily_count} 条, 技术指标 {indicator_count} 条")
            
            # 保留数据最多的那个，删除其他的
            stocks_sorted = sorted(stocks, key=lambda s: (
                session.query(DailyData).filter_by(symbol=s.symbol).count(),
                len(s.symbol)  # 如果数据量相同，保留代码较短的（如0700.HK而不是700.HK）
            ), reverse=True)
            
            keep_stock = stocks_sorted[0]
            delete_stocks = stocks_sorted[1:]
            
            print(f"  ✅ 保留: {keep_stock.symbol}")
            
            for stock in delete_stocks:
                print(f"  ❌ 删除: {stock.symbol}")
                
                # 删除相关数据
                session.query(DailyData).filter_by(symbol=stock.symbol).delete()
                session.query(TechnicalIndicator).filter_by(symbol=stock.symbol).delete()
                session.query(StockSelection).filter_by(symbol=stock.symbol).delete()
                session.delete(stock)
            
            print()
        
        # 提交更改
        session.commit()
        
        print("=" * 60)
        print("✅ 清理完成！")
        print("=" * 60)


if __name__ == '__main__':
    clean_duplicate_stocks()

