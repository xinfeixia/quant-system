#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查今天是否是交易日，并尝试获取今天的数据
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import init_config
import tushare as ts

def main():
    """检查今天是否是交易日"""
    config_loader = init_config()
    
    # 获取Tushare配置
    tushare_config = config_loader.api_config.get('tushare', {})
    token = tushare_config.get('token')
    if not token:
        raise ValueError("Tushare token未配置")
    
    ts.set_token(token)
    pro = ts.pro_api()
    
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    
    print(f"\n{'='*60}")
    print(f"📅 今天日期: {today.strftime('%Y年%m月%d日 %A')}")
    print(f"{'='*60}\n")
    
    # 尝试获取最近几天的交易日数据
    print("🔍 检查最近的交易日...\n")
    
    for i in range(0, 5):
        check_date = today - timedelta(days=i)
        check_date_str = check_date.strftime('%Y%m%d')
        
        try:
            # 尝试获取该日期的数据
            df = pro.daily(trade_date=check_date_str)
            
            if df is not None and not df.empty:
                print(f"✅ {check_date.strftime('%Y-%m-%d (%A)')}: 有交易数据 ({len(df)} 条记录)")
                if i == 0:
                    print(f"   👉 今天是交易日！数据已更新")
                elif i == 1:
                    print(f"   👉 昨天是最近的交易日")
                else:
                    print(f"   👉 这是 {i} 天前的交易日")
            else:
                print(f"❌ {check_date.strftime('%Y-%m-%d (%A)')}: 无交易数据（休市）")
                
        except Exception as e:
            print(f"⚠️  {check_date.strftime('%Y-%m-%d (%A)')}: 查询失败 - {e}")
    
    print(f"\n{'='*60}")
    print("💡 说明:")
    print("- 如果今天有数据，说明是交易日且数据已更新")
    print("- 如果今天无数据，可能是:")
    print("  1. 今天是周末/节假日（休市）")
    print("  2. 数据还未更新（通常收盘后1-2小时更新）")
    print("  3. API限制或网络问题")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()

