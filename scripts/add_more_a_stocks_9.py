#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加更多A股股票到数据库 - 第9批（中小盘优质股）
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import get_db_manager, init_database
from database.models import StockInfo
from datetime import datetime
from utils.config_loader import init_config

def main():
    """添加第9批A股股票"""
    config_loader = init_config()
    init_database(config_loader.config)
    db_manager = get_db_manager()
    
    # 第9批：50只中小盘优质股（细分行业龙头）
    new_stocks = [
        # 医疗器械与服务
        ('300529.SZ', '健帆生物', 'CN', 'SZ'),  # 血液净化
        ('300676.SZ', '华大基因', 'CN', 'SZ'),  # 基因测序
        ('300482.SZ', '万孚生物', 'CN', 'SZ'),  # POCT
        ('688278.SH', '特宝生物', 'CN', 'SH'),  # 生物制药
        ('688520.SH', '神州细胞', 'CN', 'SH'),  # 创新药
        ('300595.SZ', '欧普康视', 'CN', 'SZ'),  # 角膜塑形镜
        ('300896.SZ', '爱美客', 'CN', 'SZ'),  # 医美
        ('688016.SH', '心脉医疗', 'CN', 'SH'),  # 血管介入
        ('688617.SH', '惠泰医疗', 'CN', 'SH'),  # 心脏介入
        ('300347.SZ', '泰格医药', 'CN', 'SZ'),  # CRO
        
        # 半导体设备与材料
        ('688072.SH', '拓荆科技', 'CN', 'SH'),  # 薄膜沉积设备
        ('688508.SH', '芯朋微', 'CN', 'SH'),  # 电源管理芯片
        ('688536.SH', '思瑞浦', 'CN', 'SH'),  # 模拟芯片
        ('688368.SH', '晶丰明源', 'CN', 'SH'),  # LED驱动芯片
        ('688595.SH', '芯海科技', 'CN', 'SH'),  # MCU芯片
        ('688019.SH', '安集科技', 'CN', 'SH'),  # 半导体材料
        ('688388.SH', '嘉元科技', 'CN', 'SH'),  # 锂电铜箔
        ('688123.SH', '聚和材料', 'CN', 'SH'),  # 光学材料
        ('688680.SH', '海优新材', 'CN', 'SH'),  # 胶粘剂
        ('688608.SH', '恒玄科技', 'CN', 'SH'),  # 智能音频芯片
        
        # 新能源与储能
        ('688390.SH', '固德威', 'CN', 'SH'),  # 逆变器
        ('688032.SH', '禾迈股份', 'CN', 'SH'),  # 微型逆变器
        ('300763.SZ', '锦浪科技', 'CN', 'SZ'),  # 逆变器
        ('688063.SH', '派能科技', 'CN', 'SH'),  # 储能系统
        ('300443.SZ', '金雷股份', 'CN', 'SZ'),  # 风电主轴
        ('688339.SH', '亿华通', 'CN', 'SH'),  # 氢燃料电池
        ('601615.SH', '明阳智能', 'CN', 'SH'),  # 风电整机
        ('002202.SZ', '金风科技', 'CN', 'SZ'),  # 风电整机
        
        # 军工与航天
        ('688122.SH', '西部超导', 'CN', 'SH'),  # 超导材料
        ('688559.SH', '海目星', 'CN', 'SH'),  # 激光设备
        ('688066.SH', '航天宏图', 'CN', 'SH'),  # 卫星应用
        ('300775.SZ', '三角防务', 'CN', 'SZ'),  # 航空锻件
        ('300726.SZ', '宏达电子', 'CN', 'SZ'),  # 军用电容
        
        # 软件与信息安全
        ('688088.SH', '虹软科技', 'CN', 'SH'),  # 视觉AI
        ('688023.SH', '安恒信息', 'CN', 'SH'),  # 网络安全
        ('688561.SH', '奇安信', 'CN', 'SH'),  # 网络安全
        ('688777.SH', '中控技术', 'CN', 'SH'),  # 工业自动化
        ('688169.SH', '石头科技', 'CN', 'SH'),  # 扫地机器人
        
        # 消费品与服务
        ('002570.SZ', '贝因美', 'CN', 'SZ'),  # 婴幼儿奶粉
        ('300999.SZ', '金龙鱼', 'CN', 'SZ'),  # 食用油
        ('603345.SH', '安井食品', 'CN', 'SH'),  # 速冻食品
        ('603517.SH', '绝味食品', 'CN', 'SH'),  # 卤制品
        ('603866.SH', '桃李面包', 'CN', 'SH'),  # 烘焙食品
        ('002507.SZ', '涪陵榨菜', 'CN', 'SZ'),  # 榨菜
        ('603127.SH', '昭衍新药', 'CN', 'SH'),  # CRO
        ('002821.SZ', '凯莱英', 'CN', 'SZ'),  # CDMO
        
        # 新材料
        ('688005.SH', '容百科技', 'CN', 'SH'),  # 三元正极材料
        ('300568.SZ', '星源材质', 'CN', 'SZ'),  # 锂电隔膜
        ('300037.SZ', '新宙邦', 'CN', 'SZ'),  # 电解液
        ('002709.SZ', '天赐材料', 'CN', 'SZ'),  # 电解液
    ]
    
    added = 0
    skipped = 0
    
    with db_manager.get_session() as session:
        for symbol, name, market, exchange in new_stocks:
            # 检查是否已存在
            existing = session.query(StockInfo).filter_by(symbol=symbol).first()
            if existing:
                print(f"⚠️  {symbol} - {name} 已存在，跳过")
                skipped += 1
                continue
            
            # 添加新股票
            stock = StockInfo(
                symbol=symbol,
                name=name,
                market=market,
                exchange=exchange,
                created_at=datetime.now()
            )
            session.add(stock)
            print(f"✅ 添加 {symbol} - {name}")
            added += 1
        
        session.commit()
    
    print(f"\n{'='*60}")
    print(f"第9批A股添加完成！")
    print(f"新增: {added} 只")
    print(f"跳过: {skipped} 只（已存在）")
    print(f"总计: {added + skipped} 只")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

