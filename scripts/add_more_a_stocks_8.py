#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多A股股票到数据库 - 第8批
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
    """添加第8批A股股票"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 第8批：50只优质A股（补充更多行业龙头和成长股）
    new_stocks = [
        # 消费电子
        ('002475.SZ', '立讯精密', 'CN', 'SZ'),
        ('002241.SZ', '歌尔股份', 'CN', 'SZ'),
        ('300433.SZ', '蓝思科技', 'CN', 'SZ'),
        ('002456.SZ', '欧菲光', 'CN', 'SZ'),
        ('002008.SZ', '大族激光', 'CN', 'SZ'),
        
        # 新能源汽车产业链
        ('300014.SZ', '亿纬锂能', 'CN', 'SZ'),
        ('002460.SZ', '赣锋锂业', 'CN', 'SZ'),
        ('002466.SZ', '天齐锂业', 'CN', 'SZ'),
        ('603799.SH', '华友钴业', 'CN', 'SH'),
        ('002812.SZ', '恩捷股份', 'CN', 'SZ'),
        ('300750.SZ', '宁德时代', 'CN', 'SZ'),
        ('002594.SZ', '比亚迪', 'CN', 'SZ'),
        
        # 光伏产业链
        ('601012.SH', '隆基绿能', 'CN', 'SH'),
        ('688223.SH', '晶科能源', 'CN', 'SH'),
        ('002459.SZ', '晶澳科技', 'CN', 'SZ'),
        ('688599.SH', '天合光能', 'CN', 'SH'),
        ('002129.SZ', 'TCL中环', 'CN', 'SZ'),
        ('300274.SZ', '阳光电源', 'CN', 'SZ'),
        ('603806.SH', '福斯特', 'CN', 'SH'),
        
        # 半导体产业链
        ('688981.SH', '中芯国际', 'CN', 'SH'),
        ('688012.SH', '中微公司', 'CN', 'SH'),
        ('688008.SH', '澜起科技', 'CN', 'SH'),
        ('603501.SH', '韦尔股份', 'CN', 'SH'),
        ('688396.SH', '华润微', 'CN', 'SH'),
        ('688126.SH', '沪硅产业', 'CN', 'SH'),
        ('002371.SZ', '北方华创', 'CN', 'SZ'),
        ('603986.SH', '兆易创新', 'CN', 'SH'),
        ('688256.SH', '寒武纪', 'CN', 'SH'),
        ('688099.SH', '晶晨股份', 'CN', 'SH'),
        
        # 医药生物
        ('600276.SH', '恒瑞医药', 'CN', 'SH'),
        ('300760.SZ', '迈瑞医疗', 'CN', 'SZ'),
        ('300015.SZ', '爱尔眼科', 'CN', 'SZ'),
        ('603259.SH', '药明康德', 'CN', 'SH'),
        ('688185.SH', '康希诺', 'CN', 'SH'),
        ('688180.SH', '君实生物', 'CN', 'SH'),
        ('300122.SZ', '智飞生物', 'CN', 'SZ'),
        ('603392.SH', '万泰生物', 'CN', 'SH'),
        
        # 白酒食品
        ('600519.SH', '贵州茅台', 'CN', 'SH'),
        ('000858.SZ', '五粮液', 'CN', 'SZ'),
        ('000568.SZ', '泸州老窖', 'CN', 'SZ'),
        ('000596.SZ', '古井贡酒', 'CN', 'SZ'),
        ('000799.SZ', '酒鬼酒', 'CN', 'SZ'),
        ('603369.SH', '今世缘', 'CN', 'SH'),
        ('600702.SH', '舍得酒业', 'CN', 'SH'),
        ('603589.SH', '口子窖', 'CN', 'SH'),
        ('600887.SH', '伊利股份', 'CN', 'SH'),
        ('000895.SZ', '双汇发展', 'CN', 'SZ'),
        ('603288.SH', '海天味业', 'CN', 'SH'),
        ('600600.SH', '青岛啤酒', 'CN', 'SH'),
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
    print(f"第8批A股添加完成！")
    print(f"新增: {added} 只")
    print(f"跳过: {skipped} 只（已存在）")
    print(f"总计: {added + skipped} 只")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

