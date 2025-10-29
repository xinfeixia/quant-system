"""
API配置切换工具
支持在多个API Key之间切换
"""
import sys
import yaml
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def backup_current_config():
    """备份当前配置"""
    config_file = Path('config/api_config.yaml')
    backup_file = Path(f'config/api_config_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml')
    
    if config_file.exists():
        shutil.copy(config_file, backup_file)
        print(f"✅ 当前配置已备份到: {backup_file}")
        return backup_file
    else:
        print("⚠️  配置文件不存在")
        return None


def load_config():
    """加载当前配置"""
    config_file = Path('config/api_config.yaml')
    
    if not config_file.exists():
        print("❌ 配置文件不存在")
        return None
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_config(config):
    """保存配置"""
    config_file = Path('config/api_config.yaml')
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✅ 配置已保存到: {config_file}")


def update_longport_credentials(app_key, app_secret, access_token):
    """更新长桥API凭证"""
    
    # 备份当前配置
    backup_current_config()
    
    # 加载配置
    config = load_config()
    if not config:
        return False
    
    # 更新凭证
    if 'longport' not in config:
        config['longport'] = {}
    
    config['longport']['app_key'] = app_key
    config['longport']['app_secret'] = app_secret
    config['longport']['access_token'] = access_token
    
    # 保存配置
    save_config(config)
    
    print("\n✅ 长桥API凭证已更新！")
    return True


def show_current_config():
    """显示当前配置（隐藏敏感信息）"""
    config = load_config()
    if not config:
        return
    
    print("\n" + "="*60)
    print("当前API配置")
    print("="*60)
    
    if 'longport' in config:
        lp = config['longport']
        print(f"App Key: {lp.get('app_key', '')[:10]}...")
        print(f"App Secret: {lp.get('app_secret', '')[:10]}...")
        print(f"Access Token: {lp.get('access_token', '')[:10]}...")
    else:
        print("未配置长桥API")
    
    print("="*60 + "\n")


def list_backup_configs():
    """列出所有备份配置"""
    config_dir = Path('config')
    backups = list(config_dir.glob('api_config_backup_*.yaml'))
    
    if not backups:
        print("没有找到备份配置文件")
        return []
    
    print("\n" + "="*60)
    print("备份配置文件")
    print("="*60)
    
    for i, backup in enumerate(sorted(backups, reverse=True), 1):
        print(f"{i}. {backup.name}")
    
    print("="*60 + "\n")
    
    return backups


def restore_backup(backup_file):
    """恢复备份配置"""
    config_file = Path('config/api_config.yaml')
    
    # 先备份当前配置
    backup_current_config()
    
    # 恢复备份
    shutil.copy(backup_file, config_file)
    print(f"✅ 已恢复配置: {backup_file}")


def main():
    print("\n" + "="*60)
    print("API配置切换工具")
    print("="*60)
    print()
    print("功能：")
    print("  1. 查看当前配置")
    print("  2. 更新API凭证")
    print("  3. 查看备份配置")
    print("  4. 恢复备份配置")
    print("  5. 退出")
    print()
    print("="*60 + "\n")
    
    while True:
        try:
            choice = input("请选择操作 (1-5): ").strip()
            
            if choice == '1':
                show_current_config()
                
            elif choice == '2':
                print("\n请输入新的API凭证：\n")
                app_key = input("App Key: ").strip()
                app_secret = input("App Secret: ").strip()
                access_token = input("Access Token: ").strip()
                
                if not app_key or not app_secret or not access_token:
                    print("\n❌ 错误: 所有字段都必须填写！\n")
                    continue
                
                if update_longport_credentials(app_key, app_secret, access_token):
                    print("\n💡 建议：运行测试脚本验证新凭证")
                    print("   python scripts/test_api_with_new_key.py\n")
                
            elif choice == '3':
                list_backup_configs()
                
            elif choice == '4':
                backups = list_backup_configs()
                if not backups:
                    continue
                
                try:
                    idx = int(input("\n请选择要恢复的备份 (输入编号): ").strip())
                    if 1 <= idx <= len(backups):
                        restore_backup(sorted(backups, reverse=True)[idx-1])
                    else:
                        print("❌ 无效的编号")
                except ValueError:
                    print("❌ 请输入有效的数字")
                
            elif choice == '5':
                print("\n再见！\n")
                break
                
            else:
                print("\n❌ 无效的选择，请输入1-5\n")
                
        except KeyboardInterrupt:
            print("\n\n再见！\n")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}\n")


if __name__ == '__main__':
    main()

