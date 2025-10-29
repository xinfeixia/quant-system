"""重试装饰器"""
import time
import functools
from typing import Callable, Type, Tuple
from loguru import logger


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger_name: str = None
):
    """
    失败重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的倍增因子
        exceptions: 需要捕获的异常类型
        logger_name: logger名称
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger.bind(name=logger_name) if logger_name else logger
            
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        _logger.warning(
                            f"函数 {func.__name__} 执行失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}"
                        )
                        _logger.info(f"等待 {current_delay:.1f} 秒后重试...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        _logger.error(
                            f"函数 {func.__name__} 执行失败，已达到最大重试次数 ({max_retries + 1}): {str(e)}"
                        )
                        raise last_exception
                        
            return None
            
        return wrapper
    return decorator

