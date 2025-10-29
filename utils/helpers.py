"""辅助工具函数"""
import re
from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple
import pandas as pd


def normalize_stock_code(code: str) -> str:
    """
    标准化股票代码
    
    Args:
        code: 股票代码
        
    Returns:
        标准化后的股票代码
    """
    # 移除所有非数字字符
    code = re.sub(r'\D', '', code)
    
    # 确保是6位数字
    if len(code) < 6:
        code = code.zfill(6)
    elif len(code) > 6:
        code = code[:6]
        
    return code


def add_market_prefix(code: str) -> str:
    """
    为股票代码添加市场前缀
    
    Args:
        code: 股票代码
        
    Returns:
        带市场前缀的股票代码 (如: sh600000, sz000001)
    """
    code = normalize_stock_code(code)
    
    # 上海市场: 60开头
    if code.startswith('60') or code.startswith('68'):
        return f'sh{code}'
    # 深圳市场: 00, 30开头
    elif code.startswith('00') or code.startswith('30'):
        return f'sz{code}'
    else:
        # 默认深圳
        return f'sz{code}'


def remove_market_prefix(code: str) -> str:
    """
    移除股票代码的市场前缀
    
    Args:
        code: 带前缀的股票代码
        
    Returns:
        纯数字股票代码
    """
    # 移除sh或sz前缀
    code = re.sub(r'^(sh|sz|SH|SZ)', '', code)
    return normalize_stock_code(code)


def convert_to_tushare_code(symbol: str) -> str:
    """
    将系统股票代码转换为Tushare格式
    
    Args:
        symbol: 系统格式代码，如 '000001.SZ' 或 '600000.SH'
        
    Returns:
        Tushare格式代码，如 '000001.SZ' 或 '600000.SH'
    """
    # 如果已经是正确格式，直接返回
    if '.' in symbol:
        return symbol
    
    # 移除可能的市场前缀
    code = remove_market_prefix(symbol)
    
    # 判断市场
    if code.startswith('6'):
        return f"{code}.SH"  # 上海
    elif code.startswith('0') or code.startswith('3'):
        return f"{code}.SZ"  # 深圳
    elif code.startswith('688'):
        return f"{code}.SH"  # 科创板
    elif code.startswith('8'):
        return f"{code}.BJ"  # 北交所
    else:
        return f"{code}.SZ"  # 默认深圳


def convert_from_tushare_code(ts_code: str) -> str:
    """
    将Tushare格式代码转换为系统格式
    
    Args:
        ts_code: Tushare格式代码，如 '000001.SZ'
        
    Returns:
        系统格式代码，如 '000001.SZ'
    """
    # 系统格式和Tushare格式相同
    return ts_code


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全除法
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 分母为0时的默认值
        
    Returns:
        除法结果
    """
    if denominator == 0:
        return default
    return numerator / denominator


def dataframe_to_dict_list(df: pd.DataFrame) -> List[dict]:
    """
    将DataFrame转换为字典列表
    
    Args:
        df: DataFrame
        
    Returns:
        字典列表
    """
    if df is None or df.empty:
        return []
    return df.to_dict('records')


def ensure_datetime(date_input) -> Optional[datetime]:
    """
    确保输入为datetime对象
    
    Args:
        date_input: 日期输入（字符串或datetime对象）
        
    Returns:
        datetime对象
    """
    if date_input is None:
        return None
        
    if isinstance(date_input, datetime):
        return date_input
        
    if isinstance(date_input, str):
        try:
            return datetime.strptime(date_input, '%Y-%m-%d')
        except ValueError:
            try:
                return datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None
                
    return None

