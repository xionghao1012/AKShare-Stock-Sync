"""
控制台视图 - 负责用户界面显示和交互
"""
import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConsoleView:
    """控制台视图类"""
    
    @staticmethod
    def show_welcome_message():
        """显示欢迎信息"""
        print("=" * 60)
        print("🚀 中国股票数据收集系统")
        print("=" * 60)
    
    @staticmethod
    def show_data_preview(df: pd.DataFrame, info: Dict[str, Any]):
        """显示数据预览"""
        if df is None or df.empty:
            print("❌ 没有数据可以显示")
            return
        
        print("\n📊 数据预览:")
        print("-" * 40)
        print(f"数据形状: {info.get('shape', 'N/A')}")
        print(f"数据列: {info.get('columns', [])}")
        print(f"内存使用: {info.get('memory_usage', 0) / 1024:.2f} KB")
        
        print("\n前5行数据:")
        print(df.head().to_string())
        
        # 显示数据类型
        if 'dtypes' in info:
            print("\n数据类型:")
            for col, dtype in info['dtypes'].items():
                print(f"  {col}: {dtype}")
        
        # 显示空值统计
        null_counts = info.get('null_counts', {})
        if any(count > 0 for count in null_counts.values()):
            print("\n⚠️  空值统计:")
            for col, count in null_counts.items():
                if count > 0:
                    print(f"  {col}: {count}")
    
    @staticmethod
    def show_progress(message: str, step: int = None, total: int = None):
        """显示进度信息"""
        if step is not None and total is not None:
            progress = f"[{step}/{total}] "
        else:
            progress = ""
        
        print(f"⏳ {progress}{message}")
    
    @staticmethod
    def show_success(message: str):
        """显示成功信息"""
        print(f"✅ {message}")
    
    @staticmethod
    def show_warning(message: str):
        """显示警告信息"""
        print(f"⚠️  {message}")
    
    @staticmethod
    def show_error(message: str):
        """显示错误信息"""
        print(f"❌ {message}")
    
    @staticmethod
    def show_info(message: str):
        """显示一般信息"""
        print(f"ℹ️  {message}")
    
    @staticmethod
    def show_data_summary(record_count: int, table_name: str):
        """显示数据汇总信息"""
        print(f"\n📈 数据汇总:")
        print("-" * 40)
        print(f"表名: {table_name}")
        print(f"总记录数: {record_count:,}")
    
    @staticmethod
    def show_completion_message(success: bool):
        """显示完成信息"""
        print("\n" + "=" * 60)
        if success:
            print("🎉 程序执行成功完成！")
        else:
            print("💥 程序执行失败，请查看日志获取详细信息")
        print("=" * 60)
    
    @staticmethod
    def prompt_user_input(prompt: str) -> str:
        """获取用户输入"""
        return input(f"❓ {prompt}: ").strip()
    
    @staticmethod
    def confirm_action(message: str) -> bool:
        """确认操作"""
        response = input(f"❓ {message} (y/N): ").strip().lower()
        return response in ['y', 'yes', '是', 'Y']