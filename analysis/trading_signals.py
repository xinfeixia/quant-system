"""
买卖信号分析引擎
计算最佳买入卖出点
"""
import numpy as np
from datetime import datetime, timedelta
from loguru import logger


class TradingSignalAnalyzer:
    """买卖信号分析器"""
    
    def __init__(self, kline_data):
        """
        初始化
        
        Args:
            kline_data: K线数据列表，每个元素包含 date, open, high, low, close, volume 等
        """
        self.data = kline_data
        self.current_price = kline_data[-1]['close'] if kline_data else 0
        
    def calculate_support_resistance(self, periods=[20, 60]):
        """
        计算支撑位和阻力位
        
        Args:
            periods: 计算周期列表
            
        Returns:
            dict: 支撑位和阻力位信息
        """
        if len(self.data) < max(periods):
            return {'support': [], 'resistance': []}
        
        support_levels = []
        resistance_levels = []
        
        for period in periods:
            recent_data = self.data[-period:]
            
            # 计算支撑位（近期低点）
            lows = [d['low'] for d in recent_data]
            support = min(lows)
            support_levels.append({
                'price': support,
                'period': period,
                'distance': ((self.current_price - support) / support * 100)
            })
            
            # 计算阻力位（近期高点）
            highs = [d['high'] for d in recent_data]
            resistance = max(highs)
            resistance_levels.append({
                'price': resistance,
                'period': period,
                'distance': ((resistance - self.current_price) / self.current_price * 100)
            })
        
        return {
            'support': sorted(support_levels, key=lambda x: x['price'], reverse=True),
            'resistance': sorted(resistance_levels, key=lambda x: x['price'])
        }
    
    def generate_buy_signals(self):
        """
        生成买入信号
        
        Returns:
            dict: 买入信号信息
        """
        if len(self.data) < 30:
            return {'signal': 'HOLD', 'strength': 0, 'reasons': []}
        
        latest = self.data[-1]
        prev = self.data[-2]
        
        signals = []
        strength = 0
        
        # 1. MACD金叉
        if latest.get('macd') and prev.get('macd'):
            if latest['macd'] > latest['signal'] and prev['macd'] <= prev['signal']:
                signals.append('MACD金叉')
                strength += 25
        
        # 2. RSI超卖
        if latest.get('rsi'):
            if latest['rsi'] < 30:
                signals.append(f'RSI超卖({latest["rsi"]:.1f})')
                strength += 20
            elif latest['rsi'] < 40:
                signals.append(f'RSI偏低({latest["rsi"]:.1f})')
                strength += 10
        
        # 3. KDJ金叉
        if latest.get('kdj_k') and latest.get('kdj_d'):
            if latest['kdj_k'] > latest['kdj_d'] and prev.get('kdj_k', 0) <= prev.get('kdj_d', 0):
                signals.append('KDJ金叉')
                strength += 20
        
        # 4. 价格在布林带下轨附近
        if latest.get('boll_lower'):
            distance = (latest['close'] - latest['boll_lower']) / latest['boll_lower'] * 100
            if distance < 2:
                signals.append('接近布林带下轨')
                strength += 15
        
        # 5. 均线多头排列
        if latest.get('ma5') and latest.get('ma10') and latest.get('ma20'):
            if latest['ma5'] > latest['ma10'] > latest['ma20']:
                signals.append('均线多头排列')
                strength += 20
        
        # 判断信号强度
        if strength >= 60:
            signal = 'STRONG_BUY'
        elif strength >= 40:
            signal = 'BUY'
        elif strength >= 20:
            signal = 'WEAK_BUY'
        else:
            signal = 'HOLD'
        
        return {
            'signal': signal,
            'strength': strength,
            'reasons': signals,
            'current_price': self.current_price
        }
    
    def generate_sell_signals(self):
        """
        生成卖出信号
        
        Returns:
            dict: 卖出信号信息
        """
        if len(self.data) < 30:
            return {'signal': 'HOLD', 'strength': 0, 'reasons': []}
        
        latest = self.data[-1]
        prev = self.data[-2]
        
        signals = []
        strength = 0
        
        # 1. MACD死叉
        if latest.get('macd') and prev.get('macd'):
            if latest['macd'] < latest['signal'] and prev['macd'] >= prev['signal']:
                signals.append('MACD死叉')
                strength += 25
        
        # 2. RSI超买
        if latest.get('rsi'):
            if latest['rsi'] > 70:
                signals.append(f'RSI超买({latest["rsi"]:.1f})')
                strength += 20
            elif latest['rsi'] > 60:
                signals.append(f'RSI偏高({latest["rsi"]:.1f})')
                strength += 10
        
        # 3. KDJ死叉
        if latest.get('kdj_k') and latest.get('kdj_d'):
            if latest['kdj_k'] < latest['kdj_d'] and prev.get('kdj_k', 0) >= prev.get('kdj_d', 0):
                signals.append('KDJ死叉')
                strength += 20
        
        # 4. 价格在布林带上轨附近
        if latest.get('boll_upper'):
            distance = (latest['boll_upper'] - latest['close']) / latest['close'] * 100
            if distance < 2:
                signals.append('接近布林带上轨')
                strength += 15
        
        # 5. 均线空头排列
        if latest.get('ma5') and latest.get('ma10') and latest.get('ma20'):
            if latest['ma5'] < latest['ma10'] < latest['ma20']:
                signals.append('均线空头排列')
                strength += 20
        
        # 判断信号强度
        if strength >= 60:
            signal = 'STRONG_SELL'
        elif strength >= 40:
            signal = 'SELL'
        elif strength >= 20:
            signal = 'WEAK_SELL'
        else:
            signal = 'HOLD'
        
        return {
            'signal': signal,
            'strength': strength,
            'reasons': signals,
            'current_price': self.current_price
        }
    
    def calculate_target_prices(self):
        """
        计算目标价和止损价
        
        Returns:
            dict: 目标价和止损价信息
        """
        if len(self.data) < 20:
            return {}
        
        latest = self.data[-1]
        
        # 计算ATR（平均真实波幅）
        atr = latest.get('atr', 0)
        if not atr:
            # 简单计算ATR
            recent_ranges = [(d['high'] - d['low']) for d in self.data[-14:]]
            atr = np.mean(recent_ranges)
        
        # 支撑阻力位
        sr = self.calculate_support_resistance()
        
        # 止损价：当前价 - 2*ATR 或 最近支撑位
        stop_loss_atr = self.current_price - 2 * atr
        stop_loss_support = sr['support'][0]['price'] if sr['support'] else stop_loss_atr
        stop_loss = max(stop_loss_atr, stop_loss_support)
        
        # 目标价1：当前价 + 3*ATR
        target1 = self.current_price + 3 * atr
        
        # 目标价2：当前价 + 5*ATR 或 最近阻力位
        target2_atr = self.current_price + 5 * atr
        target2_resistance = sr['resistance'][0]['price'] if sr['resistance'] else target2_atr
        target2 = min(target2_atr, target2_resistance)
        
        # 计算风险收益比
        risk = self.current_price - stop_loss
        reward1 = target1 - self.current_price
        reward2 = target2 - self.current_price
        
        return {
            'current_price': self.current_price,
            'stop_loss': stop_loss,
            'stop_loss_pct': ((stop_loss - self.current_price) / self.current_price * 100),
            'target1': target1,
            'target1_pct': ((target1 - self.current_price) / self.current_price * 100),
            'target2': target2,
            'target2_pct': ((target2 - self.current_price) / self.current_price * 100),
            'risk_reward_ratio1': reward1 / risk if risk > 0 else 0,
            'risk_reward_ratio2': reward2 / risk if risk > 0 else 0,
            'atr': atr
        }
    
    def find_best_historical_trades(self, days_back=90):
        """
        找出历史最佳买卖点
        
        Args:
            days_back: 回溯天数
            
        Returns:
            list: 最佳交易机会列表
        """
        if len(self.data) < 10:
            return []
        
        trades = []
        data_to_analyze = self.data[-days_back:] if len(self.data) > days_back else self.data
        
        # 寻找局部低点（买入点）和高点（卖出点）
        for i in range(5, len(data_to_analyze) - 5):
            current = data_to_analyze[i]
            
            # 检查是否是局部低点
            is_local_low = all(current['low'] <= data_to_analyze[j]['low'] 
                              for j in range(i-5, i+5) if j != i)
            
            if is_local_low:
                # 找到这个低点之后的最高点
                future_data = data_to_analyze[i+1:]
                if future_data:
                    max_price = max(d['high'] for d in future_data)
                    max_idx = next(idx for idx, d in enumerate(future_data) if d['high'] == max_price)
                    
                    buy_price = current['low']
                    sell_price = max_price
                    profit_pct = (sell_price - buy_price) / buy_price * 100
                    
                    if profit_pct > 5:  # 只记录收益超过5%的交易
                        trades.append({
                            'buy_date': current['date'],
                            'buy_price': buy_price,
                            'sell_date': future_data[max_idx]['date'],
                            'sell_price': sell_price,
                            'profit_pct': profit_pct,
                            'holding_days': max_idx + 1
                        })
        
        # 按收益率排序
        trades.sort(key=lambda x: x['profit_pct'], reverse=True)
        
        return trades[:10]  # 返回前10个最佳交易

