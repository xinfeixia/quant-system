"""
Minute-level scheduler for HK Paper Trading.
- Runs every minute during HK market hours (approx local time 09:30-12:00, 13:00-16:00)
- Currently records portfolio snapshots each tick (foundation for strategy execution)
"""
from __future__ import annotations
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

from loguru import logger

# Lazy imports inside methods to avoid circular imports


class MinuteScheduler:
    def __init__(self):
        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.interval_sec = 60
        self.last_run_at: Optional[datetime] = None
        self.next_run_at: Optional[datetime] = None

    def start(self, interval_sec: int = 60):
        if self._running.is_set():
            return False
        self.interval_sec = max(5, int(interval_sec))
        self._running.set()
        self.next_run_at = self._ceil_to_next_minute(datetime.now())
        self._thread = threading.Thread(target=self._loop, name="HK-MinuteScheduler", daemon=True)
        self._thread.start()
        logger.info(f"Scheduler started: interval={self.interval_sec}s, next_run_at={self.next_run_at}")
        return True

    def stop(self):
        if not self._running.is_set():
            return False
        self._running.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")
        return True

    def status(self):
        return {
            "running": self._running.is_set(),
            "interval_sec": self.interval_sec,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
        }

    def _loop(self):
        while self._running.is_set():
            now = datetime.now()
            if not self.next_run_at:
                self.next_run_at = self._ceil_to_next_minute(now)

            if now >= self.next_run_at:
                if self._is_hk_market_open(now):
                    try:
                        self._run_tick()
                    except Exception as e:
                        logger.error(f"Scheduler tick error: {e}")
                self.last_run_at = datetime.now()
                self.next_run_at = self._ceil_to_next_minute(self.last_run_at)
            # sleep small increments to allow quick stop
            time.sleep(0.5)

    def _is_hk_market_open(self, now: datetime) -> bool:
        # Approx local-time windows: 09:30-12:00 and 13:00-16:00, weekdays
        if now.weekday() >= 5:
            return False
        t = now.time()
        return ((t >= self._time(9, 30) and t < self._time(12, 0)) or
                (t >= self._time(13, 0) and t < self._time(16, 0)))

    @staticmethod
    def _time(h: int, m: int):
        from datetime import time as _time
        return _time(hour=h, minute=m)

    @staticmethod
    def _ceil_to_next_minute(dt: datetime) -> datetime:
        return (dt.replace(second=0, microsecond=0) + timedelta(minutes=1))

    def _run_tick(self):
        """One tick:
        - Record a portfolio snapshot
        - Execute strategy signals (TradingSignal) for HK market (BUY/SELL)
        """
        from database import get_db_manager
        from database.models import PortfolioSnapshot, Position, DailyData, TradingSignal
        from datetime import datetime as _d
        from trading.engine_factory import get_trading_engine

        def _latest_price(session, symbol: str):
            row = (
                session.query(DailyData)
                .filter(DailyData.symbol == symbol)
                .order_by(DailyData.trade_date.desc())
                .first()
            )
            return row.close if row else None

        db = get_db_manager()
        engine = get_trading_engine()

        with db.get_session() as session:
            # 1) snapshot
            last = (
                session.query(PortfolioSnapshot)
                .order_by(PortfolioSnapshot.snapshot_time.desc())
                .first()
            )
            cash = last.cash if last else 1_000_000.0
            equity = 0.0
            for p in session.query(Position).all():
                lp = _latest_price(session, p.symbol)
                price = (lp if lp is not None else p.avg_price) or 0.0
                equity += (p.quantity or 0) * price
            total = cash + equity
            session.add(PortfolioSnapshot(cash=cash, equity=equity, total_value=total, note="minute-scheduler"))
            session.commit()

            # 2) execute today's unexecuted signals (HK only)
            today = _d.now().date()
            signals = (
                session.query(TradingSignal)
                .filter(TradingSignal.signal_date == today, TradingSignal.is_executed == False)
                .all()
            )

            # 提前提取所有信号数据，避免 session detached 问题
            signal_data_list = []
            for sig in signals:
                signal_data_list.append({
                    'id': sig.id,
                    'symbol': (sig.symbol or '').upper(),
                    'signal_type': (sig.signal_type or '').upper(),
                    'signal_price': sig.signal_price,
                    'source': sig.source
                })

            for sig_data in signal_data_list:
                sig_id = sig_data['id']
                symbol = sig_data['symbol']
                signal_type = sig_data['signal_type']
                signal_price = sig_data['signal_price']
                signal_source = sig_data['source']

                if not symbol.endswith('.HK'):
                    continue

                mkt_price = _latest_price(session, symbol)
                if not mkt_price:
                    continue

                # 使用交易引擎执行信号
                try:
                    if signal_type == 'BUY':
                        # 使用信号价格或市场价格
                        price = signal_price if signal_price else mkt_price
                        # 数量由引擎根据风控计算
                        result = engine.place_order(
                            symbol=symbol,
                            side='BUY',
                            order_type='LIMIT',
                            price=float(price),
                            quantity=999999,  # 大数量，引擎会根据风控限制
                            strategy_tag=signal_source or 'signal'
                        )
                        logger.info(f"调度器执行BUY信号: {symbol}, 结果: {result}")

                    elif signal_type == 'SELL':
                        # 查询持仓数量
                        pos = session.query(Position).filter_by(symbol=symbol).first()
                        if not pos or pos.quantity <= 0:
                            logger.warning(f"调度器跳过SELL信号（无持仓）: {symbol}")
                            continue

                        price = signal_price if signal_price else mkt_price
                        result = engine.place_order(
                            symbol=symbol,
                            side='SELL',
                            order_type='LIMIT',
                            price=float(price),
                            quantity=pos.quantity,  # 全量卖出
                            strategy_tag=signal_source or 'signal'
                        )
                        logger.info(f"调度器执行SELL信号: {symbol}, 结果: {result}")

                    # 标记信号已执行（重新查询以避免 detached 问题）
                    sig_to_update = session.query(TradingSignal).filter_by(id=sig_id).first()
                    if sig_to_update:
                        sig_to_update.is_executed = True
                        sig_to_update.executed_at = _d.now()
                        session.commit()

                except Exception as e:
                    logger.error(f"调度器执行信号失败: {symbol} {signal_type}, 错误: {e}")
                    session.rollback()
                    continue
        logger.debug("Scheduler tick: snapshot + strategy execution done")


# Singleton access
_scheduler: Optional[MinuteScheduler] = None

def get_scheduler() -> MinuteScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = MinuteScheduler()
    return _scheduler

