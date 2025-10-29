"""
资金流入监控脚本
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import ConfigLoader
from utils.logger import logger
from database.db_manager import DatabaseManager
from data_collection.longport_client import LongPortClient
from trading.money_flow_monitor import MoneyFlowMonitor


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='资金流入监控')
    parser.add_argument('--symbols', nargs='+', help='指定监控的股票代码列表')
    parser.add_argument('--interval', type=int, help='监控间隔（秒）')
    parser.add_argument('--test-email', action='store_true', help='发送测试邮件')
    args = parser.parse_args()
    
    try:
        # 加载配置
        logger.info("加载配置...")
        config_loader = ConfigLoader()
        config = config_loader.config
        
        # 如果指定了间隔，覆盖配置
        if args.interval:
            if 'money_flow_monitor' not in config:
                config['money_flow_monitor'] = {}
            config['money_flow_monitor']['interval'] = args.interval
        
        # 初始化数据库
        logger.info("初始化数据库...")
        db_manager = DatabaseManager(config)
        
        # 初始化LongPort客户端
        logger.info("初始化LongPort客户端...")
        client = LongPortClient(config)
        
        # 初始化监控器
        logger.info("初始化资金流入监控器...")
        monitor = MoneyFlowMonitor(config, db_manager, client)
        
        # 测试邮件
        if args.test_email:
            logger.info("发送测试邮件...")
            success = monitor.email_notifier.send_test_email()
            if success:
                logger.info("✅ 测试邮件发送成功")
            else:
                logger.error("❌ 测试邮件发送失败")
            return
        
        # 加载监控列表
        if args.symbols:
            monitor.load_watch_list(args.symbols)
        else:
            monitor.load_watch_list()
        
        # 启动监控
        monitor.start()
        
    except KeyboardInterrupt:
        logger.info("\n用户中断，退出程序")
    except Exception as e:
        logger.error(f"程序异常: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

