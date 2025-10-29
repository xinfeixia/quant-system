"""
简单测试A股数据获取 - 直接使用longport API
"""
import os
from datetime import datetime, timedelta

# 设置环境变量（如果需要）
# os.environ['LONGPORT_APP_KEY'] = 'your_key'
# os.environ['LONGPORT_APP_SECRET'] = 'your_secret'
# os.environ['LONGPORT_ACCESS_TOKEN'] = 'your_token'

from longport.openapi import Config, QuoteContext

# 从配置文件读取
import yaml
with open('config/api_config.yaml', 'r', encoding='utf-8') as f:
    config_data = yaml.safe_load(f)
    lp_config = config_data['longport']

# 创建配置
config = Config(
    app_key=lp_config['app_key'],
    app_secret=lp_config['app_secret'],
    access_token=lp_config['access_token']
)

# 创建行情上下文
ctx = QuoteContext(config)

print("\n" + "="*60)
print("测试A股数据获取")
print("="*60 + "\n")

# 测试股票列表
test_stocks = [
    ('600519.SH', '贵州茅台'),
    ('000001.SZ', '平安银行'),
    ('300750.SZ', '宁德时代'),
]

for symbol, name in test_stocks:
    print(f"\n测试: {symbol} - {name}")
    print("-" * 60)
    
    try:
        # 获取静态信息
        static_info = ctx.static_info([symbol])
        if static_info and len(static_info) > 0:
            info = static_info[0]
            print(f"✅ 静态信息:")
            print(f"   代码: {info.symbol}")
            print(f"   名称: {info.name_cn or info.name_en}")
            
            # 获取实时行情
            try:
                quotes = ctx.quote([symbol])
                if quotes and len(quotes) > 0:
                    quote = quotes[0]
                    print(f"✅ 实时行情:")
                    print(f"   最新价: {quote.last_done}")
                    print(f"   开盘价: {quote.open}")
                    print(f"   最高价: {quote.high}")
                    print(f"   最低价: {quote.low}")
                    print(f"   成交量: {quote.volume}")
            except Exception as e:
                print(f"❌ 实时行情获取失败: {e}")
            
            # 获取历史K线 - 使用history_candlesticks_by_date
            try:
                from longport.openapi import Period, AdjustType
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=10)
                
                candlesticks = ctx.history_candlesticks_by_date(
                    symbol,
                    Period.Day,
                    AdjustType.NoAdjust,
                    start_date,
                    end_date
                )
                
                if candlesticks and len(candlesticks) > 0:
                    print(f"✅ 历史K线: 获取到 {len(candlesticks)} 条数据")
                    latest = candlesticks[-1]
                    print(f"   最新日期: {latest.timestamp.date()}")
                    print(f"   收盘价: {latest.close}")
                    print(f"   开盘价: {latest.open}")
                    print(f"   最高价: {latest.high}")
                    print(f"   最低价: {latest.low}")
                    print(f"   成交量: {latest.volume}")
                else:
                    print(f"❌ 历史K线: 无数据")
            except Exception as e:
                print(f"❌ 历史K线获取失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ 无法获取静态信息")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("测试完成")
print("="*60 + "\n")

