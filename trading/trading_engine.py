"""
交易引擎抽象层
支持本地Paper Trading和LongPort模拟/实盘交易
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, List
from loguru import logger


class TradingEngine(ABC):
    """交易引擎抽象基类"""
    
    @abstractmethod
    def place_order(self, symbol: str, side: str, order_type: str, 
                   price: float, quantity: int, **kwargs) -> Dict:
        """
        下单
        
        Args:
            symbol: 股票代码
            side: BUY/SELL
            order_type: LIMIT/MARKET
            price: 价格
            quantity: 数量
            **kwargs: 其他参数
            
        Returns:
            订单信息字典
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict:
        """获取订单状态"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """获取持仓"""
        pass
    
    @abstractmethod
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        pass


class LocalPaperEngine(TradingEngine):
    """本地Paper Trading引擎（即刻撮合）"""
    
    def __init__(self, db_manager, config: Dict):
        self.db = db_manager
        self.config = config
        self.risk_config = config.get('trading', {}).get('risk', {})
        self.initial_cash = self.risk_config.get('initial_cash', 1000000.0)
        self.max_per_position = self.risk_config.get('max_per_position', 0.05)
        self.max_gross = self.risk_config.get('max_gross', 0.80)
        self.slippage = self.risk_config.get('default_slippage', 0.003)
        logger.info("本地Paper Trading引擎初始化完成")
    
    def _get_latest_price(self, session, symbol: str) -> Optional[float]:
        """获取最新价格"""
        from database.models import DailyData
        row = (
            session.query(DailyData)
            .filter(DailyData.symbol == symbol)
            .order_by(DailyData.trade_date.desc())
            .first()
        )
        return float(row.close) if row else None
    
    def _get_portfolio_state(self, session):
        """获取组合状态"""
        from database.models import Position, PortfolioSnapshot
        
        snapshot = (
            session.query(PortfolioSnapshot)
            .order_by(PortfolioSnapshot.snapshot_time.desc())
            .first()
        )
        cash = snapshot.cash if snapshot else self.initial_cash
        
        positions = session.query(Position).all()
        equity = 0.0
        for p in positions:
            last_price = self._get_latest_price(session, p.symbol) or p.avg_price or 0.0
            equity += (p.quantity or 0) * last_price
        
        total_value = cash + equity
        return cash, equity, total_value
    
    def place_order(self, symbol: str, side: str, order_type: str,
                   price: float, quantity: int, **kwargs) -> Dict:
        """本地Paper下单（即刻撮合）"""
        from database.models import Order, Execution, Position, PortfolioSnapshot

        logger.info(f"⚡⚡⚡ LocalPaperEngine.place_order 被调用: {symbol} {side} {quantity}")

        strategy_tag = kwargs.get('strategy_tag')
        
        with self.db.get_session() as session:
            # 获取组合状态
            cash, equity, total_value = self._get_portfolio_state(session)
            if total_value <= 0:
                total_value = self.initial_cash
            
            per_pos_cap = total_value * self.max_per_position
            gross_cap = total_value * self.max_gross
            
            mkt_price = self._get_latest_price(session, symbol)
            if mkt_price is None:
                raise ValueError(f'无最新价格：{symbol}')
            
            if side == 'BUY':
                # 计算有效价格（考虑滑点）
                eff_price = min(float(price), mkt_price * (1.0 + self.slippage))
                
                # 风控：单票上限
                max_qty_perpos = int(per_pos_cap // eff_price)
                
                # 风控：总仓上限
                max_equity_after = equity + quantity * eff_price
                if max_equity_after > gross_cap:
                    allow_equity_add = max(0.0, gross_cap - equity)
                    max_qty_gross = int(allow_equity_add // eff_price)
                else:
                    max_qty_gross = quantity
                
                max_qty = max(0, min(quantity, max_qty_perpos, max_qty_gross))
                if max_qty <= 0:
                    raise ValueError('风控限制：单票或总仓上限')
                
                cost = max_qty * eff_price
                if cash < cost:
                    raise ValueError('可用现金不足')
                
                # 创建订单并即刻撮合
                order = Order(
                    symbol=symbol, market='HK', side=side, order_type='LIMIT',
                    price=price, quantity=quantity, status='FILLED',
                    filled_quantity=max_qty, avg_fill_price=eff_price,
                    strategy_tag=strategy_tag
                )
                session.add(order)
                session.flush()
                
                # 创建成交记录
                execution = Execution(
                    order_id=order.id, symbol=symbol, side=side,
                    price=eff_price, quantity=max_qty
                )
                session.add(execution)
                
                # 更新持仓
                pos = session.query(Position).filter_by(symbol=symbol).first()
                if pos:
                    total_cost = pos.avg_price * pos.quantity + eff_price * max_qty
                    pos.quantity += max_qty
                    pos.avg_price = total_cost / pos.quantity if pos.quantity > 0 else eff_price
                else:
                    pos = Position(symbol=symbol, market='HK', quantity=max_qty, avg_price=eff_price)
                    session.add(pos)
                
                # 更新快照
                new_cash = cash - cost
                new_equity = equity + cost
                snap = PortfolioSnapshot(
                    snapshot_time=datetime.now(),
                    cash=new_cash,
                    equity=new_equity,
                    total_value=new_cash + new_equity
                )
                session.add(snap)
                session.commit()
                
                logger.info(f"本地Paper BUY: {symbol} {max_qty}股 @ {eff_price:.2f}")
                return {
                    'order_id': str(order.id),
                    'symbol': symbol,
                    'side': side,
                    'status': 'FILLED',
                    'filled_quantity': max_qty,
                    'avg_fill_price': eff_price
                }
            
            elif side == 'SELL':
                # 查询持仓
                pos = session.query(Position).filter_by(symbol=symbol).first()
                if not pos or pos.quantity <= 0:
                    raise ValueError(f'无持仓：{symbol}')
                
                sell_qty = min(quantity, pos.quantity)
                eff_price = max(float(price), mkt_price * (1.0 - self.slippage))
                
                # 创建订单
                order = Order(
                    symbol=symbol, market='HK', side=side, order_type='LIMIT',
                    price=price, quantity=quantity, status='FILLED',
                    filled_quantity=sell_qty, avg_fill_price=eff_price,
                    strategy_tag=strategy_tag
                )
                session.add(order)
                session.flush()
                
                # 成交记录
                execution = Execution(
                    order_id=order.id, symbol=symbol, side=side,
                    price=eff_price, quantity=sell_qty
                )
                session.add(execution)
                
                # 更新持仓
                pos.quantity -= sell_qty
                
                # 更新快照
                proceeds = sell_qty * eff_price
                new_cash = cash + proceeds
                new_equity = equity - proceeds
                snap = PortfolioSnapshot(
                    snapshot_time=datetime.now(),
                    cash=new_cash,
                    equity=new_equity,
                    total_value=new_cash + new_equity
                )
                session.add(snap)
                session.commit()
                
                logger.info(f"本地Paper SELL: {symbol} {sell_qty}股 @ {eff_price:.2f}")
                return {
                    'order_id': str(order.id),
                    'symbol': symbol,
                    'side': side,
                    'status': 'FILLED',
                    'filled_quantity': sell_qty,
                    'avg_fill_price': eff_price
                }
            
            else:
                raise ValueError(f'不支持的方向：{side}')
    
    def get_order_status(self, order_id: str) -> Dict:
        """获取订单状态"""
        from database.models import Order
        with self.db.get_session() as session:
            order = session.query(Order).filter_by(id=int(order_id)).first()
            if not order:
                raise ValueError(f'订单不存在：{order_id}')
            return {
                'order_id': str(order.id),
                'symbol': order.symbol,
                'side': order.side,
                'status': order.status,
                'filled_quantity': order.filled_quantity,
                'avg_fill_price': order.avg_fill_price
            }
    
    def cancel_order(self, order_id: str) -> bool:
        """撤单（本地Paper已即刻成交，无法撤单）"""
        logger.warning(f"本地Paper订单已即刻成交，无法撤单：{order_id}")
        return False
    
    def get_positions(self) -> List[Dict]:
        """获取持仓"""
        from database.models import Position
        with self.db.get_session() as session:
            positions = session.query(Position).filter(Position.quantity > 0).all()
            return [
                {
                    'symbol': p.symbol,
                    'quantity': p.quantity,
                    'avg_price': p.avg_price,
                    'market': p.market
                }
                for p in positions
            ]
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        with self.db.get_session() as session:
            cash, equity, total_value = self._get_portfolio_state(session)
            return {
                'cash': cash,
                'equity': equity,
                'total_value': total_value,
                'mode': 'local_paper'
            }

