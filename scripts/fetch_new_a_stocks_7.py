#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取第7批A股历史数据
"""

import sys
from pathlib import Path
import time
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import DailyData
from data_collection.tushare_client import TushareClient
from utils.config_loader import init_config

def main():
    """获取第7批A股历史数据"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()

    # 获取Tushare配置
    tushare_config = config_loader.api_config.get('tushare', {})
    token = tushare_config.get('token')
    if not token:
        raise ValueError("Tushare token未配置")

    tushare_client = TushareClient(token=token)
    
    # 第7批股票代码（与add_more_a_stocks_7.py保持一致）
    new_symbols = [
        # 医药生物
        '603127.SH', '300347.SZ', '002821.SZ', '688278.SH', '688180.SH',
        '688520.SH', '300595.SZ', '688016.SH', '688617.SH', '300896.SZ',
        
        # 半导体
        '688256.SH', '688099.SH', '688508.SH', '688595.SH', '688536.SH',
        '688368.SH', '688072.SH', '688012.SH', '688981.SH', '688396.SH',
        
        # 新能源
        '300750.SZ', '688390.SH', '688032.SH', '300763.SZ', '688063.SH',
        '300274.SZ', '601615.SH', '300443.SZ', '002202.SZ', '688339.SH',
        
        # 消费
        '603345.SH', '603517.SH', '603866.SH', '002507.SZ', '600887.SH',
        '002570.SZ', '603288.SH', '603369.SH', '603589.SH', '600702.SH',
        
        # 军工
        '600893.SH', '600760.SH', '600038.SH', '002179.SZ', '600150.SH',
        '688122.SH', '688559.SH', '688066.SH',
        
        # 软件互联网
        '688088.SH', '688023.SH', '688561.SH', '688019.SH', '688608.SH',
        
        # 新材料
        '688599.SH', '688005.SH', '688388.SH', '688123.SH', '688680.SH',
        
        # 汽车零部件
        '601799.SH', '600699.SH', '002050.SZ', '600741.SH', '002920.SZ',
    ]
    
    # 获取最近1年的数据
    end_date = datetime.now()
    start_date = datetime.now() - timedelta(days=365)
    
    success_count = 0
    fail_count = 0
    total_records = 0
    
    print(f"\n{'='*60}")
    print(f"开始获取第7批A股历史数据")
    print(f"股票数量: {len(new_symbols)} 只")
    print(f"时间范围: {start_date.strftime('%Y%m%d')} - {end_date.strftime('%Y%m%d')}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    for i, symbol in enumerate(new_symbols, 1):
        try:
            print(f"[{i}/{len(new_symbols)}] 获取 {symbol} 数据...", end=' ')
            
            # 获取历史数据
            daily_data = tushare_client.get_daily_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if daily_data and len(daily_data) > 0:
                # 保存到数据库
                with db_manager.get_session() as session:
                    # 删除旧数据
                    session.query(DailyData).filter_by(symbol=symbol).delete()
                    
                    # 插入新数据
                    session.bulk_insert_mappings(DailyData, daily_data)
                    session.commit()
                
                print(f"✅ 保存 {len(daily_data)} 条数据")
                success_count += 1
                total_records += len(daily_data)
            else:
                print(f"⚠️  无数据")
                fail_count += 1
            
            # 控制请求频率（Tushare限制50次/分钟）
            time.sleep(1.5)
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            fail_count += 1
            time.sleep(2)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"\n{'='*60}")
    print(f"第7批A股数据获取完成！")
    print(f"成功: {success_count}/{len(new_symbols)} ({success_count/len(new_symbols)*100:.1f}%)")
    print(f"失败: {fail_count}/{len(new_symbols)} ({fail_count/len(new_symbols)*100:.1f}%)")
    print(f"总数据: {total_records} 条")
    print(f"总用时: {elapsed/60:.1f} 分钟")
    print(f"平均速度: {elapsed/len(new_symbols):.1f} 秒/股票")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

