"""
从文件导入股票列表
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from data_collection import init_longport_client
from loguru import logger


def read_stock_list(file_path):
    """
    从文件读取股票列表
    
    Args:
        file_path: 文件路径
        
    Returns:
        股票代码列表
    """
    symbols = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 提取股票代码（可能包含注释）
            symbol = line.split('#')[0].strip()
            
            if symbol:
                symbols.append(symbol)
    
    # 去重
    symbols = list(set(symbols))
    
    return symbols


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='从文件导入股票列表',
        epilog='''
示例:
  # 导入港股主要股票列表
  python import_stock_list.py --file data/hk_main_stocks.txt --market HK
  
  # 导入自定义列表
  python import_stock_list.py --file my_stocks.txt --market HK
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--file', type=str, required=True,
                       help='股票列表文件路径')
    parser.add_argument('--market', type=str, default='HK',
                       choices=['HK', 'US', 'CN'],
                       help='市场代码')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='每批处理数量（默认50）')
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        config_loader = init_config()
        config = config_loader.config
        api_config = config_loader.api_config
        
        # 设置日志
        setup_logger(config)
        
        logger.info("=" * 60)
        logger.info("导入股票列表")
        logger.info("=" * 60)
        
        # 读取股票列表
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"文件不存在: {args.file}")
            sys.exit(1)
        
        symbols = read_stock_list(file_path)
        logger.info(f"从文件读取到 {len(symbols)} 只股票")
        
        if not symbols:
            logger.warning("股票列表为空")
            sys.exit(0)
        
        # 初始化长桥客户端
        init_longport_client(api_config)
        
        # 分批导入
        batch_size = args.batch_size
        total_batches = (len(symbols) + batch_size - 1) // batch_size
        
        logger.info(f"将分 {total_batches} 批导入，每批 {batch_size} 只")
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"\n批次 {batch_num}/{total_batches}: 导入 {len(batch)} 只股票")
            
            # 调用 fetch_stock_list.py 的功能
            from scripts.fetch_stock_list import add_stock_manually
            saved = add_stock_manually(batch, args.market)
            
            logger.info(f"批次 {batch_num} 完成，成功添加 {saved} 只股票")
        
        logger.info("=" * 60)
        logger.info(f"导入完成！共处理 {len(symbols)} 只股票")
        logger.info("=" * 60)
        
        # 提示下一步
        logger.info("\n下一步:")
        logger.info("  1. 检查数据: python scripts/check_data.py")
        logger.info("  2. 获取历史数据: python scripts/fetch_historical_data.py --batch --market HK --limit 10")
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

