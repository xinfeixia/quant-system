"""
自动交易执行器
"""
import time
from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy import and_

from database.db_manager import DatabaseManager
from database.models import TradingSignal, Position, Order
from trading.trading_engine import LocalPaperEngine
from trading.longport_engine import LongPortPaperEngine
from utils.logger import logger


class AutoTrader:
    """自动交易执行器"""
    
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager):
        """
        初始化自动交易执行器
        
        Args:
            config: 配置字典
            db_manager: 数据库管理器
        """
        self.config = config
        self.db = db_manager
        
        # 自动交易配置
        auto_config = config.get('auto_trading', {})
        self.enabled = auto_config.get('enabled', False)
        self.execution_interval = auto_config.get('execution_interval', 30)
        
        # 初始化交易引擎
        engine_type = auto_config.get('engine_type', 'local_paper')
        if engine_type == 'longport':
            # 需要LongPort客户端
            from data_collection.longport_client import get_longport_client
            lp_client = get_longport_client()
            self.engine = LongPortPaperEngine(lp_client, db_manager, config)
            logger.info("使用LongPort模拟交易引擎")
        else:
            self.engine = LocalPaperEngine(config, db_manager)
            logger.info("使用本地模拟交易引擎")
        
        logger.info("自动交易执行器初始化完成")
    
    def get_pending_signals(self) -> List[TradingSignal]:
        """
        获取待执行的交易信号
        
        Returns:
            待执行信号列表
        """
        today = date.today()
        
        with self.db.get_session() as session:
            # 查询今日未执行的信号
            signals = session.query(TradingSignal).filter(
                and_(
                    TradingSignal.signal_date == today,
                    TradingSignal.is_executed == False
                )
            ).all()
            
            # 提取数据到字典，避免detached instance错误
            result = []
            for sig in signals:
                result.append(TradingSignal(
                    id=sig.id,
                    symbol=sig.symbol,
                    signal_date=sig.signal_date,
                    signal_type=sig.signal_type,
                    signal_strength=sig.signal_strength,
                    signal_price=sig.signal_price,
                    source=sig.source,
                    reason=sig.reason,
                    is_executed=sig.is_executed
                ))
            
            return result
    
    def execute_signal(self, signal: TradingSignal) -> bool:
        """
        执行交易信号
        
        Args:
            signal: 交易信号
            
        Returns:
            是否执行成功
        """
        try:
            if signal.signal_type == 'BUY':
                return self._execute_buy(signal)
            elif signal.signal_type == 'SELL':
                return self._execute_sell(signal)
            else:
                logger.warning(f"未知信号类型: {signal.signal_type}")
                return False
                
        except Exception as e:
            logger.error(f"执行信号失败 {signal.symbol}: {e}")
            return False
    
    def _execute_buy(self, signal: TradingSignal) -> bool:
        """
        执行买入信号
        
        Args:
            signal: 买入信号
            
        Returns:
            是否执行成功
        """
        try:
            # 检查是否已持有
            with self.db.get_session() as session:
                pos = session.query(Position).filter_by(symbol=signal.symbol).first()
                if pos and pos.quantity > 0:
                    logger.info(f"已持有 {signal.symbol}，跳过买入")
                    return False
            
            # 执行买入
            logger.info(f"执行买入: {signal.symbol} @ {signal.signal_price:.2f}")
            result = self.engine.place_order(
                symbol=signal.symbol,
                side='BUY',
                order_type='LIMIT',
                price=float(signal.signal_price),
                quantity=999999,  # 大数量，引擎会根据风控计算实际数量
                strategy_tag=signal.source or 'auto_trader'
            )
            
            logger.info(f"✅ 买入成功: {signal.symbol} | {result}")
            
            # 标记信号已执行
            self._mark_signal_executed(signal.id)
            
            return True
            
        except Exception as e:
            logger.error(f"买入失败 {signal.symbol}: {e}")
            return False
    
    def _execute_sell(self, signal: TradingSignal) -> bool:
        """
        执行卖出信号
        
        Args:
            signal: 卖出信号
            
        Returns:
            是否执行成功
        """
        try:
            # 查询持仓
            with self.db.get_session() as session:
                pos = session.query(Position).filter_by(symbol=signal.symbol).first()
                if not pos or pos.quantity <= 0:
                    logger.info(f"无持仓 {signal.symbol}，跳过卖出")
                    return False
                
                quantity = pos.quantity
            
            # 执行卖出
            logger.info(f"执行卖出: {signal.symbol} @ {signal.signal_price:.2f} x {quantity}")
            result = self.engine.place_order(
                symbol=signal.symbol,
                side='SELL',
                order_type='LIMIT',
                price=float(signal.signal_price),
                quantity=quantity,
                strategy_tag=signal.source or 'auto_trader'
            )
            
            logger.info(f"✅ 卖出成功: {signal.symbol} | {result}")
            
            # 标记信号已执行
            self._mark_signal_executed(signal.id)
            
            return True
            
        except Exception as e:
            logger.error(f"卖出失败 {signal.symbol}: {e}")
            return False
    
    def _mark_signal_executed(self, signal_id: int):
        """
        标记信号已执行
        
        Args:
            signal_id: 信号ID
        """
        try:
            with self.db.get_session() as session:
                signal = session.query(TradingSignal).filter_by(id=signal_id).first()
                if signal:
                    signal.is_executed = True
                    signal.executed_at = datetime.now()
                    session.commit()
        except Exception as e:
            logger.error(f"标记信号执行状态失败: {e}")
    
    def execute_once(self):
        """执行一次交易"""
        # 获取待执行信号
        signals = self.get_pending_signals()
        
        if not signals:
            logger.debug("没有待执行的交易信号")
            return
        
        logger.info(f"发现 {len(signals)} 个待执行信号")
        
        # 执行信号
        success_count = 0
        for signal in signals:
            logger.info(f"处理信号: {signal.symbol} {signal.signal_type} | 来源: {signal.source} | 原因: {signal.reason}")
            
            if self.execute_signal(signal):
                success_count += 1
            
            # 避免请求过快
            time.sleep(1)
        
        logger.info(f"执行完成: 成功 {success_count}/{len(signals)}")
    
    def start(self):
        """启动自动交易"""
        if not self.enabled:
            logger.warning("自动交易未启用")
            return
        
        logger.info("=" * 60)
        logger.info("启动自动交易执行器")
        logger.info("=" * 60)
        logger.info(f"执行间隔: {self.execution_interval}秒")
        logger.info("=" * 60)
        
        try:
            while True:
                logger.info(f"\n[{datetime.now().strftime('%H:%M:%S')}] 检查待执行信号...")
                self.execute_once()
                
                # 等待下一次执行
                logger.debug(f"等待 {self.execution_interval} 秒...")
                time.sleep(self.execution_interval)
                
        except KeyboardInterrupt:
            logger.info("\n自动交易已停止")
        except Exception as e:
            logger.error(f"自动交易出错: {e}")
            raise
    
    def stop(self):
        """停止自动交易"""
        logger.info("停止自动交易执行器")

