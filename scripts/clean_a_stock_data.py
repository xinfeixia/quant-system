"""
清理A股错误数据
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo, DailyData, TechnicalIndicator, StockSelection
from utils.config_loader import init_config, get_config_loader
from loguru import logger


def clean_a_stock_data():
    """清理A股数据"""
    # 初始化
    init_config()
    config_loader = get_config_loader()
    init_database(config_loader.config)
    
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 获取所有A股代码
        cn_stocks = session.query(StockInfo).filter_by(market='CN').all()
        cn_symbols = [s.symbol for s in cn_stocks]
        
        logger.info(f"找到 {len(cn_symbols)} 只A股")
        
        # 删除A股的日线数据
        deleted_daily = session.query(DailyData).filter(
            DailyData.symbol.in_(cn_symbols)
        ).delete(synchronize_session=False)
        
        logger.info(f"删除 {deleted_daily} 条A股日线数据")
        
        # 删除A股的技术指标
        deleted_indicators = session.query(TechnicalIndicator).filter(
            TechnicalIndicator.symbol.in_(cn_symbols)
        ).delete(synchronize_session=False)
        
        logger.info(f"删除 {deleted_indicators} 条A股技术指标数据")
        
        # 删除A股的选股结果
        deleted_selections = session.query(StockSelection).filter(
            StockSelection.symbol.in_(cn_symbols)
        ).delete(synchronize_session=False)
        
        logger.info(f"删除 {deleted_selections} 条A股选股结果")
        
        session.commit()
        
        logger.info("✅ A股数据清理完成！")
        logger.info("\n下一步：重新获取A股数据")
        logger.info("python scripts/fetch_a_stocks_tushare.py --days 365")


if __name__ == '__main__':
    clean_a_stock_data()

