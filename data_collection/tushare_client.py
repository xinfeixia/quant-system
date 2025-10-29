"""
Tushare数据源客户端
用于获取A股历史数据，避免长桥API频率限制
"""
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import tushare as ts
from loguru import logger
import time

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.retry import retry_on_failure
from utils.helpers import convert_to_tushare_code


class TushareClient:
    """Tushare数据源客户端"""

    def __init__(self, token: str, request_interval: float = 0.3, enable_daily_basic: bool = True):
        """
        初始化Tushare客户端

        Args:
            token: Tushare API Token
            request_interval: 请求间隔（秒）
            enable_daily_basic: 是否尝试调用 daily_basic 接口（无权限时应关闭以加速）
        """
        self.logger = logger.bind(name='tushare_client')

        # 设置token并初始化API
        ts.set_token(token)
        self.pro = ts.pro_api()

        # 设置请求间隔与开关
        self.request_interval = request_interval
        self.last_request_time = 0
        self.enable_daily_basic = enable_daily_basic

        self.logger.info(f"Tushare客户端初始化成功 (请求间隔: {request_interval}秒, daily_basic: {'ON' if enable_daily_basic else 'OFF'})")

    def _wait_before_request(self):
        """请求前等待，避免请求过快"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_interval:
            wait_time = self.request_interval - time_since_last_request
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    @retry_on_failure(max_retries=3, delay=2.0, logger_name='tushare_client')
    def get_daily_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        获取日线数据
        
        Args:
            symbol: 股票代码，如 '000001.SZ'
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日线数据列表
        """
        self._wait_before_request()
        
        try:
            # 转换为Tushare格式
            ts_code = convert_to_tushare_code(symbol)
            
            # 转换日期格式：YYYY-MM-DD -> YYYYMMDD
            start_date_str = start_date.strftime('%Y%m%d')
            end_date_str = end_date.strftime('%Y%m%d')
            
            # 确保日期不超过今天
            today = datetime.now().strftime('%Y%m%d')
            if end_date_str > today:
                end_date_str = today
            
            self.logger.info(f"获取 {symbol} 从 {start_date_str} 到 {end_date_str} 的日线数据")
            
            # 获取日线数据
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date_str,
                end_date=end_date_str
            )
            
            if df.empty:
                self.logger.warning(f"股票 {symbol} 在指定期间没有数据")
                return []
            
            # 可选：获取每日指标数据（包含换手率）
            if self.enable_daily_basic:
                try:
                    self._wait_before_request()
                    daily_basic_df = self.pro.daily_basic(
                        ts_code=ts_code,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        fields='ts_code,trade_date,turnover_rate,turnover_rate_f,volume_ratio,pe,pb'
                    )

                    if not daily_basic_df.empty:
                        df = df.merge(daily_basic_df, on='trade_date', how='left', suffixes=('', '_basic'))
                        self.logger.debug(f"成功获取每日指标数据")
                except Exception as e:
                    if '权限' in str(e) or 'permission' in str(e).lower():
                        self.logger.warning(f"无权限访问 daily_basic 接口，部分字段将为空")
                    else:
                        self.logger.warning(f"获取 daily_basic 数据失败: {e}")

            # 不使用复权 - 使用原始价格进行技术分析
            # 复权主要用于长期收益率计算，对于技术指标分析应使用不复权价格
            # 如果需要复权，可以在后续分析中单独处理

            # # 获取复权因子（已禁用）
            # try:
            #     self._wait_before_request()
            #     adj_df = self.pro.adj_factor(
            #         ts_code=ts_code,
            #         start_date=start_date_str,
            #         end_date=end_date_str
            #     )
            #
            #     if not adj_df.empty:
            #         df = df.merge(adj_df[['trade_date', 'adj_factor']], on='trade_date', how='left')
            #         df['adj_factor'] = df['adj_factor'].ffill().fillna(1.0)
            #
            #         # 应用前复权
            #         for col in ['open', 'high', 'low', 'close', 'pre_close']:
            #             if col in df.columns:
            #                 df[col] = df[col] * df['adj_factor']
            # except Exception as e:
            #     self.logger.warning(f"获取复权因子失败: {e}")
            
            # 转换为系统格式
            results = []
            for _, row in df.iterrows():
                # 转换日期格式：YYYYMMDD -> datetime
                trade_date = datetime.strptime(str(row['trade_date']), '%Y%m%d')
                
                data = {
                    'symbol': symbol,
                    'trade_date': trade_date,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['vol'] * 100) if pd.notna(row['vol']) else 0,  # Tushare的vol单位是手，转换为股
                    'turnover': float(row['amount'] * 1000) if pd.notna(row['amount']) else 0.0,  # Tushare的amount单位是千元，转换为元
                    'created_at': datetime.now()
                }
                
                # 添加可选字段
                if 'turnover_rate' in row and pd.notna(row['turnover_rate']):
                    data['turnover_rate'] = float(row['turnover_rate'])

                if 'pct_chg' in row and pd.notna(row['pct_chg']):
                    data['change_pct'] = float(row['pct_chg'])  # 注意：字段名是change_pct不是change_percent
                
                results.append(data)
            
            # 按日期升序排序
            results.sort(key=lambda x: x['trade_date'])
            
            self.logger.info(f"成功获取 {symbol} 的 {len(results)} 条日线数据")
            return results
            
        except Exception as e:
            self.logger.error(f"获取 {symbol} 日线数据失败: {e}")
            raise
    
    @retry_on_failure(max_retries=3, delay=2.0, logger_name='tushare_client')
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票基本信息字典
        """
        self._wait_before_request()
        
        try:
            ts_code = convert_to_tushare_code(symbol)
            
            df = self.pro.stock_basic(
                ts_code=ts_code,
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            
            if df.empty:
                self.logger.warning(f"股票 {symbol} 没有基本信息")
                return {}
            
            row = df.iloc[0]
            return {
                'symbol': symbol,
                'name': row['name'],
                'area': row['area'],
                'industry': row['industry'],
                'market': row['market'],
                'list_date': row['list_date']
            }
            
        except Exception as e:
            self.logger.error(f"获取股票 {symbol} 基本信息失败: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        测试Tushare连接

        Returns:
            是否连接成功
        """
        try:
            self.logger.info("测试Tushare连接...")

            # 简单测试：检查pro对象是否存在
            if self.pro is None:
                self.logger.error("Tushare连接失败：pro对象未初始化")
                return False

            # 不调用stock_basic接口，因为它有严格的频率限制（1次/分钟）
            # 直接返回成功，实际连接会在第一次获取数据时验证
            self.logger.info(f"✅ Tushare客户端初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"❌ Tushare连接失败: {e}")
            return False


# 全局Tushare客户端实例
_tushare_client = None


def init_tushare_client(config: Dict[str, Any]) -> TushareClient:
    """
    初始化Tushare客户端
    
    Args:
        config: 配置字典，需要包含 token
        
    Returns:
        TushareClient实例
    """
    global _tushare_client
    
    token = config.get('token')
    if not token:
        raise ValueError("配置中缺少 Tushare token")
    
    request_interval = config.get('request_interval', 0.3)
    
    _tushare_client = TushareClient(token, request_interval)
    return _tushare_client


def get_tushare_client() -> TushareClient:
    """
    获取Tushare客户端实例
    
    Returns:
        TushareClient实例
    """
    if _tushare_client is None:
        raise RuntimeError("Tushare客户端未初始化，请先调用 init_tushare_client()")
    
    return _tushare_client

