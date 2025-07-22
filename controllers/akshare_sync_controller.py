"""
AKShare数据同步控制器 - 优化错误处理
"""
from models.akshare_sync_model import AKShareSyncModel
from views.console_view import ConsoleView
from config.database_config import DatabaseConfig
from utils.logger_util import setup_logger
from utils.error_handler import ErrorHandler, SafeExecutor
import logging

logger = logging.getLogger(__name__)


class AKShareSyncController:
    """AKShare数据同步控制器"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.model = AKShareSyncModel(self.db_config)
        self.view = ConsoleView()
        self.error_handler = ErrorHandler(__name__)
        self.safe_executor = SafeExecutor(self.error_handler)
    
    def initialize(self) -> bool:
        """初始化系统，带错误处理"""
        try:
            setup_logger()
            self.view.show_welcome_message()
            
            # 安全执行数据库连接
            connection_result = self.safe_executor.safe_execute(
                self.model.connect_database,
                default_return=False,
                context="数据库连接初始化"
            )
            
            if not connection_result:
                self.view.show_error("数据库连接失败")
                return False
            
            self.view.show_success("系统初始化完成")
            logger.info("系统初始化成功")
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "系统初始化")
            self.view.show_error(f"系统初始化失败: {error_info['message']}")
            return False
    
    def sync_by_category(self, category: str) -> bool:
        """按分类同步数据，带错误处理"""
        try:
            self.view.show_progress(f"开始同步 {category} 数据")
            logger.info(f"开始同步 {category} 数据")
            
            # 安全获取数据
            data_dict = self.safe_executor.safe_execute(
                self.model.fetch_data_by_category,
                category,
                default_return={},
                context=f"获取 {category} 数据"
            )
            
            if not data_dict:
                self.view.show_warning(f"没有获取到 {category} 数据")
                return False
            
            success_count = 0
            total_count = len(data_dict)
            
            for data_name, df in data_dict.items():
                table_name = f"{category}_{data_name}"
                
                # 安全保存数据
                save_result = self.safe_executor.safe_execute(
                    self.model.save_data_to_table,
                    df, table_name,
                    default_return=False,
                    context=f"保存 {table_name} 数据"
                )
                
                if save_result:
                    success_count += 1
                    logger.info(f"成功保存 {table_name} 数据")
                else:
                    logger.warning(f"保存 {table_name} 数据失败")
            
            # 显示结果
            result_message = f"{category} 数据同步完成: {success_count}/{total_count}"
            if success_count == total_count:
                self.view.show_success(result_message)
                logger.info(result_message)
            else:
                self.view.show_warning(result_message)
                logger.warning(result_message)
            
            return success_count == total_count
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, f"同步 {category} 数据")
            self.view.show_error(f"同步 {category} 数据失败: {error_info['message']}")
            return False
    
    def sync_all_data(self) -> bool:
        """同步所有数据"""
        return self.model.sync_all_data()
    
    def interactive_sync(self):
        """交互式同步"""
        categories = list(self.model.data_sources.keys())
        
        self.view.show_info("可用的数据分类:")
        for i, category in enumerate(categories, 1):
            print(f"{i}. {category}")
        
        choice = self.view.prompt_user_input("请选择要同步的分类 (输入数字，0表示全部)")
        
        try:
            choice_num = int(choice)
            if choice_num == 0:
                return self.sync_all_data()
            elif 1 <= choice_num <= len(categories):
                category = categories[choice_num - 1]
                return self.sync_by_category(category)
            else:
                self.view.show_error("无效的选择")
                return False
        except ValueError:
            self.view.show_error("请输入有效的数字")
            return False
    
    def cleanup(self):
        """清理资源"""
        if self.model:
            self.model.close_connection()