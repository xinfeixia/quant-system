#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多A股股票到数据库 - 第7批
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
    """添加第7批A股股票"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 第7批：50只优质A股（补充细分行业龙头、成长股）
    new_stocks = [
        # 医药生物 - CXO、创新药、医疗器械
        ('603127.SH', '昭衍新药', 'CN', 'SH'),  # 已存在，但再次确认
        ('300347.SZ', '泰格医药', 'CN', 'SZ'),  # CRO龙头
        ('002821.SZ', '凯莱英', 'CN', 'SZ'),  # CDMO龙头
        ('688278.SH', '特宝生物', 'CN', 'SH'),  # 生物制药
        ('688180.SH', '君实生物', 'CN', 'SH'),  # 已存在
        ('688520.SH', '神州细胞', 'CN', 'SH'),  # 创新药
        ('300595.SZ', '欧普康视', 'CN', 'SZ'),  # 眼科医疗
        ('688016.SH', '心脉医疗', 'CN', 'SH'),  # 医疗器械
        ('688617.SH', '惠泰医疗', 'CN', 'SH'),  # 医疗器械
        ('300896.SZ', '爱美客', 'CN', 'SZ'),  # 医美
        
        # 半导体 - 设计、制造、材料
        ('688256.SH', '寒武纪', 'CN', 'SH'),  # 已存在
        ('688099.SH', '晶晨股份', 'CN', 'SH'),  # 已存在
        ('688508.SH', '芯朋微', 'CN', 'SH'),  # 芯片设计
        ('688595.SH', '芯海科技', 'CN', 'SH'),  # 芯片设计
        ('688536.SH', '思瑞浦', 'CN', 'SH'),  # 模拟芯片
        ('688368.SH', '晶丰明源', 'CN', 'SH'),  # LED驱动芯片
        ('688072.SH', '拓荆科技', 'CN', 'SH'),  # 半导体设备
        ('688012.SH', '中微公司', 'CN', 'SH'),  # 已存在
        ('688981.SH', '中芯国际', 'CN', 'SH'),  # 已存在
        ('688396.SH', '华润微', 'CN', 'SH'),  # 已存在
        
        # 新能源 - 储能、氢能、风电
        ('300750.SZ', '宁德时代', 'CN', 'SZ'),  # 已存在
        ('688390.SH', '固德威', 'CN', 'SH'),  # 逆变器
        ('688032.SH', '禾迈股份', 'CN', 'SH'),  # 微型逆变器
        ('300763.SZ', '锦浪科技', 'CN', 'SZ'),  # 逆变器
        ('688063.SH', '派能科技', 'CN', 'SH'),  # 储能
        ('300274.SZ', '阳光电源', 'CN', 'SZ'),  # 已存在
        ('601615.SH', '明阳智能', 'CN', 'SH'),  # 风电
        ('300443.SZ', '金雷股份', 'CN', 'SZ'),  # 风电主轴
        ('002202.SZ', '金风科技', 'CN', 'SZ'),  # 风电整机
        ('688339.SH', '亿华通', 'CN', 'SH'),  # 氢燃料电池
        
        # 消费 - 食品饮料、纺织服装、家居
        ('603345.SH', '安井食品', 'CN', 'SH'),  # 已存在
        ('603517.SH', '绝味食品', 'CN', 'SH'),  # 已存在
        ('603866.SH', '桃李面包', 'CN', 'SH'),  # 已存在
        ('002507.SZ', '涪陵榨菜', 'CN', 'SZ'),  # 已存在
        ('600887.SH', '伊利股份', 'CN', 'SH'),  # 已存在
        ('002570.SZ', '贝因美', 'CN', 'SZ'),  # 婴幼儿奶粉
        ('603288.SH', '海天味业', 'CN', 'SH'),  # 已存在
        ('603369.SH', '今世缘', 'CN', 'SH'),  # 已存在
        ('603589.SH', '口子窖', 'CN', 'SH'),  # 已存在
        ('600702.SH', '舍得酒业', 'CN', 'SH'),  # 已存在
        
        # 军工 - 航空航天、军工电子
        ('600893.SH', '航发动力', 'CN', 'SH'),  # 已存在
        ('600760.SH', '中航沈飞', 'CN', 'SH'),  # 已存在
        ('600038.SH', '中直股份', 'CN', 'SH'),  # 已存在
        ('002179.SZ', '中航光电', 'CN', 'SZ'),  # 已存在
        ('600150.SH', '中国船舶', 'CN', 'SH'),  # 已存在
        ('688122.SH', '西部超导', 'CN', 'SH'),  # 军工材料
        ('688559.SH', '海目星', 'CN', 'SH'),  # 激光设备
        ('688066.SH', '航天宏图', 'CN', 'SH'),  # 卫星应用
        
        # 软件互联网
        ('688088.SH', '虹软科技', 'CN', 'SH'),  # 视觉AI
        ('688023.SH', '安恒信息', 'CN', 'SH'),  # 网络安全
        ('688561.SH', '奇安信', 'CN', 'SH'),  # 已存在
        ('688019.SH', '安集科技', 'CN', 'SH'),  # 半导体材料
        ('688608.SH', '恒玄科技', 'CN', 'SH'),  # 智能音频芯片
        
        # 新材料
        ('688599.SH', '天合光能', 'CN', 'SH'),  # 已存在
        ('688005.SH', '容百科技', 'CN', 'SH'),  # 已存在
        ('688388.SH', '嘉元科技', 'CN', 'SH'),  # 锂电铜箔
        ('688123.SH', '聚和材料', 'CN', 'SH'),  # 光学材料
        ('688680.SH', '海优新材', 'CN', 'SH'),  # 胶粘剂
        
        # 汽车零部件
        ('601799.SH', '星宇股份', 'CN', 'SH'),  # 已存在
        ('600699.SH', '均胜电子', 'CN', 'SZ'),  # 已存在
        ('002050.SZ', '三花智控', 'CN', 'SZ'),  # 已存在
        ('600741.SH', '华域汽车', 'CN', 'SH'),  # 已存在
        ('002920.SZ', '德赛西威', 'CN', 'SZ'),  # 已存在
        ('688981.SH', '中芯国际', 'CN', 'SH'),  # 已存在（重复）
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
    print(f"第7批A股添加完成！")
    print(f"新增: {added} 只")
    print(f"跳过: {skipped} 只（已存在）")
    print(f"总计: {added + skipped} 只")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

