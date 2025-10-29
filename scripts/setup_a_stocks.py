"""
添加A股股票到数据库
包含沪深300、科创50、创业板指等主要指数成分股
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_database, get_db_manager
from database.models import StockInfo
from data_collection.longport_client import init_longport_client, get_longport_client
from utils.config_loader import init_config
from loguru import logger


# 沪深300成分股（精选50只龙头）
HS300_STOCKS = {
    # 金融银行 (10只)
    '600036.SH': '招商银行',
    '601318.SH': '中国平安',
    '600000.SH': '浦发银行',
    '601166.SH': '兴业银行',
    '600016.SH': '民生银行',
    '601328.SH': '交通银行',
    '601398.SH': '工商银行',
    '601939.SH': '建设银行',
    '601288.SH': '农业银行',
    '601988.SH': '中国银行',
    
    # 白酒食品 (5只)
    '600519.SH': '贵州茅台',
    '000858.SZ': '五粮液',
    '000568.SZ': '泸州老窖',
    '600809.SH': '山西汾酒',
    '603288.SH': '海天味业',
    
    # 新能源汽车 (8只)
    '300750.SZ': '宁德时代',
    '002594.SZ': '比亚迪',
    '601633.SH': '长城汽车',
    '600104.SH': '上汽集团',
    '002460.SZ': '赣锋锂业',
    '002466.SZ': '天齐锂业',
    '300014.SZ': '亿纬锂能',
    '688005.SH': '容百科技',
    
    # 科技互联网 (7只)
    '000063.SZ': '中兴通讯',
    '002415.SZ': '海康威视',
    '300059.SZ': '东方财富',
    '002475.SZ': '立讯精密',
    '002241.SZ': '歌尔股份',
    '300433.SZ': '蓝思科技',
    '002371.SZ': '北方华创',
    
    # 医药生物 (6只)
    '300760.SZ': '迈瑞医疗',
    '600276.SH': '恒瑞医药',
    '000661.SZ': '长春高新',
    '300122.SZ': '智飞生物',
    '603259.SH': '药明康德',
    '300015.SZ': '爱尔眼科',
    
    # 消费零售 (5只)
    '600887.SH': '伊利股份',
    '000333.SZ': '美的集团',
    '000651.SZ': '格力电器',
    '002304.SZ': '洋河股份',
    '603501.SH': '韦尔股份',
    
    # 地产建筑 (4只)
    '000002.SZ': '万科A',
    '001979.SZ': '招商蛇口',
    '600048.SH': '保利发展',
    '000001.SZ': '平安银行',
    
    # 能源化工 (5只)
    '600028.SH': '中国石化',
    '601857.SH': '中国石油',
    '600309.SH': '万华化学',
    '601225.SH': '陕西煤业',
    '601088.SH': '中国神华',
}

# 科创50成分股（精选20只）
STAR50_STOCKS = {
    '688981.SH': '中芯国际',
    '688111.SH': '金山办公',
    '688599.SH': '天合光能',
    '688012.SH': '中微公司',
    '688008.SH': '澜起科技',
    '688036.SH': '传音控股',
    '688223.SH': '晶科能源',
    '688041.SH': '海光信息',
    '688187.SH': '时代电气',
    '688561.SH': '奇安信-U',
    '688396.SH': '华润微',
    '688169.SH': '石头科技',
    '688126.SH': '沪硅产业-U',
    '688303.SH': '大全能源',
    '688065.SH': '凯盛新材',
    '688185.SH': '康希诺-U',
    '688256.SH': '寒武纪-U',
    '688099.SH': '晶晨股份',
    '688981.SH': '中芯国际',
    '688777.SH': '中控技术',
}

# 创业板指成分股（精选20只）
CHINEXT_STOCKS = {
    '300750.SZ': '宁德时代',
    '300059.SZ': '东方财富',
    '300760.SZ': '迈瑞医疗',
    '300015.SZ': '爱尔眼科',
    '300122.SZ': '智飞生物',
    '300014.SZ': '亿纬锂能',
    '300274.SZ': '阳光电源',
    '300124.SZ': '汇川技术',
    '300433.SZ': '蓝思科技',
    '300408.SZ': '三环集团',
    '300347.SZ': '泰格医药',
    '300454.SZ': '深信服',
    '300661.SZ': '圣邦股份',
    '300750.SZ': '宁德时代',
    '300896.SZ': '爱美客',
    '300919.SZ': '中伟股份',
    '301029.SZ': '怡合达',
    '301236.SZ': '软通动力',
    '301269.SZ': '华大九天',
    '301308.SZ': '江波龙',
}


def add_a_stocks():
    """添加A股股票到数据库"""
    
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    init_longport_client(config_loader.api_config)
    
    client = get_longport_client()
    db_manager = get_db_manager()
    
    # 合并所有股票（去重）
    all_stocks = {}
    all_stocks.update(HS300_STOCKS)
    all_stocks.update(STAR50_STOCKS)
    all_stocks.update(CHINEXT_STOCKS)
    
    print(f"\n准备添加 {len(all_stocks)} 只A股股票到数据库...\n")
    
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    with db_manager.get_session() as session:
        for i, (symbol, name) in enumerate(all_stocks.items(), 1):
            try:
                # 检查是否已存在
                existing = session.query(StockInfo).filter_by(symbol=symbol).first()
                if existing:
                    print(f"[{i}/{len(all_stocks)}] ⏭️  {symbol} - {name} (已存在)")
                    skipped_count += 1
                    continue
                
                # 从长桥API获取股票信息
                try:
                    info_list = client.get_static_info([symbol])
                    if not info_list or len(info_list) == 0:
                        print(f"[{i}/{len(all_stocks)}] ❌ {symbol} - {name} (API无数据)")
                        error_count += 1
                        continue
                    
                    info = info_list[0]
                    
                    # 创建股票记录
                    stock = StockInfo(
                        symbol=symbol,
                        name=info.name_cn or name,
                        market='CN',  # A股市场
                        exchange='SH' if symbol.endswith('.SH') else 'SZ',
                        currency='CNY',
                        lot_size=100  # A股最小交易单位100股
                    )
                    
                    session.add(stock)
                    session.commit()
                    
                    print(f"[{i}/{len(all_stocks)}] ✅ {symbol} - {stock.name}")
                    added_count += 1
                    
                except Exception as e:
                    print(f"[{i}/{len(all_stocks)}] ❌ {symbol} - {name} (错误: {str(e)})")
                    error_count += 1
                    session.rollback()
                    
            except Exception as e:
                print(f"[{i}/{len(all_stocks)}] ❌ {symbol} - {name} (数据库错误: {str(e)})")
                error_count += 1
                session.rollback()
    
    print(f"\n" + "="*60)
    print(f"A股股票添加完成！")
    print(f"="*60)
    print(f"✅ 新增: {added_count} 只")
    print(f"⏭️  跳过: {skipped_count} 只 (已存在)")
    print(f"❌ 失败: {error_count} 只")
    print(f"📊 总计: {added_count + skipped_count} 只A股在数据库中")
    print(f"="*60 + "\n")


if __name__ == '__main__':
    add_a_stocks()

