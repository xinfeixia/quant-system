#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多A股股票到数据库 - 第10批（补充更多优质股）
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo
from datetime import datetime
from utils.config_loader import init_config

def main():
    """添加第10批A股股票"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 第10批：60只优质A股（补充更多行业龙头和成长股）
    new_stocks = [
        # 化工新材料
        ('600309.SH', '万华化学', 'CN', 'SH'),  # 化工龙头
        ('002648.SZ', '卫星化学', 'CN', 'SZ'),  # C3产业链
        ('600426.SH', '华鲁恒升', 'CN', 'SH'),  # 煤化工
        ('002601.SZ', '龙佰集团', 'CN', 'SZ'),  # 钛白粉
        ('002407.SZ', '多氟多', 'CN', 'SZ'),  # 氟化工
        ('600989.SH', '宝丰能源', 'CN', 'SH'),  # 煤化工
        ('603806.SH', '福斯特', 'CN', 'SH'),  # 光伏胶膜
        ('300568.SZ', '星源材质', 'CN', 'SZ'),  # 锂电隔膜
        ('300037.SZ', '新宙邦', 'CN', 'SZ'),  # 电解液
        ('002709.SZ', '天赐材料', 'CN', 'SZ'),  # 电解液
        
        # 机械设备
        ('603501.SH', '韦尔股份', 'CN', 'SH'),  # 半导体
        ('300124.SZ', '汇川技术', 'CN', 'SZ'),  # 工控
        ('300450.SZ', '先导智能', 'CN', 'SZ'),  # 锂电设备
        ('688169.SH', '石头科技', 'CN', 'SH'),  # 扫地机器人
        ('688777.SH', '中控技术', 'CN', 'SH'),  # 工业自动化
        ('300316.SZ', '晶盛机电', 'CN', 'SZ'),  # 光伏设备
        ('688012.SH', '中微公司', 'CN', 'SH'),  # 半导体设备
        ('688126.SH', '沪硅产业', 'CN', 'SH'),  # 半导体材料
        ('002371.SZ', '北方华创', 'CN', 'SZ'),  # 半导体设备
        ('688008.SH', '澜起科技', 'CN', 'SH'),  # 芯片设计
        
        # 家电家居
        ('000333.SZ', '美的集团', 'CN', 'SZ'),  # 家电龙头
        ('000651.SZ', '格力电器', 'CN', 'SZ'),  # 空调龙头
        ('600690.SH', '海尔智家', 'CN', 'SH'),  # 家电
        ('000596.SZ', '古井贡酒', 'CN', 'SZ'),  # 白酒
        ('603369.SH', '今世缘', 'CN', 'SH'),  # 白酒
        ('603589.SH', '口子窖', 'CN', 'SH'),  # 白酒
        ('600702.SH', '舍得酒业', 'CN', 'SH'),  # 白酒
        ('002572.SZ', '索菲亚', 'CN', 'SZ'),  # 定制家居
        ('603833.SH', '欧派家居', 'CN', 'SH'),  # 定制家居
        ('002833.SZ', '弘亚数控', 'CN', 'SZ'),  # 家具设备
        
        # 汽车产业链
        ('601799.SH', '星宇股份', 'CN', 'SH'),  # 车灯
        ('600699.SH', '均胜电子', 'CN', 'SH'),  # 汽车电子
        ('002920.SZ', '德赛西威', 'CN', 'SZ'),  # 智能座舱
        ('002050.SZ', '三花智控', 'CN', 'SZ'),  # 热管理
        ('600741.SH', '华域汽车', 'CN', 'SH'),  # 汽车零部件
        ('002594.SZ', '比亚迪', 'CN', 'SZ'),  # 新能源车
        ('601633.SH', '长城汽车', 'CN', 'SH'),  # 汽车
        ('000625.SZ', '长安汽车', 'CN', 'SZ'),  # 汽车
        ('601238.SH', '广汽集团', 'CN', 'SH'),  # 汽车
        ('600104.SH', '上汽集团', 'CN', 'SH'),  # 汽车
        
        # 食品饮料
        ('600519.SH', '贵州茅台', 'CN', 'SH'),  # 白酒龙头
        ('000858.SZ', '五粮液', 'CN', 'SZ'),  # 白酒
        ('000568.SZ', '泸州老窖', 'CN', 'SZ'),  # 白酒
        ('000799.SZ', '酒鬼酒', 'CN', 'SZ'),  # 白酒
        ('600887.SH', '伊利股份', 'CN', 'SH'),  # 乳制品
        ('000895.SZ', '双汇发展', 'CN', 'SZ'),  # 肉制品
        ('603288.SH', '海天味业', 'CN', 'SH'),  # 调味品
        ('600600.SH', '青岛啤酒', 'CN', 'SH'),  # 啤酒
        ('603345.SH', '安井食品', 'CN', 'SH'),  # 速冻食品
        ('603517.SH', '绝味食品', 'CN', 'SH'),  # 卤制品
        
        # 医药生物
        ('300122.SZ', '智飞生物', 'CN', 'SZ'),  # 疫苗
        ('603392.SH', '万泰生物', 'CN', 'SH'),  # 疫苗
        ('688185.SH', '康希诺', 'CN', 'SH'),  # 疫苗
        ('300760.SZ', '迈瑞医疗', 'CN', 'SZ'),  # 医疗器械
        ('300015.SZ', '爱尔眼科', 'CN', 'SZ'),  # 眼科医疗
        ('600276.SH', '恒瑞医药', 'CN', 'SH'),  # 创新药
        ('603259.SH', '药明康德', 'CN', 'SH'),  # CRO
        ('688180.SH', '君实生物', 'CN', 'SH'),  # 创新药
        ('300529.SZ', '健帆生物', 'CN', 'SZ'),  # 血液净化
        ('300676.SZ', '华大基因', 'CN', 'SZ'),  # 基因测序
    ]
    
    added = 0
    skipped = 0
    
    with db_manager.get_session() as session:
        for symbol, name, market, exchange in new_stocks:
            # 检查是否已存在
            existing = session.query(StockInfo).filter_by(symbol=symbol).first()
            if existing:
                print(f"⚠️  {symbol} - {name} 已存在，跳过")
                skipped += 1
                continue
            
            # 添加新股票
            stock = StockInfo(
                symbol=symbol,
                name=name,
                market=market,
                exchange=exchange,
                created_at=datetime.now()
            )
            session.add(stock)
            print(f"✅ 添加 {symbol} - {name}")
            added += 1
        
        session.commit()
    
    print(f"\n{'='*60}")
    print(f"第10批A股添加完成！")
    print(f"新增: {added} 只")
    print(f"跳过: {skipped} 只（已存在）")
    print(f"总计: {added + skipped} 只")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

