"""
初始化数据库脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from database import init_database
from loguru import logger


def main():
    """主函数"""
    try:
        # 加载配置
        config_loader = init_config()
        config = config_loader.config
        
        # 设置日志
        setup_logger(config)
        
        logger.info("=" * 60)
        logger.info("初始化数据库")
        logger.info("=" * 60)
        
        # 初始化数据库
        db_manager = init_database(config)
        
        # 创建表
        logger.info("创建数据库表...")
        db_manager.create_tables()
        
        logger.info("=" * 60)
        logger.info("数据库初始化完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

