#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取新增A股的历史数据（第二批）
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
    """获取新增股票的历史数据"""

    # 初始化配置和数据库
    config_loader = init_config()
    config = config_loader.config
    init_database(config)

    # 直接使用token
    tushare_token = "39ba31bd5a19622303139eafd1f51b214efcb6e94986a949ad0f928f"
    tushare_client = TushareClient(token=tushare_token)
    
    # 新增的股票代码列表（第二批）
    new_symbols = [
        '601818.SH',  # 光大银行
        '601998.SH',  # 中信银行
        '600837.SH',  # 海通证券
        '000166.SZ',  # 申万宏源
        '601377.SH',  # 兴业证券
        '600019.SH',  # 宝钢股份
        '000709.SZ',  # 河钢股份
        '600010.SH',  # 包钢股份
        '601600.SH',  # 中国铝业
        '600362.SH',  # 江西铜业
        '000878.SZ',  # 云南铜业
        '600383.SH',  # 金地集团
        '601933.SH',  # 永辉超市
        '002024.SZ',  # 苏宁易购
        '600729.SH',  # 重庆百货
        '600660.SH',  # 福耀玻璃
        '600741.SH',  # 华域汽车
        '002050.SZ',  # 三花智控
        '601111.SH',  # 中国国航
        '600029.SH',  # 南方航空
        '600115.SH',  # 东方航空
        '600089.SH',  # 特变电工
        '000400.SZ',  # 许继电气
        '002074.SZ',  # 国轩高科
        '600352.SH',  # 浙江龙盛
        '000157.SZ',  # 中联重科
        '002008.SZ',  # 大族激光
        '000401.SZ',  # 冀东水泥
        '600801.SH',  # 华新水泥
        '000538.SZ',  # 云南白药
        '600436.SH',  # 片仔癀
        '300027.SZ',  # 华谊兄弟
        '300413.SZ',  # 芒果超媒
        '600588.SH',  # 用友网络
        '300033.SZ',  # 同花顺
    ]
    
    db_manager = get_db_manager()
    
    # 获取365天的历史数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    total = len(new_symbols)
    success_count = 0
    fail_count = 0
    total_saved = 0
    
    print(f"\n{'='*60}")
    print(f"开始获取 {total} 只新增A股的历史数据")
    print(f"时间范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    for idx, symbol in enumerate(new_symbols, 1):
        try:
            # 获取股票信息
            with db_manager.get_session() as session:
                stock = session.query(StockInfo).filter_by(symbol=symbol).first()
                if not stock:
                    print(f"[{idx}/{total}] ⚠️  {symbol} - 股票不存在，跳过")
                    fail_count += 1
                    continue
                
                stock_name = stock.name
            
            print(f"[{idx}/{total}] 获取 {symbol} - {stock_name}")
            
            # 获取历史数据
            data_list = tushare_client.get_daily_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if not data_list:
                print(f"  ⚠️  没有获取到数据")
                fail_count += 1
                continue
            
            # 保存到数据库
            saved_count = 0
            with db_manager.get_session() as session:
                for data in data_list:
                    # 检查是否已存在
                    existing = session.query(DailyData).filter_by(
                        symbol=data['symbol'],
                        trade_date=data['trade_date']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # 创建新记录
                    daily_data = DailyData(**data)
                    session.add(daily_data)
                    saved_count += 1
                
                session.commit()
            
            total_saved += saved_count
            print(f"  ✅ 保存 {saved_count} 条数据")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            fail_count += 1
            continue
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"数据获取完成！")
    print(f"成功: {success_count}/{total}")
    print(f"失败: {fail_count}/{total}")
    print(f"总保存: {total_saved} 条数据")
    print(f"总用时: {elapsed_time/60:.1f} 分钟")
    print(f"平均速度: {elapsed_time/total:.1f} 秒/股票")
    print(f"{'='*60}")

if __name__ == '__main__':
    fetch_new_stocks_data()

