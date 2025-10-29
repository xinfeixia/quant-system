#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动卖出策略

支持多种卖出条件：
1. 止损：跌幅超过设定比例
2. 止盈：涨幅超过设定比例
3. 固定持有期：持有天数达到设定值
4. 技术指标：MACD死叉、RSI超买等
5. 移动止损：跟随最高价设置止损线
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from loguru import logger


class AutoSellStrategy:
    """自动卖出策略基类"""
    
    def __init__(self, config: Dict):
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        self.config = config
        self.enabled = config.get('enabled', False)
    
    def should_sell(self, position: Dict, current_price: float, indicators: Dict = None) -> tuple:
        """
        判断是否应该卖出
        
        Args:
            position: 持仓信息 {symbol, quantity, avg_price, entry_date, ...}
            current_price: 当前价格
            indicators: 技术指标 {macd, rsi, kdj, ...}
        
        Returns:
            (should_sell: bool, reason: str)
        """
        raise NotImplementedError


class StopLossStrategy(AutoSellStrategy):
    """止损策略"""
    
    def __init__(self, config: Dict):
        """
        初始化止损策略
        
        Args:
            config: {
                'enabled': True,
                'stop_loss_pct': -0.05  # 止损比例 -5%
            }
        """
        super().__init__(config)
        self.stop_loss_pct = config.get('stop_loss_pct', -0.05)
    
    def should_sell(self, position: Dict, current_price: float, indicators: Dict = None) -> tuple:
        """止损判断"""
        if not self.enabled:
            return False, ""
        
        avg_price = position.get('avg_price', 0)
        if avg_price <= 0:
            return False, ""
        
        # 计算收益率
        return_pct = (current_price - avg_price) / avg_price
        
        # 触发止损
        if return_pct <= self.stop_loss_pct:
            return True, f"止损: 收益率{return_pct*100:.2f}% <= {self.stop_loss_pct*100:.2f}%"
        
        return False, ""


class TakeProfitStrategy(AutoSellStrategy):
    """止盈策略"""
    
    def __init__(self, config: Dict):
        """
        初始化止盈策略
        
        Args:
            config: {
                'enabled': True,
                'take_profit_pct': 0.10  # 止盈比例 +10%
            }
        """
        super().__init__(config)
        self.take_profit_pct = config.get('take_profit_pct', 0.10)
    
    def should_sell(self, position: Dict, current_price: float, indicators: Dict = None) -> tuple:
        """止盈判断"""
        if not self.enabled:
            return False, ""
        
        avg_price = position.get('avg_price', 0)
        if avg_price <= 0:
            return False, ""
        
        # 计算收益率
        return_pct = (current_price - avg_price) / avg_price
        
        # 触发止盈
        if return_pct >= self.take_profit_pct:
            return True, f"止盈: 收益率{return_pct*100:.2f}% >= {self.take_profit_pct*100:.2f}%"
        
        return False, ""


class FixedHoldStrategy(AutoSellStrategy):
    """固定持有期策略"""
    
    def __init__(self, config: Dict):
        """
        初始化固定持有期策略
        
        Args:
            config: {
                'enabled': True,
                'hold_days': 7  # 持有天数
            }
        """
        super().__init__(config)
        self.hold_days = config.get('hold_days', 7)
    
    def should_sell(self, position: Dict, current_price: float, indicators: Dict = None) -> tuple:
        """固定持有期判断"""
        if not self.enabled:
            return False, ""
        
        entry_date = position.get('entry_date')
        if not entry_date:
            return False, ""
        
        # 如果是字符串，转换为 date
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
        elif isinstance(entry_date, datetime):
            entry_date = entry_date.date()
        
        # 计算持有天数
        days_held = (date.today() - entry_date).days
        
        # 达到持有期限
        if days_held >= self.hold_days:
            return True, f"固定持有期: 已持有{days_held}天 >= {self.hold_days}天"
        
        return False, ""


class TrailingStopStrategy(AutoSellStrategy):
    """移动止损策略（跟随最高价）"""
    
    def __init__(self, config: Dict):
        """
        初始化移动止损策略
        
        Args:
            config: {
                'enabled': True,
                'trailing_stop_pct': 0.05  # 从最高价回撤5%触发止损
            }
        """
        super().__init__(config)
        self.trailing_stop_pct = config.get('trailing_stop_pct', 0.05)
        self.highest_prices = {}  # 记录每只股票的最高价
    
    def should_sell(self, position: Dict, current_price: float, indicators: Dict = None) -> tuple:
        """移动止损判断"""
        if not self.enabled:
            return False, ""
        
        symbol = position.get('symbol')
        avg_price = position.get('avg_price', 0)
        
        # 更新最高价
        if symbol not in self.highest_prices:
            self.highest_prices[symbol] = max(avg_price, current_price)
        else:
            self.highest_prices[symbol] = max(self.highest_prices[symbol], current_price)
        
        highest_price = self.highest_prices[symbol]
        
        # 计算从最高价的回撤
        drawdown = (current_price - highest_price) / highest_price
        
        # 触发移动止损
        if drawdown <= -self.trailing_stop_pct:
            return True, f"移动止损: 从最高价{highest_price:.2f}回撤{abs(drawdown)*100:.2f}% >= {self.trailing_stop_pct*100:.2f}%"
        
        return False, ""


class TechnicalIndicatorStrategy(AutoSellStrategy):
    """技术指标策略"""
    
    def __init__(self, config: Dict):
        """
        初始化技术指标策略
        
        Args:
            config: {
                'enabled': True,
                'rsi_overbought': 70,  # RSI超买阈值
                'macd_death_cross': True  # MACD死叉
            }
        """
        super().__init__(config)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.macd_death_cross = config.get('macd_death_cross', True)
    
    def should_sell(self, position: Dict, current_price: float, indicators: Dict = None) -> tuple:
        """技术指标判断"""
        if not self.enabled or not indicators:
            return False, ""
        
        reasons = []
        
        # RSI超买
        rsi = indicators.get('rsi')
        if rsi and rsi > self.rsi_overbought:
            reasons.append(f"RSI超买({rsi:.1f} > {self.rsi_overbought})")
        
        # MACD死叉
        if self.macd_death_cross:
            macd = indicators.get('macd')
            signal = indicators.get('macd_signal')
            prev_macd = indicators.get('prev_macd')
            prev_signal = indicators.get('prev_signal')
            
            if all([macd, signal, prev_macd, prev_signal]):
                # 当前MACD < Signal，前一天MACD >= Signal
                if macd < signal and prev_macd >= prev_signal:
                    reasons.append("MACD死叉")
        
        if reasons:
            return True, "技术指标: " + ", ".join(reasons)
        
        return False, ""


class CompositeStrategy:
    """组合策略（多个策略组合）"""
    
    def __init__(self, config: Dict):
        """
        初始化组合策略
        
        Args:
            config: {
                'stop_loss': {'enabled': True, 'stop_loss_pct': -0.05},
                'take_profit': {'enabled': True, 'take_profit_pct': 0.10},
                'fixed_hold': {'enabled': False, 'hold_days': 7},
                'trailing_stop': {'enabled': False, 'trailing_stop_pct': 0.05},
                'technical': {'enabled': False, 'rsi_overbought': 70}
            }
        """
        self.strategies = []
        
        # 止损策略
        if config.get('stop_loss', {}).get('enabled', False):
            self.strategies.append(StopLossStrategy(config['stop_loss']))
        
        # 止盈策略
        if config.get('take_profit', {}).get('enabled', False):
            self.strategies.append(TakeProfitStrategy(config['take_profit']))
        
        # 固定持有期策略
        if config.get('fixed_hold', {}).get('enabled', False):
            self.strategies.append(FixedHoldStrategy(config['fixed_hold']))
        
        # 移动止损策略
        if config.get('trailing_stop', {}).get('enabled', False):
            self.strategies.append(TrailingStopStrategy(config['trailing_stop']))
        
        # 技术指标策略
        if config.get('technical', {}).get('enabled', False):
            self.strategies.append(TechnicalIndicatorStrategy(config['technical']))
    
    def should_sell(self, position: Dict, current_price: float, indicators: Dict = None) -> tuple:
        """
        判断是否应该卖出（任一策略触发即卖出）
        
        Returns:
            (should_sell: bool, reasons: List[str])
        """
        reasons = []
        
        for strategy in self.strategies:
            should_sell, reason = strategy.should_sell(position, current_price, indicators)
            if should_sell:
                reasons.append(reason)
        
        return len(reasons) > 0, reasons

