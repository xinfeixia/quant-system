#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多A股股票（第三批）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager, init_database
from database.models import StockInfo
from datetime import datetime
from utils.config_loader import init_config

def add_more_stocks():
    """添加更多A股股票（第三批）"""
    
    # 初始化配置和数据库
    config = init_config()
    init_database(config)
    
    # 第三批A股（40只）- 补充各行业重要股票
    new_stocks = [
        # 白酒（补充）
        ('600702.SH', '舍得酒业', 'CN', 'SH'),
        ('603369.SH', '迎驾贡酒', 'CN', 'SH'),  # 可能重复
        ('603589.SH', '口子窖', 'CN', 'SH'),
        
        # 食品饮料
        ('002507.SZ', '涪陵榨菜', 'CN', 'SZ'),
        ('603345.SH', '安井食品', 'CN', 'SH'),
        ('603517.SH', '绝味食品', 'CN', 'SH'),
        ('603866.SH', '桃李面包', 'CN', 'SH'),
        
        # 软件
        ('002065.SZ', '东方国信', 'CN', 'SZ'),
        ('600845.SH', '宝信软件', 'CN', 'SH'),
        ('002405.SZ', '四维图新', 'CN', 'SZ'),
        
        # 半导体设备
        ('688082.SH', '盛美上海', 'CN', 'SH'),
        ('688200.SH', '华峰测控', 'CN', 'SH'),
        
        # 通信设备
        ('600498.SH', '烽火通信', 'CN', 'SH'),
        ('002281.SZ', '光迅科技', 'CN', 'SZ'),
        ('300308.SZ', '中际旭创', 'CN', 'SZ'),
        
        # 医疗器械
        ('002223.SZ', '鱼跃医疗', 'CN', 'SZ'),
        ('688029.SH', '南微医学', 'CN', 'SH'),
        
        # CRO
        ('300759.SZ', '康龙化成', 'CN', 'SZ'),
        ('603127.SH', '昭衍新药', 'CN', 'SH'),
        
        # 医疗服务
        ('600763.SH', '通策医疗', 'CN', 'SH'),
        ('002044.SZ', '美年健康', 'CN', 'SZ'),
        
        # 创新药
        ('688235.SH', '百济神州-U', 'CN', 'SH'),
        ('688180.SH', '君实生物', 'CN', 'SH'),
        
        # 锂电材料
        ('603659.SH', '璞泰来', 'CN', 'SH'),
        ('300037.SZ', '新宙邦', 'CN', 'SZ'),
        ('002709.SZ', '天赐材料', 'CN', 'SZ'),
        ('002407.SZ', '多氟多', 'CN', 'SZ'),
        
        # 光伏辅材
        ('603806.SH', '福斯特', 'CN', 'SH'),
        ('688002.SH', '睿创微纳', 'CN', 'SH'),
        
        # 稀土
        ('600111.SH', '北方稀土', 'CN', 'SH'),
        ('600392.SH', '盛和资源', 'CN', 'SH'),
        
        # 工程机械
        ('000528.SZ', '柳工', 'CN', 'SZ'),
        ('000680.SZ', '山推股份', 'CN', 'SZ'),
        ('601766.SH', '中国中车', 'CN', 'SH'),
        
        # 化工
        ('600486.SH', '扬农化工', 'CN', 'SH'),
        ('002258.SZ', '利尔化学', 'CN', 'SZ'),
        
        # 有色金属
        ('603993.SH', '洛阳钼业', 'CN', 'SH'),
        ('002532.SZ', '天山铝业', 'CN', 'SZ'),
        
        # 券商
        ('601555.SH', '东吴证券', 'CN', 'SH'),
        ('000783.SZ', '长江证券', 'CN', 'SZ'),
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
    print(f"跳过: {skipped} 只")
    print(f"A股总数: {added + skipped} 只（本批次）")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    add_more_stocks()

