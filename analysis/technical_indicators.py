"""
技术指标计算模块
"""
import pandas as pd
import numpy as np
from loguru import logger


class TechnicalIndicators:
    """技术指标计算器"""
    
    def __init__(self, df):
        """
        初始化技术指标计算器
        
        Args:
            df: DataFrame，必须包含 ['open', 'high', 'low', 'close', 'volume'] 列
        """
        self.df = df.copy()
        self._validate_data()
    
    def _validate_data(self):
        """验证数据格式"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            raise ValueError(f"数据缺少必要的列: {missing_columns}")
        
        if len(self.df) == 0:
            raise ValueError("数据为空")
    
    # ==================== 趋势指标 ====================
    
    def calculate_ma(self, periods=[5, 10, 20, 60]):
        """
        计算移动平均线 (MA)
        
        Args:
            periods: 周期列表
            
        Returns:
            DataFrame with MA columns
        """
        for period in periods:
            self.df[f'ma{period}'] = self.df['close'].rolling(window=period).mean()
        
        logger.debug(f"计算MA完成: {periods}")
        return self.df
    
    def calculate_ema(self, periods=[12, 26]):
        """
        计算指数移动平均线 (EMA)
        
        Args:
            periods: 周期列表
            
        Returns:
            DataFrame with EMA columns
        """
        for period in periods:
            self.df[f'ema{period}'] = self.df['close'].ewm(span=period, adjust=False).mean()
        
        logger.debug(f"计算EMA完成: {periods}")
        return self.df
    
    def calculate_macd(self, fast=12, slow=26, signal=9):
        """
        计算MACD指标
        
        Args:
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        Returns:
            DataFrame with MACD columns
        """
        # 计算EMA
        ema_fast = self.df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = self.df['close'].ewm(span=slow, adjust=False).mean()
        
        # MACD线 = 快线 - 慢线
        self.df['macd'] = ema_fast - ema_slow
        
        # 信号线 = MACD的EMA
        self.df['macd_signal'] = self.df['macd'].ewm(span=signal, adjust=False).mean()
        
        # MACD柱状图 = MACD - 信号线
        self.df['macd_hist'] = self.df['macd'] - self.df['macd_signal']
        
        logger.debug(f"计算MACD完成: fast={fast}, slow={slow}, signal={signal}")
        return self.df
    
    # ==================== 震荡指标 ====================
    
    def calculate_rsi(self, period=14):
        """
        计算相对强弱指标 (RSI)
        
        Args:
            period: 周期
            
        Returns:
            DataFrame with RSI column
        """
        # 计算价格变化
        delta = self.df['close'].diff()
        
        # 分离上涨和下跌
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # 计算RS和RSI
        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))
        
        logger.debug(f"计算RSI完成: period={period}")
        return self.df
    
    def calculate_kdj(self, n=9, m1=3, m2=3):
        """
        计算KDJ指标
        
        Args:
            n: RSV周期
            m1: K值平滑周期
            m2: D值平滑周期
            
        Returns:
            DataFrame with KDJ columns
        """
        # 计算RSV (未成熟随机值)
        low_n = self.df['low'].rolling(window=n).min()
        high_n = self.df['high'].rolling(window=n).max()
        
        rsv = (self.df['close'] - low_n) / (high_n - low_n) * 100
        
        # 计算K值 (RSV的移动平均)
        self.df['kdj_k'] = rsv.ewm(com=m1-1, adjust=False).mean()
        
        # 计算D值 (K值的移动平均)
        self.df['kdj_d'] = self.df['kdj_k'].ewm(com=m2-1, adjust=False).mean()
        
        # 计算J值
        self.df['kdj_j'] = 3 * self.df['kdj_k'] - 2 * self.df['kdj_d']
        
        logger.debug(f"计算KDJ完成: n={n}, m1={m1}, m2={m2}")
        return self.df
    
    # ==================== 波动指标 ====================
    
    def calculate_bollinger_bands(self, period=20, std_dev=2):
        """
        计算布林带 (Bollinger Bands)
        
        Args:
            period: 周期
            std_dev: 标准差倍数
            
        Returns:
            DataFrame with Bollinger Bands columns
        """
        # 中轨 = 移动平均线
        self.df['boll_middle'] = self.df['close'].rolling(window=period).mean()
        
        # 标准差
        std = self.df['close'].rolling(window=period).std()
        
        # 上轨 = 中轨 + 标准差 * 倍数
        self.df['boll_upper'] = self.df['boll_middle'] + (std * std_dev)
        
        # 下轨 = 中轨 - 标准差 * 倍数
        self.df['boll_lower'] = self.df['boll_middle'] - (std * std_dev)
        
        logger.debug(f"计算布林带完成: period={period}, std_dev={std_dev}")
        return self.df
    
    def calculate_atr(self, period=14):
        """
        计算平均真实波幅 (ATR)
        
        Args:
            period: 周期
            
        Returns:
            DataFrame with ATR column
        """
        # 计算真实波幅 (TR)
        high_low = self.df['high'] - self.df['low']
        high_close = np.abs(self.df['high'] - self.df['close'].shift())
        low_close = np.abs(self.df['low'] - self.df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR = TR的移动平均
        self.df['atr'] = tr.rolling(window=period).mean()
        
        logger.debug(f"计算ATR完成: period={period}")
        return self.df
    
    # ==================== 成交量指标 ====================
    
    def calculate_obv(self):
        """
        计算能量潮 (OBV)
        
        Returns:
            DataFrame with OBV column
        """
        # 价格上涨时加上成交量，下跌时减去成交量
        obv = []
        obv_value = 0
        
        for i in range(len(self.df)):
            if i == 0:
                obv_value = self.df['volume'].iloc[i]
            else:
                if self.df['close'].iloc[i] > self.df['close'].iloc[i-1]:
                    obv_value += self.df['volume'].iloc[i]
                elif self.df['close'].iloc[i] < self.df['close'].iloc[i-1]:
                    obv_value -= self.df['volume'].iloc[i]
            obv.append(obv_value)
        
        self.df['obv'] = obv
        
        logger.debug("计算OBV完成")
        return self.df
    
    def calculate_volume_ma(self, periods=[5, 10]):
        """
        计算成交量移动平均线
        
        Args:
            periods: 周期列表
            
        Returns:
            DataFrame with volume MA columns
        """
        for period in periods:
            self.df[f'volume_ma{period}'] = self.df['volume'].rolling(window=period).mean()
        
        logger.debug(f"计算成交量MA完成: {periods}")
        return self.df
    
    # ==================== 综合计算 ====================
    
    def calculate_all(self):
        """
        计算所有技术指标
        
        Returns:
            DataFrame with all indicators
        """
        logger.info("开始计算所有技术指标...")
        
        # 趋势指标
        self.calculate_ma([5, 10, 20, 60])
        self.calculate_ema([12, 26])
        self.calculate_macd()
        
        # 震荡指标
        self.calculate_rsi()
        self.calculate_kdj()
        
        # 波动指标
        self.calculate_bollinger_bands()
        self.calculate_atr()
        
        # 成交量指标
        self.calculate_obv()
        self.calculate_volume_ma([5, 10])
        
        logger.info("所有技术指标计算完成")
        return self.df
    
    def get_latest_indicators(self):
        """
        获取最新的技术指标值
        
        Returns:
            dict: 最新指标值
        """
        if len(self.df) == 0:
            return {}
        
        latest = self.df.iloc[-1]
        
        indicators = {
            # 趋势指标
            'ma5': latest.get('ma5'),
            'ma10': latest.get('ma10'),
            'ma20': latest.get('ma20'),
            'ma60': latest.get('ma60'),
            'ema12': latest.get('ema12'),
            'ema26': latest.get('ema26'),
            'macd': latest.get('macd'),
            'macd_signal': latest.get('macd_signal'),
            'macd_hist': latest.get('macd_hist'),
            
            # 震荡指标
            'rsi': latest.get('rsi'),
            'kdj_k': latest.get('kdj_k'),
            'kdj_d': latest.get('kdj_d'),
            'kdj_j': latest.get('kdj_j'),
            
            # 波动指标
            'boll_upper': latest.get('boll_upper'),
            'boll_middle': latest.get('boll_middle'),
            'boll_lower': latest.get('boll_lower'),
            'atr': latest.get('atr'),
            
            # 成交量指标
            'obv': latest.get('obv'),
            'volume_ma5': latest.get('volume_ma5'),
            'volume_ma10': latest.get('volume_ma10'),
        }
        
        return indicators

