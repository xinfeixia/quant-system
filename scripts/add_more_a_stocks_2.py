#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多A股股票到数据库（第二批）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager, init_database
from database.models import StockInfo
from datetime import datetime
from utils.config_loader import init_config

def add_more_stocks():
    """添加更多A股股票"""

    # 初始化配置和数据库
    config = init_config()
    init_database(config)

    # 更多重要A股（按行业分类）
    new_stocks = [
        # 银行股（补充）
        ('601818.SH', '光大银行', 'CN', 'SH'),
        ('600036.SH', '招商银行', 'CN', 'SH'),  # 可能重复，会自动跳过
        ('601998.SH', '中信银行', 'CN', 'SH'),
        ('600015.SH', '华夏银行', 'CN', 'SH'),  # 可能重复
        
        # 券商股（补充）
        ('600030.SH', '中信证券', 'CN', 'SH'),  # 可能重复
        ('600837.SH', '海通证券', 'CN', 'SH'),
        ('000166.SZ', '申万宏源', 'CN', 'SZ'),
        ('601377.SH', '兴业证券', 'CN', 'SH'),
        
        # 保险股（补充）
        ('601601.SH', '中国太保', 'CN', 'SH'),  # 可能重复
        
        # 钢铁股
        ('600019.SH', '宝钢股份', 'CN', 'SH'),
        ('000709.SZ', '河钢股份', 'CN', 'SZ'),
        ('600010.SH', '包钢股份', 'CN', 'SH'),
        
        # 有色金属
        ('601600.SH', '中国铝业', 'CN', 'SH'),
        ('600362.SH', '江西铜业', 'CN', 'SH'),
        ('000878.SZ', '云南铜业', 'CN', 'SZ'),
        ('002460.SZ', '赣锋锂业', 'CN', 'SZ'),  # 可能重复
        
        # 房地产（补充）
        ('600383.SH', '金地集团', 'CN', 'SH'),
        ('000002.SZ', '万科A', 'CN', 'SZ'),  # 可能重复
        ('001979.SZ', '招商蛇口', 'CN', 'SZ'),  # 可能重复
        
        # 零售消费
        ('601933.SH', '永辉超市', 'CN', 'SH'),
        ('002024.SZ', '苏宁易购', 'CN', 'SZ'),
        ('600729.SH', '重庆百货', 'CN', 'SH'),
        
        # 汽车零部件
        ('600660.SH', '福耀玻璃', 'CN', 'SH'),
        ('600741.SH', '华域汽车', 'CN', 'SH'),
        ('002050.SZ', '三花智控', 'CN', 'SZ'),
        
        # 航空航天
        ('601111.SH', '中国国航', 'CN', 'SH'),
        ('600029.SH', '南方航空', 'CN', 'SH'),
        ('600115.SH', '东方航空', 'CN', 'SH'),
        
        # 电力设备
        ('600089.SH', '特变电工', 'CN', 'SH'),
        ('000400.SZ', '许继电气', 'CN', 'SZ'),
        ('002074.SZ', '国轩高科', 'CN', 'SZ'),
        
        # 化工（补充）
        ('600426.SH', '华鲁恒升', 'CN', 'SH'),  # 可能重复
        ('600352.SH', '浙江龙盛', 'CN', 'SH'),
        ('002648.SZ', '卫星化学', 'CN', 'SZ'),  # 可能重复
        
        # 机械设备
        ('600031.SH', '三一重工', 'CN', 'SH'),  # 可能重复
        ('000157.SZ', '中联重科', 'CN', 'SZ'),
        ('002008.SZ', '大族激光', 'CN', 'SZ'),
        
        # 建材
        ('600585.SH', '海螺水泥', 'CN', 'SH'),  # 可能重复
        ('000401.SZ', '冀东水泥', 'CN', 'SZ'),
        ('600801.SH', '华新水泥', 'CN', 'SH'),
        
        # 家电（补充）
        ('000333.SZ', '美的集团', 'CN', 'SZ'),  # 可能重复
        ('000651.SZ', '格力电器', 'CN', 'SZ'),  # 可能重复
        ('600690.SH', '海尔智家', 'CN', 'SH'),  # 可能重复
        
        # 食品饮料（补充）
        ('600887.SH', '伊利股份', 'CN', 'SH'),  # 可能重复
        ('000858.SZ', '五粮液', 'CN', 'SZ'),  # 可能重复
        ('600519.SH', '贵州茅台', 'CN', 'SH'),  # 可能重复
        
        # 医药（补充）
        ('600276.SH', '恒瑞医药', 'CN', 'SH'),  # 可能重复
        ('000538.SZ', '云南白药', 'CN', 'SZ'),
        ('600436.SH', '片仔癀', 'CN', 'SH'),
        
        # 传媒
        ('300027.SZ', '华谊兄弟', 'CN', 'SZ'),
        ('002027.SZ', '分众传媒', 'CN', 'SZ'),  # 可能重复
        ('300413.SZ', '芒果超媒', 'CN', 'SZ'),
        
        # 通信
        ('600050.SH', '中国联通', 'CN', 'SH'),  # 可能重复
        ('600941.SH', '中国移动', 'CN', 'SH'),  # 可能重复
        ('600050.SH', '中国联通', 'CN', 'SH'),  # 可能重复
        
        # 计算机软件（补充）
        ('600588.SH', '用友网络', 'CN', 'SH'),
        ('002230.SZ', '科大讯飞', 'CN', 'SZ'),  # 可能重复
        ('300033.SZ', '同花顺', 'CN', 'SZ'),
        
        # 电子元器件（补充）
        ('002475.SZ', '立讯精密', 'CN', 'SZ'),  # 可能重复
        ('002456.SZ', '欧菲光', 'CN', 'SZ'),  # 可能重复
        ('002008.SZ', '大族激光', 'CN', 'SZ'),  # 可能重复
    ]
    
    db_manager = get_db_manager()
    
    added_count = 0
    skipped_count = 0
    
    with db_manager.get_session() as session:
        for symbol, name, market, exchange in new_stocks:
            # 检查是否已存在
            existing = session.query(StockInfo).filter_by(symbol=symbol).first()
            if existing:
                print(f"⚠️  跳过已存在: {symbol} - {name}")
                skipped_count += 1
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
            print(f"✅ 添加: {symbol} - {name}")
            added_count += 1
        
        session.commit()
    
    print(f"\n{'='*60}")
    print(f"添加完成！")
    print(f"新增: {added_count} 只")
    print(f"跳过: {skipped_count} 只（已存在）")
    print(f"{'='*60}")

if __name__ == '__main__':
    add_more_stocks()

