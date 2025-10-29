#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
极速版：按交易日一次性获取全市场A股当日数据并入库
用法：
    python scripts/fetch_today_a_stocks_fast.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Set

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import init_config
from database import get_db_manager, init_database
from database.models import DailyData, StockInfo
from loguru import logger

import tushare as ts
import pandas as pd


def get_last_trade_date(pro) -> str:
    """
    获取A股最近一个交易日（YYYYMMDD）
    优先用 trade_cal；若无权限，则从今天起向前逐日尝试 pro.daily 直到拿到非空数据
    """
    today = datetime.now().strftime('%Y%m%d')
    # 优先尝试 trade_cal
    try:
        start = (datetime.now() - timedelta(days=20)).strftime('%Y%m%d')
        cal = pro.trade_cal(exchange='SSE', start_date=start, end_date=today)
        cal = cal[cal['is_open'] == 1]
        if not cal.empty:
            return str(cal.iloc[-1]['cal_date'])
    except Exception as e:
        logger.warning(f"trade_cal 无权限或失败，使用回退方案：{e}")

    # 回退：从今天往前最多10天逐日尝试
    for i in range(0, 10):
        d = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
        try:
            df = pro.daily(trade_date=d)
            if df is not None and not df.empty:
                logger.info(f"回退方案命中交易日：{d}，记录数：{len(df)}")
                return d
        except Exception as e:
            logger.warning(f"尝试 {d} 失败：{e}")

    raise RuntimeError('未能确定最近交易日：trade_cal 无权限且回退方案未命中')


def load_cn_symbols(db_manager) -> Set[str]:
    """从库中加载已跟踪A股代码集合（如 600000.SH/000001.SZ）"""
    with db_manager.get_session() as session:
        rows = session.query(StockInfo.symbol).filter_by(market='CN').all()
        return {r[0] for r in rows}


def upsert_daily_rows(db_manager, df: pd.DataFrame, trade_date_str: str, symbols: Set[str]):
    """将当日数据写入 daily_data，存在则更新，不存在则插入"""
    trade_date = datetime.strptime(trade_date_str, '%Y%m%d').date()
    # 仅保留我们跟踪的A股
    df = df[df['ts_code'].isin(symbols)].copy()
    if df.empty:
        logger.warning('当日数据在当前跟踪列表中为空，可能是代码不匹配或列表为空')
        return 0, 0

    insert_cnt = 0
    update_cnt = 0

    with db_manager.get_session() as session:
        for _, row in df.iterrows():
            symbol = str(row['ts_code'])
            existing = session.query(DailyData).filter_by(symbol=symbol, trade_date=trade_date).first()

            payload = {
                'open': float(row['open']) if pd.notna(row['open']) else None,
                'high': float(row['high']) if pd.notna(row['high']) else None,
                'low': float(row['low']) if pd.notna(row['low']) else None,
                'close': float(row['close']) if pd.notna(row['close']) else None,
                # Tushare vol 单位：手；amount 单位：千元
                'volume': int(row['vol'] * 100) if pd.notna(row['vol']) else None,
                'turnover': float(row['amount'] * 1000) if pd.notna(row['amount']) else None,
                'change': float(row['change']) if 'change' in row and pd.notna(row['change']) else None,
                'change_pct': float(row['pct_chg']) if 'pct_chg' in row and pd.notna(row['pct_chg']) else None,
            }

            if existing:
                for k, v in payload.items():
                    if k not in ['symbol', 'trade_date']:
                        setattr(existing, k, v)
                update_cnt += 1
            else:
                rec = DailyData(
                    symbol=symbol,
                    trade_date=trade_date,
                    **payload
                )
                session.add(rec)
                insert_cnt += 1

        session.commit()

    return insert_cnt, update_cnt


def main():
    logger.info('初始化配置与数据库...')
    config_dir = str(project_root / 'config')
    cfg_loader = init_config(config_dir=config_dir)
    init_database(cfg_loader.config)
    db_manager = get_db_manager()

    # 读取Tushare token
    ts_cfg = cfg_loader.api_config.get('tushare', {})
    token = ts_cfg.get('token')
    if not token:
        raise ValueError('Tushare token未配置')

    ts.set_token(token)
    pro = ts.pro_api()

    # 确定最近交易日
    trade_date = get_last_trade_date(pro)

    # 加载A股代码白名单
    symbols = load_cn_symbols(db_manager)
    logger.info(f'跟踪A股数量: {len(symbols)}，交易日: {trade_date}')

    print('\n' + '=' * 60)
    print('按交易日一次性获取当日A股数据（极速版）')
    print(f'交易日: {trade_date}')
    print('=' * 60 + '\n')

    # 一次性拉取当日全市场日线数据
    logger.info('请求 Tushare pro.daily(trade_date=...) 全市场数据...')
    df = pro.daily(trade_date=trade_date)
    if df is None or df.empty:
        logger.warning('当日全市场数据为空，可能是节假日或网络问题')
        print('⚠️ 当日全市场数据为空')
        return

    # 入库
    ins, upd = upsert_daily_rows(db_manager, df, trade_date, symbols)

    print('\n' + '=' * 60)
    print('A股当日数据入库完成（极速版）')
    print(f'交易日: {trade_date}')
    print(f'新增: {ins} 条，更新: {upd} 条，总计: {ins + upd} 条')
    print('=' * 60)


if __name__ == '__main__':
    main()

