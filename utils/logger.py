"""
日志工具模块
"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(config):
    """
    设置日志系统
    
    Args:
        config: 配置字典
    """
    # 移除默认的logger
    logger.remove()
    
    # 获取日志配置
    log_config = config.get('logging', {})
    level = log_config.get('level', 'INFO')
    log_format = log_config.get('format', '{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}')
    
    # 控制台输出
    console_config = log_config.get('console', {})
    if console_config.get('enabled', True):
        colorize = console_config.get('colorize', True)
        logger.add(
            sys.stdout,
            format=log_format,
            level=level,
            colorize=colorize
        )
    
    # 文件输出
    file_config = log_config.get('file', {})
    if file_config.get('enabled', True):
        log_path = file_config.get('path', 'logs/longport_quant.log')
        rotation = file_config.get('rotation', '100 MB')
        retention = file_config.get('retention', '30 days')
        
        # 确保日志目录存在
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_path,
            format=log_format,
            level=level,
            rotation=rotation,
            retention=retention,
            encoding='utf-8'
        )
    
    logger.info("日志系统初始化成功")

