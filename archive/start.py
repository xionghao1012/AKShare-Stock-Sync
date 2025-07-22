"""
AKShare数据同步系统启动器
"""
import sys
import argparse
import subprocess
import os


def show_menu():
    """显示主菜单"""
    print("🚀 AKShare数据同步系统")
    print("=" * 50)
    print("1. 手动数据同步")
    print("2. 启动自动调度器")
    print("3. 数据管理工具")
    print("4. 数据转换工具")
    print("5. 批量同步股票")
    print("6. 系统监控面板")
    print("7. 安装依赖包")
    print("0. 退出")
    print("=" * 50)


def run_command(command):
    """运行命令"""
    try:
        result = subprocess.run(command, shell=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        return False


def main():
    """主程序"""
    parser = argparse.ArgumentParser(description='AKShare数据同步系统启动器')
    parser.add_argument('--mode', '-m', 
                       choices=['sync', 'scheduler', 'manager', 'transform', 'monitor', 'install'],
                       help='直接启动指定模式')
    
    args = parser.parse_args()
    
    if args.mode:
        # 直接模式
        if args.mode == 'sync':
            run_command('python akshare_sync_main.py --interactive')
        elif args.mode == 'scheduler':
            run_command('python scheduler_main.py')
        elif args.mode == 'manager':
            run_command('python data_manager_main.py')
        elif args.mode == 'transform':
            run_command('python transform_data.py')
        elif args.mode == 'monitor':
            run_command('python system_monitor.py')
        elif args.mode == 'install':
            run_command('pip install -r requirements.txt')
    else:
        # 交互模式
        while True:
            show_menu()
            choice = input("请选择操作: ").strip()
            
            if choice == '0':
                print("👋 再见！")
                break
            elif choice == '1':
                print("启动手动数据同步...")
                run_command('python akshare_sync_main.py --interactive')
            elif choice == '2':
                print("启动自动调度器...")
                run_command('python scheduler_main.py')
            elif choice == '3':
                print("启动数据管理工具...")
                run_command('python data_manager_main.py')
            elif choice == '4':
                print("启动数据转换工具...")
                run_command('python transform_data.py')
            elif choice == '5':
                print("启动批量同步股票...")
                count = input("请输入要同步的股票数量 (默认10): ").strip()
                if not count:
                    count = "10"
                run_command(f'python batch_sync_stocks.py {count}')
            elif choice == '6':
                print("启动系统监控面板...")
                run_command('python system_monitor.py')
            elif choice == '7':
                print("安装依赖包...")
                if run_command('pip install -r requirements.txt'):
                    print("✅ 依赖包安装完成")
                else:
                    print("❌ 依赖包安装失败")
            else:
                print("❌ 无效的选择")
            
            input("\n按回车键继续...")


if __name__ == "__main__":
    main()