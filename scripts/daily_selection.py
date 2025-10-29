"""
每日自动选股任务
"""
import sys
from pathlib import Path
from datetime import datetime
import time
import schedule

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from utils.config_loader import init_config
from database import init_database


def daily_selection_task():
    """每日选股任务"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 开始每日选股任务")
        logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        # 初始化配置和数据库
        logger.info("初始化配置和数据库...")
        config_loader = init_config()
        config = config_loader.config
        db_manager = init_database(config)

        # 1. 运行选股分析
        logger.info("步骤 1/2: 运行选股分析...")
        from run_stock_selection import run_stock_selection
        run_stock_selection(market='HK', min_score=50, top_n=50)
        
        # 2. 导出结果
        logger.info("步骤 2/2: 导出选股结果...")
        timestamp = datetime.now().strftime('%Y%m%d')
        output_file = f'reports/选股结果_HK_{timestamp}.xlsx'

        # 确保reports目录存在
        Path('reports').mkdir(exist_ok=True)

        from export_selections import export_to_excel
        export_to_excel(market='HK', output_file=output_file)
        
        logger.info("=" * 60)
        logger.info("✅ 每日选股任务完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 每日选股任务失败: {e}")
        import traceback
        traceback.print_exc()


def run_scheduler():
    """运行定时任务调度器"""
    # 设置每天的运行时间
    schedule.every().day.at("09:00").do(daily_selection_task)  # 每天早上9点
    schedule.every().day.at("15:30").do(daily_selection_task)  # 每天下午3:30（收盘后）
    
    logger.info("=" * 60)
    logger.info("⏰ 定时任务调度器已启动")
    logger.info("=" * 60)
    logger.info("任务计划:")
    logger.info("  - 每天 09:00 运行选股")
    logger.info("  - 每天 15:30 运行选股（收盘后）")
    logger.info("=" * 60)
    logger.info("按 Ctrl+C 停止...")
    logger.info("")
    
    # 立即运行一次
    logger.info("立即运行一次选股任务...")
    daily_selection_task()
    
    # 持续运行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='每日自动选股任务')
    parser.add_argument('--once', action='store_true', help='只运行一次，不启动定时任务')
    parser.add_argument('--schedule', action='store_true', help='启动定时任务调度器')
    
    args = parser.parse_args()
    
    if args.schedule:
        # 启动定时任务
        run_scheduler()
    else:
        # 只运行一次
        daily_selection_task()


if __name__ == '__main__':
    main()

