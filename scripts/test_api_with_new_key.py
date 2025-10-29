"""
测试新的API Key是否可以绕过频率限制
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from longport.openapi import Config, QuoteContext, Period, AdjustType


def test_api_key(app_key, app_secret, access_token):
    """
    测试API Key是否可以获取历史数据
    
    Args:
        app_key: 应用Key
        app_secret: 应用Secret
        access_token: 访问令牌
    
    Returns:
        bool: 是否可以成功获取数据
    """
    print("\n" + "="*60)
    print("测试API Key")
    print("="*60)
    print(f"App Key: {app_key[:10]}...")
    print("="*60 + "\n")
    
    try:
        # 创建配置
        config = Config(
            app_key=app_key,
            app_secret=app_secret,
            access_token=access_token
        )
        
        # 创建行情上下文
        ctx = QuoteContext(config)
        print("✅ 行情上下文创建成功\n")
        
        # 测试股票列表（A股、港股、美股各一只）
        test_stocks = [
            ('600519.SH', '贵州茅台', 'A股'),
            ('0700.HK', '腾讯控股', '港股'),
            ('AAPL.US', 'Apple', '美股'),
        ]
        
        success_count = 0
        
        for symbol, name, market in test_stocks:
            print(f"测试 {market}: {symbol} - {name}")
            print("-" * 60)
            
            try:
                # 1. 测试静态信息
                static_info = ctx.static_info([symbol])
                if static_info and len(static_info) > 0:
                    print(f"  ✅ 静态信息: {static_info[0].name_cn or static_info[0].name_en}")
                else:
                    print(f"  ❌ 静态信息: 无数据")
                    continue
                
                # 2. 测试实时行情
                try:
                    quotes = ctx.quote([symbol])
                    if quotes and len(quotes) > 0:
                        print(f"  ✅ 实时行情: 最新价 {quotes[0].last_done}")
                    else:
                        print(f"  ⚠️  实时行情: 无数据")
                except Exception as e:
                    print(f"  ⚠️  实时行情: {str(e)}")
                
                # 3. 测试历史K线（关键测试）
                try:
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
                        print(f"  ✅ 历史K线: 成功获取 {len(candlesticks)} 条数据")
                        print(f"     最新日期: {candlesticks[-1].timestamp.date()}")
                        print(f"     收盘价: {candlesticks[-1].close}")
                        success_count += 1
                    else:
                        print(f"  ❌ 历史K线: 无数据")
                        
                except Exception as e:
                    if '301607' in str(e):
                        print(f"  ❌ 历史K线: 频率限制（301607）")
                        print(f"     错误: {str(e)}")
                    else:
                        print(f"  ❌ 历史K线: {str(e)}")
                
                print()
                
            except Exception as e:
                print(f"  ❌ 错误: {str(e)}\n")
        
        print("="*60)
        print(f"测试结果: {success_count}/3 个市场可以获取历史K线")
        print("="*60 + "\n")
        
        if success_count > 0:
            print("✅ 新的API Key可以获取历史数据！")
            print("   可以使用这个Key继续获取A股数据。\n")
            return True
        else:
            print("❌ 新的API Key仍然受到频率限制。")
            print("   可能的原因：")
            print("   1. 限制是基于账户而非App Key")
            print("   2. 限制是基于IP地址")
            print("   3. 需要等待更长时间\n")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}\n")
        return False


def main():
    print("\n" + "="*60)
    print("API Key切换测试工具")
    print("="*60)
    print()
    print("此工具用于测试新的API Key是否可以绕过频率限制。")
    print()
    print("请准备好新的API凭证：")
    print("  - App Key")
    print("  - App Secret")
    print("  - Access Token")
    print()
    print("="*60 + "\n")
    
    # 获取用户输入
    print("请输入新的API凭证（或按Ctrl+C取消）：\n")
    
    try:
        app_key = input("App Key: ").strip()
        app_secret = input("App Secret: ").strip()
        access_token = input("Access Token: ").strip()
        
        if not app_key or not app_secret or not access_token:
            print("\n❌ 错误: 所有字段都必须填写！")
            return
        
        # 测试API Key
        success = test_api_key(app_key, app_secret, access_token)
        
        if success:
            print("💡 下一步操作：")
            print()
            print("1. 更新配置文件：")
            print("   编辑 config/api_config.yaml")
            print("   替换 longport 部分的凭证")
            print()
            print("2. 或者创建备用配置：")
            print("   复制 config/api_config.yaml 为 config/api_config_backup.yaml")
            print("   在新文件中使用新的凭证")
            print()
            print("3. 开始获取A股数据：")
            print("   python scripts/fetch_a_stocks_slowly.py --days 365 --delay 30 --limit 10")
            print()
        else:
            print("💡 建议：")
            print()
            print("1. 等待6-12小时后再试")
            print("2. 尝试使用不同账户的API Key")
            print("3. 联系长桥客服咨询限制详情")
            print()
            
    except KeyboardInterrupt:
        print("\n\n已取消。")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == '__main__':
    main()

