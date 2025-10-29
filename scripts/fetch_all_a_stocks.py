"""
自动获取所有A股历史数据
分批执行，自动处理所有批次
"""
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import init_database, get_db_manager
from database.models import StockInfo, DailyData
from utils.config_loader import init_config


def get_cn_stock_count():
    """获取A股总数"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        count = session.query(StockInfo).filter_by(market='CN').count()
    
    return count


def get_fetched_count():
    """获取已有数据的A股数量"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # 查询有历史数据的A股股票
        fetched = session.query(DailyData.symbol).distinct().join(
            StockInfo, DailyData.symbol == StockInfo.symbol
        ).filter(StockInfo.market == 'CN').count()
    
    return fetched


def run_batch(start_from, limit, delay=30):
    """
    运行一个批次
    
    Args:
        start_from: 起始位置
        limit: 数量
        delay: 延迟秒数
    
    Returns:
        bool: 是否成功
    """
    cmd = [
        'python',
        'scripts/fetch_a_stocks_slowly.py',
        '--days', '365',
        '--delay', str(delay),
        '--start-from', str(start_from),
        '--limit', str(limit)
    ]
    
    print(f"\n{'='*60}")
    print(f"执行批次: 第{start_from+1}-{start_from+limit}只")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 批次执行失败: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n\n⚠️  用户中断")
        return False


def main():
    print("\n" + "="*60)
    print("自动获取所有A股历史数据")
    print("="*60)
    
    # 获取总数
    total_stocks = get_cn_stock_count()
    print(f"\n📊 A股总数: {total_stocks}只")
    
    # 获取已完成数量
    fetched = get_fetched_count()
    print(f"✅ 已获取: {fetched}只")
    print(f"⏳ 待获取: {total_stocks - fetched}只")
    
    if fetched >= total_stocks:
        print("\n🎉 所有A股数据已获取完成！")
        return
    
    # 批次配置
    batch_size = 30
    delay = 30
    
    # 计算批次
    batches = []
    start = fetched
    
    while start < total_stocks:
        limit = min(batch_size, total_stocks - start)
        batches.append((start, limit))
        start += limit
    
    print(f"\n📋 计划执行 {len(batches)} 个批次")
    print(f"⏱️  每批次约 {batch_size * delay / 60:.1f} 分钟")
    print(f"⏱️  总预计时间: {sum(limit * delay for _, limit in batches) / 60:.1f} 分钟")
    
    # 显示批次计划
    print("\n批次计划:")
    for i, (start_from, limit) in enumerate(batches, 1):
        print(f"  批次{i}: 第{start_from+1}-{start_from+limit}只 ({limit}只)")
    
    # 确认
    print("\n" + "="*60)
    response = input("是否开始执行？(y/n): ").strip().lower()
    
    if response != 'y':
        print("\n已取消。")
        return
    
    # 执行批次
    print("\n" + "="*60)
    print("开始执行批次...")
    print("="*60)
    
    start_time = datetime.now()
    success_count = 0
    
    for i, (start_from, limit) in enumerate(batches, 1):
        print(f"\n\n{'#'*60}")
        print(f"# 批次 {i}/{len(batches)}")
        print(f"# 第{start_from+1}-{start_from+limit}只")
        print(f"{'#'*60}")
        
        success = run_batch(start_from, limit, delay)
        
        if success:
            success_count += 1
            print(f"\n✅ 批次{i}完成")
        else:
            print(f"\n❌ 批次{i}失败")
            
            # 询问是否继续
            response = input("\n是否继续下一批次？(y/n): ").strip().lower()
            if response != 'y':
                print("\n已停止。")
                break
        
        # 显示总体进度
        elapsed = (datetime.now() - start_time).total_seconds()
        completed_batches = i
        remaining_batches = len(batches) - i
        avg_time = elapsed / completed_batches if completed_batches > 0 else 0
        remaining_time = remaining_batches * avg_time
        
        print(f"\n{'='*60}")
        print(f"总体进度: {completed_batches}/{len(batches)} 批次")
        print(f"已用时: {elapsed/60:.1f} 分钟")
        print(f"预计剩余: {remaining_time/60:.1f} 分钟")
        print(f"{'='*60}")
        
        # 批次间短暂休息
        if i < len(batches):
            print(f"\n休息5秒后继续...")
            time.sleep(5)
    
    # 最终统计
    total_time = (datetime.now() - start_time).total_seconds()
    
    print("\n\n" + "="*60)
    print("执行完成！")
    print("="*60)
    print(f"✅ 成功批次: {success_count}/{len(batches)}")
    print(f"⏱️  总用时: {total_time/60:.1f} 分钟")
    
    # 检查最终数据
    final_fetched = get_fetched_count()
    print(f"\n📊 最终统计:")
    print(f"   A股总数: {total_stocks}只")
    print(f"   已获取: {final_fetched}只")
    print(f"   完成度: {final_fetched*100//total_stocks}%")
    
    if final_fetched >= total_stocks:
        print("\n🎉 所有A股历史数据获取完成！")
        print("\n💡 下一步:")
        print("   1. 计算技术指标:")
        print("      python scripts/calculate_indicators.py --batch --market CN")
        print("   2. 运行选股:")
        print("      python scripts/run_stock_selection.py --market CN --top 50")
        print("   3. 查看结果:")
        print("      http://localhost:5000/selections?market=CN")
    else:
        print(f"\n⚠️  还有 {total_stocks - final_fetched} 只股票未获取")
        print("   可以重新运行此脚本继续获取")
    
    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断\n")
    except Exception as e:
        print(f"\n❌ 错误: {e}\n")

