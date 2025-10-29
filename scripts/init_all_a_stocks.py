#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从Tushare获取所有A股列表并添加到数据库
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import init_config
from database import get_db_manager, init_database
from database.models import StockInfo
from loguru import logger
import tushare as ts


def main():
    """从Tushare获取所有A股列表"""
    
    print("\n" + "=" * 60)
    print("从Tushare获取所有A股列表")
    print("=" * 60 + "\n")
    
    # 初始化
    logger.info('初始化配置与数据库...')
    config_dir = str(project_root / 'config')
    cfg_loader = init_config(config_dir=config_dir)
    init_database(cfg_loader.config)
    db_manager = get_db_manager()
    
    # 读取Tushare token
    ts_cfg = cfg_loader.api_config.get('tushare', {})
    token = ts_cfg.get('token')
    if not token:
        raise ValueError('Tushare token未配置')
    
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 获取所有A股列表
    logger.info('从 Tushare 获取所有A股列表...')
    print("正在从 Tushare 获取所有A股列表...\n")
    
    # 获取所有A股列表（不指定交易所，一次性获取）
    df = pro.stock_basic(list_status='L', fields='ts_code,symbol,name,area,industry,list_date,market')
    
    # 只保留沪深A股（排除北交所等）
    df = df[df['market'].isin(['主板', '创业板', '科创板'])].copy()
    
    logger.info(f'获取到 {len(df)} 只A股')
    print(f"获取到 {len(df)} 只A股\n")
    
    # 添加到数据库
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    print("开始添加到数据库...\n")
    
    with db_manager.get_session() as session:
        for i, row in df.iterrows():
            try:
                symbol = row['ts_code']  # 如 600000.SH
                name = row['name']
                industry = row['industry'] if 'industry' in row else None
                exchange = 'SH' if symbol.endswith('.SH') else 'SZ'
                
                # 检查是否已存在
                existing = session.query(StockInfo).filter_by(symbol=symbol).first()
                if existing:
                    skipped_count += 1
                    if (i + 1) % 100 == 0:
                        print(f"[{i+1}/{len(df)}] 处理中... (已添加: {added_count}, 跳过: {skipped_count})")
                    continue
                
                # 创建股票记录
                stock = StockInfo(
                    symbol=symbol,
                    name=name,
                    market='CN',
                    exchange=exchange,
                    currency='CNY',
                    lot_size=100,  # A股最小交易单位100股
                    industry=industry,
                    is_active=True,
                    created_at=datetime.now()
                )
                
                session.add(stock)
                added_count += 1
                
                if (i + 1) % 100 == 0:
                    session.commit()
                    print(f"[{i+1}/{len(df)}] 处理中... (已添加: {added_count}, 跳过: {skipped_count})")
                
            except Exception as e:
                logger.error(f"添加 {symbol} 失败: {e}")
                error_count += 1
                session.rollback()
        
        # 最后提交
        session.commit()
    
    print("\n" + "=" * 60)
    print("A股列表添加完成！")
    print("=" * 60)
    print(f"✅ 新增: {added_count} 只")
    print(f"⏭️  跳过: {skipped_count} 只 (已存在)")
    print(f"❌ 失败: {error_count} 只")
    print(f"📊 总计: {added_count + skipped_count} 只A股在数据库中")
    print("=" * 60 + "\n")
    
    print("💡 下一步:")
    print("   运行以下命令获取今日A股数据:")
    print("   python scripts/fetch_today_a_stocks_fast.py\n")


if __name__ == '__main__':
    main()

