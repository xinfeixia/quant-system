#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取新增A股的历史数据（第六批）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager, init_database
from database.models import StockInfo, DailyData
from data_collection.tushare_client import TushareClient
from utils.config_loader import init_config
from datetime import datetime, timedelta
import time

def fetch_new_stocks_data():
    """获取新增股票的历史数据（第六批）"""
    
    # 初始化配置和数据库
    config_loader = init_config()
    config = config_loader.config
    init_database(config)

    # 直接使用token
    tushare_token = "39ba31bd5a19622303139eafd1f51b214efcb6e94986a949ad0f928f"
    tushare_client = TushareClient(token=tushare_token)
    
    # 新增的股票代码列表（第六批）
    new_symbols = [
        '300750.SZ',  # 宁德时代
        '300059.SZ',  # 东方财富
        '300015.SZ',  # 爱尔眼科
        '300760.SZ',  # 迈瑞医疗
        '300014.SZ',  # 亿纬锂能
        '688981.SH',  # 中芯国际
        '688599.SH',  # 天合光能
        '688223.SH',  # 晶科能源
        '688111.SH',  # 金山办公
        '688008.SH',  # 澜起科技
        '600519.SH',  # 贵州茅台
        '000858.SZ',  # 五粮液
        '000568.SZ',  # 泸州老窖
        '000596.SZ',  # 古井贡酒
        '600276.SH',  # 恒瑞医药
        '603259.SH',  # 药明康德
        '300122.SZ',  # 智飞生物
        '000538.SZ',  # 云南白药
        '600436.SH',  # 片仔癀
        '000333.SZ',  # 美的集团
        '000651.SZ',  # 格力电器
        '600690.SH',  # 海尔智家
        '600887.SH',  # 伊利股份
        '603288.SH',  # 海天味业
        '000895.SZ',  # 双汇发展
        '600600.SH',  # 青岛啤酒
        '002594.SZ',  # 比亚迪
        '601633.SH',  # 长城汽车
        '000625.SZ',  # 长安汽车
        '601238.SH',  # 广汽集团
        '601012.SH',  # 隆基绿能
        '002459.SZ',  # 晶澳科技
        '002129.SZ',  # TCL中环
        '300274.SZ',  # 阳光电源
        '002812.SZ',  # 恩捷股份
        '002460.SZ',  # 赣锋锂业
        '002466.SZ',  # 天齐锂业
        '002756.SZ',  # 永兴材料
        '002371.SZ',  # 北方华创
        '603501.SH',  # 韦尔股份
        '688012.SH',  # 中微公司
        '688396.SH',  # 华润微
        '603986.SH',  # 兆易创新
        '000063.SZ',  # 中兴通讯
        '600941.SH',  # 中国移动
        '600050.SH',  # 中国联通
        '601728.SH',  # 中国电信
        '002415.SZ',  # 海康威视
        '002475.SZ',  # 立讯精密
        '000725.SZ',  # 京东方A
        '002241.SZ',  # 歌尔股份
        '600150.SH',  # 中国船舶
        '600893.SH',  # 航发动力
        '002179.SZ',  # 中航光电
        '600038.SH',  # 中直股份
        '600030.SH',  # 中信证券
        '601688.SH',  # 华泰证券
        '601211.SH',  # 国泰君安
        '000776.SZ',  # 广发证券
    ]
    
    db_manager = get_db_manager()
    
    # 获取日期范围（最近1年）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"\n{'='*60}")
    print(f"开始获取 {len(new_symbols)} 只新增A股的历史数据")
    print(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")
    
    success_count = 0
    fail_count = 0
    total_records = 0
    
    start_time = time.time()
    
    for i, symbol in enumerate(new_symbols, 1):
        try:
            # 获取股票信息
            with db_manager.get_session() as session:
                stock = session.query(StockInfo).filter_by(symbol=symbol).first()
                if not stock:
                    print(f"⚠️  [{i}/{len(new_symbols)}] {symbol} 不存在于数据库")
                    fail_count += 1
                    continue
                
                stock_name = stock.name
            
            print(f"[{i}/{len(new_symbols)}] 获取 {symbol} - {stock_name}")
            
            # 获取历史数据
            daily_data = tushare_client.get_daily_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if daily_data and len(daily_data) > 0:
                # 保存到数据库
                with db_manager.get_session() as session:
                    # 删除已存在的数据（避免重复）
                    session.query(DailyData).filter_by(symbol=symbol).delete()
                    
                    # 批量插入
                    session.bulk_insert_mappings(DailyData, daily_data)
                    session.commit()
                
                print(f"  ✅ 保存 {len(daily_data)} 条数据")
                success_count += 1
                total_records += len(daily_data)
            else:
                print(f"  ❌ 未获取到数据")
                fail_count += 1
            
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            fail_count += 1
            continue
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"数据获取完成！")
    print(f"成功: {success_count}/{len(new_symbols)}")
    print(f"失败: {fail_count}/{len(new_symbols)}")
    print(f"总数据: {total_records:,} 条")
    print(f"总用时: {elapsed_time/60:.1f} 分钟")
    print(f"平均速度: {elapsed_time/len(new_symbols):.1f} 秒/股票")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    fetch_new_stocks_data()

