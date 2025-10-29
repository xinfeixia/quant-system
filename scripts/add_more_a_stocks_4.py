#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多A股股票（第四批）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager, init_database
from database.models import StockInfo
from datetime import datetime
from utils.config_loader import init_config

def add_more_stocks():
    """添加更多A股股票（第四批）"""
    
    # 初始化配置和数据库
    config = init_config()
    init_database(config)
    
    # 第四批A股（50只）- 补充各行业重要股票
    new_stocks = [
        # 银行（地方性银行）
        ('601916.SH', '浙商银行', 'CN', 'SH'),
        ('002839.SZ', '张家港行', 'CN', 'SZ'),
        ('601128.SH', '常熟银行', 'CN', 'SH'),
        ('601577.SH', '长沙银行', 'CN', 'SH'),

        # 房地产
        ('600606.SH', '绿地控股', 'CN', 'SH'),
        ('001872.SZ', '招商积余', 'CN', 'SZ'),
        ('600208.SH', '新湖中宝', 'CN', 'SH'),

        # 汽车及零部件
        ('601799.SH', '星宇股份', 'CN', 'SH'),
        ('600699.SH', '均胜电子', 'CN', 'SH'),
        ('002920.SZ', '德赛西威', 'CN', 'SZ'),
        ('600104.SH', '上汽集团', 'CN', 'SH'),

        # 电子元器件
        ('002463.SZ', '沪电股份', 'CN', 'SZ'),
        ('002185.SZ', '华天科技', 'CN', 'SZ'),
        ('600584.SH', '长电科技', 'CN', 'SH'),
        ('002156.SZ', '通富微电', 'CN', 'SZ'),
        ('002371.SZ', '北方华创', 'CN', 'SZ'),

        # 半导体
        ('603501.SH', '韦尔股份', 'CN', 'SH'),
        ('688256.SH', '寒武纪-U', 'CN', 'SH'),
        ('688521.SH', '芯原股份-U', 'CN', 'SH'),

        # 通信
        ('600050.SH', '中国联通', 'CN', 'SH'),
        ('600941.SH', '中国移动', 'CN', 'SH'),
        ('601728.SH', '中国电信', 'CN', 'SH'),

        # 传媒互联网
        ('300059.SZ', '东方财富', 'CN', 'SZ'),
        ('002027.SZ', '分众传媒', 'CN', 'SZ'),
        ('002555.SZ', '三七互娱', 'CN', 'SZ'),
        ('002624.SZ', '完美世界', 'CN', 'SZ'),
        ('300418.SZ', '昆仑万维', 'CN', 'SZ'),

        # 计算机软件
        ('600588.SH', '用友网络', 'CN', 'SH'),
        ('300454.SZ', '深信服', 'CN', 'SZ'),
        ('688111.SH', '金山办公', 'CN', 'SH'),
        ('002410.SZ', '广联达', 'CN', 'SZ'),

        # 食品饮料
        ('600887.SH', '伊利股份', 'CN', 'SH'),
        ('000568.SZ', '泸州老窖', 'CN', 'SZ'),
        ('603288.SH', '海天味业', 'CN', 'SH'),
        ('600132.SH', '重庆啤酒', 'CN', 'SH'),

        # 商贸零售
        ('601888.SH', '中国中免', 'CN', 'SH'),
        ('601100.SH', '恒立液压', 'CN', 'SH'),

        # 建筑装饰
        ('002271.SZ', '东方雨虹', 'CN', 'SZ'),
        ('002372.SZ', '伟星新材', 'CN', 'SZ'),
        ('603605.SH', '珀莱雅', 'CN', 'SH'),

        # 环保
        ('603568.SH', '伟明环保', 'CN', 'SH'),
        ('300070.SZ', '碧水源', 'CN', 'SZ'),

        # 农业
        ('002714.SZ', '牧原股份', 'CN', 'SZ'),
        ('000876.SZ', '新希望', 'CN', 'SZ'),
        ('002311.SZ', '海大集团', 'CN', 'SZ'),
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

