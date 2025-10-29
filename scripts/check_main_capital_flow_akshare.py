#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用AkShare查询主力资金流向（类似同花顺的暗盘资金指标）
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


def get_main_capital_flow_akshare(symbol, stock_name):
    """
    使用AkShare获取主力资金流向数据
    
    Args:
        symbol: 股票代码（如300364.SZ）
        stock_name: 股票名称
    """
    try:
        import akshare as ak
    except ImportError:
        print("\n❌ AkShare未安装")
        print("请运行: pip install akshare")
        return
    
    print(f"\n📊 查询 {stock_name}({symbol}) 的主力资金流向...")
    print("="*120)
    
    try:
        # 转换股票代码格式：300364.SZ -> 300364
        # 判断市场：SH=上海，SZ=深圳
        code = symbol.split('.')[0]
        market_code = symbol.split('.')[1].lower() if '.' in symbol else 'sz'

        # 获取个股资金流向数据
        print(f"\n正在获取数据...")
        df = ak.stock_individual_fund_flow(stock=code, market=market_code)

        if df is None or df.empty:
            print(f"\n❌ 未获取到资金流向数据")
            return

        # 按日期排序（最新的在前面）
        df = df.sort_values('日期', ascending=False)

        # 只显示最近5天
        df = df.head(5)

        # 检查数据日期
        if len(df) > 0:
            latest_date = str(df.iloc[0]['日期'])[:10]
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            print(f"\n最新数据日期: {latest_date}")
            print(f"今天日期: {today}")
        
        print(f"\n✅ 获取到 {len(df)} 天的资金流向数据")
        print("="*120)
        
        # 显示详细数据
        print(f"\n{'日期':<12} {'收盘价':<10} {'主力净流入':<18} {'超大单':<18} {'大单':<18} {'中单':<18} {'小单':<18}")
        print("-"*120)
        
        total_main_net = 0
        total_elg_net = 0
        total_lg_net = 0
        
        for _, row in df.iterrows():
            date = str(row['日期'])[:10] if '日期' in row else ''
            close = row.get('收盘价', 0)
            
            # 主力净流入（万元）
            main_net = row.get('主力净流入-净额', 0)
            
            # 超大单净流入（万元）
            elg_net = row.get('超大单净流入-净额', 0)
            
            # 大单净流入（万元）
            lg_net = row.get('大单净流入-净额', 0)
            
            # 中单净流入（万元）
            md_net = row.get('中单净流入-净额', 0)
            
            # 小单净流入（万元）
            sm_net = row.get('小单净流入-净额', 0)
            
            # 累计
            total_main_net += main_net
            total_elg_net += elg_net
            total_lg_net += lg_net
            
            # 格式化显示
            main_net_str = f"{'✅' if main_net >= 0 else '❌'} {main_net:>13.2f}万"
            elg_net_str = f"{'✅' if elg_net >= 0 else '❌'} {elg_net:>13.2f}万"
            lg_net_str = f"{'✅' if lg_net >= 0 else '❌'} {lg_net:>13.2f}万"
            md_net_str = f"{'✅' if md_net >= 0 else '❌'} {md_net:>13.2f}万"
            sm_net_str = f"{'✅' if sm_net >= 0 else '❌'} {sm_net:>13.2f}万"
            
            print(f"{date:<12} {close:<10.2f} {main_net_str:<18} {elg_net_str:<18} {lg_net_str:<18} {md_net_str:<18} {sm_net_str:<18}")
        
        print("="*120)
        
        # 统计分析
        print(f"\n📈 统计分析（最近5天）")
        print("="*120)
        
        print(f"主力资金累计净流入: {total_main_net:>18.2f} 万元")
        print(f"超大单累计净流入:   {total_elg_net:>18.2f} 万元")
        print(f"大单累计净流入:     {total_lg_net:>18.2f} 万元")
        
        # 判断资金流向
        print("\n" + "="*120)
        print("💡 资金流向判断")
        print("="*120)
        
        if total_main_net > 0:
            print(f"✅ 主力资金净流入 {total_main_net:.2f} 万元")
            if total_elg_net > 0:
                print(f"✅ 超大单（机构）净流入 {total_elg_net:.2f} 万元 - 机构看好")
            else:
                print(f"⚠️ 超大单（机构）净流出 {abs(total_elg_net):.2f} 万元 - 机构减仓")
            
            if total_lg_net > 0:
                print(f"✅ 大单（游资）净流入 {total_lg_net:.2f} 万元 - 游资进场")
            else:
                print(f"⚠️ 大单（游资）净流出 {abs(total_lg_net):.2f} 万元 - 游资离场")
        else:
            print(f"❌ 主力资金净流出 {abs(total_main_net):.2f} 万元")
            print(f"⚠️ 建议观望，等待主力资金回流")
        
        # 今天的资金流向
        if len(df) > 0:
            today_row = df.iloc[0]
            today_date = str(today_row['日期'])[:10] if '日期' in today_row else ''
            today_main_net = today_row.get('主力净流入-净额', 0)
            today_elg_net = today_row.get('超大单净流入-净额', 0)
            today_lg_net = today_row.get('大单净流入-净额', 0)
            
            print("\n" + "="*120)
            print(f"🎯 {today_date} 资金流向（今天）")
            print("="*120)
            
            if today_main_net > 0:
                print(f"💰 今天主力资金净流入: {today_main_net:.2f} 万元")
                if today_elg_net > 0 and today_lg_net > 0:
                    print(f"   ✅ 机构和游资同时流入 - 强烈看好信号！")
                elif today_elg_net > 0:
                    print(f"   ✅ 机构流入 {today_elg_net:.2f} 万元 - 机构建仓")
                elif today_lg_net > 0:
                    print(f"   ✅ 游资流入 {today_lg_net:.2f} 万元 - 游资炒作")
            else:
                print(f"💸 今天主力资金净流出: {abs(today_main_net):.2f} 万元")
                print(f"   ⚠️ 建议观望")
        
        print("="*120)
        
        # 显示主力净流入占比
        print(f"\n📊 主力净流入占比（最近5天）")
        print("="*120)
        
        for _, row in df.iterrows():
            date = str(row['日期'])[:10] if '日期' in row else ''
            main_pct = row.get('主力净流入-净占比', 0)
            elg_pct = row.get('超大单净流入-净占比', 0)
            lg_pct = row.get('大单净流入-净占比', 0)
            
            print(f"{date:<12} 主力: {main_pct:>6.2f}%  超大单: {elg_pct:>6.2f}%  大单: {lg_pct:>6.2f}%")
        
        print("="*120)
        
    except Exception as e:
        logger.error(f"获取资金流向数据失败: {e}")
        print(f"\n❌ 获取资金流向数据失败: {e}")
        print(f"\n💡 可能的原因：")
        print(f"  1. 网络连接问题")
        print(f"  2. AkShare数据源暂时不可用")
        print(f"  3. 股票代码格式错误")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='查询主力资金流向（暗盘资金）')
    parser.add_argument('--keyword', type=str, help='股票名称关键词')
    parser.add_argument('--symbol', type=str, help='股票代码')
    
    args = parser.parse_args()
    
    if args.keyword:
        stocks = find_stock(args.keyword)
        if stocks and len(stocks) == 1:
            symbol = stocks[0]['symbol']
            name = stocks[0]['name']
            print(f"\n将查询 {name}({symbol}) 的主力资金流向...")
            get_main_capital_flow_akshare(symbol, name)
        elif stocks and len(stocks) > 1:
            print(f"\n找到多只股票，请使用 --symbol 参数指定具体的股票代码")
    elif args.symbol:
        # 需要先查询股票名称
        stocks = find_stock('')
        get_main_capital_flow_akshare(args.symbol, args.symbol)
    else:
        print("请使用 --keyword 或 --symbol 参数")
        print("示例: python scripts/check_main_capital_flow_akshare.py --keyword 中文在线")

