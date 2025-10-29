#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询北交所股票的主力资金流向
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


def get_bj_stock_capital_flow(stock_code, stock_name):
    """
    获取北交所股票的主力资金流向
    
    Args:
        stock_code: 股票代码（如836807或920807）
        stock_name: 股票名称
    """
    try:
        import akshare as ak
    except ImportError:
        print("\n❌ AkShare未安装")
        print("请运行: pip install akshare")
        return
    
    print(f"\n📊 查询 {stock_name}({stock_code}) 的主力资金流向...")
    print("="*120)
    
    try:
        # 北交所股票使用bj作为市场代码
        print(f"\n正在获取数据...")
        
        # 尝试使用不同的代码格式
        codes_to_try = [stock_code, f"8{stock_code[1:]}", f"4{stock_code[1:]}"]
        
        df = None
        for code in codes_to_try:
            try:
                print(f"尝试代码: {code}")
                df = ak.stock_individual_fund_flow(stock=code, market="bj")
                if df is not None and not df.empty:
                    print(f"✅ 使用代码 {code} 成功获取数据")
                    break
            except Exception as e:
                logger.debug(f"代码 {code} 失败: {e}")
                continue
        
        if df is None or df.empty:
            print(f"\n❌ 未获取到资金流向数据")
            print(f"\n💡 可能的原因：")
            print(f"  1. 北交所股票可能不支持资金流向数据")
            print(f"  2. AkShare暂不支持北交所个股资金流")
            print(f"  3. 股票代码格式不正确")
            print(f"\n💡 建议：")
            print(f"  1. 查看北交所整体资金流向")
            print(f"  2. 使用同花顺等专业软件查看")
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
            print(f"🎯 {today_date} 资金流向（最新）")
            print("="*120)
            
            if today_main_net > 0:
                print(f"💰 最新主力资金净流入: {today_main_net:.2f} 万元")
                if today_elg_net > 0 and today_lg_net > 0:
                    print(f"   ✅ 机构和游资同时流入 - 强烈看好信号！")
                elif today_elg_net > 0:
                    print(f"   ✅ 机构流入 {today_elg_net:.2f} 万元 - 机构建仓")
                elif today_lg_net > 0:
                    print(f"   ✅ 游资流入 {today_lg_net:.2f} 万元 - 游资炒作")
            else:
                print(f"💸 最新主力资金净流出: {abs(today_main_net):.2f} 万元")
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
        print(f"  1. 北交所股票可能不支持资金流向数据")
        print(f"  2. AkShare暂不支持北交所个股资金流")
        print(f"  3. 网络连接问题")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='查询北交所股票主力资金流向')
    parser.add_argument('--code', type=str, required=True, help='股票代码（如836807）')
    parser.add_argument('--name', type=str, default='', help='股票名称')
    
    args = parser.parse_args()
    
    stock_name = args.name if args.name else args.code
    get_bj_stock_capital_flow(args.code, stock_name)

