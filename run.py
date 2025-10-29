"""
长桥证券量化交易系统 - 主运行脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from database import init_database
from data_collection.longport_client import init_longport_client
from loguru import logger


def main():
    """主函数"""
    try:
        # 1. 加载配置
        logger.info("=" * 60)
        logger.info("长桥证券量化交易系统启动中...")
        logger.info("=" * 60)
        
        config_loader = init_config()
        config = config_loader.config
        api_config = config_loader.api_config
        
        # 2. 设置日志
        setup_logger(config)
        
        # 3. 初始化数据库
        logger.info("初始化数据库...")
        db_manager = init_database(config)
        db_manager.create_tables()
        
        # 4. 初始化长桥客户端
        logger.info("初始化长桥API客户端...")
        longport_client = init_longport_client(api_config)
        
        # 5. 启动Web服务器
        logger.info("启动Web服务器...")
        from web.app import create_app
        
        web_config = config.get('web', {})
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 5000)
        debug = web_config.get('debug', False)
        
        app = create_app(config)
        
        logger.info(f"Web服务器启动成功: http://{host}:{port}")
        logger.info("=" * 60)
        
        app.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        logger.info("\n用户中断，系统退出")
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理资源
        try:
            from database import get_db_manager
            from data_collection.longport_client import get_longport_client
            
            db_manager = get_db_manager()
            db_manager.close()
            
            longport_client = get_longport_client()
            longport_client.close()
            
            logger.info("系统已关闭")
        except:
            pass


if __name__ == '__main__':
    main()

