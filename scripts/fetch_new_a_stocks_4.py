#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取新增A股的历史数据（第四批）
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
    """获取新增股票的历史数据（第四批）"""
    
    # 初始化配置和数据库
    config_loader = init_config()
    config = config_loader.config
    init_database(config)

    # 直接使用token
    tushare_token = "39ba31bd5a19622303139eafd1f51b214efcb6e94986a949ad0f928f"
    tushare_client = TushareClient(token=tushare_token)
    
    # 新增的股票代码列表（第四批）
    new_symbols = [
        '601916.SH',  # 浙商银行
        '002839.SZ',  # 张家港行
        '601128.SH',  # 常熟银行
        '601577.SH',  # 长沙银行
        '600606.SH',  # 绿地控股
        '001872.SZ',  # 招商积余
        '600208.SH',  # 新湖中宝
        '601799.SH',  # 星宇股份
        '600699.SH',  # 均胜电子
        '002920.SZ',  # 德赛西威
        '600104.SH',  # 上汽集团
        '002463.SZ',  # 沪电股份
        '002185.SZ',  # 华天科技
        '600584.SH',  # 长电科技
        '002156.SZ',  # 通富微电
        '002371.SZ',  # 北方华创
        '603501.SH',  # 韦尔股份
        '688256.SH',  # 寒武纪-U
        '688521.SH',  # 芯原股份-U
        '600050.SH',  # 中国联通
        '600941.SH',  # 中国移动
        '601728.SH',  # 中国电信
        '300059.SZ',  # 东方财富
        '002027.SZ',  # 分众传媒
        '002555.SZ',  # 三七互娱
        '002624.SZ',  # 完美世界
        '300418.SZ',  # 昆仑万维
        '600588.SH',  # 用友网络
        '300454.SZ',  # 深信服
        '688111.SH',  # 金山办公
        '002410.SZ',  # 广联达
        '600887.SH',  # 伊利股份
        '000568.SZ',  # 泸州老窖
        '603288.SH',  # 海天味业
        '600132.SH',  # 重庆啤酒
        '601888.SH',  # 中国中免
        '601100.SH',  # 恒立液压
        '002271.SZ',  # 东方雨虹
        '002372.SZ',  # 伟星新材
        '603605.SH',  # 珀莱雅
        '603568.SH',  # 伟明环保
        '300070.SZ',  # 碧水源
        '002714.SZ',  # 牧原股份
        '000876.SZ',  # 新希望
        '002311.SZ',  # 海大集团
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

