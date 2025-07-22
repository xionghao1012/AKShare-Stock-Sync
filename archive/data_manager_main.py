"""
数据管理主程序
"""
import sys
import argparse
from utils.data_manager import DataManager
from config.database_config import DatabaseConfig
from views.console_view import ConsoleView
import pandas as pd


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AKShare数据管理工具')
    parser.add_argument('--list-tables', '-l', action='store_true',
                       help='列出所有数据表')
    parser.add_argument('--table-info', '-i', type=str,
                       help='显示指定表的详细信息')
    parser.add_argument('--sample', '-s', type=str,
                       help='显示指定表的数据样本')
    parser.add_argument('--export', '-e', type=str,
                       help='导出指定表到CSV文件')
    parser.add_argument('--output', '-o', type=str, default='export.csv',
                       help='导出文件路径')
    
    return parser.parse_args()


def main():
    """主程序"""
    try:
        args = parse_arguments()
        
        # 初始化组件
        db_config = DatabaseConfig()
        data_manager = DataManager(db_config)
        view = ConsoleView()
        
        view.show_welcome_message()
        
        if args.list_tables:
            # 列出所有表
            tables = data_manager.get_table_list()
            view.show_info("数据库中的表:")
            for i, table in enumerate(tables, 1):
                print(f"{i:2d}. {table}")
            print(f"\n总共 {len(tables)} 个表")
        
        elif args.table_info:
            # 显示表信息
            table_info = data_manager.get_table_info(args.table_info)
            if table_info:
                view.show_info(f"表 {args.table_info} 的信息:")
                print(f"记录数: {table_info['record_count']:,}")
                print(f"最后更新: {table_info['last_updated']}")
                print("\n列信息:")
                for col in table_info['columns']:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                view.show_error(f"无法获取表 {args.table_info} 的信息")
        
        elif args.sample:
            # 显示数据样本
            df = data_manager.get_data_sample(args.sample)
            if df is not None:
                view.show_info(f"表 {args.sample} 的数据样本:")
                print(df.to_string())
            else:
                view.show_error(f"无法获取表 {args.sample} 的数据样本")
        
        elif args.export:
            # 导出数据
            view.show_progress(f"正在导出表 {args.export}")
            if data_manager.export_table_to_csv(args.export, args.output):
                view.show_success(f"数据已导出到 {args.output}")
            else:
                view.show_error("数据导出失败")
        
        else:
            # 交互模式
            interactive_mode(data_manager, view)
        
        return True
        
    except Exception as e:
        print(f"程序执行错误: {e}")
        return False


def interactive_mode(data_manager: DataManager, view: ConsoleView):
    """交互模式"""
    while True:
        print("\n" + "="*50)
        print("数据管理工具")
        print("="*50)
        print("1. 列出所有表")
        print("2. 查看表信息")
        print("3. 查看数据样本")
        print("4. 导出表数据")
        print("0. 退出")
        
        choice = input("\n请选择操作: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            tables = data_manager.get_table_list()
            view.show_info("数据库中的表:")
            for i, table in enumerate(tables, 1):
                print(f"{i:2d}. {table}")
            print(f"\n总共 {len(tables)} 个表")
        
        elif choice == '2':
            table_name = input("请输入表名: ").strip()
            table_info = data_manager.get_table_info(table_name)
            if table_info:
                view.show_info(f"表 {table_name} 的信息:")
                print(f"记录数: {table_info['record_count']:,}")
                print(f"最后更新: {table_info['last_updated']}")
                print("\n列信息:")
                for col in table_info['columns']:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                view.show_error(f"无法获取表 {table_name} 的信息")
        
        elif choice == '3':
            table_name = input("请输入表名: ").strip()
            df = data_manager.get_data_sample(table_name)
            if df is not None:
                view.show_info(f"表 {table_name} 的数据样本:")
                print(df.to_string())
            else:
                view.show_error(f"无法获取表 {table_name} 的数据样本")
        
        elif choice == '4':
            table_name = input("请输入表名: ").strip()
            output_path = input("请输入导出文件路径 (默认: export.csv): ").strip()
            if not output_path:
                output_path = "export.csv"
            
            view.show_progress(f"正在导出表 {table_name}")
            if data_manager.export_table_to_csv(table_name, output_path):
                view.show_success(f"数据已导出到 {output_path}")
            else:
                view.show_error("数据导出失败")
        
        else:
            view.show_error("无效的选择")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)