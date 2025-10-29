#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多A股股票（第五批）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager, init_database
from database.models import StockInfo
from datetime import datetime
from utils.config_loader import init_config

def add_more_stocks():
    """添加更多A股股票（第五批）"""
    
    # 初始化配置和数据库
    config = init_config()
    init_database(config)
    
    # 第五批A股（50只）- 继续补充各行业龙头和重要股票
    new_stocks = [
        # 煤炭
        ('601225.SH', '陕西煤业', 'CN', 'SH'),
        ('601898.SH', '中煤能源', 'CN', 'SH'),
        ('600188.SH', '兖矿能源', 'CN', 'SH'),
        
        # 石油石化
        ('600028.SH', '中国石化', 'CN', 'SH'),
        ('601857.SH', '中国石油', 'CN', 'SH'),
        ('600346.SH', '恒力石化', 'CN', 'SH'),
        
        # 电力
        ('600900.SH', '长江电力', 'CN', 'SH'),
        ('600886.SH', '国投电力', 'CN', 'SH'),
        ('600027.SH', '华电国际', 'CN', 'SH'),
        ('601991.SH', '大唐发电', 'CN', 'SH'),
        
        # 交通运输
        ('601006.SH', '大秦铁路', 'CN', 'SH'),
        ('601333.SH', '广深铁路', 'CN', 'SH'),
        ('600009.SH', '上海机场', 'CN', 'SH'),
        ('000089.SZ', '深圳机场', 'CN', 'SZ'),
        ('600004.SH', '白云机场', 'CN', 'SH'),
        
        # 港口航运
        ('601919.SH', '中远海控', 'CN', 'SH'),
        ('600018.SH', '上港集团', 'CN', 'SH'),
        ('601872.SH', '招商港口', 'CN', 'SH'),
        
        # 高速公路
        ('600548.SH', '深高速', 'CN', 'SH'),
        ('000429.SZ', '粤高速A', 'CN', 'SZ'),
        ('600377.SH', '宁沪高速', 'CN', 'SH'),
        
        # 建筑工程
        ('601800.SH', '中国交建', 'CN', 'SH'),
        ('601186.SH', '中国铁建', 'CN', 'SH'),
        ('601117.SH', '中国化学', 'CN', 'SH'),
        ('002051.SZ', '中工国际', 'CN', 'SZ'),
        
        # 钢铁
        ('600019.SH', '宝钢股份', 'CN', 'SH'),
        ('000709.SZ', '河钢股份', 'CN', 'SZ'),
        ('000898.SZ', '鞍钢股份', 'CN', 'SZ'),
        ('600808.SH', '马钢股份', 'CN', 'SH'),
        
        # 有色金属
        ('601899.SH', '紫金矿业', 'CN', 'SH'),
        ('600547.SH', '山东黄金', 'CN', 'SH'),
        ('002155.SZ', '湖南黄金', 'CN', 'SZ'),
        ('600489.SH', '中金黄金', 'CN', 'SH'),
        
        # 化工
        ('600309.SH', '万华化学', 'CN', 'SH'),
        ('600426.SH', '华鲁恒升', 'CN', 'SH'),
        ('002648.SZ', '卫星化学', 'CN', 'SZ'),
        ('600989.SH', '宝丰能源', 'CN', 'SH'),
        ('000830.SZ', '鲁西化工', 'CN', 'SZ'),
        
        # 建材
        ('600585.SH', '海螺水泥', 'CN', 'SH'),
        ('000877.SZ', '天山股份', 'CN', 'SZ'),
        ('601636.SH', '旗滨集团', 'CN', 'SH'),
        ('600176.SH', '中国巨石', 'CN', 'SH'),
        
        # 轻工制造
        ('002078.SZ', '太阳纸业', 'CN', 'SZ'),
        ('600793.SH', '宜宾纸业', 'CN', 'SH'),
        ('000488.SZ', '晨鸣纸业', 'CN', 'SZ'),
        
        # 纺织服装
        ('603899.SH', '晨光文具', 'CN', 'SH'),
        ('002563.SZ', '森马服饰', 'CN', 'SZ'),
        ('600398.SH', '海澜之家', 'CN', 'SH'),
        
        # 商贸零售
        ('601933.SH', '永辉超市', 'CN', 'SH'),
        ('601808.SH', '中海油服', 'CN', 'SH'),
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

