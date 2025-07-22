"""
股票数据控制器 - 负责业务逻辑控制和协调
"""
from models.stock_data_model import StockDataModel
from views.console_view import ConsoleView
from config.database_config import DatabaseConfig
from utils.logger_util import setup_logger
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class StockDataController:
    """股票数据控制器类"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.model = StockDataModel(self.db_config)
        self.view = ConsoleView()
        self.setup_complete = False
    
    def initialize(self) -> bool:
        """初始化控制器"""
        try:
            # 设置日志
            setup_logger()
            
            # 显示欢迎信息
            self.view.show_welcome_message()
            
            # 连接数据库
            self.view.show_progress("初始化数据库连接")
            if not self.model.connect_database():
                self.view.show_error("数据库连接失败")
                return False
            
            self.view.show_success("系统初始化完成")
            self.setup_complete = True
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            self.view.show_error(f"初始化失败: {e}")
            return False
    
    def fetch_and_process_data(self, params: Optional[Dict[str, str]] = None) -> bool:
        """获取和处理数据的主要流程"""
        if not self.setup_complete:
            self.view.show_error("系统未初始化")
            return False
        
        try:
            # 设置默认参数
            if params is None:
                params = {
                    'var': 'RB',
                    'start_day': '20180618',
                    'end_day': '20180718'
                }
            
            # 步骤1: 获取数据
            self.view.show_progress("获取股票数据", 1, 4)
            raw_data = self.model.fetch_roll_yield_data(params)
            
            if raw_data is None:
                self.view.show_error("数据获取失败")
                return False
            
            self.view.show_success(f"成功获取 {len(raw_data)} 条原始数据")
            
            # 步骤2: 数据清洗
            self.view.show_progress("清洗数据", 2, 4)
            cleaned_data = self.model.clean_data(raw_data)
            
            if cleaned_data is None or cleaned_data.empty:
                self.view.show_error("数据清洗后为空")
                return False
            
            self.view.show_success(f"数据清洗完成，剩余 {len(cleaned_data)} 条有效数据")
            
            # 步骤3: 显示数据预览
            self.view.show_progress("生成数据预览", 3, 4)
            data_info = self.model.get_data_info(cleaned_data)
            self.view.show_data_preview(cleaned_data, data_info)
            
            # 步骤4: 保存数据
            self.view.show_progress("保存数据到数据库", 4, 4)
            if not self.model.save_data(cleaned_data):
                self.view.show_error("数据保存失败")
                return False
            
            self.view.show_success("数据保存成功")
            
            # 验证数据完整性
            record_count = self.model.get_data_count()
            if record_count is not None:
                self.view.show_data_summary(record_count, self.db_config.table_name)
            
            return True
            
        except Exception as e:
            logger.error(f"数据处理过程中发生错误: {e}")
            self.view.show_error(f"处理失败: {e}")
            return False
    
    def interactive_mode(self):
        """交互模式"""
        try:
            self.view.show_info("进入交互模式")
            
            # 获取用户输入的参数
            var = self.view.prompt_user_input("请输入品种代码 (默认: RB)")
            if not var:
                var = "RB"
            
            start_day = self.view.prompt_user_input("请输入开始日期 (格式: YYYYMMDD, 默认: 20180618)")
            if not start_day:
                start_day = "20180618"
            
            end_day = self.view.prompt_user_input("请输入结束日期 (格式: YYYYMMDD, 默认: 20180718)")
            if not end_day:
                end_day = "20180718"
            
            params = {
                'var': var,
                'start_day': start_day,
                'end_day': end_day
            }
            
            # 确认执行
            if self.view.confirm_action(f"确认获取 {var} 从 {start_day} 到 {end_day} 的数据吗？"):
                return self.fetch_and_process_data(params)
            else:
                self.view.show_info("操作已取消")
                return False
                
        except KeyboardInterrupt:
            self.view.show_info("用户中断操作")
            return False
        except Exception as e:
            logger.error(f"交互模式错误: {e}")
            self.view.show_error(f"交互模式错误: {e}")
            return False
    
    def run_default_task(self) -> bool:
        """运行默认任务"""
        return self.fetch_and_process_data()
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.model:
                self.model.close_connection()
            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
    
    def get_system_status(self) -> Dict[str, str]:
        """获取系统状态"""
        return {
            'database_connected': str(self.model.engine is not None),
            'setup_complete': str(self.setup_complete),
            'database_name': self.db_config.database,
            'table_name': self.db_config.table_name
        }