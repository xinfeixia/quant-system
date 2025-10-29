"""
止盈监控器 - 监控持仓并在达到目标利润时自动生成卖出信号
"""
import time
from datetime import datetime, date
from typing import Dict, List, Any
from sqlalchemy import and_

from database.db_manager import DatabaseManager
from database.models import Position, TradingSignal, DailyData
from trading.auto_sell_strategy import TakeProfitStrategy, StopLossStrategy, TrailingStopStrategy, CompositeStrategy
from utils.logger import logger


class ProfitMonitor:
    """止盈监控器"""
    
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager):
        """
        初始化止盈监控器
        
        Args:
            config: 配置字典
            db_manager: 数据库管理器
        """
        self.config = config
        self.db = db_manager
        
        # 自动交易配置
        auto_config = config.get('auto_trading', {})
        self.enabled = auto_config.get('enabled', False)
        self.check_interval = auto_config.get('execution_interval', 30)
        
        # 初始化卖出策略
        strategy_config = {
            'take_profit': auto_config.get('take_profit', {}),
            'stop_loss': auto_config.get('stop_loss', {}),
            'trailing_stop': auto_config.get('trailing_stop', {})
        }
        self.strategy = CompositeStrategy(strategy_config)
        
        logger.info("止盈监控器初始化完成")
    
    def get_positions(self) -> List[Position]:
        """
        获取所有持仓
        
        Returns:
            持仓列表
        """
        with self.db.get_session() as session:
            positions = session.query(Position).filter(Position.quantity > 0).all()
            
            # 提取数据到新对象，避免detached instance错误
            result = []
            for pos in positions:
                result.append(Position(
                    id=pos.id,
                    symbol=pos.symbol,
                    market=pos.market,
                    quantity=pos.quantity,
                    avg_price=pos.avg_price,
                    updated_at=pos.updated_at
                ))
            
            return result
    
    def get_latest_price(self, symbol: str) -> float:
        """
        获取最新价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            最新价格，如果没有则返回None
        """
        with self.db.get_session() as session:
            latest = session.query(DailyData).filter(
                DailyData.symbol == symbol
            ).order_by(DailyData.trade_date.desc()).first()
            
            if latest:
                return latest.close
            return None
    
    def check_position(self, position: Position) -> tuple:
        """
        检查单个持仓是否需要卖出
        
        Args:
            position: 持仓信息
            
        Returns:
            (是否卖出, 原因列表)
        """
        # 获取当前价格
        current_price = self.get_latest_price(position.symbol)
        if not current_price:
            logger.warning(f"{position.symbol}: 无法获取最新价格")
            return False, []
        
        # 构造持仓信息
        position_info = {
            'symbol': position.symbol,
            'quantity': position.quantity,
            'avg_price': position.avg_price,
            'entry_date': position.updated_at.date() if position.updated_at else date.today()
        }
        
        # 判断是否应该卖出
        should_sell, reasons = self.strategy.should_sell(position_info, current_price)
        
        return should_sell, reasons, current_price
    
    def create_sell_signal(self, position: Position, price: float, reasons: List[str]) -> bool:
        """
        创建卖出信号
        
        Args:
            position: 持仓信息
            price: 卖出价格
            reasons: 卖出原因
            
        Returns:
            是否创建成功
        """
        today = date.today()
        
        try:
            with self.db.get_session() as session:
                # 检查是否已有今日卖出信号
                existing = session.query(TradingSignal).filter(
                    and_(
                        TradingSignal.symbol == position.symbol,
                        TradingSignal.signal_date == today,
                        TradingSignal.signal_type == 'SELL',
                        TradingSignal.is_executed == False
                    )
                ).first()
                
                if existing:
                    logger.debug(f"今日已有卖出信号，跳过: {position.symbol}")
                    return False
                
                # 计算盈亏
                pnl_pct = (price - position.avg_price) / position.avg_price * 100
                
                # 创建卖出信号
                signal = TradingSignal(
                    symbol=position.symbol,
                    signal_date=today,
                    signal_type='SELL',
                    signal_strength=1.0,
                    signal_price=price,
                    source='profit_monitor',
                    reason=f'{", ".join(reasons)} (盈亏: {pnl_pct:+.2f}%)',
                    is_executed=False
                )
                session.add(signal)
                session.commit()
                
                logger.info(
                    f"✅ 创建卖出信号: {position.symbol} | "
                    f"价格: {price:.2f} | 盈亏: {pnl_pct:+.2f}% | "
                    f"原因: {', '.join(reasons)}"
                )
                
                return True
                
        except Exception as e:
            logger.error(f"创建卖出信号失败 {position.symbol}: {e}")
            return False
    
    def check_once(self):
        """执行一次检查"""
        # 获取所有持仓
        positions = self.get_positions()
        
        if not positions:
            logger.debug("没有持仓")
            return
        
        logger.info(f"检查 {len(positions)} 个持仓...")
        
        # 检查每个持仓
        signal_count = 0
        for position in positions:
            should_sell, reasons, current_price = self.check_position(position)
            
            if should_sell:
                logger.info(f"🔔 {position.symbol} 触发卖出: {', '.join(reasons)}")
                
                # 创建卖出信号
                if self.create_sell_signal(position, current_price, reasons):
                    signal_count += 1
        
        if signal_count > 0:
            logger.info(f"✅ 已生成 {signal_count} 个卖出信号")
        else:
            logger.info("未触发卖出条件")
    
    def start(self):
        """启动止盈监控"""
        if not self.enabled:
            logger.warning("自动交易未启用")
            return
        
        logger.info("=" * 60)
        logger.info("启动止盈监控器")
        logger.info("=" * 60)
        logger.info(f"检查间隔: {self.check_interval}秒")
        logger.info("=" * 60)
        
        # 打印策略配置
        auto_config = self.config.get('auto_trading', {})
        take_profit = auto_config.get('take_profit', {})
        stop_loss = auto_config.get('stop_loss', {})
        trailing_stop = auto_config.get('trailing_stop', {})
        
        if take_profit.get('enabled'):
            logger.info(f"止盈策略: {take_profit.get('target_profit_pct', 0.10)*100:.1f}%")
        if stop_loss.get('enabled'):
            logger.info(f"止损策略: {stop_loss.get('stop_loss_pct', -0.05)*100:.1f}%")
        if trailing_stop.get('enabled'):
            logger.info(f"移动止损: {trailing_stop.get('trailing_stop_pct', 0.03)*100:.1f}%")
        
        logger.info("=" * 60)
        
        try:
            while True:
                logger.info(f"\n[{datetime.now().strftime('%H:%M:%S')}] 检查持仓...")
                self.check_once()
                
                # 等待下一次检查
                logger.debug(f"等待 {self.check_interval} 秒...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n止盈监控已停止")
        except Exception as e:
            logger.error(f"止盈监控出错: {e}")
            raise
    
    def stop(self):
        """停止止盈监控"""
        logger.info("停止止盈监控器")

