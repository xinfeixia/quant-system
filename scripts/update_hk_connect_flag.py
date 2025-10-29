"""
更新港股通标识
使用akshare获取港股通标的列表，并更新数据库中的is_hk_connect字段
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import init_config
from database import init_database, get_db_manager
from database.models import StockInfo
from loguru import logger

try:
    import akshare as ak
except ImportError:
    print("❌ 需要安装akshare: pip install akshare")
    sys.exit(1)


def get_hk_connect_stocks():
    """
    获取港股通标的列表（沪港通+深港通）

    Returns:
        set: 港股通股票代码集合
    """
    hk_connect_symbols = set()

    try:
        # 获取港股通标的（包含沪港通和深港通）
        print("正在获取港股通标的...")
        df = ak.stock_hk_ggt_components_em()

        if df is not None and not df.empty:
            # akshare返回的格式是 "01855" 这样的5位数字
            for code in df['代码']:
                # 转换为数据库格式：去掉前导0，保留4位数字
                # 例如：01855 -> 1855.HK, 00700 -> 0700.HK
                code_str = str(code).zfill(5)  # 先补齐到5位
                # 去掉最前面的0，但保留至少4位
                code_num = str(int(code_str)).zfill(4)  # 转为整数去掉前导0，再补齐到4位
                symbol = f"{code_num}.HK"
                hk_connect_symbols.add(symbol)

            print(f"✅ 港股通标的: {len(df)} 只")

            # 显示前10只
            print("\n前10只港股通标的:")
            for i, row in df.head(10).iterrows():
                code = str(row['代码']).zfill(5)
                print(f"  {i+1}. {code}.HK - {row['名称']}")
        else:
            logger.warning("获取港股通标的返回空数据")

    except Exception as e:
        logger.error(f"获取港股通标的失败: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n📊 港股通标的总数: {len(hk_connect_symbols)} 只")
    return hk_connect_symbols


def update_hk_connect_flag():
    """更新数据库中的港股通标识"""
    print("\n" + "="*80)
    print("更新港股通标识")
    print("="*80 + "\n")
    
    # 初始化配置和数据库
    config_loader = init_config('config')
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 获取港股通标的列表
    hk_connect_symbols = get_hk_connect_stocks()
    
    if not hk_connect_symbols:
        print("❌ 未获取到港股通标的列表")
        return
    
    # 更新数据库
    print("\n正在更新数据库...")
    with db_manager.get_session() as session:
        # 获取所有港股
        hk_stocks = session.query(StockInfo).filter_by(market='HK', is_active=True).all()
        print(f"数据库中港股总数: {len(hk_stocks)}")
        
        updated = 0
        hk_connect_count = 0
        
        for stock in hk_stocks:
            is_hk_connect = stock.symbol in hk_connect_symbols
            
            # 检查是否需要更新
            if hasattr(stock, 'is_hk_connect'):
                if stock.is_hk_connect != is_hk_connect:
                    stock.is_hk_connect = is_hk_connect
                    stock.updated_at = datetime.now()
                    updated += 1
            else:
                # 如果字段不存在，需要先添加字段
                print("⚠️ 数据库中没有is_hk_connect字段，需要先运行数据库迁移")
                return
            
            if is_hk_connect:
                hk_connect_count += 1
        
        session.commit()
        
        print(f"\n✅ 更新完成！")
        print(f"   - 港股通标的: {hk_connect_count} 只")
        print(f"   - 非港股通: {len(hk_stocks) - hk_connect_count} 只")
        print(f"   - 更新记录数: {updated} 条")
        
        # 显示部分港股通标的
        print("\n港股通标的示例（前20只）:")
        hk_connect_stocks = session.query(StockInfo).filter_by(
            market='HK', 
            is_active=True,
            is_hk_connect=True
        ).limit(20).all()
        
        for i, stock in enumerate(hk_connect_stocks, 1):
            print(f"  {i}. {stock.symbol} - {stock.name}")


def main():
    """主函数"""
    try:
        update_hk_connect_flag()
    except Exception as e:
        logger.error(f"更新港股通标识失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

