"""
Seed 1-2 HK symbols with minimal DailyData to enable Paper Trading tests.
"""
from datetime import date
from pathlib import Path
import sys

# Ensure package import works when run from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.config_loader import init_config
from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from loguru import logger


def upsert_stock(session, symbol: str, name: str):
    stock = session.query(StockInfo).filter_by(symbol=symbol).first()
    if not stock:
        stock = StockInfo(
            symbol=symbol,
            name=name,
            market='HK',
            exchange='HKEX',
            currency='HKD',
            lot_size=100,
            is_active=True,
        )
        session.add(stock)
        logger.info(f"Inserted StockInfo: {symbol} {name}")
    return stock


def upsert_daily(session, symbol: str, d: date, close: float):
    row = (
        session.query(DailyData)
        .filter_by(symbol=symbol, trade_date=d)
        .first()
    )
    if not row:
        row = DailyData(
            symbol=symbol,
            trade_date=d,
            open=close,
            high=close,
            low=close,
            close=close,
            volume=1_000_000,
            turnover=close * 1_000_000,
            change=0.0,
            change_pct=0.0,
            turnover_rate=0.0,
        )
        session.add(row)
        logger.info(f"Inserted DailyData: {symbol} {d} close={close}")
    else:
        row.close = close
        logger.info(f"Updated DailyData: {symbol} {d} close={close}")


def main():
    config_loader = init_config(config_dir=str(ROOT / 'config'))
    config = config_loader.config
    db = init_database(config)
    db.create_tables()

    today = date.today()
    items = [
        ("0700.HK", "Tencent", 300.0),
        ("0005.HK", "HSBC Holdings", 60.0),
    ]

    with db.get_session() as session:
        for sym, name, px in items:
            upsert_stock(session, sym, name)
            upsert_daily(session, sym, today, px)

    logger.info("Seeding complete.")


if __name__ == '__main__':
    main()

