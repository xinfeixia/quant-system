#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取第9批A股历史数据
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
    """获取第9批A股历史数据"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 获取Tushare配置
    tushare_config = config_loader.api_config.get('tushare', {})
    token = tushare_config.get('token')
    if not token:
        raise ValueError("Tushare token未配置")
    
    tushare_client = TushareClient(token=token)
    
    # 第9批股票代码
    new_symbols = [
        # 医疗器械与服务
        '300529.SZ', '300676.SZ', '300482.SZ', '688278.SH', '688520.SH',
        '300595.SZ', '300896.SZ', '688016.SH', '688617.SH', '300347.SZ',
        
        # 半导体设备与材料
        '688072.SH', '688508.SH', '688536.SH', '688368.SH', '688595.SH',
        '688019.SH', '688388.SH', '688123.SH', '688680.SH', '688608.SH',
        
        # 新能源与储能
        '688390.SH', '688032.SH', '300763.SZ', '688063.SH', '300443.SZ',
        '688339.SH', '601615.SH', '002202.SZ',
        
        # 军工与航天
        '688122.SH', '688559.SH', '688066.SH', '300775.SZ', '300726.SZ',
        
        # 软件与信息安全
        '688088.SH', '688023.SH', '688561.SH', '688777.SH', '688169.SH',
        
        # 消费品与服务
        '002570.SZ', '300999.SZ', '603345.SH', '603517.SH', '603866.SH',
        '002507.SZ', '603127.SH', '002821.SZ',
        
        # 新材料
        '688005.SH', '300568.SZ', '300037.SZ', '002709.SZ',
    ]
    
    # 获取最近1年的数据
    end_date = datetime.now()
    start_date = datetime.now() - timedelta(days=365)
    
    success_count = 0
    fail_count = 0
    total_records = 0
    
    print(f"\n{'='*60}")
    print(f"开始获取第9批A股历史数据")
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
    print(f"第9批A股数据获取完成！")
    print(f"成功: {success_count}/{len(new_symbols)} ({success_count/len(new_symbols)*100:.1f}%)")
    print(f"失败: {fail_count}/{len(new_symbols)} ({fail_count/len(new_symbols)*100:.1f}%)")
    print(f"总数据: {total_records} 条")
    print(f"总用时: {elapsed/60:.1f} 分钟")
    print(f"平均速度: {elapsed/len(new_symbols):.1f} 秒/股票")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

