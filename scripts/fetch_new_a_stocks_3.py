#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取新增A股的历史数据（第三批）
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
    """获取新增股票的历史数据（第三批）"""
    
    # 初始化配置和数据库
    config_loader = init_config()
    config = config_loader.config
    init_database(config)

    # 直接使用token
    tushare_token = "39ba31bd5a19622303139eafd1f51b214efcb6e94986a949ad0f928f"
    tushare_client = TushareClient(token=tushare_token)
    
    # 新增的股票代码列表（第三批）
    new_symbols = [
        '600702.SH',  # 舍得酒业
        '603589.SH',  # 口子窖
        '002507.SZ',  # 涪陵榨菜
        '603345.SH',  # 安井食品
        '603517.SH',  # 绝味食品
        '603866.SH',  # 桃李面包
        '002065.SZ',  # 东方国信
        '600845.SH',  # 宝信软件
        '002405.SZ',  # 四维图新
        '688082.SH',  # 盛美上海
        '688200.SH',  # 华峰测控
        '600498.SH',  # 烽火通信
        '002281.SZ',  # 光迅科技
        '300308.SZ',  # 中际旭创
        '002223.SZ',  # 鱼跃医疗
        '688029.SH',  # 南微医学
        '300759.SZ',  # 康龙化成
        '603127.SH',  # 昭衍新药
        '600763.SH',  # 通策医疗
        '002044.SZ',  # 美年健康
        '688235.SH',  # 百济神州-U
        '688180.SH',  # 君实生物
        '603659.SH',  # 璞泰来
        '300037.SZ',  # 新宙邦
        '002709.SZ',  # 天赐材料
        '002407.SZ',  # 多氟多
        '603806.SH',  # 福斯特
        '688002.SH',  # 睿创微纳
        '600111.SH',  # 北方稀土
        '600392.SH',  # 盛和资源
        '000528.SZ',  # 柳工
        '000680.SZ',  # 山推股份
        '601766.SH',  # 中国中车
        '600486.SH',  # 扬农化工
        '002258.SZ',  # 利尔化学
        '603993.SH',  # 洛阳钼业
        '002532.SZ',  # 天山铝业
        '601555.SH',  # 东吴证券
        '000783.SZ',  # 长江证券
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

