#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 LongPort 持仓 API
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_collection.longport_client import init_longport_client, get_longport_client
from utils.config_loader import init_config

def main():
    """主函数"""
    print("\n" + "="*80)
    print("测试 LongPort 持仓 API")
    print("="*80 + "\n")
    
    # 初始化配置
    config_loader = init_config()
    
    # 初始化 LongPort 客户端
    init_longport_client(config_loader.api_config)
    longport_client = get_longport_client()
    trade_ctx = longport_client.get_trade_context()
    
    print("获取持仓...\n")
    
    try:
        response = trade_ctx.stock_positions()
        
        print(f"Response 类型: {type(response)}")
        print(f"Response 属性:")
        for attr in dir(response):
            if not attr.startswith('_'):
                try:
                    value = getattr(response, attr)
                    if not callable(value):
                        print(f"  {attr}: {value}")
                except:
                    pass
        
        print("\n" + "="*80)
        
        # 尝试访问 channels
        if hasattr(response, 'channels'):
            channels = response.channels
            print(f"\nChannels 类型: {type(channels)}")
            print(f"Channels 数量: {len(channels) if hasattr(channels, '__len__') else 'N/A'}")
            
            if channels:
                print(f"\n第一个 Channel 的属性:")
                first_channel = channels[0] if hasattr(channels, '__getitem__') else next(iter(channels))
                for attr in dir(first_channel):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(first_channel, attr)
                            if not callable(value):
                                print(f"  {attr}: {value}")
                        except:
                            pass
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

