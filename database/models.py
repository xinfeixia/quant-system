"""
数据库模型定义
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class StockInfo(Base):
    """股票基本信息表"""
    __tablename__ = 'stock_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True, comment='股票代码（如700.HK）')
    name = Column(String(100), nullable=False, comment='股票名称')
    name_en = Column(String(100), comment='英文名称')
    market = Column(String(10), nullable=False, index=True, comment='市场（HK/US/CN）')

    # 基本信息
    exchange = Column(String(20), comment='交易所')
    currency = Column(String(10), comment='货币')
    lot_size = Column(Integer, comment='每手股数')

    # 分类信息
    sector = Column(String(50), comment='行业')
    industry = Column(String(50), comment='子行业')

    # 市值信息
    market_cap = Column(Float, comment='市值')
    shares_outstanding = Column(Float, comment='流通股本')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否活跃')
    is_suspended = Column(Boolean, default=False, comment='是否停牌')
    is_st = Column(Boolean, default=False, comment='是否ST')
    is_hk_connect = Column(Boolean, default=False, comment='是否港股通标的')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关系
    daily_data = relationship('DailyData', back_populates='stock', cascade='all, delete-orphan')
    selections = relationship('StockSelection', back_populates='stock', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<StockInfo(symbol='{self.symbol}', name='{self.name}', market='{self.market}')>"


class DailyData(Base):
    """日线数据表"""
    __tablename__ = 'daily_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey('stock_info.symbol'), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True, comment='交易日期')

    # OHLCV数据
    open = Column(Float, comment='开盘价')
    high = Column(Float, comment='最高价')
    low = Column(Float, comment='最低价')
    close = Column(Float, nullable=False, comment='收盘价')
    volume = Column(Float, comment='成交量')
    turnover = Column(Float, comment='成交额')

    # 复权价格
    adj_close = Column(Float, comment='复权收盘价')

    # 涨跌幅
    change = Column(Float, comment='涨跌额')
    change_pct = Column(Float, comment='涨跌幅(%)')

    # 换手率
    turnover_rate = Column(Float, comment='换手率(%)')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 关系
    stock = relationship('StockInfo', back_populates='daily_data')

    # 复合索引
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'trade_date'),
    )

    def __repr__(self):
        return f"<DailyData(symbol='{self.symbol}', date='{self.trade_date}', close={self.close})>"


class TechnicalIndicator(Base):
    """技术指标表"""
    __tablename__ = 'technical_indicators'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey('stock_info.symbol'), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True, comment='交易日期')

    # 趋势指标
    ma5 = Column(Float, comment='5日均线')
    ma10 = Column(Float, comment='10日均线')
    ma20 = Column(Float, comment='20日均线')
    ma60 = Column(Float, comment='60日均线')
    ema12 = Column(Float, comment='12日EMA')
    ema26 = Column(Float, comment='26日EMA')

    # MACD
    macd = Column(Float, comment='MACD')
    macd_signal = Column(Float, comment='MACD信号线')
    macd_hist = Column(Float, comment='MACD柱状图')

    # RSI
    rsi = Column(Float, comment='RSI')

    # KDJ
    kdj_k = Column(Float, comment='KDJ-K')
    kdj_d = Column(Float, comment='KDJ-D')
    kdj_j = Column(Float, comment='KDJ-J')

    # 布林带
    boll_upper = Column(Float, comment='布林带上轨')
    boll_middle = Column(Float, comment='布林带中轨')
    boll_lower = Column(Float, comment='布林带下轨')

    # ATR
    atr = Column(Float, comment='ATR')

    # 成交量指标
    obv = Column(Float, comment='OBV')
    volume_ma5 = Column(Float, comment='5日成交量均线')
    volume_ma10 = Column(Float, comment='10日成交量均线')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 复合索引
    __table_args__ = (
        Index('idx_ti_symbol_date', 'symbol', 'trade_date'),
    )

    def __repr__(self):
        return f"<TechnicalIndicator(symbol='{self.symbol}', date='{self.trade_date}')>"


class StockSelection(Base):
    """选股结果表"""
    __tablename__ = 'stock_selection'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey('stock_info.symbol'), nullable=False, index=True)
    name = Column(String(100), comment='股票名称')
    market = Column(String(10), index=True, comment='市场代码')
    selection_date = Column(Date, nullable=False, index=True, comment='选股日期')

    # 评分
    total_score = Column(Float, nullable=False, comment='总分')
    technical_score = Column(Float, comment='技术指标分')
    volume_score = Column(Float, comment='量价分析分')
    trend_score = Column(Float, comment='趋势分析分')
    pattern_score = Column(Float, comment='形态识别分')

    # 排名
    rank = Column(Integer, comment='排名')

    # 推荐理由
    reason = Column(Text, comment='推荐理由')

    # 关键指标
    latest_price = Column(Float, comment='最新价格')
    current_price = Column(Float, comment='当前价格')
    target_price = Column(Float, comment='目标价格')
    stop_loss_price = Column(Float, comment='止损价格')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 关系
    stock = relationship('StockInfo', back_populates='selections')

    # 复合索引
    __table_args__ = (
        Index('idx_selection_date_score', 'selection_date', 'total_score'),
    )

    def __repr__(self):
        return f"<StockSelection(symbol='{self.symbol}', date='{self.selection_date}', score={self.total_score})>"


class BacktestResult(Base):
    """回测结果表"""
    __tablename__ = 'backtest_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(100), nullable=False, comment='策略名称')
    start_date = Column(Date, nullable=False, comment='回测开始日期')
    end_date = Column(Date, nullable=False, comment='回测结束日期')

    # 资金信息
    initial_capital = Column(Float, nullable=False, comment='初始资金')
    final_capital = Column(Float, comment='最终资金')

    # 收益指标
    total_return = Column(Float, comment='总收益率(%)')
    annual_return = Column(Float, comment='年化收益率(%)')
    max_drawdown = Column(Float, comment='最大回撤(%)')

    # 风险指标
    sharpe_ratio = Column(Float, comment='夏普比率')
    sortino_ratio = Column(Float, comment='索提诺比率')
    volatility = Column(Float, comment='波动率(%)')

    # 交易统计
    total_trades = Column(Integer, comment='总交易次数')
    winning_trades = Column(Integer, comment='盈利次数')
    losing_trades = Column(Integer, comment='亏损次数')
    win_rate = Column(Float, comment='胜率(%)')

    # 盈亏统计
    avg_profit = Column(Float, comment='平均盈利(%)')
    avg_loss = Column(Float, comment='平均亏损(%)')
    profit_loss_ratio = Column(Float, comment='盈亏比')

    # 配置参数
    config = Column(Text, comment='策略配置（JSON）')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    def __repr__(self):
        return f"<BacktestResult(strategy='{self.strategy_name}', return={self.total_return}%)>"


class TradingSignal(Base):
    """交易信号表"""
    __tablename__ = 'trading_signals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey('stock_info.symbol'), nullable=False, index=True)
    signal_date = Column(Date, nullable=False, index=True, comment='信号日期')

    # 信号类型
    signal_type = Column(String(10), nullable=False, comment='信号类型（BUY/SELL）')
    signal_strength = Column(Float, comment='信号强度（0-1）')

    # 价格信息
    signal_price = Column(Float, comment='信号价格')
    target_price = Column(Float, comment='目标价格')
    stop_loss_price = Column(Float, comment='止损价格')

    # 信号来源
    source = Column(String(50), comment='信号来源')
    reason = Column(Text, comment='信号原因')

    # 状态
    is_executed = Column(Boolean, default=False, comment='是否已执行')
    executed_at = Column(DateTime, comment='执行时间')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 复合索引
    __table_args__ = (
        Index('idx_signal_date_type', 'signal_date', 'signal_type'),
    )

    def __repr__(self):
        return f"<TradingSignal(symbol='{self.symbol}', type='{self.signal_type}', date='{self.signal_date}')>"




class Order(Base):
    """订单表（Paper/Live 通用结构）"""
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True, comment='股票代码，如 0700.HK')
    market = Column(String(10), nullable=False, default='HK', comment='市场，默认HK')

    side = Column(String(4), nullable=False, comment='买卖方向：BUY/SELL')
    order_type = Column(String(10), nullable=False, default='LIMIT', comment='订单类型：LIMIT/MARKET')
    price = Column(Float, comment='委托价（限价单必填）')
    quantity = Column(Integer, nullable=False, comment='委托数量（股）')

    status = Column(String(20), nullable=False, default='NEW', index=True, comment='订单状态：NEW/PARTIALLY_FILLED/FILLED/CANCELLED/REJECTED')
    filled_quantity = Column(Integer, default=0, comment='已成交数量')
    avg_fill_price = Column(Float, comment='成交均价')

    strategy_tag = Column(String(50), comment='策略标签/来源')
    external_order_id = Column(String(100), unique=True, index=True, comment='外部订单ID（LongPort等）')

    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    executions = relationship('Execution', back_populates='order', cascade='all, delete-orphan')


class Execution(Base):
    """成交明细"""
    __tablename__ = 'executions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)

    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(4), nullable=False)

    price = Column(Float, nullable=False, comment='成交价')
    quantity = Column(Integer, nullable=False, comment='成交数量')
    exec_time = Column(DateTime, default=datetime.now, comment='成交时间')

    order = relationship('Order', back_populates='executions')


class Position(Base):
    """持仓表（按标的汇总）"""
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    market = Column(String(10), nullable=False, default='HK')

    quantity = Column(Integer, nullable=False, default=0, comment='当前持仓股数')
    avg_price = Column(Float, nullable=False, default=0.0, comment='持仓成本均价')

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PortfolioSnapshot(Base):
    """组合快照（用于PnL/净值曲线）"""
    __tablename__ = 'portfolio_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_time = Column(DateTime, default=datetime.now, index=True)

    cash = Column(Float, nullable=False, default=1000000.0, comment='可用现金')
    equity = Column(Float, comment='持仓市值')
    total_value = Column(Float, comment='总资产=现金+市值')

    note = Column(String(100), comment='备注，如盘中/收盘')


class MinuteData(Base):
    """分钟数据表"""
    __tablename__ = 'minute_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey('stock_info.symbol'), nullable=False, index=True)
    trade_datetime = Column(DateTime, nullable=False, index=True, comment='交易时间（精确到分钟）')

    # OHLCV数据
    open = Column(Float, comment='开盘价')
    high = Column(Float, comment='最高价')
    low = Column(Float, comment='最低价')
    close = Column(Float, nullable=False, comment='收盘价')
    volume = Column(Float, comment='成交量')
    turnover = Column(Float, comment='成交额')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 复合索引
    __table_args__ = (
        Index('idx_minute_symbol_datetime', 'symbol', 'trade_datetime'),
    )

    def __repr__(self):
        return f"<MinuteData(symbol='{self.symbol}', datetime='{self.trade_datetime}', close={self.close})>"


class MoneyFlowAlert(Base):
    """资金流入告警记录表"""
    __tablename__ = 'money_flow_alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), ForeignKey('stock_info.symbol'), nullable=False, index=True)
    alert_datetime = Column(DateTime, nullable=False, index=True, comment='告警时间')

    # 告警指标
    alert_type = Column(String(50), comment='告警类型（volume_surge/turnover_surge/price_surge）')
    current_volume = Column(Float, comment='当前成交量')
    avg_volume = Column(Float, comment='平均成交量')
    volume_ratio = Column(Float, comment='成交量倍数')
    current_turnover = Column(Float, comment='当前成交额')
    avg_turnover = Column(Float, comment='平均成交额')
    turnover_ratio = Column(Float, comment='成交额倍数')
    price_change_pct = Column(Float, comment='价格变动百分比')

    # 股票信息
    current_price = Column(Float, comment='当前价格')
    stock_name = Column(String(100), comment='股票名称')

    # 告警状态
    is_sent = Column(Boolean, default=False, comment='是否已发送邮件')
    sent_at = Column(DateTime, comment='发送时间')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 复合索引
    __table_args__ = (
        Index('idx_alert_symbol_datetime', 'symbol', 'alert_datetime'),
    )

    def __repr__(self):
        return f"<MoneyFlowAlert(symbol='{self.symbol}', type='{self.alert_type}', datetime='{self.alert_datetime}')>"
