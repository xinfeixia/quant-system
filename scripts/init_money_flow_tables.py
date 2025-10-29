"""
初始化资金流入监控相关数据库表
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import ConfigLoader
from utils.logger import logger
from database.db_manager import DatabaseManager
from database.models import Base, MinuteData, MoneyFlowAlert


def main():
    """主函数"""
    try:
        # 加载配置
        logger.info("加载配置...")
        config_loader = ConfigLoader()
        config = config_loader.config
        
        # 初始化数据库
        logger.info("初始化数据库...")
        db_manager = DatabaseManager(config)
        
        # 创建表
        logger.info("创建资金流入监控相关表...")
        Base.metadata.create_all(db_manager.engine, tables=[
            MinuteData.__table__,
            MoneyFlowAlert.__table__
        ])
        
        logger.info("✅ 数据库表创建成功！")
        logger.info("已创建以下表：")
        logger.info("  - minute_data: 分钟数据表")
        logger.info("  - money_flow_alerts: 资金流入告警记录表")
        
    except Exception as e:
        logger.error(f"创建数据库表失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

