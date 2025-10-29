#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取新增A股的历史数据（第五批）
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
    """获取新增股票的历史数据（第五批）"""
    
    # 初始化配置和数据库
    config_loader = init_config()
    config = config_loader.config
    init_database(config)

    # 直接使用token
    tushare_token = "39ba31bd5a19622303139eafd1f51b214efcb6e94986a949ad0f928f"
    tushare_client = TushareClient(token=tushare_token)
    
    # 新增的股票代码列表（第五批）
    new_symbols = [
        '601225.SH',  # 陕西煤业
        '601898.SH',  # 中煤能源
        '600188.SH',  # 兖矿能源
        '600028.SH',  # 中国石化
        '601857.SH',  # 中国石油
        '600346.SH',  # 恒力石化
        '600900.SH',  # 长江电力
        '600886.SH',  # 国投电力
        '600027.SH',  # 华电国际
        '601991.SH',  # 大唐发电
        '601006.SH',  # 大秦铁路
        '601333.SH',  # 广深铁路
        '600009.SH',  # 上海机场
        '000089.SZ',  # 深圳机场
        '600004.SH',  # 白云机场
        '601919.SH',  # 中远海控
        '600018.SH',  # 上港集团
        '601872.SH',  # 招商港口
        '600548.SH',  # 深高速
        '000429.SZ',  # 粤高速A
        '600377.SH',  # 宁沪高速
        '601800.SH',  # 中国交建
        '601186.SH',  # 中国铁建
        '601117.SH',  # 中国化学
        '002051.SZ',  # 中工国际
        '600019.SH',  # 宝钢股份
        '000709.SZ',  # 河钢股份
        '000898.SZ',  # 鞍钢股份
        '600808.SH',  # 马钢股份
        '601899.SH',  # 紫金矿业
        '600547.SH',  # 山东黄金
        '002155.SZ',  # 湖南黄金
        '600489.SH',  # 中金黄金
        '600309.SH',  # 万华化学
        '600426.SH',  # 华鲁恒升
        '002648.SZ',  # 卫星化学
        '600989.SH',  # 宝丰能源
        '000830.SZ',  # 鲁西化工
        '600585.SH',  # 海螺水泥
        '000877.SZ',  # 天山股份
        '601636.SH',  # 旗滨集团
        '600176.SH',  # 中国巨石
        '002078.SZ',  # 太阳纸业
        '600793.SH',  # 宜宾纸业
        '000488.SZ',  # 晨鸣纸业
        '603899.SH',  # 晨光文具
        '002563.SZ',  # 森马服饰
        '600398.SH',  # 海澜之家
        '601933.SH',  # 永辉超市
        '601808.SH',  # 中海油服
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

