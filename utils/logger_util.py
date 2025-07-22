"""
日志工具类
"""
import logging
import os
from datetime import datetime


def setup_logger(log_level: str = None, log_file: str = None) -> logging.Logger:
    """设置日志配置"""
    
    # 获取日志级别
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # 获取日志文件名
    if log_file is None:
        log_file = os.getenv('LOG_FILE', 'stock_data.log')
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 获取根日志器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)


class LoggerMixin:
    """日志混入类"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志器"""
        return logging.getLogger(self.__class__.__name__)