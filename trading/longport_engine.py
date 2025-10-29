"""
LongPort 交易引擎（模拟账号/实盘）
"""
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
from longport.openapi import TradeContext, OrderSide, OrderType, TimeInForceType

from .trading_engine import TradingEngine


class LongPortPaperEngine(TradingEngine):
    """LongPort 模拟账号交易引擎"""
    
    def __init__(self, longport_client, db_manager, config: Dict):
        """
        初始化 LongPort Paper 引擎

        Args:
            longport_client: LongPortClient 实例
            db_manager: 数据库管理器
            config: 配置字典
        """
        self.client = longport_client
        self.db = db_manager
        self.config = config
        self.trade_ctx = None

        # 风控参数
        self.risk_config = config.get('trading', {}).get('risk', {})
        self.initial_cash = self.risk_config.get('initial_cash', 1000000.0)
        self.max_per_position = self.risk_config.get('max_per_position', 0.05)
        self.max_gross = self.risk_config.get('max_gross', 0.80)
        self.slippage = self.risk_config.get('default_slippage', 0.003)

        self._init_trade_context()
        logger.info("LongPort Paper Trading 引擎初始化完成")
    
    def _init_trade_context(self):
        """初始化交易上下文"""
        try:
            self.trade_ctx = self.client.get_trade_context()
            logger.info("LongPort TradeContext 创建成功")
        except Exception as e:
            logger.error(f"创建 TradeContext 失败: {e}")
            raise

    def _get_portfolio_state(self, session):
        """获取组合状态（现金、持仓市值、总资产）"""
        from database.models import PortfolioSnapshot
        snap = session.query(PortfolioSnapshot).order_by(PortfolioSnapshot.snapshot_time.desc()).first()
        if snap:
            return snap.cash, snap.equity or 0.0, snap.total_value or snap.cash
        return self.initial_cash, 0.0, self.initial_cash

    def _get_latest_price(self, session, symbol: str):
        """获取最新价格"""
        from database.models import DailyData
        row = session.query(DailyData).filter(DailyData.symbol == symbol).order_by(DailyData.trade_date.desc()).first()
        return row.close if row else None

    def _get_lot_size(self, symbol: str) -> int:
        """
        获取股票的每手股数

        港股不同股票的每手股数不同，需要查询
        常见的：
        - 腾讯(0700.HK): 100股/手
        - 中国移动(0941.HK): 500股/手
        - 建设银行(0939.HK): 1000股/手
        """
        try:
            # 从 LongPort API 获取静态信息
            static_info = self.client.get_quote_context().static_info([symbol])
            if static_info and len(static_info) > 0:
                info = static_info[0]
                lot_size = info.lot_size
                if lot_size and lot_size > 0:
                    logger.debug(f"{symbol} 每手股数: {lot_size}")
                    return lot_size
        except Exception as e:
            logger.warning(f"获取 {symbol} 手数失败: {e}，使用默认值100")

        # 默认返回100（最常见）
        return 100
    
    def place_order(self, symbol: str, side: str, order_type: str,
                   price: float, quantity: int, **kwargs) -> Dict:
        """
        通过 LongPort API 下单到模拟账号

        Args:
            symbol: 股票代码（如 0700.HK）
            side: BUY/SELL
            order_type: LIMIT/MARKET
            price: 价格
            quantity: 数量（如果是大数量如999999，会根据风控计算实际数量）
            **kwargs: 其他参数

        Returns:
            订单信息字典
        """
        from database.models import Order, Position

        logger.info(f"🔥🔥🔥 LongPortPaperEngine.place_order 被调用: {symbol} {side} {quantity}")

        try:
            with self.db.get_session() as session:
                # 获取每手股数
                lot_size = self._get_lot_size(symbol)

                # 如果是BUY且数量很大（如999999），进行风控计算
                if side == 'BUY' and quantity > 10000:
                    # 获取组合状态
                    cash, equity, total_value = self._get_portfolio_state(session)
                    if total_value <= 0:
                        total_value = self.initial_cash

                    # 获取市场价格
                    mkt_price = self._get_latest_price(session, symbol)
                    if not mkt_price:
                        raise ValueError(f'无最新价格：{symbol}')

                    # 使用信号价格或市场价格
                    eff_price = min(float(price), mkt_price * (1.0 + self.slippage))

                    # 风控：单票上限（总资产的5%）
                    per_pos_cap = total_value * self.max_per_position
                    max_qty_perpos = int(per_pos_cap // eff_price)

                    # 风控：总仓上限（总资产的80%）
                    gross_cap = total_value * self.max_gross
                    allow_equity_add = max(0.0, gross_cap - equity)
                    max_qty_gross = int(allow_equity_add // eff_price)

                    # 风控：现金限制
                    max_qty_cash = int(cash // eff_price)

                    # 取最小值
                    max_qty = max(0, min(max_qty_perpos, max_qty_gross, max_qty_cash))

                    # 转换为手数（向下取整）
                    max_lots = max_qty // lot_size
                    actual_quantity = max_lots * lot_size

                    if actual_quantity <= 0:
                        raise ValueError(f'风控限制：无法买入 {symbol}（单票上限/总仓上限/现金不足）')

                    logger.info(f"风控计算: {symbol} 原始数量={quantity}, 实际数量={actual_quantity} ({max_lots}手 × {lot_size}股/手)")
                    quantity = actual_quantity

                elif side == 'SELL':
                    # 卖出时，确保数量是手数的整数倍
                    lots = quantity // lot_size
                    quantity = lots * lot_size

                    if quantity <= 0:
                        raise ValueError(f'卖出数量不足一手：{symbol}')

                # 转换参数
                lp_side = OrderSide.Buy if side == 'BUY' else OrderSide.Sell
                lp_type = OrderType.LO if order_type == 'LIMIT' else OrderType.MO

                # 提交订单到 LongPort
                resp = self.trade_ctx.submit_order(
                    symbol=symbol,
                    order_type=lp_type,
                    side=lp_side,
                    submitted_quantity=quantity,
                    submitted_price=price if order_type == 'LIMIT' else None,
                    time_in_force=TimeInForceType.Day,
                    remark=kwargs.get('strategy_tag', '')
                )

                # 保存订单到本地数据库
                order = Order(
                    symbol=symbol,
                    market='HK',
                    side=side,
                    order_type=order_type,
                    price=price,
                    quantity=quantity,
                    status='NEW',  # 初始状态为 NEW
                    external_order_id=resp.order_id,  # LongPort 订单ID
                    strategy_tag=kwargs.get('strategy_tag')
                )
                session.add(order)
                session.commit()

                logger.info(f"LongPort Paper 下单成功: {symbol} {side} {quantity}股 @ {price}, 订单ID: {resp.order_id}")

                return {
                    'order_id': str(order.id),
                    'external_order_id': resp.order_id,
                    'symbol': symbol,
                    'side': side,
                    'status': 'NEW',
                    'submitted_quantity': quantity,
                    'submitted_price': price
                }
        
        except Exception as e:
            logger.error(f"LongPort 下单失败: {e}")
            raise
    
    def get_order_status(self, order_id: str) -> Dict:
        """
        获取订单状态（从 LongPort 同步）
        
        Args:
            order_id: 本地订单ID
            
        Returns:
            订单状态字典
        """
        from database.models import Order
        
        try:
            with self.db.get_session() as session:
                order = session.query(Order).filter_by(id=int(order_id)).first()
                if not order or not order.external_order_id:
                    raise ValueError(f'订单不存在或无外部订单ID：{order_id}')
                
                # 从 LongPort 查询订单详情
                lp_order = self.trade_ctx.order_detail(order.external_order_id)
                
                # 更新本地订单状态
                order.status = self._convert_order_status(lp_order.status)
                order.filled_quantity = lp_order.executed_quantity or 0
                order.avg_fill_price = lp_order.executed_price or 0.0
                session.commit()
                
                return {
                    'order_id': str(order.id),
                    'external_order_id': order.external_order_id,
                    'symbol': order.symbol,
                    'side': order.side,
                    'status': order.status,
                    'filled_quantity': order.filled_quantity,
                    'avg_fill_price': order.avg_fill_price
                }
        
        except Exception as e:
            logger.error(f"获取订单状态失败: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> bool:
        """
        撤单
        
        Args:
            order_id: 本地订单ID
            
        Returns:
            是否成功
        """
        from database.models import Order
        
        try:
            with self.db.get_session() as session:
                order = session.query(Order).filter_by(id=int(order_id)).first()
                if not order or not order.external_order_id:
                    raise ValueError(f'订单不存在或无外部订单ID：{order_id}')
                
                # 调用 LongPort 撤单
                self.trade_ctx.cancel_order(order.external_order_id)
                
                # 更新本地状态
                order.status = 'CANCELLED'
                session.commit()
                
                logger.info(f"撤单成功: {order_id} (LongPort: {order.external_order_id})")
                return True
        
        except Exception as e:
            logger.error(f"撤单失败: {e}")
            return False
    
    def get_positions(self) -> List[Dict]:
        """
        获取持仓（从 LongPort 同步）
        
        Returns:
            持仓列表
        """
        try:
            # 从 LongPort 获取持仓
            positions = self.trade_ctx.stock_positions()
            
            result = []
            for pos in positions:
                result.append({
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'avg_price': pos.cost_price,
                    'market': 'HK',  # 根据 symbol 判断市场
                    'market_value': pos.market_value,
                    'unrealized_pnl': getattr(pos, 'unrealized_pnl', 0.0)
                })
            
            # 同步到本地数据库
            self._sync_positions_to_db(result)
            
            return result
        
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            raise
    
    def get_account_info(self) -> Dict:
        """
        获取账户信息（从 LongPort 同步）
        
        Returns:
            账户信息字典
        """
        try:
            # 获取账户余额
            balances = self.trade_ctx.account_balance()
            
            # 通常返回多个币种，这里取第一个（或根据需要筛选）
            if balances and len(balances) > 0:
                balance = balances[0]
                cash = balance.cash
                total_value = balance.net_assets
                equity = total_value - cash
            else:
                cash = 0.0
                equity = 0.0
                total_value = 0.0
            
            return {
                'cash': cash,
                'equity': equity,
                'total_value': total_value,
                'mode': 'longport_paper'
            }
        
        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            raise
    
    def sync_orders(self):
        """同步所有未完成订单的状态"""
        from database.models import Order
        
        try:
            with self.db.get_session() as session:
                # 查询所有未完成的订单
                pending_orders = session.query(Order).filter(
                    Order.status.in_(['NEW', 'PARTIAL_FILLED'])
                ).all()
                
                for order in pending_orders:
                    if not order.external_order_id:
                        continue
                    
                    try:
                        # 从 LongPort 查询订单详情
                        lp_order = self.trade_ctx.order_detail(order.external_order_id)
                        
                        # 更新本地订单状态
                        order.status = self._convert_order_status(lp_order.status)
                        order.filled_quantity = lp_order.executed_quantity or 0
                        order.avg_fill_price = lp_order.executed_price or 0.0
                    
                    except Exception as e:
                        logger.warning(f"同步订单 {order.id} 失败: {e}")
                
                session.commit()
                logger.info(f"订单同步完成，共 {len(pending_orders)} 条")
        
        except Exception as e:
            logger.error(f"订单同步失败: {e}")
    
    def _sync_positions_to_db(self, positions: List[Dict]):
        """将持仓同步到本地数据库"""
        from database.models import Position
        
        try:
            with self.db.get_session() as session:
                # 清空现有持仓（或更新）
                for pos_data in positions:
                    pos = session.query(Position).filter_by(symbol=pos_data['symbol']).first()
                    if pos:
                        pos.quantity = pos_data['quantity']
                        pos.avg_price = pos_data['avg_price']
                        pos.updated_at = datetime.now()
                    else:
                        pos = Position(
                            symbol=pos_data['symbol'],
                            market=pos_data['market'],
                            quantity=pos_data['quantity'],
                            avg_price=pos_data['avg_price']
                        )
                        session.add(pos)
                
                session.commit()
                logger.debug(f"持仓同步到数据库完成，共 {len(positions)} 条")
        
        except Exception as e:
            logger.error(f"持仓同步到数据库失败: {e}")
    
    def _convert_order_status(self, lp_status) -> str:
        """转换 LongPort 订单状态到本地状态"""
        # 根据 LongPort SDK 的状态枚举进行映射
        status_map = {
            'NotReported': 'NEW',
            'ReplacedNotReported': 'NEW',
            'ProtectedNotReported': 'NEW',
            'VarietiesNotReported': 'NEW',
            'Filled': 'FILLED',
            'WaitToNew': 'NEW',
            'NewRejected': 'REJECTED',
            'Pending': 'NEW',
            'Rejected': 'REJECTED',
            'Active': 'NEW',
            'Inactive': 'CANCELLED',
            'PartiallyFilled': 'PARTIAL_FILLED',
            'Expired': 'EXPIRED',
            'PartialWithdrawal': 'PARTIAL_CANCELLED',
        }
        return status_map.get(str(lp_status), 'UNKNOWN')

