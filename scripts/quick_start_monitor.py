"""
资金流入监控快速启动脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import logger


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "=" * 70)
    print("🚀 资金流入监控系统 - 快速启动向导")
    print("=" * 70 + "\n")


def check_config():
    """检查配置"""
    from utils.config_loader import ConfigLoader
    
    logger.info("检查配置文件...")
    config_loader = ConfigLoader()
    config = config_loader.config
    
    # 检查邮件配置
    email_config = config.get('notification', {}).get('email', {})
    email_enabled = email_config.get('enabled', False)
    
    if not email_enabled:
        print("⚠️  邮件通知未启用")
        print("\n请按以下步骤配置邮件通知：")
        print("1. 编辑 config/config.yaml")
        print("2. 找到 notification.email 部分")
        print("3. 设置 enabled: true")
        print("4. 填写您的邮箱配置（参考 config/email_config_example.yaml）")
        print("\n配置示例：")
        print("  notification:")
        print("    email:")
        print("      enabled: true")
        print("      smtp_server: smtp.gmail.com")
        print("      smtp_port: 587")
        print("      username: your_email@gmail.com")
        print("      password: your_app_password")
        print("      from_addr: your_email@gmail.com")
        print("      to_addrs:")
        print("        - recipient@example.com")
        print("\n配置完成后，重新运行此脚本。")
        return False
    
    # 检查监控配置
    monitor_config = config.get('money_flow_monitor', {})
    monitor_enabled = monitor_config.get('enabled', False)
    
    if not monitor_enabled:
        print("⚠️  资金流入监控未启用")
        print("\n请按以下步骤启用监控：")
        print("1. 编辑 config/config.yaml")
        print("2. 找到 money_flow_monitor 部分")
        print("3. 设置 enabled: true")
        print("\n配置完成后，重新运行此脚本。")
        return False
    
    print("✅ 配置检查通过")
    return True


def test_email():
    """测试邮件发送"""
    from utils.config_loader import ConfigLoader
    from utils.email_notifier import EmailNotifier
    
    logger.info("测试邮件发送...")
    config_loader = ConfigLoader()
    config = config_loader.config
    
    email_config = config.get('notification', {}).get('email', {})
    notifier = EmailNotifier(email_config)
    
    print("\n正在发送测试邮件...")
    success = notifier.send_test_email()
    
    if success:
        print("✅ 测试邮件发送成功！请检查您的邮箱。")
        return True
    else:
        print("❌ 测试邮件发送失败！")
        print("\n常见问题：")
        print("1. Gmail用户：需要使用'应用专用密码'，不是登录密码")
        print("2. QQ/163邮箱：需要使用'授权码'，不是登录密码")
        print("3. 检查SMTP服务器和端口是否正确")
        print("4. 检查网络连接是否正常")
        print("\n详细配置说明请参考：config/email_config_example.yaml")
        return False


def check_watch_list():
    """检查监控列表"""
    from utils.config_loader import ConfigLoader
    from database.db_manager import DatabaseManager
    from database.models import StockSelection
    from sqlalchemy import func
    
    logger.info("检查监控列表...")
    config_loader = ConfigLoader()
    config = config_loader.config
    
    db_manager = DatabaseManager(config)
    
    with db_manager.get_session() as session:
        # 获取最新选股日期
        latest_date = session.query(func.max(StockSelection.selection_date)).scalar()
        
        if not latest_date:
            print("⚠️  没有找到选股结果")
            print("\n请先运行选股分析：")
            print("  python scripts/run_stock_selection.py --market CN --min-score 50")
            print("  python scripts/run_stock_selection.py --market HK --min-score 50 --hk-connect-only")
            return False
        
        # 获取高分股票数量
        count = session.query(StockSelection).filter(
            StockSelection.selection_date == latest_date,
            StockSelection.total_score >= 70
        ).count()
        
        if count == 0:
            print("⚠️  没有找到高分股票（评分>=70）")
            print("\n建议：")
            print("1. 降低评分阈值，或")
            print("2. 手动指定监控股票：")
            print("   python scripts/monitor_money_flow.py --symbols 0700.HK 9988.HK")
            return False
        
        print(f"✅ 找到 {count} 只高分股票（评分>=70）")
        
        # 显示前10只
        selections = session.query(StockSelection).filter(
            StockSelection.selection_date == latest_date,
            StockSelection.total_score >= 70
        ).order_by(StockSelection.total_score.desc()).limit(10).all()
        
        print("\n将监控以下股票（Top 10）：")
        for i, sel in enumerate(selections, 1):
            print(f"  {i}. {sel.symbol} - {sel.name} (评分: {sel.total_score})")
        
        if count > 10:
            print(f"  ... 还有 {count - 10} 只股票")
        
        return True


def start_monitor():
    """启动监控"""
    import subprocess
    
    print("\n" + "=" * 70)
    print("🚀 启动资金流入监控...")
    print("=" * 70)
    print("\n监控参数：")
    print("  - 监控间隔：60秒（可通过 --interval 参数修改）")
    print("  - 回溯时间：30分钟")
    print("  - 成交量倍数阈值：3.0x")
    print("  - 成交额倍数阈值：3.0x")
    print("  - 价格变动阈值：5%")
    print("\n按 Ctrl+C 停止监控\n")
    print("=" * 70 + "\n")
    
    try:
        subprocess.run([
            sys.executable,
            "scripts/monitor_money_flow.py"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n\n监控已停止")


def main():
    """主函数"""
    print_banner()
    
    # 1. 检查配置
    if not check_config():
        return
    
    # 2. 测试邮件
    print("\n" + "-" * 70)
    response = input("\n是否测试邮件发送？(y/n): ").strip().lower()
    if response == 'y':
        if not test_email():
            response = input("\n邮件测试失败，是否继续？(y/n): ").strip().lower()
            if response != 'y':
                return
    
    # 3. 检查监控列表
    print("\n" + "-" * 70)
    if not check_watch_list():
        return
    
    # 4. 启动监控
    print("\n" + "-" * 70)
    response = input("\n是否立即启动监控？(y/n): ").strip().lower()
    if response == 'y':
        start_monitor()
    else:
        print("\n您可以稍后手动启动监控：")
        print("  python scripts/monitor_money_flow.py")
        print("\n或指定监控股票：")
        print("  python scripts/monitor_money_flow.py --symbols 0700.HK 9988.HK")


if __name__ == '__main__':
    main()

