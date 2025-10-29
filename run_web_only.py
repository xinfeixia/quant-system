"""
仅启动Web服务（不初始化长桥API），用于内网/移动端访问查看页面。
"""
import sys
from pathlib import Path

# 确保可以import到项目包
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_loader import init_config
from utils.logger import setup_logger
from database import init_database
from loguru import logger


def main():
    try:
        # 1) 加载配置与日志
        config_loader = init_config(config_dir=str(Path(__file__).parent / 'config'))
        config = config_loader.config
        setup_logger(config)

        # 2) 初始化数据库（不初始化长桥API）
        db_manager = init_database(config)
        db_manager.create_tables()

        # 3) 初始化交易引擎（根据配置自动选择模式）
        from trading.engine_factory import create_trading_engine, reset_trading_engine

        # 重置引擎实例（确保使用最新配置）
        reset_trading_engine()

        trading_mode = config.get('trading', {}).get('mode', 'local_paper')

        if trading_mode == 'local_paper':
            # 本地Paper模式，不需要LongPort客户端
            trading_engine = create_trading_engine(config, db_manager, longport_client=None)
            logger.info(f"交易引擎已初始化: {trading_mode}")
        else:
            # LongPort模拟/实盘模式，需要初始化LongPort客户端
            from data_collection.longport_client import LongPortClient
            api_config = config_loader.api_config
            longport_client = LongPortClient(api_config)
            trading_engine = create_trading_engine(config, db_manager, longport_client)
            logger.info(f"交易引擎已初始化: {trading_mode} (LongPort)")

        # 4) 启动Web服务（在创建引擎之后才导入 app）
        from web.app import create_app

        web_config = config.get('web', {})
        host = web_config.get('host', '0.0.0.0')
        port = web_config.get('port', 5000)
        debug = web_config.get('debug', False)

        app = create_app(config)
        logger.info(f"Web服务器启动: http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)

    except KeyboardInterrupt:
        logger.info("\n用户中断，退出")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()

