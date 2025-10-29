"""
测试长桥API是否支持A股数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from data_collection.longport_client import init_longport_client, get_longport_client
from loguru import logger


def test_a_stock_symbols():
    """测试不同的A股代码格式"""
    
    # 初始化
    config_loader = init_config()
    init_longport_client(config_loader.api_config)
    client = get_longport_client()
    
    print("\n" + "="*60)
    print("测试长桥API对A股的支持")
    print("="*60 + "\n")
    
    # 测试不同的股票代码格式
    test_symbols = [
        # 上海证券交易所
        '600519.SH',  # 贵州茅台
        '600036.SH',  # 招商银行
        '601318.SH',  # 中国平安
        '600000.SH',  # 浦发银行
        
        # 深圳证券交易所
        '000001.SZ',  # 平安银行
        '000002.SZ',  # 万科A
        '000858.SZ',  # 五粮液
        '300750.SZ',  # 宁德时代
        
        # 其他可能的格式
        '600519.SS',  # 上海（Yahoo Finance格式）
        '000001.SS',
        '600519.CN',  # 中国格式
        '000001.CN',
    ]
    
    for symbol in test_symbols:
        print(f"\n测试股票代码: {symbol}")
        print("-" * 60)
        
        try:
            # 尝试获取股票静态信息
            static_info = client.get_static_info([symbol])
            
            if static_info and len(static_info) > 0:
                info = static_info[0]
                print(f"✅ 成功获取信息:")
                print(f"   代码: {info.symbol}")
                print(f"   名称: {info.name_cn or info.name_en}")
                print(f"   市场: {getattr(info, 'market', 'N/A')}")
                
                # 尝试获取历史数据
                try:
                    candlesticks = client.get_candlesticks(
                        symbol=symbol,
                        period='day',
                        count=5
                    )
                    
                    if candlesticks and len(candlesticks) > 0:
                        print(f"   历史数据: ✅ 成功获取 {len(candlesticks)} 条K线")
                        latest = candlesticks[-1]
                        print(f"   最新价格: {latest.close}")
                        print(f"   日期: {latest.timestamp.date()}")
                    else:
                        print(f"   历史数据: ❌ 无数据")
                        
                except Exception as e:
                    print(f"   历史数据: ❌ 获取失败 - {str(e)}")
                    
            else:
                print(f"❌ 无法获取股票信息")
                
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


def test_market_list():
    """测试获取支持的市场列表"""
    
    config_loader = init_config()
    init_longport_client(config_loader.api_config)
    client = get_longport_client()
    
    print("\n" + "="*60)
    print("尝试获取支持的市场列表")
    print("="*60 + "\n")
    
    try:
        # 尝试获取一些已知的港股和美股
        test_symbols = {
            '0700.HK': '腾讯控股（港股）',
            'AAPL.US': 'Apple（美股）',
            '600519.SH': '贵州茅台（A股-上海）',
            '000001.SZ': '平安银行（A股-深圳）',
        }
        
        for symbol, name in test_symbols.items():
            try:
                info = client.get_static_info([symbol])
                if info and len(info) > 0:
                    print(f"✅ {symbol} ({name}) - 支持")
                else:
                    print(f"❌ {symbol} ({name}) - 不支持或无数据")
            except Exception as e:
                print(f"❌ {symbol} ({name}) - 错误: {str(e)}")
                
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    print("\n🔍 开始测试长桥API对A股的支持...\n")
    
    # 测试市场列表
    test_market_list()
    
    # 测试A股代码
    test_a_stock_symbols()
    
    print("\n💡 总结:")
    print("   - 如果看到 ✅，说明该市场/代码格式被支持")
    print("   - 如果看到 ❌，说明该市场/代码格式不被支持")
    print("   - 长桥API可能需要特定的权限才能访问A股数据")
    print("   - 建议查看长桥API文档或联系客服确认A股数据权限\n")

