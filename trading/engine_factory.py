"""
交易引擎工厂
根据配置创建对应的交易引擎实例
"""
from loguru import logger
from .trading_engine import TradingEngine
from .trading_engine import LocalPaperEngine
from .longport_engine import LongPortPaperEngine


_engine_instance = None


def create_trading_engine(config: dict, db_manager, longport_client=None) -> TradingEngine:
    """
    创建交易引擎实例
    
    Args:
        config: 配置字典
        db_manager: 数据库管理器
        longport_client: LongPortClient 实例（可选）
        
    Returns:
        TradingEngine 实例
    """
    global _engine_instance
    
    if _engine_instance is not None:
        return _engine_instance
    
    trading_config = config.get('trading', {})
    mode = trading_config.get('mode', 'local_paper')
    
    logger.info(f"创建交易引擎，模式: {mode}")
    
    if mode == 'local_paper':
        _engine_instance = LocalPaperEngine(db_manager, config)
    
    elif mode == 'longport_paper':
        if longport_client is None:
            raise ValueError("LongPort Paper 模式需要提供 longport_client")
        _engine_instance = LongPortPaperEngine(longport_client, db_manager, config)
    
    elif mode == 'longport_live':
        # 实盘模式（暂未实现，可复用 LongPortPaperEngine 逻辑）
        if longport_client is None:
            raise ValueError("LongPort Live 模式需要提供 longport_client")
        logger.warning("⚠️  实盘模式已启用，请谨慎操作！")
        _engine_instance = LongPortPaperEngine(longport_client, db_manager, config)
    
    else:
        raise ValueError(f"不支持的交易模式: {mode}")
    
    logger.info(f"交易引擎创建成功: {_engine_instance.__class__.__name__}")
    return _engine_instance


def get_trading_engine() -> TradingEngine:
    """
    获取当前交易引擎实例

    Returns:
        TradingEngine 实例

    Raises:
        RuntimeError: 如果引擎未初始化
    """
    global _engine_instance

    if _engine_instance is None:
        logger.error("❌ 交易引擎未初始化！")
        raise RuntimeError("交易引擎未初始化，请先调用 create_trading_engine()")

    logger.debug(f"获取交易引擎: {_engine_instance.__class__.__name__} (ID: {id(_engine_instance)})")
    return _engine_instance


def reset_trading_engine():
    """重置交易引擎实例（用于切换模式）"""
    global _engine_instance
    _engine_instance = None
    logger.info("交易引擎已重置")

