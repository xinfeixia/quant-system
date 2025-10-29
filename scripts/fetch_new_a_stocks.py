"""
获取新增A股的历史数据
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo, DailyData
from data_collection.tushare_client import TushareClient
from utils.config_loader import init_config, get_config_loader
from datetime import datetime, timedelta
from loguru import logger
import time


# 新增的19只股票
NEW_STOCKS = [
    ('601009.SH', '南京银行'),
    ('600015.SH', '华夏银行'),
    ('601169.SH', '北京银行'),
    ('601066.SH', '中信建投'),
    ('600999.SH', '招商证券'),
    ('601211.SH', '国泰君安'),
    ('600958.SH', '东方证券'),
    ('601319.SH', '中国人保'),
    ('600340.SH', '华夏幸福'),
    ('000596.SZ', '古井贡酒'),
    ('000799.SZ', '酒鬼酒'),
    ('603369.SH', '今世缘'),
    ('603392.SH', '万泰生物'),
    ('600600.SH', '青岛啤酒'),
    ('000895.SZ', '双汇发展'),
    ('000921.SZ', '海信家电'),
    ('000625.SZ', '长安汽车'),
    ('601238.SH', '广汽集团'),
    ('600150.SH', '中国船舶'),
]


def get_tushare_client():
    """获取Tushare客户端"""
    config_loader = get_config_loader()
    api_config = config_loader.api_config
    
    token = api_config.get('tushare', {}).get('token')
    request_interval = api_config.get('tushare', {}).get('request_interval', 2.5)
    
    return TushareClient(token=token, request_interval=request_interval)


def fetch_stock_data(symbol: str, name: str, days: int = 365):
    """获取单只股票的历史数据"""
    client = get_tushare_client()
    db_manager = get_db_manager()
    
    # 计算日期范围
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    logger.info(f"开始获取 {symbol} - {name} 的历史数据...")
    
    try:
        # 获取数据
        daily_data_list = client.get_daily_data(symbol, start_datetime, end_datetime)
        logger.info(f"获取到 {len(daily_data_list)} 条数据")
        
        # 保存到数据库
        saved_count = 0
        with db_manager.get_session() as session:
            for data in daily_data_list:
                # 检查是否已存在
                existing = session.query(DailyData).filter_by(
                    symbol=symbol,
                    trade_date=data['trade_date']
                ).first()
                
                if existing:
                    continue
                
                # 创建新记录
                daily_data = DailyData(**data)
                session.add(daily_data)
                saved_count += 1
            
            session.commit()
        
        logger.info(f"✅ {symbol} - {name}: 保存 {saved_count} 条新数据")
        return True, saved_count
        
    except Exception as e:
        logger.error(f"❌ {symbol} - {name}: 获取失败 - {e}")
        return False, 0


def main():
    """主函数"""
    # 初始化
    init_config()
    config_loader = get_config_loader()
    init_database(config_loader.config)
    
    logger.info("=" * 60)
    logger.info("获取新增A股的历史数据")
    logger.info("=" * 60)
    logger.info(f"股票数量: {len(NEW_STOCKS)}")
    logger.info(f"获取天数: 365")
    logger.info("=" * 60)
    
    success_count = 0
    fail_count = 0
    total_saved = 0
    
    start_time = time.time()
    
    for i, (symbol, name) in enumerate(NEW_STOCKS, 1):
        logger.info(f"\n[{i}/{len(NEW_STOCKS)}] {symbol} - {name}")
        logger.info("-" * 60)
        
        success, saved = fetch_stock_data(symbol, name, days=365)
        
        if success:
            success_count += 1
            total_saved += saved
        else:
            fail_count += 1
        
        # 显示进度
        elapsed = time.time() - start_time
        avg_time = elapsed / i
        remaining = avg_time * (len(NEW_STOCKS) - i)
        
        logger.info(f"进度: {i}/{len(NEW_STOCKS)} ({i*100//len(NEW_STOCKS)}%)")
        logger.info(f"成功: {success_count}, 失败: {fail_count}, 总保存: {total_saved}条")
        logger.info(f"已用时: {elapsed:.1f}秒, 预计剩余: {remaining:.1f}秒")
    
    # 最终统计
    total_time = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("✅ 数据获取完成！")
    logger.info("=" * 60)
    logger.info(f"成功: {success_count}/{len(NEW_STOCKS)}")
    logger.info(f"失败: {fail_count}/{len(NEW_STOCKS)}")
    logger.info(f"总保存: {total_saved} 条数据")
    logger.info(f"总用时: {total_time/60:.1f} 分钟")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

