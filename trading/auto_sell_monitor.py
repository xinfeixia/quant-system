#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动卖出监控器

定期检查持仓，根据策略自动生成卖出信号
"""

from datetime import datetime, date
from typing import Dict, List
from loguru import logger

from database.models import Position, TradingSignal, DailyData, TechnicalIndicator
from trading.auto_sell_strategy import CompositeStrategy


class AutoSellMonitor:
    """自动卖出监控器"""
    
    def __init__(self, db_manager, strategy_config: Dict):
        """
        初始化监控器
        
        Args:
            db_manager: 数据库管理器
            strategy_config: 策略配置
        """
        self.db = db_manager
        self.strategy = CompositeStrategy(strategy_config)
        logger.info("自动卖出监控器初始化完成")
    
    def check_positions(self) -> List[Dict]:
        """
        检查所有持仓，生成卖出信号
        
        Returns:
            卖出信号列表
        """
        sell_signals = []
        
        with self.db.get_session() as session:
            # 获取所有持仓
            positions = session.query(Position).filter(Position.quantity > 0).all()
            
            logger.info(f"检查 {len(positions)} 个持仓...")
            
            for pos in positions:
                # 获取当前价格
                current_price = self._get_latest_price(session, pos.symbol)
                if not current_price:
                    logger.warning(f"{pos.symbol}: 无法获取最新价格，跳过")
                    continue
                
                # 获取技术指标
                indicators = self._get_latest_indicators(session, pos.symbol)
                
                # 构造持仓信息
                position_info = {
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'avg_price': pos.avg_price,
                    'entry_date': pos.updated_at.date() if pos.updated_at else date.today()
                }
                
                # 判断是否应该卖出
                should_sell, reasons = self.strategy.should_sell(
                    position_info, 
                    current_price, 
                    indicators
                )
                
                if should_sell:
                    signal = {
                        'symbol': pos.symbol,
                        'quantity': pos.quantity,
                        'current_price': current_price,
                        'avg_price': pos.avg_price,
                        'reasons': reasons,
                        'pnl_pct': (current_price - pos.avg_price) / pos.avg_price * 100
                    }
                    sell_signals.append(signal)
                    
                    logger.info(f"🔔 {pos.symbol} 触发卖出: {', '.join(reasons)}")
        
        return sell_signals
    
    def generate_sell_signals(self, auto_execute: bool = False) -> int:
        """
        生成卖出信号并写入数据库
        
        Args:
            auto_execute: 是否自动执行（写入 TradingSignal 表）
        
        Returns:
            生成的信号数量
        """
        sell_signals = self.check_positions()
        
        if not sell_signals:
            logger.info("没有触发卖出条件的持仓")
            return 0
        
        if auto_execute:
            count = self._write_signals_to_db(sell_signals)
            logger.info(f"已生成 {count} 个卖出信号到数据库")
            return count
        else:
            logger.info(f"检测到 {len(sell_signals)} 个卖出信号（未自动执行）")
            for sig in sell_signals:
                logger.info(f"  {sig['symbol']}: {', '.join(sig['reasons'])} (盈亏: {sig['pnl_pct']:.2f}%)")
            return len(sell_signals)
    
    def _write_signals_to_db(self, sell_signals: List[Dict]) -> int:
        """将卖出信号写入数据库"""
        count = 0
        today = date.today()
        
        with self.db.get_session() as session:
            for sig in sell_signals:
                # 检查是否已有今日该股票的卖出信号
                existing = session.query(TradingSignal).filter(
                    TradingSignal.symbol == sig['symbol'],
                    TradingSignal.signal_date == today,
                    TradingSignal.signal_type == 'SELL',
                    TradingSignal.is_executed == False
                ).first()
                
                if existing:
                    logger.debug(f"{sig['symbol']}: 今日已有卖出信号，跳过")
                    continue
                
                # 创建新信号
                signal = TradingSignal(
                    symbol=sig['symbol'],
                    signal_date=today,
                    signal_type='SELL',
                    signal_strength=1.0,  # 自动卖出信号强度为1.0
                    signal_price=sig['current_price'],
                    source='auto_sell_monitor',
                    reason=', '.join(sig['reasons'])
                )
                session.add(signal)
                count += 1
            
            session.commit()
        
        return count
    
    def _get_latest_price(self, session, symbol: str) -> float:
        """获取最新价格"""
        row = session.query(DailyData).filter(
            DailyData.symbol == symbol
        ).order_by(DailyData.trade_date.desc()).first()
        
        return row.close if row else None
    
    def _get_latest_indicators(self, session, symbol: str) -> Dict:
        """获取最新技术指标"""
        # 获取最近两天的指标（用于判断MACD死叉等）
        rows = session.query(TechnicalIndicator).filter(
            TechnicalIndicator.symbol == symbol
        ).order_by(TechnicalIndicator.trade_date.desc()).limit(2).all()
        
        if not rows:
            return {}
        
        latest = rows[0]
        prev = rows[1] if len(rows) > 1 else None
        
        indicators = {
            'rsi': latest.rsi,
            'macd': latest.macd,
            'macd_signal': latest.macd_signal,
            'kdj_k': latest.kdj_k,
            'kdj_d': latest.kdj_d,
        }
        
        if prev:
            indicators['prev_macd'] = prev.macd
            indicators['prev_signal'] = prev.macd_signal
        
        return indicators


def run_auto_sell_check(db_manager, strategy_config: Dict, auto_execute: bool = False):
    """
    运行自动卖出检查
    
    Args:
        db_manager: 数据库管理器
        strategy_config: 策略配置
        auto_execute: 是否自动执行
    
    Returns:
        生成的信号数量
    """
    monitor = AutoSellMonitor(db_manager, strategy_config)
    return monitor.generate_sell_signals(auto_execute)


if __name__ == '__main__':
    # 测试用例
    import sys
    from pathlib import Path
    
    base = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(base))
    
    from utils.config_loader import init_config
    from database import init_database
    
    # 初始化
    cfg = init_config(config_dir=str(base / 'config'))
    db = init_database(cfg.config)
    
    # 策略配置示例
    strategy_config = {
        'stop_loss': {
            'enabled': True,
            'stop_loss_pct': -0.05  # 止损 -5%
        },
        'take_profit': {
            'enabled': True,
            'take_profit_pct': 0.10  # 止盈 +10%
        },
        'fixed_hold': {
            'enabled': False,
            'hold_days': 7
        },
        'trailing_stop': {
            'enabled': False,
            'trailing_stop_pct': 0.05
        },
        'technical': {
            'enabled': False,
            'rsi_overbought': 70
        }
    }
    
    # 运行检查
    print("=" * 80)
    print("自动卖出监控器测试")
    print("=" * 80)
    
    count = run_auto_sell_check(db, strategy_config, auto_execute=False)
    print(f"\n检测到 {count} 个卖出信号")

