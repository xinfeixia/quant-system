"""
一键设置港股数据（导入股票 + 获取历史数据 + 计算指标）
"""
import sys
import argparse
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from data_collection import init_longport_client
from database import init_database
from loguru import logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='一键设置港股数据',
        epilog='''
这个脚本会自动完成以下步骤:
  1. 导入港股主要股票列表（200+只）
  2. 批量获取历史数据（1年）
  3. 计算技术指标
  
示例:
  # 完整流程（推荐先测试少量）
  python setup_hk_stocks.py --limit 10
  
  # 完整流程（所有股票）
  python setup_hk_stocks.py
  
  # 只导入股票列表
  python setup_hk_stocks.py --import-only
  
  # 只获取历史数据
  python setup_hk_stocks.py --data-only --limit 50
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--limit', type=int,
                       help='限制处理的股票数量（用于测试）')
    parser.add_argument('--import-only', action='store_true',
                       help='只导入股票列表')
    parser.add_argument('--data-only', action='store_true',
                       help='只获取历史数据（跳过导入）')
    parser.add_argument('--indicators-only', action='store_true',
                       help='只计算技术指标（跳过导入和数据获取）')
    parser.add_argument('--days', type=int, default=365,
                       help='获取历史数据的天数（默认365天）')
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        config_loader = init_config()
        config = config_loader.config
        api_config = config_loader.api_config
        
        # 设置日志
        setup_logger(config)
        
        print("\n" + "=" * 80)
        print("🚀 港股数据一键设置")
        print("=" * 80)
        
        # 初始化
        init_database(config)
        init_longport_client(api_config)
        
        # 步骤1: 导入股票列表
        if not args.data_only and not args.indicators_only:
            print("\n" + "=" * 80)
            print("📋 步骤 1/3: 导入股票列表")
            print("=" * 80)
            
            from scripts.import_stock_list import read_stock_list
            from scripts.fetch_stock_list import add_stock_manually

            stock_file = Path(__file__).parent.parent / 'data' / 'hk_main_stocks.txt'
            symbols = read_stock_list(stock_file)
            
            if args.limit:
                symbols = symbols[:args.limit]
                logger.info(f"限制导入前 {args.limit} 只股票")
            
            logger.info(f"准备导入 {len(symbols)} 只股票...")
            
            # 分批导入（每批50只）
            batch_size = 50
            total_saved = 0
            
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i+batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(symbols) + batch_size - 1) // batch_size
                
                logger.info(f"批次 {batch_num}/{total_batches}: 处理 {len(batch)} 只股票")

                saved = add_stock_manually(batch, 'HK')
                total_saved += saved
                
                time.sleep(1)  # 避免请求过快
            
            logger.info(f"✅ 导入完成！成功添加 {total_saved} 只股票")
            
            if args.import_only:
                print("\n" + "=" * 80)
                print("✅ 股票列表导入完成！")
                print("=" * 80)
                print("\n下一步:")
                print("  python setup_hk_stocks.py --data-only --limit 10")
                return
        
        # 步骤2: 获取历史数据
        if not args.import_only and not args.indicators_only:
            print("\n" + "=" * 80)
            print("📊 步骤 2/3: 获取历史数据")
            print("=" * 80)
            
            from scripts.fetch_historical_data import fetch_batch_history
            
            logger.info(f"开始获取历史数据（最近 {args.days} 天）...")
            
            fetch_batch_history(
                market='HK',
                limit=args.limit,
                days=args.days
            )
            
            logger.info("✅ 历史数据获取完成！")
            
            if args.data_only:
                print("\n" + "=" * 80)
                print("✅ 历史数据获取完成！")
                print("=" * 80)
                print("\n下一步:")
                print("  python setup_hk_stocks.py --indicators-only --limit 10")
                return
        
        # 步骤3: 计算技术指标
        if not args.import_only and not args.data_only:
            print("\n" + "=" * 80)
            print("📈 步骤 3/3: 计算技术指标")
            print("=" * 80)
            
            from scripts.calculate_indicators import calculate_batch_indicators
            
            logger.info("开始计算技术指标...")
            
            calculate_batch_indicators(
                market='HK',
                limit=args.limit
            )
            
            logger.info("✅ 技术指标计算完成！")
        
        # 完成
        print("\n" + "=" * 80)
        print("🎉 所有步骤完成！")
        print("=" * 80)
        
        # 显示统计
        print("\n📊 数据统计:")
        from scripts.check_data import check_data_status
        check_data_status()
        
        print("\n🌐 访问Web界面:")
        print("  http://localhost:5000")
        print("  http://localhost:5000/api/stocks?market=HK")
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

