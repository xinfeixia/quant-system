#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时信号监控器

功能：
1. 实时监控持仓，检查卖出条件
2. 实时监控选股结果，检查买入条件
3. 自动生成买入/卖出信号
4. 自动执行信号
"""

import time
from datetime import datetime, date
from typing import Dict, List
from loguru import logger

from database.models import Position, StockSelection, TradingSignal
from trading.auto_sell_monitor import AutoSellMonitor


class RealtimeSignalMonitor:
    """实时信号监控器"""
    
    def __init__(self, db_manager, longport_client, config: Dict):
        """
        初始化实时监控器
        
        Args:
            db_manager: 数据库管理器
            longport_client: LongPort客户端（用于获取实时行情）
            config: 配置字典
        """
        self.db = db_manager
        self.client = longport_client
        self.config = config
        
        # 卖出策略配置
        self.sell_strategy_config = config.get('sell_strategy', {
            'stop_loss': {'enabled': True, 'stop_loss_pct': -0.05},
            'take_profit': {'enabled': True, 'take_profit_pct': 0.10},
            'trailing_stop': {'enabled': True, 'trailing_stop_pct': 0.05}
        })
        
        # 买入策略配置
        self.buy_strategy_config = config.get('buy_strategy', {
            'max_positions': 20,
            'min_score': 70,
            'enabled': True
        })
        
        # 监控间隔（秒）
        self.check_interval = config.get('check_interval', 60)  # 默认60秒
        
        # 是否运行
        self.running = False
        
        logger.info(f"实时信号监控器初始化完成，检查间隔: {self.check_interval}秒")
    
    
    def start(self):
        """启动实时监控"""
        self.running = True
        logger.info("🚀 实时信号监控器启动")
        
        while self.running:
            try:
                # 检查是否在交易时间
                if not self._is_trading_time():
                    logger.debug("非交易时间，跳过检查")
                    time.sleep(60)
                    continue
                
                # 1. 检查卖出信号
                sell_count = self._check_sell_signals()
                
                # 2. 检查买入信号
                buy_count = self._check_buy_signals()
                
                if sell_count > 0 or buy_count > 0:
                    logger.info(f"✅ 信号检查完成: 买入{buy_count}个, 卖出{sell_count}个")
                
                # 等待下一次检查
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("收到停止信号，退出监控")
                break
            except Exception as e:
                logger.error(f"监控过程出错: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.check_interval)
    
    
    def stop(self):
        """停止实时监控"""
        self.running = False
        logger.info("⏹️ 实时信号监控器停止")
    
    
    def _is_trading_time(self) -> bool:
        """
        检查是否在交易时间
        
        港股交易时间：
        - 上午: 09:30 - 12:00
        - 下午: 13:00 - 16:00
        
        A股交易时间：
        - 上午: 09:30 - 11:30
        - 下午: 13:00 - 15:00
        """
        now = datetime.now()
        
        # 周末不交易
        if now.weekday() >= 5:
            return False
        
        current_time = now.time()
        
        # 港股交易时间（更宽松）
        morning_start = datetime.strptime("09:30", "%H:%M").time()
        morning_end = datetime.strptime("12:00", "%H:%M").time()
        afternoon_start = datetime.strptime("13:00", "%H:%M").time()
        afternoon_end = datetime.strptime("16:00", "%H:%M").time()
        
        is_trading = (morning_start <= current_time <= morning_end) or \
                     (afternoon_start <= current_time <= afternoon_end)
        
        return is_trading
    
    
    def _check_sell_signals(self) -> int:
        """
        检查卖出信号（实时）
        
        Returns:
            生成的卖出信号数量
        """
        if not self.sell_strategy_config:
            return 0
        
        try:
            # 使用 AutoSellMonitor 检查卖出条件
            monitor = AutoSellMonitor(self.db, self.sell_strategy_config)
            
            # 获取卖出信号（但不立即写入数据库）
            sell_signals = monitor.check_positions()
            
            if not sell_signals:
                return 0
            
            # 写入数据库
            count = 0
            today = date.today()
            
            with self.db.get_session() as session:
                for sig in sell_signals:
                    # 检查是否已有今日卖出信号
                    existing = session.query(TradingSignal).filter(
                        TradingSignal.symbol == sig['symbol'],
                        TradingSignal.signal_date == today,
                        TradingSignal.signal_type == 'SELL',
                        TradingSignal.is_executed == False
                    ).first()
                    
                    if existing:
                        logger.debug(f"{sig['symbol']}: 今日已有卖出信号，跳过")
                        continue
                    
                    # 创建卖出信号
                    signal = TradingSignal(
                        symbol=sig['symbol'],
                        signal_date=today,
                        signal_type='SELL',
                        signal_strength=sig.get('strength', 0.8),
                        signal_price=sig.get('current_price'),
                        source='realtime_monitor',
                        reason='; '.join(sig.get('reasons', []))
                    )
                    session.add(signal)
                    count += 1
                    
                    logger.info(f"🔴 生成卖出信号: {sig['symbol']} - {sig.get('reasons', [])}")
                
                session.commit()
            
            return count
            
        except Exception as e:
            logger.error(f"检查卖出信号失败: {e}")
            return 0
    
    
    def _check_buy_signals(self) -> int:
        """
        检查买入信号（实时）
        
        基于今日选股结果，检查是否有新的买入机会
        
        Returns:
            生成的买入信号数量
        """
        if not self.buy_strategy_config.get('enabled', True):
            return 0
        
        try:
            today = date.today()
            max_positions = self.buy_strategy_config.get('max_positions', 20)
            min_score = self.buy_strategy_config.get('min_score', 70)
            
            count = 0
            
            with self.db.get_session() as session:
                # 检查当前持仓数
                current_positions = session.query(Position).filter(
                    Position.quantity > 0
                ).count()
                
                if current_positions >= max_positions:
                    logger.debug(f"持仓已满 ({current_positions}/{max_positions})，不生成买入信号")
                    return 0
                
                # 可买入数量
                available_slots = max_positions - current_positions
                
                # 获取今日选股结果（未持有且未生成信号的）
                selections = session.query(StockSelection).filter(
                    StockSelection.selection_date == today,
                    StockSelection.total_score >= min_score
                ).order_by(StockSelection.rank).all()
                
                for sel in selections[:available_slots * 2]:  # 多查一些备选
                    # 检查是否已持有
                    pos = session.query(Position).filter_by(symbol=sel.symbol).first()
                    if pos and pos.quantity > 0:
                        continue
                    
                    # 检查是否已有今日买入信号
                    existing = session.query(TradingSignal).filter(
                        TradingSignal.symbol == sel.symbol,
                        TradingSignal.signal_date == today,
                        TradingSignal.signal_type == 'BUY',
                        TradingSignal.is_executed == False
                    ).first()
                    
                    if existing:
                        continue
                    
                    # 获取实时价格（可选）
                    # current_price = self._get_realtime_price(sel.symbol)
                    
                    # 创建买入信号
                    signal = TradingSignal(
                        symbol=sel.symbol,
                        signal_date=today,
                        signal_type='BUY',
                        signal_strength=sel.total_score / 100.0,
                        signal_price=sel.latest_price or sel.current_price,
                        source='realtime_monitor',
                        reason=f'选股评分{sel.total_score}分，排名{sel.rank}'
                    )
                    session.add(signal)
                    count += 1
                    
                    logger.info(f"🟢 生成买入信号: {sel.symbol} ({sel.name}) - 评分{sel.total_score}分")
                    
                    if count >= available_slots:
                        break
                
                session.commit()
            
            return count
            
        except Exception as e:
            logger.error(f"检查买入信号失败: {e}")
            return 0
    
    
    def _get_realtime_price(self, symbol: str) -> float:
        """
        获取实时价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            实时价格
        """
        try:
            # 使用 LongPort 获取实时行情
            quote_ctx = self.client.get_quote_context()
            quotes = quote_ctx.quote([symbol])
            
            if quotes and len(quotes) > 0:
                return float(quotes[0].last_done)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"获取实时价格失败 {symbol}: {e}")
            return 0.0


def run_realtime_monitor(config_dir: str = None):
    """
    运行实时监控器
    
    Args:
        config_dir: 配置文件目录
    """
    from pathlib import Path
    import sys
    
    if config_dir is None:
        base = Path(__file__).resolve().parent.parent
        config_dir = str(base / 'config')
    
    from utils.config_loader import init_config
    from database import init_database
    from data_collection.longport_client import LongPortClient
    
    # 初始化
    cfg = init_config(config_dir=config_dir)
    db = init_database(cfg.config)
    client = LongPortClient(cfg.api_config)
    
    # 配置
    monitor_config = {
        'sell_strategy': {
            'stop_loss': {'enabled': True, 'stop_loss_pct': -0.05},
            'take_profit': {'enabled': True, 'take_profit_pct': 0.10},
            'trailing_stop': {'enabled': True, 'trailing_stop_pct': 0.05}
        },
        'buy_strategy': {
            'max_positions': 20,
            'min_score': 70,
            'enabled': True
        },
        'check_interval': 60  # 60秒检查一次
    }
    
    # 创建并启动监控器
    monitor = RealtimeSignalMonitor(db, client, monitor_config)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        monitor.stop()
        logger.info("监控器已停止")


if __name__ == '__main__':
    run_realtime_monitor()

