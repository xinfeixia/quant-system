"""
长桥证券API客户端
"""
import os
from longport.openapi import Config, QuoteContext, TradeContext, Period as LPPeriod, AdjustType
from loguru import logger


class LongPortClient:
    """长桥证券API客户端"""
    
    def __init__(self, api_config):
        """
        初始化长桥客户端
        
        Args:
            api_config: API配置字典
        """
        self.api_config = api_config.get('longport', {})
        self.quote_ctx = None
        self.trade_ctx = None
        self._init_config()
    
    def _init_config(self):
        """初始化配置"""
        # 优先使用环境变量
        app_key = os.getenv('LONGPORT_APP_KEY') or self.api_config.get('app_key')
        app_secret = os.getenv('LONGPORT_APP_SECRET') or self.api_config.get('app_secret')
        access_token = os.getenv('LONGPORT_ACCESS_TOKEN') or self.api_config.get('access_token')
        
        if not all([app_key, app_secret, access_token]):
            raise ValueError(
                "长桥API配置不完整，请设置环境变量或在 config/api_config.yaml 中配置:\n"
                "- LONGPORT_APP_KEY\n"
                "- LONGPORT_APP_SECRET\n"
                "- LONGPORT_ACCESS_TOKEN"
            )
        
        # 创建配置对象
        try:
            self.config = Config(
                app_key=app_key,
                app_secret=app_secret,
                access_token=access_token
            )
            logger.info("长桥API配置初始化成功")
        except Exception as e:
            logger.error(f"长桥API配置初始化失败: {e}")
            raise
    
    def get_quote_context(self):
        """
        获取行情上下文
        
        Returns:
            QuoteContext实例
        """
        if self.quote_ctx is None:
            try:
                self.quote_ctx = QuoteContext(self.config)
                logger.info("行情上下文创建成功")
            except Exception as e:
                logger.error(f"创建行情上下文失败: {e}")
                raise
        return self.quote_ctx
    
    def get_trade_context(self):
        """
        获取交易上下文
        
        Returns:
            TradeContext实例
        """
        if self.trade_ctx is None:
            try:
                self.trade_ctx = TradeContext(self.config)
                logger.info("交易上下文创建成功")
            except Exception as e:
                logger.error(f"创建交易上下文失败: {e}")
                raise
        return self.trade_ctx
    
    def get_quote(self, symbols):
        """
        获取股票实时行情
        
        Args:
            symbols: 股票代码列表，如 ["700.HK", "AAPL.US"]
            
        Returns:
            行情数据列表
        """
        try:
            ctx = self.get_quote_context()
            quotes = ctx.quote(symbols)
            logger.info(f"获取 {len(symbols)} 只股票的实时行情成功")
            return quotes
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            raise
    
    def get_static_info(self, symbols):
        """
        获取股票静态信息
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            静态信息列表
        """
        try:
            ctx = self.get_quote_context()
            info = ctx.static_info(symbols)
            logger.info(f"获取 {len(symbols)} 只股票的静态信息成功")
            return info
        except Exception as e:
            logger.error(f"获取静态信息失败: {e}")
            raise
    
    def get_candlesticks(self, symbol, period, count=100):
        """
        获取K线数据

        Args:
            symbol: 股票代码，如 "700.HK"
            period: K线周期，如 "day", "week", "month"
            count: 获取数量

        Returns:
            K线数据列表
        """
        try:
            ctx = self.get_quote_context()

            # 转换周期格式 - 使用字符串形式的枚举值
            period_map = {
                'day': LPPeriod.Day,
                'week': LPPeriod.Week,
                'month': LPPeriod.Month,
                '1min': LPPeriod.Min_1,
                '5min': LPPeriod.Min_5,
                '15min': LPPeriod.Min_15,
                '30min': LPPeriod.Min_30,
                '60min': LPPeriod.Min_60
            }

            period_enum = period_map.get(period.lower())
            if not period_enum:
                raise ValueError(f"不支持的K线周期: {period}")

            # 获取K线数据 - 添加复权类型参数
            candlesticks = ctx.candlesticks(symbol, period_enum, count, AdjustType.ForwardAdjust)
            logger.info(f"获取 {symbol} 的 {count} 条 {period} K线数据成功")
            return candlesticks
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise
    
    def get_history_candlesticks(self, symbol, period, start_date, end_date):
        """
        获取历史K线数据
        
        Args:
            symbol: 股票代码
            period: K线周期
            start_date: 开始日期 (datetime.date)
            end_date: 结束日期 (datetime.date)
            
        Returns:
            K线数据列表
        """
        try:
            ctx = self.get_quote_context()

            # 转换周期格式
            period_map = {
                'day': LPPeriod.Day,
                'week': LPPeriod.Week,
                'month': LPPeriod.Month
            }

            period_enum = period_map.get(period.lower())
            if not period_enum:
                raise ValueError(f"不支持的K线周期: {period}")

            # 获取历史K线
            candlesticks = ctx.history_candlesticks_by_date(
                symbol,
                period_enum,
                AdjustType.ForwardAdjust,  # 前复权
                start_date,
                end_date
            )
            logger.info(f"获取 {symbol} 从 {start_date} 到 {end_date} 的历史K线成功")
            return candlesticks
        except Exception as e:
            logger.error(f"获取历史K线失败: {e}")
            raise
    
    def subscribe_quote(self, symbols, callback):
        """
        订阅实时行情
        
        Args:
            symbols: 股票代码列表
            callback: 回调函数，接收 (symbol, quote) 参数
        """
        try:
            from longport.openapi import SubType
            
            ctx = self.get_quote_context()
            ctx.set_on_quote(callback)
            ctx.subscribe(symbols, [SubType.Quote], is_first_push=True)
            logger.info(f"订阅 {len(symbols)} 只股票的实时行情成功")
        except Exception as e:
            logger.error(f"订阅实时行情失败: {e}")
            raise
    
    def unsubscribe_quote(self, symbols):
        """
        取消订阅实时行情
        
        Args:
            symbols: 股票代码列表
        """
        try:
            from longport.openapi import SubType
            
            ctx = self.get_quote_context()
            ctx.unsubscribe(symbols, [SubType.Quote])
            logger.info(f"取消订阅 {len(symbols)} 只股票的实时行情成功")
        except Exception as e:
            logger.error(f"取消订阅实时行情失败: {e}")
            raise
    
    def get_watch_list(self):
        """
        获取自选股列表

        Returns:
            自选股列表
        """
        try:
            ctx = self.get_quote_context()
            watch_list = ctx.watchlist()  # 修正：watch_list -> watchlist
            logger.info("获取自选股列表成功")
            return watch_list
        except Exception as e:
            logger.error(f"获取自选股列表失败: {e}")
            raise
    
    def close(self):
        """关闭连接"""
        if self.quote_ctx:
            # QuoteContext 会自动管理连接
            self.quote_ctx = None
        if self.trade_ctx:
            self.trade_ctx = None
        logger.info("长桥API客户端已关闭")


# 全局客户端实例
_longport_client = None


def init_longport_client(api_config):
    """
    初始化全局长桥客户端
    
    Args:
        api_config: API配置字典
    """
    global _longport_client
    _longport_client = LongPortClient(api_config)
    return _longport_client


def get_longport_client():
    """
    获取全局长桥客户端
    
    Returns:
        LongPortClient实例
    """
    if _longport_client is None:
        raise RuntimeError("长桥客户端未初始化，请先调用 init_longport_client()")
    return _longport_client

