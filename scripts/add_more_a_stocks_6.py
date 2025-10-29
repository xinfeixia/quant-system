#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多A股股票（第六批）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager, init_database
from database.models import StockInfo
from datetime import datetime
from utils.config_loader import init_config

def add_more_stocks():
    """添加更多A股股票（第六批）"""
    
    # 初始化配置和数据库
    config = init_config()
    init_database(config)
    
    # 第六批A股（60只）- 继续补充各行业重要股票
    new_stocks = [
        # 创业板龙头
        ('300750.SZ', '宁德时代', 'CN', 'SZ'),
        ('300059.SZ', '东方财富', 'CN', 'SZ'),
        ('300015.SZ', '爱尔眼科', 'CN', 'SZ'),
        ('300760.SZ', '迈瑞医疗', 'CN', 'SZ'),
        ('300014.SZ', '亿纬锂能', 'CN', 'SZ'),
        
        # 科创板龙头
        ('688981.SH', '中芯国际', 'CN', 'SH'),
        ('688599.SH', '天合光能', 'CN', 'SH'),
        ('688223.SH', '晶科能源', 'CN', 'SH'),
        ('688111.SH', '金山办公', 'CN', 'SH'),
        ('688008.SH', '澜起科技', 'CN', 'SH'),
        
        # 白酒
        ('600519.SH', '贵州茅台', 'CN', 'SH'),
        ('000858.SZ', '五粮液', 'CN', 'SZ'),
        ('000568.SZ', '泸州老窖', 'CN', 'SZ'),
        ('000596.SZ', '古井贡酒', 'CN', 'SZ'),
        
        # 医药
        ('600276.SH', '恒瑞医药', 'CN', 'SH'),
        ('603259.SH', '药明康德', 'CN', 'SH'),
        ('300122.SZ', '智飞生物', 'CN', 'SZ'),
        ('000538.SZ', '云南白药', 'CN', 'SZ'),
        ('600436.SH', '片仔癀', 'CN', 'SH'),
        
        # 家电
        ('000333.SZ', '美的集团', 'CN', 'SZ'),
        ('000651.SZ', '格力电器', 'CN', 'SZ'),
        ('600690.SH', '海尔智家', 'CN', 'SH'),
        
        # 食品饮料
        ('600887.SH', '伊利股份', 'CN', 'SH'),
        ('603288.SH', '海天味业', 'CN', 'SH'),
        ('000895.SZ', '双汇发展', 'CN', 'SZ'),
        ('600600.SH', '青岛啤酒', 'CN', 'SH'),
        
        # 汽车
        ('002594.SZ', '比亚迪', 'CN', 'SZ'),
        ('601633.SH', '长城汽车', 'CN', 'SH'),
        ('000625.SZ', '长安汽车', 'CN', 'SZ'),
        ('601238.SH', '广汽集团', 'CN', 'SH'),
        
        # 光伏
        ('601012.SH', '隆基绿能', 'CN', 'SH'),
        ('002459.SZ', '晶澳科技', 'CN', 'SZ'),
        ('002129.SZ', 'TCL中环', 'CN', 'SZ'),
        ('300274.SZ', '阳光电源', 'CN', 'SZ'),
        
        # 锂电池
        ('002812.SZ', '恩捷股份', 'CN', 'SZ'),
        ('002460.SZ', '赣锋锂业', 'CN', 'SZ'),
        ('002466.SZ', '天齐锂业', 'CN', 'SZ'),
        ('002756.SZ', '永兴材料', 'CN', 'SZ'),
        
        # 半导体
        ('002371.SZ', '北方华创', 'CN', 'SZ'),
        ('603501.SH', '韦尔股份', 'CN', 'SH'),
        ('688012.SH', '中微公司', 'CN', 'SH'),
        ('688396.SH', '华润微', 'CN', 'SH'),
        ('603986.SH', '兆易创新', 'CN', 'SH'),
        
        # 通信
        ('000063.SZ', '中兴通讯', 'CN', 'SZ'),
        ('600941.SH', '中国移动', 'CN', 'SH'),
        ('600050.SH', '中国联通', 'CN', 'SH'),
        ('601728.SH', '中国电信', 'CN', 'SH'),
        
        # 电子
        ('002415.SZ', '海康威视', 'CN', 'SZ'),
        ('002475.SZ', '立讯精密', 'CN', 'SZ'),
        ('000725.SZ', '京东方A', 'CN', 'SZ'),
        ('002241.SZ', '歌尔股份', 'CN', 'SZ'),
        
        # 军工
        ('600150.SH', '中国船舶', 'CN', 'SH'),
        ('600893.SH', '航发动力', 'CN', 'SH'),
        ('002179.SZ', '中航光电', 'CN', 'SZ'),
        ('600038.SH', '中直股份', 'CN', 'SH'),
        
        # 券商
        ('600030.SH', '中信证券', 'CN', 'SH'),
        ('601688.SH', '华泰证券', 'CN', 'SH'),
        ('601211.SH', '国泰君安', 'CN', 'SH'),
        ('000776.SZ', '广发证券', 'CN', 'SZ'),
    ]
    
    db_manager = get_db_manager()
    
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
    print(f"添加完成！")
    print(f"新增: {added} 只")
    print(f"跳过: {skipped} 只（已存在）")
    print(f"本批次总数: {len(new_stocks)} 只")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    add_more_stocks()

