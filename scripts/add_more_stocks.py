"""
批量添加更多股票
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from database import init_database, get_db_manager
from database.models import StockInfo
from data_collection.longport_client import init_longport_client, get_longport_client
from loguru import logger


# 港股股票列表（扩充版）
HK_STOCKS = {
    # 科技互联网（已有部分，补充更多）
    '0020.HK': '商汤-W',
    '1024.HK': '快手-W',
    '2382.HK': '舜宇光学科技',
    '6690.HK': '海尔智家',
    '9698.HK': '万国数据-SW',
    '9888.HK': '百度集团-SW',
    '9961.HK': '携程集团-S',
    '9988.HK': '阿里巴巴-W',
    '9999.HK': '网易-S',
    '0700.HK': '腾讯控股',
    '3690.HK': '美团-W',
    '9618.HK': '京东集团-SW',
    '1810.HK': '小米集团-W',
    
    # 新能源汽车
    '1211.HK': '比亚迪股份',
    '0175.HK': '吉利汽车',
    '2333.HK': '长城汽车',
    '9866.HK': '蔚来-SW',
    '9868.HK': '小鹏汽车-W',
    '2015.HK': '理想汽车-W',
    '9863.HK': '零跑汽车',
    
    # 医药生物
    '1177.HK': '中国生物制药',
    '1801.HK': '信达生物',
    '2269.HK': '药明生物',
    '6185.HK': '康希诺生物',
    '9688.HK': '再鼎医药',
    '9926.HK': '康方生物',
    '2196.HK': '复星医药',
    '1093.HK': '石药集团',
    '0853.HK': '微创医疗',
    '1066.HK': '威高股份',
    
    # 金融保险
    '0388.HK': '香港交易所',
    '2318.HK': '中国平安',
    '1299.HK': '友邦保险',
    '2628.HK': '中国人寿',
    '6060.HK': '众安在线',
    '2328.HK': '中国财险',
    '6030.HK': '中信证券',
    
    # 银行
    '0005.HK': '汇丰控股',
    '0011.HK': '恒生银行',
    '0023.HK': '东亚银行',
    '0939.HK': '建设银行',
    '1398.HK': '工商银行',
    '3988.HK': '中国银行',
    '3968.HK': '招商银行',
    '2388.HK': '中银香港',
    '3328.HK': '交通银行',
    
    # 地产物业
    '0016.HK': '新鸿基地产',
    '0001.HK': '长和',
    '1113.HK': '长实集团',
    '0012.HK': '恒基地产',
    '0017.HK': '新世界发展',
    '0688.HK': '中国海外发展',
    '0960.HK': '龙湖集团',
    '1109.HK': '华润置地',
    '0823.HK': '领展房产基金',
    '6098.HK': '碧桂园服务',
    
    # 能源电力
    '0883.HK': '中国海洋石油',
    '0857.HK': '中国石油股份',
    '0386.HK': '中国石油化工股份',
    '0135.HK': '昆仑能源',
    '0384.HK': '中国燃气',
    '2688.HK': '新奥能源',
    '0836.HK': '华润电力',
    '0002.HK': '中电控股',
    '0006.HK': '电能实业',
    '0003.HK': '香港中华煤气',
    
    # 电信通讯
    '0941.HK': '中国移动',
    '0762.HK': '中国联通',
    '0728.HK': '中国电信',
    '0788.HK': '中国铁塔',
    '0763.HK': '中兴通讯',
    
    # 消费零售
    '9633.HK': '农夫山泉',
    '2319.HK': '蒙牛乳业',
    '0151.HK': '中国旺旺',
    '0322.HK': '康师傅控股',
    '1044.HK': '恒安国际',
    '9896.HK': '名创优品',
    '9987.HK': '百胜中国',
    '6862.HK': '海底捞',
    
    # 服装运动
    '2020.HK': '安踏体育',
    '2331.HK': '李宁',
    '2313.HK': '申洲国际',
    
    # 半导体芯片
    '0981.HK': '中芯国际',
    '1347.HK': '华虹半导体',
    '0522.HK': 'ASMPT',
    
    # 教育娱乐
    '9901.HK': '新东方-S',
    '0772.HK': '阅文集团',
    '9626.HK': '哔哩哔哩-W',
    
    # 其他
    '0027.HK': '银河娱乐',
    '1928.HK': '金沙中国有限公司',
    '0992.HK': '联想集团',
    '0285.HK': '比亚迪电子',
    '0669.HK': '创科实业',
}

# 美股股票列表（热门股票）
US_STOCKS = {
    # 科技巨头 (FAANG+)
    'AAPL.US': 'Apple Inc',
    'MSFT.US': 'Microsoft Corporation',
    'GOOGL.US': 'Alphabet Inc Class A',
    'GOOG.US': 'Alphabet Inc Class C',
    'AMZN.US': 'Amazon.com Inc',
    'META.US': 'Meta Platforms Inc',
    'NVDA.US': 'NVIDIA Corporation',
    'TSLA.US': 'Tesla Inc',
    
    # 芯片半导体
    'AMD.US': 'Advanced Micro Devices',
    'INTC.US': 'Intel Corporation',
    'QCOM.US': 'QUALCOMM Incorporated',
    'AVGO.US': 'Broadcom Inc',
    'TSM.US': 'Taiwan Semiconductor',
    'ASML.US': 'ASML Holding NV',
    
    # 软件云计算
    'CRM.US': 'Salesforce Inc',
    'ORCL.US': 'Oracle Corporation',
    'ADBE.US': 'Adobe Inc',
    'NOW.US': 'ServiceNow Inc',
    'SNOW.US': 'Snowflake Inc',
    
    # 电商零售
    'BABA.US': 'Alibaba Group',
    'JD.US': 'JD.com Inc',
    'PDD.US': 'PDD Holdings Inc',
    'SHOP.US': 'Shopify Inc',
    
    # 电动车
    'NIO.US': 'NIO Inc',
    'XPEV.US': 'XPeng Inc',
    'LI.US': 'Li Auto Inc',
    'RIVN.US': 'Rivian Automotive',
    'LCID.US': 'Lucid Group Inc',
    
    # 金融支付
    'V.US': 'Visa Inc',
    'MA.US': 'Mastercard Inc',
    'PYPL.US': 'PayPal Holdings',
    'SQ.US': 'Block Inc',
    
    # 银行保险
    'JPM.US': 'JPMorgan Chase',
    'BAC.US': 'Bank of America',
    'WFC.US': 'Wells Fargo',
    'GS.US': 'Goldman Sachs',
    'MS.US': 'Morgan Stanley',
    
    # 消费品牌
    'NKE.US': 'Nike Inc',
    'SBUX.US': 'Starbucks Corporation',
    'MCD.US': 'McDonald\'s Corporation',
    'KO.US': 'Coca-Cola Company',
    'PEP.US': 'PepsiCo Inc',
    
    # 医药生物
    'PFE.US': 'Pfizer Inc',
    'JNJ.US': 'Johnson & Johnson',
    'MRNA.US': 'Moderna Inc',
    'ABBV.US': 'AbbVie Inc',
    
    # 娱乐传媒
    'DIS.US': 'Walt Disney Company',
    'NFLX.US': 'Netflix Inc',
    'SPOT.US': 'Spotify Technology',
    
    # 其他
    'UBER.US': 'Uber Technologies',
    'ABNB.US': 'Airbnb Inc',
    'COIN.US': 'Coinbase Global',
}


def add_stocks(stock_dict, market):
    """添加股票到数据库"""
    try:
        client = get_longport_client()
        db_manager = get_db_manager()
        
        total = len(stock_dict)
        added = 0
        existed = 0
        failed = 0
        
        print(f"\n{'='*60}")
        print(f"添加 {market} 市场股票")
        print(f"{'='*60}\n")
        
        with db_manager.get_session() as session:
            for i, (symbol, name) in enumerate(stock_dict.items(), 1):
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
                            name=info.name_cn or name,
                            market=market,
                            is_active=True
                        )
                        session.add(stock)
                        session.flush()
                        
                        print(f"[{i}/{total}] ✅ {symbol} - {stock.name} (新增)")
                        added += 1
                    else:
                        print(f"[{i}/{total}] ❌ {symbol} - {name} (API无数据)")
                        failed += 1
                        
                except Exception as e:
                    print(f"[{i}/{total}] ❌ {symbol} - {name} (错误: {str(e)})")
                    failed += 1
            
            session.commit()
        
        print(f"\n{'='*60}")
        print(f"添加完成！")
        print(f"  总计: {total} 只")
        print(f"  新增: {added} 只")
        print(f"  已存在: {existed} 只")
        print(f"  失败: {failed} 只")
        print(f"{'='*60}\n")
        
        return added
        
    except Exception as e:
        logger.error(f"添加股票失败: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='批量添加更多股票')
    parser.add_argument('--market', choices=['HK', 'US', 'ALL'], default='ALL',
                        help='市场: HK=港股, US=美股, ALL=全部')
    
    args = parser.parse_args()
    
    # 初始化
    config_loader = init_config()
    config = config_loader.config
    db_manager = init_database(config)
    init_longport_client(config_loader.api_config)
    
    total_added = 0
    
    # 添加港股
    if args.market in ['HK', 'ALL']:
        added = add_stocks(HK_STOCKS, 'HK')
        total_added += added
    
    # 添加美股
    if args.market in ['US', 'ALL']:
        added = add_stocks(US_STOCKS, 'US')
        total_added += added
    
    print(f"\n🎉 全部完成！共新增 {total_added} 只股票\n")
    
    if total_added > 0:
        print("💡 下一步:")
        print("  1. 获取历史数据: python scripts/fetch_historical_data.py --batch --market HK --days 365")
        print("  2. 计算技术指标: python scripts/calculate_indicators.py --batch --market HK")
        print("  3. 运行选股分析: python scripts/run_stock_selection.py --market HK --top 50")


if __name__ == '__main__':
    main()

