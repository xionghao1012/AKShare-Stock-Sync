"""
数据转换主程序 - 将键值对表转换为单行表
"""
import sys
import argparse
from utils.data_transformer import DataTransformer
from config.database_config import DatabaseConfig
from utils.logger_util import setup_logger
import logging

logger = logging.getLogger(__name__)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='数据转换工具')
    parser.add_argument('--table', '-t', type=str,
                       help='要转换的表名')
    parser.add_argument('--target', type=str,
                       help='目标表名（可选）')
    parser.add_argument('--batch', '-b', action='store_true',
                       help='批量转换所有个股信息表')
    parser.add_argument('--compare', '-c', type=str,
                       help='对比转换前后的数据')
    parser.add_argument('--list-transformed', '-l', action='store_true',
                       help='列出所有转换后的表')
    
    return parser.parse_args()


def list_transformed_tables(transformer: DataTransformer):
    """列出所有转换后的表"""
    try:
        from sqlalchemy import text
        with transformer.engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE '%_transformed'"))
            tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print("转换后的表:")
            for i, table in enumerate(tables, 1):
                print(f"{i:2d}. {table}")
            print(f"\n总共 {len(tables)} 个转换后的表")
        else:
            print("没有找到转换后的表")
            
    except Exception as e:
        logger.error(f"列出转换后的表失败: {e}")


def main():
    """主程序"""
    try:
        args = parse_arguments()
        
        # 设置日志
        setup_logger()
        
        # 初始化转换器
        db_config = DatabaseConfig()
        transformer = DataTransformer(db_config)
        
        print("🔄 数据转换工具")
        print("=" * 50)
        
        if args.list_transformed:
            # 列出转换后的表
            list_transformed_tables(transformer)
            
        elif args.compare:
            # 对比转换前后数据
            transformer.compare_before_after(args.compare)
            
        elif args.batch:
            # 批量转换
            print("开始批量转换个股信息表...")
            if transformer.batch_transform_individual_info():
                print("✅ 批量转换成功")
            else:
                print("❌ 批量转换失败")
                
        elif args.table:
            # 转换指定表
            print(f"开始转换表: {args.table}")
            if transformer.transform_key_value_to_row(args.table, args.target):
                print("✅ 转换成功")
                
                # 显示对比
                transformer.compare_before_after(args.table)
            else:
                print("❌ 转换失败")
                
        else:
            # 交互模式
            interactive_mode(transformer)
        
        return True
        
    except Exception as e:
        logger.error(f"程序执行错误: {e}")
        return False
    finally:
        if 'transformer' in locals():
            transformer.close_connection()


def interactive_mode(transformer: DataTransformer):
    """交互模式"""
    while True:
        print("\n" + "="*50)
        print("数据转换工具")
        print("="*50)
        print("1. 转换 stock_stock_individual_info_em 表")
        print("2. 批量转换所有个股信息表")
        print("3. 对比转换前后数据")
        print("4. 列出转换后的表")
        print("0. 退出")
        
        choice = input("\n请选择操作: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            print("正在转换 stock_stock_individual_info_em 表...")
            if transformer.transform_key_value_to_row('stock_stock_individual_info_em'):
                print("✅ 转换成功")
                transformer.compare_before_after('stock_stock_individual_info_em')
            else:
                print("❌ 转换失败")
                
        elif choice == '2':
            print("开始批量转换...")
            if transformer.batch_transform_individual_info():
                print("✅ 批量转换成功")
            else:
                print("❌ 批量转换失败")
                
        elif choice == '3':
            table_name = input("请输入要对比的表名: ").strip()
            if table_name:
                transformer.compare_before_after(table_name)
            else:
                print("❌ 表名不能为空")
                
        elif choice == '4':
            list_transformed_tables(transformer)
            
        else:
            print("❌ 无效的选择")
        
        input("\n按回车键继续...")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)