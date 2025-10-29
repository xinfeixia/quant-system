"""
补充更多A股股票
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo
from utils.config_loader import init_config, get_config_loader
from datetime import datetime
from loguru import logger


# 补充的A股列表
ADDITIONAL_A_STOCKS = [
    # 银行股（补充）
    ('601009.SH', '南京银行', 'SH'),
    ('600015.SH', '华夏银行', 'SH'),
    ('601169.SH', '北京银行', 'SH'),
    
    # 券商股（补充）
    ('601066.SH', '中信建投', 'SH'),
    ('600999.SH', '招商证券', 'SH'),
    ('601211.SH', '国泰君安', 'SH'),
    ('600958.SH', '东方证券', 'SH'),
    
    # 保险股（补充）
    ('601319.SH', '中国人保', 'SH'),
    
    # 地产股（补充）
    ('600340.SH', '华夏幸福', 'SH'),
    ('001979.SZ', '招商蛇口', 'SZ'),  # 可能已存在
    
    # 白酒股（补充）
    ('000596.SZ', '古井贡酒', 'SZ'),
    ('000799.SZ', '酒鬼酒', 'SZ'),
    ('603369.SH', '今世缘', 'SH'),
    
    # 医药股（补充）
    ('600276.SH', '恒瑞医药', 'SH'),  # 可能已存在
    ('000661.SZ', '长春高新', 'SZ'),  # 可能已存在
    ('002821.SZ', '凯莱英', 'SZ'),  # 可能已存在
    ('300760.SZ', '迈瑞医疗', 'SZ'),  # 可能已存在
    ('603392.SH', '万泰生物', 'SH'),
    ('688185.SH', '康希诺', 'SH'),  # 可能已存在
    
    # 消费股（补充）
    ('002304.SZ', '洋河股份', 'SZ'),  # 可能已存在
    ('600519.SH', '贵州茅台', 'SH'),  # 可能已存在
    ('000568.SZ', '泸州老窖', 'SZ'),  # 可能已存在
    ('600600.SH', '青岛啤酒', 'SH'),
    ('000895.SZ', '双汇发展', 'SZ'),
    ('603288.SH', '海天味业', 'SH'),  # 可能已存在
    
    # 家电股（补充）
    ('000333.SZ', '美的集团', 'SZ'),  # 可能已存在
    ('000651.SZ', '格力电器', 'SZ'),  # 可能已存在
    ('600690.SH', '海尔智家', 'SH'),  # 可能已存在
    ('000921.SZ', '海信家电', 'SZ'),
    
    # 汽车股（补充）
    ('601633.SH', '长城汽车', 'SH'),  # 可能已存在
    ('002594.SZ', '比亚迪', 'SZ'),  # 可能已存在
    ('600104.SH', '上汽集团', 'SH'),  # 可能已存在
    ('000625.SZ', '长安汽车', 'SZ'),
    ('601238.SH', '广汽集团', 'SH'),
    
    # 新能源车产业链（补充）
    ('300750.SZ', '宁德时代', 'SZ'),  # 可能已存在
    ('002460.SZ', '赣锋锂业', 'SZ'),  # 可能已存在
    ('002466.SZ', '天齐锂业', 'SZ'),  # 可能已存在
    ('300014.SZ', '亿纬锂能', 'SZ'),  # 可能已存在
    ('002812.SZ', '恩捷股份', 'SZ'),  # 可能已存在
    
    # 光伏产业链（补充）
    ('601012.SH', '隆基绿能', 'SH'),  # 可能已存在
    ('688223.SH', '晶科能源', 'SH'),  # 可能已存在
    ('688599.SH', '天合光能', 'SH'),  # 可能已存在
    ('300274.SZ', '阳光电源', 'SZ'),  # 可能已存在
    ('002459.SZ', '晶澳科技', 'SZ'),  # 可能已存在
    ('600438.SH', '通威股份', 'SH'),  # 可能已存在
    
    # 半导体（补充）
    ('688981.SH', '中芯国际', 'SH'),  # 可能已存在
    ('603986.SH', '兆易创新', 'SH'),  # 可能已存在
    ('688008.SH', '澜起科技', 'SH'),  # 可能已存在
    ('688012.SH', '中微公司', 'SH'),  # 可能已存在
    ('688396.SH', '华润微', 'SH'),  # 可能已存在
    ('002049.SZ', '紫光国微', 'SZ'),  # 可能已存在
    ('603501.SH', '豪威集团', 'SH'),  # 可能已存在
    
    # 军工股（补充）
    ('600760.SH', '中航沈飞', 'SH'),  # 可能已存在
    ('600893.SH', '航发动力', 'SH'),  # 可能已存在
    ('002179.SZ', '中航光电', 'SZ'),  # 可能已存在
    ('600150.SH', '中国船舶', 'SH'),
    
    # 5G/通信（补充）
    ('000063.SZ', '中兴通讯', 'SZ'),  # 可能已存在
    ('600050.SH', '中国联通', 'SH'),  # 可能已存在
    ('600941.SH', '中国移动', 'SH'),  # 可能已存在
    ('002415.SZ', '海康威视', 'SZ'),  # 可能已存在
    
    # 互联网/软件（补充）
    ('300059.SZ', '东方财富', 'SZ'),  # 可能已存在
    ('688111.SH', '金山办公', 'SH'),  # 可能已存在
    ('002230.SZ', '科大讯飞', 'SZ'),  # 可能已存在
    ('300454.SZ', '深信服', 'SZ'),  # 可能已存在
    ('688561.SH', '奇安信', 'SH'),  # 可能已存在
    
    # 化工（补充）
    ('600309.SH', '万华化学', 'SH'),  # 可能已存在
    ('600346.SH', '恒力石化', 'SH'),  # 可能已存在
    ('600426.SH', '华鲁恒升', 'SH'),  # 可能已存在
    ('002648.SZ', '卫星化学', 'SZ'),  # 可能已存在
    
    # 有色金属（补充）
    ('601899.SH', '紫金矿业', 'SH'),  # 可能已存在
    ('603799.SH', '华友钴业', 'SH'),  # 可能已存在
    ('002756.SZ', '永兴材料', 'SZ'),  # 可能已存在
    
    # 建材（补充）
    ('600585.SH', '海螺水泥', 'SH'),  # 可能已存在
    ('002271.SZ', '东方雨虹', 'SZ'),  # 可能已存在
    
    # 电力/公用事业（补充）
    ('600900.SH', '长江电力', 'SH'),  # 可能已存在
    ('600905.SH', '三峡能源', 'SH'),  # 可能已存在
    
    # 煤炭/石油（补充）
    ('601088.SH', '中国神华', 'SH'),  # 可能已存在
    ('601225.SH', '陕西煤业', 'SH'),  # 可能已存在
    ('601857.SH', '中国石油', 'SH'),  # 可能已存在
    ('600028.SH', '中国石化', 'SH'),  # 可能已存在
    
    # 航运/物流（补充）
    ('601919.SH', '中远海控', 'SH'),  # 可能已存在
    ('002352.SZ', '顺丰控股', 'SZ'),  # 可能已存在
    
    # 建筑/基建（补充）
    ('601668.SH', '中国建筑', 'SH'),  # 可能已存在
    ('601186.SH', '中国铁建', 'SH'),  # 可能已存在
    ('601390.SH', '中国中铁', 'SH'),  # 可能已存在
    ('600031.SH', '三一重工', 'SH'),  # 可能已存在
]


def add_stocks():
    """添加股票到数据库"""
    # 初始化
    init_config()
    config_loader = get_config_loader()
    init_database(config_loader.config)
    
    db_manager = get_db_manager()
    
    added_count = 0
    skipped_count = 0
    
    with db_manager.get_session() as session:
        for symbol, name, exchange in ADDITIONAL_A_STOCKS:
            # 检查是否已存在
            existing = session.query(StockInfo).filter_by(symbol=symbol).first()
            
            if existing:
                logger.info(f"⏭️  {symbol} - {name}: 已存在，跳过")
                skipped_count += 1
                continue
            
            # 添加新股票
            stock = StockInfo(
                symbol=symbol,
                name=name,
                market='CN',
                exchange=exchange,
                created_at=datetime.now()
            )
            session.add(stock)
            logger.info(f"✅ {symbol} - {name}: 已添加")
            added_count += 1
        
        session.commit()
    
    logger.info(f"\n{'='*80}")
    logger.info(f"添加完成！")
    logger.info(f"新增: {added_count} 只")
    logger.info(f"跳过: {skipped_count} 只（已存在）")
    logger.info(f"总计: {added_count + skipped_count} 只")
    logger.info(f"{'='*80}")
    
    # 显示当前A股总数
    with db_manager.get_session() as session:
        total_cn = session.query(StockInfo).filter_by(market='CN').count()
        logger.info(f"\n当前A股总数: {total_cn} 只")


if __name__ == '__main__':
    add_stocks()

