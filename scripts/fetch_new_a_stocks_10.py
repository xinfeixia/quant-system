#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取第10批A股历史数据
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
    """获取第10批A股历史数据"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 获取Tushare配置
    tushare_config = config_loader.api_config.get('tushare', {})
    token = tushare_config.get('token')
    if not token:
        raise ValueError("Tushare token未配置")
    
    tushare_client = TushareClient(token=token)
    
    # 第10批股票代码
    new_symbols = [
        # 化工新材料
        '600309.SH', '002648.SZ', '600426.SH', '002601.SZ', '002407.SZ',
        '600989.SH', '603806.SH', '300568.SZ', '300037.SZ', '002709.SZ',
        
        # 机械设备
        '603501.SH', '300124.SZ', '300450.SZ', '688169.SH', '688777.SH',
        '300316.SZ', '688012.SH', '688126.SH', '002371.SZ', '688008.SH',
        
        # 家电家居
        '000333.SZ', '000651.SZ', '600690.SH', '000596.SZ', '603369.SH',
        '603589.SH', '600702.SH', '002572.SZ', '603833.SH', '002833.SZ',
        
        # 汽车产业链
        '601799.SH', '600699.SH', '002920.SZ', '002050.SZ', '600741.SH',
        '002594.SZ', '601633.SH', '000625.SZ', '601238.SH', '600104.SH',
        
        # 食品饮料
        '600519.SH', '000858.SZ', '000568.SZ', '000799.SZ', '600887.SH',
        '000895.SZ', '603288.SH', '600600.SH', '603345.SH', '603517.SH',
        
        # 医药生物
        '300122.SZ', '603392.SH', '688185.SH', '300760.SZ', '300015.SZ',
        '600276.SH', '603259.SH', '688180.SH', '300529.SZ', '300676.SZ',
    ]
    
    # 获取最近1年的数据
    end_date = datetime.now()
    start_date = datetime.now() - timedelta(days=365)
    
    success_count = 0
    fail_count = 0
    total_records = 0
    
    print(f"\n{'='*60}")
    print(f"开始获取第10批A股历史数据")
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
    print(f"第10批A股数据获取完成！")
    print(f"成功: {success_count}/{len(new_symbols)} ({success_count/len(new_symbols)*100:.1f}%)")
    print(f"失败: {fail_count}/{len(new_symbols)} ({fail_count/len(new_symbols)*100:.1f}%)")
    print(f"总数据: {total_records} 条")
    print(f"总用时: {elapsed/60:.1f} 分钟")
    print(f"平均速度: {elapsed/len(new_symbols):.1f} 秒/股票")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

