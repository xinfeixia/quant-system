#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取所有港股列表并添加到数据库
使用 akshare 获取完整的港股列表
"""

import sys
from pathlib import Path
from datetime import datetime
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_loader import init_config
from database import get_db_manager, init_database
from database.models import StockInfo
from data_collection.longport_client import init_longport_client, get_longport_client
from loguru import logger

try:
    import akshare as ak
except ImportError:
    print("❌ 需要安装 akshare 库")
    print("请运行: pip install akshare")
    sys.exit(1)


def get_all_hk_stocks():
    """使用akshare获取所有港股列表"""
    try:
        logger.info("正在从akshare获取港股列表...")
        
        # 获取港股主板股票列表
        print("获取港股主板股票...")
        df_main = ak.stock_hk_spot_em()
        
        if df_main is None or df_main.empty:
            logger.error("获取港股列表为空")
            return []
        
        logger.info(f"获取到 {len(df_main)} 只港股")
        
        # 提取股票代码和名称
        stocks = []
        for _, row in df_main.iterrows():
            code = str(row['代码'])
            name = str(row['名称'])
            
            # 转换为LongPort格式 (例如: 00700 -> 0700.HK)
            # 去掉前导零，但保留至少4位
            code_num = code.lstrip('0') or '0'
            if len(code_num) < 4:
                code_num = code_num.zfill(4)
            
            symbol = f"{code_num}.HK"
            
            stocks.append({
                'symbol': symbol,
                'name': name,
                'original_code': code
            })
        
        logger.info(f"处理后得到 {len(stocks)} 只港股")
        return stocks
        
    except Exception as e:
        logger.error(f"获取港股列表失败: {e}")
        return []


def add_stocks_to_db(stocks, db_manager, longport_client):
    """将股票添加到数据库"""
    added = 0
    existed = 0
    failed = 0
    
    total = len(stocks)
    
    print(f"\n开始添加 {total} 只港股到数据库...\n")
    
    with db_manager.get_session() as session:
        for i, stock_info in enumerate(stocks, 1):
            symbol = stock_info['symbol']
            name = stock_info['name']
            
            try:
                # 检查是否已存在
                existing = session.query(StockInfo).filter_by(symbol=symbol).first()
                
                if existing:
                    if i % 100 == 0:
                        print(f"[{i}/{total}] ✓ {symbol} - {existing.name} (已存在)")
                    existed += 1
                    continue
                
                # 尝试从LongPort获取更详细的信息
                try:
                    static_info = longport_client.get_static_info([symbol])
                    if static_info and len(static_info) > 0:
                        info = static_info[0]
                        name = info.name_cn or info.name_en or name
                except Exception as e:
                    # 如果LongPort获取失败，使用akshare的名称
                    logger.debug(f"LongPort获取 {symbol} 信息失败: {e}")
                
                # 添加到数据库
                stock = StockInfo(
                    symbol=symbol,
                    name=name,
                    market='HK',
                    is_active=True
                )
                session.add(stock)
                
                if i % 100 == 0 or i <= 10:
                    print(f"[{i}/{total}] ✅ {symbol} - {name} (新增)")
                
                added += 1
                
                # 每100条提交一次
                if i % 100 == 0:
                    session.commit()
                    print(f"\n📊 进度: {i}/{total} ({i*100//total}%), 新增: {added}, 已存在: {existed}, 失败: {failed}\n")
                
                # 避免请求过快
                if i % 10 == 0:
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"添加 {symbol} 失败: {e}")
                failed += 1
                continue
        
        # 最后提交
        session.commit()
    
    return added, existed, failed


def main():
    """主函数"""
    print("\n" + "="*80)
    print("获取所有港股列表并添加到数据库")
    print("="*80)
    
    # 初始化配置和数据库
    logger.info("初始化配置与数据库...")
    config_dir = str(project_root / 'config')
    config_loader = init_config(config_dir=config_dir)
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 初始化长桥客户端
    init_longport_client(config_loader.api_config)
    longport_client = get_longport_client()
    
    # 获取所有港股列表
    stocks = get_all_hk_stocks()
    
    if not stocks:
        print("❌ 未能获取港股列表")
        return
    
    print(f"\n✅ 成功获取 {len(stocks)} 只港股")
    
    # 添加到数据库
    start_time = time.time()
    added, existed, failed = add_stocks_to_db(stocks, db_manager, longport_client)
    elapsed = time.time() - start_time
    
    # 最终统计
    print("\n" + "="*80)
    print("港股列表添加完成！")
    print("="*80)
    print(f"总计: {len(stocks)} 只港股")
    print(f"新增: {added} 只")
    print(f"已存在: {existed} 只")
    print(f"失败: {failed} 只")
    print(f"总用时: {elapsed/60:.1f} 分钟")
    print("="*80)
    
    # 查询当前数据库中的港股总数
    with db_manager.get_session() as session:
        total_hk = session.query(StockInfo).filter_by(market='HK', is_active=True).count()
        print(f"\n📊 数据库中现有港股总数: {total_hk} 只")
    
    print("\n下一步:")
    print("  运行以下命令获取所有港股的2个月历史数据:")
    print("  python scripts/fetch_hk_2months.py")


if __name__ == '__main__':
    main()

