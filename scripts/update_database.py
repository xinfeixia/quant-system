"""
更新数据库表结构
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from database import get_db_manager
from database.models import Base, StockSelection
from loguru import logger


def main():
    """主函数"""
    try:
        # 加载配置
        config_loader = init_config()
        config = config_loader.config

        # 初始化数据库
        from database import init_database
        db_manager = init_database(config)

        print("\n" + "=" * 60)
        print("更新数据库表结构")
        print("=" * 60)

        # 删除旧的 stock_selection 表
        print("删除旧的 stock_selection 表...")
        StockSelection.__table__.drop(db_manager.engine, checkfirst=True)

        # 重新创建表
        print("创建新的 stock_selection 表...")
        StockSelection.__table__.create(db_manager.engine)

        print("✅ 数据库表结构更新完成！")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

