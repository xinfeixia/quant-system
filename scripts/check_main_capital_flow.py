#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询主力资金流向（类似同花顺的暗盘资金指标）
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from database.models import StockInfo
from utils.config_loader import init_config
from loguru import logger
import tushare as ts
from datetime import datetime, timedelta


def find_stock(keyword):
    """
    根据关键词查找股票
    
    Args:
        keyword: 股票名称关键词
    """
    config = init_config()
    db = DatabaseManager(config)
    
    with db.get_session() as session:
        # 模糊查询股票名称
        stocks = session.query(StockInfo).filter(
            StockInfo.name.like(f'%{keyword}%')
        ).all()
        
        if not stocks:
            print(f"\n❌ 未找到包含 '{keyword}' 的股票")
            return None
        
        # 转换为字典列表，避免session关闭后无法访问
        stock_list = []
        for stock in stocks:
            stock_list.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'market': stock.market
            })
        
        print(f"\n找到 {len(stock_list)} 只股票：")
        print("-" * 80)
        for stock in stock_list:
            print(f"{stock['symbol']:<15} {stock['name']:<30} {stock['market']}")
        print("-" * 80)
        
        return stock_list


def get_main_capital_flow(symbol, days=5):
    """
    获取主力资金流向数据（类似同花顺的暗盘资金）
    
    Args:
        symbol: 股票代码
        days: 查询天数
    """
    config = init_config()

    # 初始化Tushare
    token = config.get_api('tushare.token')
    ts.set_token(token)
    pro = ts.pro_api()
    
    print(f"\n📊 查询 {symbol} 最近{days}天的主力资金流向...")
    print("="*100)
    
    try:
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        # 转换股票代码格式（300364.SZ -> 300364.SZ）
        ts_code = symbol
        
        # 获取个股资金流向数据
        df = pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df is None or df.empty:
            print(f"\n❌ 未获取到资金流向数据")
            print(f"\n💡 可能的原因：")
            print(f"  1. Tushare权限不足（需要积分>=2000）")
            print(f"  2. 该股票没有资金流向数据")
            print(f"  3. 日期范围内没有交易日")
            return
        
        # 按日期排序
        df = df.sort_values('trade_date', ascending=False)
        
        print(f"\n✅ 获取到 {len(df)} 天的资金流向数据")
        print("="*100)
        
        # 显示详细数据
        print(f"\n{'日期':<12} {'主力净流入':<15} {'超大单':<15} {'大单':<15} {'中单':<15} {'小单':<15}")
        print("-"*100)
        
        for _, row in df.iterrows():
            date = row['trade_date']
            # 主力净流入 = 超大单 + 大单
            main_net = row.get('buy_elg_amount', 0) - row.get('sell_elg_amount', 0) + \
                      row.get('buy_lg_amount', 0) - row.get('sell_lg_amount', 0)
            
            # 超大单净流入
            elg_net = row.get('buy_elg_amount', 0) - row.get('sell_elg_amount', 0)
            
            # 大单净流入
            lg_net = row.get('buy_lg_amount', 0) - row.get('sell_lg_amount', 0)
            
            # 中单净流入
            md_net = row.get('buy_md_amount', 0) - row.get('sell_md_amount', 0)
            
            # 小单净流入
            sm_net = row.get('buy_sm_amount', 0) - row.get('sell_sm_amount', 0)
            
            # 格式化显示（单位：万元）
            main_net_str = f"{main_net/10000:>13.2f}万" if main_net >= 0 else f"{main_net/10000:>13.2f}万"
            elg_net_str = f"{elg_net/10000:>13.2f}万" if elg_net >= 0 else f"{elg_net/10000:>13.2f}万"
            lg_net_str = f"{lg_net/10000:>13.2f}万" if lg_net >= 0 else f"{lg_net/10000:>13.2f}万"
            md_net_str = f"{md_net/10000:>13.2f}万" if md_net >= 0 else f"{md_net/10000:>13.2f}万"
            sm_net_str = f"{sm_net/10000:>13.2f}万" if sm_net >= 0 else f"{sm_net/10000:>13.2f}万"
            
            print(f"{date:<12} {main_net_str:<15} {elg_net_str:<15} {lg_net_str:<15} {md_net_str:<15} {sm_net_str:<15}")
        
        print("="*100)
        
        # 统计分析
        print(f"\n📈 统计分析（最近{days}天）")
        print("="*100)
        
        # 计算总净流入
        total_main_net = 0
        total_elg_net = 0
        total_lg_net = 0
        
        for _, row in df.iterrows():
            main_net = row.get('buy_elg_amount', 0) - row.get('sell_elg_amount', 0) + \
                      row.get('buy_lg_amount', 0) - row.get('sell_lg_amount', 0)
            elg_net = row.get('buy_elg_amount', 0) - row.get('sell_elg_amount', 0)
            lg_net = row.get('buy_lg_amount', 0) - row.get('sell_lg_amount', 0)
            
            total_main_net += main_net
            total_elg_net += elg_net
            total_lg_net += lg_net
        
        print(f"主力资金累计净流入: {total_main_net/10000:>15.2f} 万元")
        print(f"超大单累计净流入:   {total_elg_net/10000:>15.2f} 万元")
        print(f"大单累计净流入:     {total_lg_net/10000:>15.2f} 万元")
        
        # 判断资金流向
        print("\n" + "="*100)
        print("💡 资金流向判断")
        print("="*100)
        
        if total_main_net > 0:
            print(f"✅ 主力资金净流入 {total_main_net/10000:.2f} 万元")
            if total_elg_net > 0:
                print(f"✅ 超大单（机构）净流入 {total_elg_net/10000:.2f} 万元")
            else:
                print(f"⚠️ 超大单（机构）净流出 {abs(total_elg_net)/10000:.2f} 万元")
            
            if total_lg_net > 0:
                print(f"✅ 大单（游资）净流入 {total_lg_net/10000:.2f} 万元")
            else:
                print(f"⚠️ 大单（游资）净流出 {abs(total_lg_net)/10000:.2f} 万元")
        else:
            print(f"❌ 主力资金净流出 {abs(total_main_net)/10000:.2f} 万元")
            print(f"⚠️ 建议观望，等待主力资金回流")
        
        # 今天的资金流向
        if len(df) > 0:
            today_row = df.iloc[0]
            today_date = today_row['trade_date']
            today_main_net = today_row.get('buy_elg_amount', 0) - today_row.get('sell_elg_amount', 0) + \
                           today_row.get('buy_lg_amount', 0) - today_row.get('sell_lg_amount', 0)
            
            print("\n" + "="*100)
            print(f"🎯 {today_date} 资金流向")
            print("="*100)
            
            if today_main_net > 0:
                print(f"💰 今天主力资金净流入: {today_main_net/10000:.2f} 万元")
            else:
                print(f"💸 今天主力资金净流出: {abs(today_main_net)/10000:.2f} 万元")
        
        print("="*100)
        
    except Exception as e:
        logger.error(f"获取资金流向数据失败: {e}")
        print(f"\n❌ 获取资金流向数据失败: {e}")
        print(f"\n💡 可能的原因：")
        print(f"  1. Tushare权限不足（资金流向数据需要积分>=2000）")
        print(f"  2. API调用频率超限")
        print(f"  3. 网络连接问题")
        print(f"\n💡 解决方案：")
        print(f"  1. 升级Tushare积分：https://tushare.pro/document/1?doc_id=13")
        print(f"  2. 使用AkShare等其他免费数据源")
        print(f"  3. 使用我们自己的资金流入监控系统（基于分钟数据计算）")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='查询主力资金流向（暗盘资金）')
    parser.add_argument('--keyword', type=str, help='股票名称关键词')
    parser.add_argument('--symbol', type=str, help='股票代码')
    parser.add_argument('--days', type=int, default=5, help='查询天数（默认5天）')
    
    args = parser.parse_args()
    
    if args.keyword:
        stocks = find_stock(args.keyword)
        if stocks and len(stocks) == 1:
            symbol = stocks[0]['symbol']
            print(f"\n将查询 {symbol} 的主力资金流向...")
            get_main_capital_flow(symbol, args.days)
        elif stocks and len(stocks) > 1:
            print(f"\n请使用 --symbol 参数指定具体的股票代码")
    elif args.symbol:
        get_main_capital_flow(args.symbol, args.days)
    else:
        print("请使用 --keyword 或 --symbol 参数")
        print("示例: python scripts/check_main_capital_flow.py --keyword 中文在线 --days 5")

