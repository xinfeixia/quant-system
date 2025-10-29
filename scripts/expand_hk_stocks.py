"""
扩充港股股票列表 - 添加更多港股
包括：恒生指数、国企指数、红筹指数、港股通等
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from database import init_database, get_db_manager
from database.models import StockInfo
from data_collection.longport_client import init_longport_client, get_longport_client
from loguru import logger


# 恒生指数成分股（82只）
HSI_STOCKS = [
    '0001.HK', '0002.HK', '0003.HK', '0005.HK', '0006.HK', '0011.HK', '0012.HK', '0016.HK',
    '0017.HK', '0027.HK', '0066.HK', '0101.HK', '0175.HK', '0241.HK', '0267.HK', '0288.HK',
    '0291.HK', '0316.HK', '0322.HK', '0386.HK', '0388.HK', '0669.HK', '0688.HK', '0700.HK',
    '0762.HK', '0823.HK', '0857.HK', '0883.HK', '0939.HK', '0941.HK', '0960.HK', '0968.HK',
    '0981.HK', '0992.HK', '1038.HK', '1044.HK', '1093.HK', '1109.HK', '1113.HK', '1177.HK',
    '1211.HK', '1299.HK', '1398.HK', '1810.HK', '1876.HK', '1928.HK', '1997.HK', '2007.HK',
    '2020.HK', '2269.HK', '2313.HK', '2318.HK', '2319.HK', '2331.HK', '2382.HK', '2388.HK',
    '2628.HK', '3690.HK', '3968.HK', '3988.HK', '6098.HK', '6862.HK', '9618.HK', '9633.HK',
    '9888.HK', '9988.HK', '9999.HK',
    # 新增的恒指成分股
    '0868.HK', '1024.HK', '1347.HK', '1801.HK', '2015.HK', '2333.HK', '6185.HK', '9626.HK',
    '9866.HK', '9868.HK', '9863.HK', '0522.HK', '1928.HK', '6618.HK',
]

# 国企指数成分股（50只）
HSCEI_STOCKS = [
    '0386.HK', '0388.HK', '0688.HK', '0700.HK', '0857.HK', '0883.HK', '0939.HK', '0941.HK',
    '0960.HK', '0981.HK', '1038.HK', '1093.HK', '1109.HK', '1177.HK', '1211.HK', '1398.HK',
    '1810.HK', '2007.HK', '2020.HK', '2269.HK', '2313.HK', '2318.HK', '2319.HK', '2331.HK',
    '2382.HK', '2628.HK', '3690.HK', '3968.HK', '3988.HK', '6098.HK', '6862.HK', '9618.HK',
    '9633.HK', '9888.HK', '9988.HK', '9999.HK',
    # 新增
    '0762.HK', '0728.HK', '1347.HK', '2333.HK', '3800.HK', '6030.HK', '9626.HK', '9866.HK',
    '9868.HK', '1801.HK', '2015.HK', '6185.HK', '9863.HK', '0522.HK',
]

# 科技股（互联网、软件、半导体等）
TECH_STOCKS = [
    '0700.HK', '9988.HK', '3690.HK', '9618.HK', '9999.HK', '1810.HK', '1024.HK', '9626.HK',
    '0981.HK', '1347.HK', '0522.HK', '0763.HK', '0992.HK', '2382.HK', '0285.HK', '0669.HK',
    '9698.HK', '9888.HK', '9901.HK', '0772.HK', '2013.HK', '0909.HK', '9961.HK', '0020.HK',
    '6690.HK', '2018.HK',
]

# 新能源与电动车
EV_STOCKS = [
    '1211.HK', '0175.HK', '2333.HK', '9866.HK', '9868.HK', '2015.HK', '9863.HK', '0285.HK',
    '6862.HK', '3800.HK', '0968.HK', '0868.HK', '1772.HK', '2238.HK', '1458.HK',
]

# 医药生物
PHARMA_STOCKS = [
    '1177.HK', '1801.HK', '2269.HK', '6185.HK', '9688.HK', '9926.HK', '2196.HK', '1093.HK',
    '0853.HK', '1066.HK', '1530.HK', '2359.HK', '6160.HK', '1952.HK', '1833.HK', '0867.HK',
]

# 消费零售
CONSUMER_STOCKS = [
    '9633.HK', '2319.HK', '0151.HK', '0322.HK', '1044.HK', '9896.HK', '9987.HK', '6862.HK',
    '2020.HK', '2331.HK', '2313.HK', '1876.HK', '0291.HK', '0288.HK', '1458.HK', '6060.HK',
]

# 金融保险
FINANCE_STOCKS = [
    '0388.HK', '2318.HK', '1299.HK', '2628.HK', '6060.HK', '2328.HK', '6030.HK', '1658.HK',
    '0005.HK', '0011.HK', '0023.HK', '0939.HK', '1398.HK', '3988.HK', '3968.HK', '2388.HK',
    '3328.HK', '1288.HK', '6886.HK', '2899.HK',
]

# 地产建筑
PROPERTY_STOCKS = [
    '0016.HK', '0001.HK', '1113.HK', '0012.HK', '0017.HK', '0688.HK', '0960.HK', '1109.HK',
    '0823.HK', '6098.HK', '2007.HK', '1918.HK', '3333.HK', '0101.HK', '1997.HK', '0083.HK',
]

# 能源电力
ENERGY_STOCKS = [
    '0883.HK', '0857.HK', '0386.HK', '0135.HK', '0384.HK', '2688.HK', '0836.HK', '0002.HK',
    '0006.HK', '0003.HK', '1088.HK', '1171.HK', '1898.HK',
]

# 工业制造
INDUSTRIAL_STOCKS = [
    '0669.HK', '0316.HK', '0576.HK', '0177.HK', '0144.HK', '1038.HK', '0066.HK', '1378.HK',
]

# 其他重要股票
OTHER_STOCKS = [
    '0027.HK', '1928.HK', '6618.HK', '9989.HK', '0656.HK', '0267.HK', '0788.HK',
]


def add_stocks_from_list(stock_list, category_name):
    """从列表添加股票"""
    try:
        client = get_longport_client()
        db_manager = get_db_manager()
        
        added = 0
        existed = 0
        failed = 0
        
        print(f"\n{'='*60}")
        print(f"添加 {category_name}")
        print(f"{'='*60}\n")
        
        # 去重
        unique_stocks = list(set(stock_list))
        total = len(unique_stocks)
        
        with db_manager.get_session() as session:
            for i, symbol in enumerate(unique_stocks, 1):
                # 检查是否已存在
                existing = session.query(StockInfo).filter_by(symbol=symbol).first()
                
                if existing:
                    print(f"[{i}/{total}] ✓ {symbol} - {existing.name} (已存在)")
                    existed += 1
                    continue
                
                # 获取股票信息
                try:
                    static_info = client.get_static_info([symbol])
                    if static_info and len(static_info) > 0:
                        info = static_info[0]
                        
                        stock = StockInfo(
                            symbol=symbol,
                            name=info.name_cn or info.name_en,
                            market='HK',
                            is_active=True
                        )
                        session.add(stock)
                        session.flush()
                        
                        print(f"[{i}/{total}] ✅ {symbol} - {stock.name} (新增)")
                        added += 1
                    else:
                        print(f"[{i}/{total}] ❌ {symbol} (API无数据)")
                        failed += 1
                        
                except Exception as e:
                    print(f"[{i}/{total}] ❌ {symbol} (错误: {str(e)})")
                    failed += 1
            
            session.commit()
        
        print(f"\n{'='*60}")
        print(f"{category_name} 添加完成")
        print(f"  总计: {total} 只")
        print(f"  新增: {added} 只")
        print(f"  已存在: {existed} 只")
        print(f"  失败: {failed} 只")
        print(f"{'='*60}\n")
        
        return added
        
    except Exception as e:
        logger.error(f"添加股票失败: {e}")
        return 0


def main():
    # 初始化
    config_loader = init_config()
    config = config_loader.config
    db_manager = init_database(config)
    init_longport_client(config_loader.api_config)
    
    print("\n" + "="*60)
    print("扩充港股股票列表")
    print("="*60)
    
    total_added = 0
    
    # 合并所有股票列表
    all_stocks = set()
    all_stocks.update(HSI_STOCKS)
    all_stocks.update(HSCEI_STOCKS)
    all_stocks.update(TECH_STOCKS)
    all_stocks.update(EV_STOCKS)
    all_stocks.update(PHARMA_STOCKS)
    all_stocks.update(CONSUMER_STOCKS)
    all_stocks.update(FINANCE_STOCKS)
    all_stocks.update(PROPERTY_STOCKS)
    all_stocks.update(ENERGY_STOCKS)
    all_stocks.update(INDUSTRIAL_STOCKS)
    all_stocks.update(OTHER_STOCKS)
    
    print(f"\n总共收集到 {len(all_stocks)} 只不重复的港股")
    
    # 批量添加
    added = add_stocks_from_list(list(all_stocks), "港股主要股票")
    total_added += added
    
    print(f"\n🎉 全部完成！共新增 {total_added} 只港股\n")
    
    # 统计当前数量
    with db_manager.get_session() as session:
        hk_count = session.query(StockInfo).filter_by(market='HK', is_active=True).count()
        us_count = session.query(StockInfo).filter_by(market='US', is_active=True).count()
        total_count = hk_count + us_count
    
    print(f"📊 当前股票数量:")
    print(f"  港股: {hk_count} 只")
    print(f"  美股: {us_count} 只")
    print(f"  总计: {total_count} 只\n")
    
    if total_added > 0:
        print("💡 下一步:")
        print("  1. 获取历史数据: python scripts/fetch_historical_data.py --batch --market HK --days 365 --limit 300")
        print("  2. 计算技术指标: python scripts/calculate_indicators.py --batch --market HK")
        print("  3. 运行选股分析: python scripts/run_stock_selection.py --market HK --top 50\n")


if __name__ == '__main__':
    main()

