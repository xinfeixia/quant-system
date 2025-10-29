"""
检查A股数据的价格和日期
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo, DailyData
from datetime import datetime, timedelta
from loguru import logger
from utils.config_loader import init_config, get_config_loader


def check_stock_data(symbol: str, name: str):
    """检查单只股票的数据"""
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 查询最近10天的数据
        data = session.query(DailyData).filter(
            DailyData.symbol == symbol
        ).order_by(DailyData.trade_date.desc()).limit(10).all()
        
        if not data:
            print(f"\n{symbol} - {name}: 无数据")
            return
        
        print(f"\n{symbol} - {name}")
        print("=" * 80)
        print(f"{'日期':<12} {'开盘':<10} {'最高':<10} {'最低':<10} {'收盘':<10} {'成交量':<15}")
        print("-" * 80)
        
        for d in data:
            print(f"{d.trade_date.strftime('%Y-%m-%d'):<12} "
                  f"{d.open:<10.2f} {d.high:<10.2f} {d.low:<10.2f} "
                  f"{d.close:<10.2f} {d.volume:<15,}")
        
        # 显示日期范围
        all_data = session.query(DailyData).filter(
            DailyData.symbol == symbol
        ).order_by(DailyData.trade_date).all()
        
        if all_data:
            print(f"\n总数据条数: {len(all_data)}")
            print(f"日期范围: {all_data[0].trade_date} 至 {all_data[-1].trade_date}")
            print(f"最新收盘价: {all_data[-1].close:.2f}")


def main():
    """主函数"""
    # 加载配置并初始化数据库
    init_config()
    config_loader = get_config_loader()
    init_database(config_loader.config)

    db_manager = get_db_manager()
    
    # 获取几只代表性的A股
    test_stocks = [
        ('000001.SZ', '平安银行'),
        ('600519.SH', '贵州茅台'),
        ('000858.SZ', '五粮液'),
        ('300750.SZ', '宁德时代'),
        ('601318.SH', '中国平安'),
    ]
    
    print("=" * 80)
    print("检查A股数据的价格和日期")
    print("=" * 80)
    
    for symbol, name in test_stocks:
        check_stock_data(symbol, name)
    
    # 检查今天的日期
    print("\n" + "=" * 80)
    print(f"当前系统日期: {datetime.now().date()}")
    print("=" * 80)


if __name__ == '__main__':
    main()

