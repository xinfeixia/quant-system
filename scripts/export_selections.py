"""
导出选股结果到Excel
"""
import sys
from pathlib import Path
from datetime import datetime
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from database import get_db_manager
from database.models import StockSelection
from loguru import logger


def export_to_excel(market='HK', output_file=None):
    """
    导出选股结果到Excel
    
    Args:
        market: 市场代码
        output_file: 输出文件路径
    """
    try:
        # 初始化
        config_loader = init_config()
        config = config_loader.config
        from database import init_database
        db_manager = init_database(config)
        
        # 查询选股结果
        with db_manager.get_session() as session:
            selections = session.query(StockSelection).filter_by(
                market=market
            ).order_by(
                StockSelection.total_score.desc()
            ).all()
            
            if not selections:
                logger.warning(f"没有找到 {market} 市场的选股结果")
                return
            
            # 转换为字典列表
            data = []
            for i, s in enumerate(selections, 1):
                data.append({
                    '排名': i,
                    '代码': s.symbol,
                    '名称': s.name,
                    '总分': round(s.total_score, 2),
                    '技术指标分': round(s.technical_score, 2),
                    '量价分析分': round(s.volume_score, 2),
                    '趋势分析分': round(s.trend_score, 2),
                    '形态识别分': round(s.pattern_score, 2),
                    '最新价': round(s.latest_price, 2) if s.latest_price else None,
                    '选股日期': s.selection_date.strftime('%Y-%m-%d')
                })
        
        # 导出到Excel
        try:
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            # 生成文件名
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'选股结果_{market}_{timestamp}.xlsx'
            
            # 导出
            df.to_excel(output_file, index=False, engine='openpyxl')
            
            logger.info(f"✅ 导出成功！文件：{output_file}")
            logger.info(f"📊 共导出 {len(data)} 只股票")
            
            print("\n" + "=" * 60)
            print(f"✅ 导出成功！")
            print("=" * 60)
            print(f"文件路径: {output_file}")
            print(f"股票数量: {len(data)}")
            print(f"市场: {market}")
            print("=" * 60 + "\n")
            
        except ImportError:
            logger.error("需要安装 pandas 和 openpyxl 库")
            logger.info("安装命令: pip install pandas openpyxl")
            
            # 导出为CSV
            import csv
            
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f'选股结果_{market}_{timestamp}.csv'
            else:
                output_file = output_file.replace('.xlsx', '.csv')
            
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"✅ 导出为CSV成功！文件：{output_file}")
            
            print("\n" + "=" * 60)
            print(f"✅ 导出为CSV成功！")
            print("=" * 60)
            print(f"文件路径: {output_file}")
            print(f"股票数量: {len(data)}")
            print(f"市场: {market}")
            print("=" * 60 + "\n")
            
    except Exception as e:
        logger.error(f"导出失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='导出选股结果到Excel')
    parser.add_argument('--market', default='HK', help='市场代码 (HK/US/CN)')
    parser.add_argument('--output', '-o', help='输出文件路径')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("📊 导出选股结果")
    print("=" * 60)
    print(f"市场: {args.market}")
    if args.output:
        print(f"输出文件: {args.output}")
    print("=" * 60 + "\n")
    
    export_to_excel(args.market, args.output)


if __name__ == '__main__':
    main()

