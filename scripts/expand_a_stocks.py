"""
扩展A股股票池 - 添加更多指数成分股
包含上证50、中证500、深证成指、行业龙头等
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


# 上证50成分股（50只蓝筹股）
SSE50_STOCKS = {
    # 金融
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
    '601601.SH': '中国太保',
    '601628.SH': '中国人寿',
    '601688.SH': '华泰证券',
    '600030.SH': '中信证券',
    
    # 消费
    '600519.SH': '贵州茅台',
    '600887.SH': '伊利股份',
    '603288.SH': '海天味业',
    '600809.SH': '山西汾酒',
    
    # 医药
    '600276.SH': '恒瑞医药',
    '603259.SH': '药明康德',
    
    # 能源
    '600028.SH': '中国石化',
    '601857.SH': '中国石油',
    '601088.SH': '中国神华',
    '600309.SH': '万华化学',
    
    # 工业
    '600585.SH': '海螺水泥',
    '601668.SH': '中国建筑',
    '601390.SH': '中国中铁',
    '601186.SH': '中国铁建',
    
    # 科技
    '600745.SH': '闻泰科技',
    '688981.SH': '中芯国际',
    
    # 其他
    '601888.SH': '中国中免',
    '600690.SH': '海尔智家',
    '601012.SH': '隆基绿能',
    '601899.SH': '紫金矿业',
    '600031.SH': '三一重工',
    '601919.SH': '中远海控',
    '600900.SH': '长江电力',
    '601225.SH': '陕西煤业',
    '601336.SH': '新华保险',
}

# 中证500成分股（精选50只中盘成长股）
CSI500_STOCKS = {
    # 科技
    '002049.SZ': '紫光国微',
    '002230.SZ': '科大讯飞',
    '002236.SZ': '大华股份',
    '002352.SZ': '顺丰控股',
    '002410.SZ': '广联达',
    '002456.SZ': '欧菲光',
    '002508.SZ': '老板电器',
    '002555.SZ': '三七互娱',
    '002600.SZ': '领益智造',
    '002648.SZ': '卫星化学',
    '002714.SZ': '牧原股份',
    '002916.SZ': '深南电路',
    '002920.SZ': '德赛西威',
    
    # 医药
    '002821.SZ': '凯莱英',
    '300003.SZ': '乐普医疗',
    '300142.SZ': '沃森生物',
    '300529.SZ': '健帆生物',
    '300595.SZ': '欧普康视',
    '300676.SZ': '华大基因',
    
    # 消费
    '002027.SZ': '分众传媒',
    '002032.SZ': '苏泊尔',
    '002120.SZ': '韵达股份',
    '002142.SZ': '宁波银行',
    '002153.SZ': '石基信息',
    '002179.SZ': '中航光电',
    '002271.SZ': '东方雨虹',
    '002311.SZ': '海大集团',
    '002372.SZ': '伟星新材',
    '002384.SZ': '东山精密',
    
    # 新能源
    '002129.SZ': '中环股份',
    '002459.SZ': '晶澳科技',
    '002812.SZ': '恩捷股份',
    '300124.SZ': '汇川技术',
    '300274.SZ': '阳光电源',
    '300450.SZ': '先导智能',
    
    # 化工
    '002601.SZ': '龙佰集团',
    '002756.SZ': '永兴材料',
    '600426.SH': '华鲁恒升',
    '600438.SH': '通威股份',
    '603799.SH': '华友钴业',
    
    # 其他
    '600132.SH': '重庆啤酒',
    '600346.SH': '恒力石化',
    '600570.SH': '恒生电子',
    '600703.SH': '三安光电',
    '600760.SH': '中航沈飞',
    '603986.SH': '兆易创新',
    '688111.SH': '金山办公',
    '688599.SH': '天合光能',
}

# 深证成指成分股（精选30只）
SZSE_STOCKS = {
    '000001.SZ': '平安银行',
    '000002.SZ': '万科A',
    '000063.SZ': '中兴通讯',
    '000100.SZ': 'TCL科技',
    '000333.SZ': '美的集团',
    '000338.SZ': '潍柴动力',
    '000425.SZ': '徐工机械',
    '000651.SZ': '格力电器',
    '000661.SZ': '长春高新',
    '000725.SZ': '京东方A',
    '000858.SZ': '五粮液',
    '000876.SZ': '新希望',
    '000938.SZ': '紫光股份',
    '001979.SZ': '招商蛇口',
    '002027.SZ': '分众传媒',
    '002142.SZ': '宁波银行',
    '002230.SZ': '科大讯飞',
    '002241.SZ': '歌尔股份',
    '002352.SZ': '顺丰控股',
    '002415.SZ': '海康威视',
    '002475.SZ': '立讯精密',
    '002594.SZ': '比亚迪',
    '002714.SZ': '牧原股份',
    '300014.SZ': '亿纬锂能',
    '300059.SZ': '东方财富',
    '300124.SZ': '汇川技术',
    '300274.SZ': '阳光电源',
    '300750.SZ': '宁德时代',
    '300760.SZ': '迈瑞医疗',
    '301029.SZ': '怡合达',
}

# 行业龙头股票（各行业代表）
SECTOR_LEADERS = {
    # 半导体
    '603501.SH': '韦尔股份',
    '688008.SH': '澜起科技',
    '688012.SH': '中微公司',
    '688036.SH': '传音控股',
    '688041.SH': '海光信息',
    '688126.SH': '沪硅产业',
    '688256.SH': '寒武纪',
    '688396.SH': '华润微',
    
    # 新材料
    '002460.SZ': '赣锋锂业',
    '002466.SZ': '天齐锂业',
    '002812.SZ': '恩捷股份',
    '300450.SZ': '先导智能',
    
    # 军工
    '600760.SH': '中航沈飞',
    '600893.SH': '航发动力',
    '002179.SZ': '中航光电',
    
    # 通信
    '600050.SH': '中国联通',
    '600941.SH': '中国移动',
    
    # 电力
    '600900.SH': '长江电力',
    '600905.SH': '三峡能源',
    
    # 煤炭
    '601225.SH': '陕西煤业',
    '601088.SH': '中国神华',
    
    # 有色
    '601899.SH': '紫金矿业',
    '603799.SH': '华友钴业',
    
    # 建材
    '600585.SH': '海螺水泥',
    '002271.SZ': '东方雨虹',
    
    # 家电
    '600690.SH': '海尔智家',
    '002032.SZ': '苏泊尔',
    
    # 食品饮料
    '600132.SH': '重庆啤酒',
    '002311.SZ': '海大集团',
    
    # 农业
    '002714.SZ': '牧原股份',
    '000876.SZ': '新希望',
    
    # 传媒
    '002027.SZ': '分众传媒',
    '002555.SZ': '三七互娱',
    
    # 物流
    '002352.SZ': '顺丰控股',
    '002120.SZ': '韵达股份',
    
    # 零售
    '601888.SH': '中国中免',
}


def expand_a_stocks():
    """扩展A股股票池"""
    
    # 初始化
    config_loader = init_config()
    init_database(config_loader.config)
    init_longport_client(config_loader.api_config)
    
    client = get_longport_client()
    db_manager = get_db_manager()
    
    # 合并所有股票（去重）
    all_stocks = {}
    all_stocks.update(SSE50_STOCKS)
    all_stocks.update(CSI500_STOCKS)
    all_stocks.update(SZSE_STOCKS)
    all_stocks.update(SECTOR_LEADERS)
    
    print(f"\n" + "="*60)
    print(f"准备扩展A股股票池")
    print(f"="*60)
    print(f"上证50成分股: {len(SSE50_STOCKS)} 只")
    print(f"中证500成分股: {len(CSI500_STOCKS)} 只")
    print(f"深证成指成分股: {len(SZSE_STOCKS)} 只")
    print(f"行业龙头股票: {len(SECTOR_LEADERS)} 只")
    print(f"合并后总数: {len(all_stocks)} 只")
    print(f"="*60 + "\n")
    
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
                        market='CN',
                        exchange='SH' if symbol.endswith('.SH') else 'SZ',
                        currency='CNY',
                        lot_size=100
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
    print(f"A股股票池扩展完成！")
    print(f"="*60)
    print(f"✅ 新增: {added_count} 只")
    print(f"⏭️  跳过: {skipped_count} 只 (已存在)")
    print(f"❌ 失败: {error_count} 只")
    print(f"📊 总计: {added_count + skipped_count} 只A股在数据库中")
    print(f"="*60 + "\n")


if __name__ == '__main__':
    expand_a_stocks()

