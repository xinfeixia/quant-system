"""
选股评分引擎
"""
import pandas as pd
import numpy as np
from loguru import logger


class ScoringEngine:
    """选股评分引擎"""
    
    def __init__(self, df):
        """
        初始化评分引擎
        
        Args:
            df: DataFrame，包含价格数据和技术指标
        """
        self.df = df.copy()
        self.scores = {}
    
    # ==================== 技术指标评分（30分） ====================
    
    def score_technical_indicators(self):
        """
        技术指标评分（30分）
        
        评分标准：
        - MACD金叉/死叉（10分）
        - RSI超买超卖（10分）
        - KDJ信号（10分）
        """
        score = 0
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else latest
        
        # 1. MACD评分（10分）
        macd_score = 0
        if pd.notna(latest.get('macd')) and pd.notna(latest.get('macd_signal')):
            macd = latest['macd']
            signal = latest['macd_signal']
            prev_macd = prev.get('macd', 0)
            prev_signal = prev.get('macd_signal', 0)
            
            # MACD金叉（MACD上穿信号线）
            if macd > signal and prev_macd <= prev_signal:
                macd_score = 10
            # MACD在信号线上方
            elif macd > signal:
                macd_score = 7
            # MACD柱状图由负转正
            elif latest.get('macd_hist', 0) > 0 and prev.get('macd_hist', 0) <= 0:
                macd_score = 8
            # MACD在零轴上方
            elif macd > 0:
                macd_score = 5
            # MACD死叉
            elif macd < signal and prev_macd >= prev_signal:
                macd_score = 0
            else:
                macd_score = 3
        
        score += macd_score
        
        # 2. RSI评分（10分）
        rsi_score = 0
        if pd.notna(latest.get('rsi')):
            rsi = latest['rsi']
            
            # RSI在50-70之间（强势但未超买）
            if 50 <= rsi <= 70:
                rsi_score = 10
            # RSI在30-50之间（从超卖恢复）
            elif 30 <= rsi < 50:
                rsi_score = 7
            # RSI在20-30之间（超卖，可能反弹）
            elif 20 <= rsi < 30:
                rsi_score = 5
            # RSI > 70（超买）
            elif rsi > 70:
                rsi_score = 3
            # RSI < 20（严重超卖）
            else:
                rsi_score = 2
        
        score += rsi_score
        
        # 3. KDJ评分（10分）
        kdj_score = 0
        if pd.notna(latest.get('kdj_k')) and pd.notna(latest.get('kdj_d')):
            k = latest['kdj_k']
            d = latest['kdj_d']
            j = latest.get('kdj_j', k)
            
            prev_k = prev.get('kdj_k', k)
            prev_d = prev.get('kdj_d', d)
            
            # KDJ金叉（K上穿D）
            if k > d and prev_k <= prev_d and k < 80:
                kdj_score = 10
            # K、D在20-80之间，且K>D
            elif 20 < k < 80 and 20 < d < 80 and k > d:
                kdj_score = 8
            # 超卖区金叉（K、D都小于20且K>D）
            elif k < 20 and d < 20 and k > d:
                kdj_score = 7
            # KDJ死叉
            elif k < d and prev_k >= prev_d:
                kdj_score = 2
            # 超买区（K>80）
            elif k > 80:
                kdj_score = 3
            else:
                kdj_score = 5
        
        score += kdj_score
        
        self.scores['technical'] = score
        logger.debug(f"技术指标评分: {score}/30 (MACD:{macd_score}, RSI:{rsi_score}, KDJ:{kdj_score})")
        return score
    
    # ==================== 量价分析评分（25分） ====================
    
    def score_volume_analysis(self):
        """
        量价分析评分（25分）
        
        评分标准：
        - 放量上涨（15分）
        - 成交量趋势（10分）
        """
        score = 0
        latest = self.df.iloc[-1]
        
        # 获取最近5天数据
        recent_5 = self.df.tail(5)
        
        # 1. 放量上涨评分（15分）
        volume_price_score = 0
        if len(recent_5) >= 2:
            # 计算价格涨跌
            price_change = (latest['close'] - recent_5.iloc[-2]['close']) / recent_5.iloc[-2]['close']
            
            # 计算成交量变化
            avg_volume = recent_5['volume'].mean()
            volume_ratio = latest['volume'] / avg_volume if avg_volume > 0 else 1
            
            # 放量上涨（价格上涨且成交量放大）
            if price_change > 0.02 and volume_ratio > 1.5:
                volume_price_score = 15
            elif price_change > 0.01 and volume_ratio > 1.2:
                volume_price_score = 12
            elif price_change > 0 and volume_ratio > 1:
                volume_price_score = 8
            # 缩量上涨
            elif price_change > 0.01 and volume_ratio < 0.8:
                volume_price_score = 6
            # 放量下跌（不好）
            elif price_change < -0.01 and volume_ratio > 1.5:
                volume_price_score = 2
            else:
                volume_price_score = 5
        
        score += volume_price_score
        
        # 2. 成交量趋势评分（10分）
        volume_trend_score = 0
        if pd.notna(latest.get('volume_ma5')) and pd.notna(latest.get('volume_ma10')):
            vol_ma5 = latest['volume_ma5']
            vol_ma10 = latest['volume_ma10']
            
            # 短期成交量均线上穿长期均线
            if vol_ma5 > vol_ma10 * 1.1:
                volume_trend_score = 10
            elif vol_ma5 > vol_ma10:
                volume_trend_score = 7
            else:
                volume_trend_score = 4
        
        score += volume_trend_score
        
        self.scores['volume'] = score
        logger.debug(f"量价分析评分: {score}/25 (放量:{volume_price_score}, 趋势:{volume_trend_score})")
        return score
    
    # ==================== 趋势分析评分（25分） ====================
    
    def score_trend_analysis(self):
        """
        趋势分析评分（25分）
        
        评分标准：
        - 均线排列（15分）
        - 价格位置（10分）
        """
        score = 0
        latest = self.df.iloc[-1]
        
        # 1. 均线排列评分（15分）
        ma_score = 0
        if all(pd.notna(latest.get(f'ma{p}')) for p in [5, 10, 20, 60]):
            ma5 = latest['ma5']
            ma10 = latest['ma10']
            ma20 = latest['ma20']
            ma60 = latest['ma60']
            close = latest['close']
            
            # 完美多头排列（价格>MA5>MA10>MA20>MA60）
            if close > ma5 > ma10 > ma20 > ma60:
                ma_score = 15
            # 强势多头（价格>MA5>MA10>MA20）
            elif close > ma5 > ma10 > ma20:
                ma_score = 12
            # 中期多头（价格>MA5>MA10）
            elif close > ma5 > ma10:
                ma_score = 9
            # 短期多头（价格>MA5）
            elif close > ma5:
                ma_score = 6
            # 空头排列
            elif close < ma5 < ma10 < ma20:
                ma_score = 2
            else:
                ma_score = 4
        
        score += ma_score
        
        # 2. 价格位置评分（10分）
        price_position_score = 0
        if pd.notna(latest.get('boll_upper')) and pd.notna(latest.get('boll_lower')):
            close = latest['close']
            boll_upper = latest['boll_upper']
            boll_middle = latest['boll_middle']
            boll_lower = latest['boll_lower']
            
            # 计算价格在布林带中的位置
            boll_range = boll_upper - boll_lower
            if boll_range > 0:
                position = (close - boll_lower) / boll_range
                
                # 价格在中轨到上轨之间（强势）
                if 0.5 <= position <= 0.8:
                    price_position_score = 10
                # 价格接近上轨（可能超买）
                elif position > 0.8:
                    price_position_score = 6
                # 价格在下轨到中轨之间
                elif 0.2 <= position < 0.5:
                    price_position_score = 7
                # 价格接近下轨（可能超卖，反弹机会）
                elif position < 0.2:
                    price_position_score = 5
                else:
                    price_position_score = 4
        
        score += price_position_score
        
        self.scores['trend'] = score
        logger.debug(f"趋势分析评分: {score}/25 (均线:{ma_score}, 位置:{price_position_score})")
        return score
    
    # ==================== 形态识别评分（20分） ====================
    
    def score_pattern_recognition(self):
        """
        形态识别评分（20分）
        
        评分标准：
        - K线形态（10分）
        - 突破信号（10分）
        """
        score = 0
        
        if len(self.df) < 3:
            self.scores['pattern'] = 0
            return 0
        
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        prev2 = self.df.iloc[-3]
        
        # 1. K线形态评分（10分）
        pattern_score = 0
        
        # 计算实体和影线
        body = abs(latest['close'] - latest['open'])
        upper_shadow = latest['high'] - max(latest['close'], latest['open'])
        lower_shadow = min(latest['close'], latest['open']) - latest['low']
        total_range = latest['high'] - latest['low']
        
        if total_range > 0:
            # 大阳线（实体占比>70%，收盘>开盘）
            if latest['close'] > latest['open'] and body / total_range > 0.7:
                pattern_score = 10
            # 锤子线（下影线长，实体小）
            elif lower_shadow > body * 2 and upper_shadow < body:
                pattern_score = 8
            # 早晨之星（三日形态）
            elif (prev2['close'] < prev2['open'] and  # 第一天阴线
                  abs(prev['close'] - prev['open']) < body and  # 第二天小实体
                  latest['close'] > latest['open']):  # 第三天阳线
                pattern_score = 9
            # 普通阳线
            elif latest['close'] > latest['open']:
                pattern_score = 6
            # 十字星
            elif body / total_range < 0.1:
                pattern_score = 5
            else:
                pattern_score = 3
        
        score += pattern_score
        
        # 2. 突破信号评分（10分）
        breakthrough_score = 0
        
        # 突破20日均线
        if pd.notna(latest.get('ma20')) and pd.notna(prev.get('ma20')):
            if latest['close'] > latest['ma20'] and prev['close'] <= prev['ma20']:
                breakthrough_score = 10
            # 站稳20日均线
            elif latest['close'] > latest['ma20']:
                breakthrough_score = 7
            else:
                breakthrough_score = 3
        
        score += breakthrough_score
        
        self.scores['pattern'] = score
        logger.debug(f"形态识别评分: {score}/20 (形态:{pattern_score}, 突破:{breakthrough_score})")
        return score
    
    # ==================== 综合评分 ====================
    
    def calculate_total_score(self):
        """
        计算总分
        
        Returns:
            dict: 包含各维度分数和总分
        """
        # 计算各维度分数
        technical_score = self.score_technical_indicators()
        volume_score = self.score_volume_analysis()
        trend_score = self.score_trend_analysis()
        pattern_score = self.score_pattern_recognition()
        
        # 计算总分
        total_score = technical_score + volume_score + trend_score + pattern_score
        
        result = {
            'total_score': total_score,
            'technical_score': technical_score,
            'volume_score': volume_score,
            'trend_score': trend_score,
            'pattern_score': pattern_score,
            'max_score': 100
        }
        
        logger.info(f"总分: {total_score}/100 (技术:{technical_score}, 量价:{volume_score}, 趋势:{trend_score}, 形态:{pattern_score})")
        
        return result

