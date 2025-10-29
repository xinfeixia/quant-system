#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动交易系统 - 整合资金流入监控、自动交易执行和止盈监控

功能：
1. 监控资金流入，自动生成买入信号
2. 自动执行买入信号
3. 监控持仓，达到目标利润时自动生成卖出信号
4. 自动执行卖出信号
"""

import sys
import os
import argparse
import threading
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config_loader import init_config
from database.db_manager import DatabaseManager
from data_collection.longport_client import LongPortClient
from trading.money_flow_monitor import MoneyFlowMonitor
from trading.auto_trader import AutoTrader
from trading.profit_monitor import ProfitMonitor
from utils.logger import logger


def run_money_flow_monitor(config, db, lp_client, symbols):
    """运行资金流入监控"""
    try:
        monitor = MoneyFlowMonitor(config, db, lp_client)
        
        if symbols:
            logger.info(f"监控指定股票: {symbols}")
            monitor.start(symbols)
        else:
            logger.info("自动选择高分股票进行监控")
            monitor.start()
            
    except Exception as e:
        logger.error(f"资金流入监控出错: {e}")


def run_auto_trader(config, db):
    """运行自动交易执行器"""
    try:
        trader = AutoTrader(config, db)
        trader.start()
    except Exception as e:
        logger.error(f"自动交易执行器出错: {e}")


def run_profit_monitor(config, db):
    """运行止盈监控器"""
    try:
        monitor = ProfitMonitor(config, db)
        monitor.start()
    except Exception as e:
        logger.error(f"止盈监控器出错: {e}")


def main():
    parser = argparse.ArgumentParser(description='自动交易系统')
    parser.add_argument('--symbols', nargs='+', help='指定监控的股票代码（可选）')
    parser.add_argument('--money-flow-only', action='store_true', help='仅运行资金流入监控')
    parser.add_argument('--trader-only', action='store_true', help='仅运行自动交易执行器')
    parser.add_argument('--profit-only', action='store_true', help='仅运行止盈监控器')

    args = parser.parse_args()

    # 加载配置
    config_loader = init_config()
    config = config_loader.config
    api_config = config_loader.api_config

    # 检查配置
    auto_config = config.get('auto_trading', {})
    if not auto_config.get('enabled', False):
        logger.error("自动交易未启用！请在 config.yaml 中设置 auto_trading.enabled = true")
        return

    money_flow_config = config.get('money_flow_monitor', {})
    if not money_flow_config.get('enabled', False):
        logger.error("资金流入监控未启用！请在 config.yaml 中设置 money_flow_monitor.enabled = true")
        return

    if not money_flow_config.get('auto_trade', False):
        logger.error("资金流入监控未启用自动交易！请在 config.yaml 中设置 money_flow_monitor.auto_trade = true")
        return

    # 初始化数据库
    db = DatabaseManager(config)

    # 初始化LongPort客户端
    lp_client = LongPortClient(api_config)
    
    # 打印配置信息
    logger.info("=" * 80)
    logger.info("🚀 自动交易系统启动")
    logger.info("=" * 80)
    logger.info(f"交易引擎: {auto_config.get('engine_type', 'local_paper')}")
    logger.info(f"执行间隔: {auto_config.get('execution_interval', 30)}秒")
    
    take_profit = auto_config.get('take_profit', {})
    stop_loss = auto_config.get('stop_loss', {})
    trailing_stop = auto_config.get('trailing_stop', {})
    
    if take_profit.get('enabled'):
        logger.info(f"止盈策略: {take_profit.get('target_profit_pct', 0.10)*100:.1f}%")
    if stop_loss.get('enabled'):
        logger.info(f"止损策略: {stop_loss.get('stop_loss_pct', -0.05)*100:.1f}%")
    if trailing_stop.get('enabled'):
        logger.info(f"移动止损: {trailing_stop.get('trailing_stop_pct', 0.03)*100:.1f}%")
    
    logger.info(f"资金流入监控间隔: {money_flow_config.get('interval', 60)}秒")
    logger.info(f"成交量倍数阈值: {money_flow_config.get('volume_ratio_threshold', 3.0)}x")
    logger.info(f"成交额倍数阈值: {money_flow_config.get('turnover_ratio_threshold', 3.0)}x")
    logger.info(f"价格变动阈值: {money_flow_config.get('price_change_threshold', 0.05)*100:.1f}%")
    logger.info("=" * 80)
    
    # 创建线程
    threads = []
    
    if args.money_flow_only:
        # 仅运行资金流入监控
        logger.info("模式: 仅资金流入监控")
        thread = threading.Thread(
            target=run_money_flow_monitor,
            args=(config, db, lp_client, args.symbols),
            daemon=True
        )
        threads.append(thread)
        
    elif args.trader_only:
        # 仅运行自动交易执行器
        logger.info("模式: 仅自动交易执行器")
        thread = threading.Thread(
            target=run_auto_trader,
            args=(config, db),
            daemon=True
        )
        threads.append(thread)
        
    elif args.profit_only:
        # 仅运行止盈监控器
        logger.info("模式: 仅止盈监控器")
        thread = threading.Thread(
            target=run_profit_monitor,
            args=(config, db),
            daemon=True
        )
        threads.append(thread)
        
    else:
        # 运行完整系统
        logger.info("模式: 完整自动交易系统")
        logger.info("启动3个模块:")
        logger.info("  1. 资金流入监控 - 检测资金流入并生成买入信号")
        logger.info("  2. 自动交易执行器 - 执行买入/卖出信号")
        logger.info("  3. 止盈监控器 - 监控持仓并生成卖出信号")
        logger.info("=" * 80)
        
        # 资金流入监控线程
        thread1 = threading.Thread(
            target=run_money_flow_monitor,
            args=(config, db, lp_client, args.symbols),
            daemon=True,
            name="MoneyFlowMonitor"
        )
        threads.append(thread1)
        
        # 自动交易执行器线程
        thread2 = threading.Thread(
            target=run_auto_trader,
            args=(config, db),
            daemon=True,
            name="AutoTrader"
        )
        threads.append(thread2)
        
        # 止盈监控器线程
        thread3 = threading.Thread(
            target=run_profit_monitor,
            args=(config, db),
            daemon=True,
            name="ProfitMonitor"
        )
        threads.append(thread3)
    
    # 启动所有线程
    for thread in threads:
        thread.start()
        logger.info(f"✅ 启动线程: {thread.name}")
        time.sleep(2)  # 错开启动时间
    
    logger.info("=" * 80)
    logger.info("所有模块已启动，按 Ctrl+C 停止")
    logger.info("=" * 80)
    
    # 主线程等待
    try:
        while True:
            time.sleep(1)
            
            # 检查线程是否还在运行
            for thread in threads:
                if not thread.is_alive():
                    logger.warning(f"线程 {thread.name} 已停止")
                    
    except KeyboardInterrupt:
        logger.info("\n正在停止自动交易系统...")
        logger.info("所有线程将在完成当前任务后停止")
        
        # 等待所有线程结束
        for thread in threads:
            thread.join(timeout=5)
        
        logger.info("自动交易系统已停止")


if __name__ == '__main__':
    main()

