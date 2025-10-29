#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用东方财富网接口查询股票信息（包括北交所）
"""
import requests
import json
from datetime import datetime


def get_stock_info_eastmoney(stock_code, stock_name):
    """
    从东方财富网获取股票信息
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
    """
    print(f"\n📊 查询 {stock_name}({stock_code}) 的实时行情...")
    print("="*100)
    
    try:
        # 北交所股票代码格式：0.836807 或 0.920807
        # 构造东方财富网API URL
        secid = f"0.{stock_code}"  # 北交所使用0作为市场代码
        
        # 实时行情接口
        url = f"http://push2.eastmoney.com/api/qt/stock/get"
        params = {
            'secid': secid,
            'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f107,f152,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f193,f194,f195,f196,f197,f198,f199,f200,f201,f202,f203,f204,f205,f206,f207,f208,f209,f210,f211,f212,f213,f214,f215,f216,f217,f218,f219,f220,f221,f222,f223,f224,f225,f226,f227,f228,f229,f230,f231,f232,f233,f234,f235,f236,f237,f238,f239,f240,f241,f242,f243,f244,f245,f246,f247,f248,f249,f250,f251,f252,f253,f254,f255,f256,f257,f258,f259,f260,f261,f262,f263,f264,f265,f266,f267,f268,f269,f270,f271,f272,f273,f274,f275,f276,f277,f278,f279,f280,f281,f282,f283,f284,f285,f286,f287,f288,f289,f290,f291,f292,f293,f294,f295,f296,f297,f298,f299,f300,f301,f302,f303,f304,f305,f306,f307,f308,f309,f310,f311,f312,f313,f314,f315,f316,f317,f318,f319,f320,f321,f322,f323,f324,f325,f326,f327,f328,f329,f330,f331,f332,f333,f334,f335,f336,f337,f338,f339,f340,f341,f342,f343,f344,f345,f346,f347,f348,f349,f350,f351,f352,f353,f354,f355,f356,f357,f358,f359,f360,f361,f362,f363,f364,f365,f366,f367,f368,f369,f370,f371,f372,f373,f374,f375,f376,f377,f378,f379,f380,f381,f382,f383,f384,f385,f386,f387,f388,f389,f390,f391,f392,f393,f394,f395,f396,f397,f398,f399,f400',
            'ut': 'fa5fd1943c7b386f172d6893dbfba10b'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return
        
        data = response.json()
        
        if data.get('rc') != 0 or not data.get('data'):
            print(f"❌ 未获取到数据")
            print(f"返回信息: {data}")
            return
        
        stock_data = data['data']
        
        # 解析数据
        print(f"\n✅ 获取到实时行情数据")
        print("="*100)
        
        # 基本信息
        print(f"\n【基本信息】")
        print(f"股票名称: {stock_name}")
        print(f"股票代码: {stock_code}")
        print(f"最新价: ¥{stock_data.get('f43', 0) / 100:.2f}")
        print(f"涨跌幅: {stock_data.get('f170', 0) / 100:+.2f}%")
        print(f"涨跌额: ¥{stock_data.get('f169', 0) / 100:+.2f}")
        print(f"今开: ¥{stock_data.get('f46', 0) / 100:.2f}")
        print(f"昨收: ¥{stock_data.get('f60', 0) / 100:.2f}")
        print(f"最高: ¥{stock_data.get('f44', 0) / 100:.2f}")
        print(f"最低: ¥{stock_data.get('f45', 0) / 100:.2f}")
        
        # 成交信息
        print(f"\n【成交信息】")
        volume = stock_data.get('f47', 0)  # 成交量（手）
        turnover = stock_data.get('f48', 0)  # 成交额（元）
        print(f"成交量: {volume:,.0f} 手")
        print(f"成交额: ¥{turnover / 100000000:.2f} 亿")
        print(f"换手率: {stock_data.get('f168', 0) / 100:.2f}%")
        
        # 资金流向（如果有）
        print(f"\n【资金流向】")
        print(f"⚠️ 东方财富网API暂不直接提供北交所个股资金流向数据")
        print(f"建议：")
        print(f"  1. 访问东方财富网查看详细资金流向")
        print(f"  2. 使用同花顺等专业软件")
        print(f"  3. 关注成交量和换手率变化")
        
        # 判断
        print(f"\n【简单分析】")
        change_pct = stock_data.get('f170', 0) / 100
        turnover_rate = stock_data.get('f168', 0) / 100
        
        if change_pct > 5:
            print(f"✅ 今日大涨 {change_pct:+.2f}%")
        elif change_pct > 2:
            print(f"✅ 今日上涨 {change_pct:+.2f}%")
        elif change_pct > 0:
            print(f"⚠️ 今日微涨 {change_pct:+.2f}%")
        elif change_pct > -2:
            print(f"⚠️ 今日微跌 {change_pct:+.2f}%")
        else:
            print(f"❌ 今日下跌 {change_pct:+.2f}%")
        
        if turnover_rate > 10:
            print(f"✅ 换手率高 {turnover_rate:.2f}% - 交易活跃")
        elif turnover_rate > 5:
            print(f"⚠️ 换手率中等 {turnover_rate:.2f}%")
        else:
            print(f"❌ 换手率低 {turnover_rate:.2f}% - 交易清淡")
        
        print("="*100)
        
        # 提供东方财富网链接
        print(f"\n💡 查看详细资金流向：")
        print(f"http://data.eastmoney.com/zjlx/detail.html?code={stock_code}")
        
    except Exception as e:
        print(f"\n❌ 获取数据失败: {e}")
        print(f"\n💡 建议：")
        print(f"  1. 检查网络连接")
        print(f"  2. 确认股票代码正确")
        print(f"  3. 访问东方财富网手动查询")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='查询股票实时行情（支持北交所）')
    parser.add_argument('--code', type=str, required=True, help='股票代码（如836807）')
    parser.add_argument('--name', type=str, default='', help='股票名称')
    
    args = parser.parse_args()
    
    stock_name = args.name if args.name else args.code
    get_stock_info_eastmoney(args.code, stock_name)

