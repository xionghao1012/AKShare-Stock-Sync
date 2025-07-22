# -*- coding: utf-8 -*-
"""
日志工具类
提供灵活的日志配置和管理功能
"""
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from config.sync_config import SyncConfig

class LoggerUtil:
    """日志工具类"""
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name=None, log_file=None, log_level=None):
        """获取日志实例
        
        Args:
            name (str): 日志名称
            log_file (str): 日志文件路径
            log_level (str): 日志级别
        
        Returns:
            logging.Logger: 日志实例
        """
        # 使用默认名称
        logger_name = name or 'akshare_sync'
        
        # 如果已经存在该名称的logger，直接返回
        if logger_name in cls._loggers:
            return cls._loggers[logger_name]
        
        # 获取配置
        config = SyncConfig()
        
        # 确定日志文件路径
        if not log_file:
            log_dir = os.path.dirname(config.log_file)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            log_file = config.log_file
        
        # 确定日志级别
        log_level = log_level or config.log_level
        level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        log_level = level_mapping.get(log_level.upper(), logging.INFO)
        
        # 创建logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.propagate = False  # 防止日志重复输出
        
        # 定义日志格式
        log_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 添加文件处理器
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5,       # 最多备份5个文件
            encoding='utf-8'
        )
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)
        
        # 缓存logger实例
        cls._loggers[logger_name] = logger
        
        return logger

# 提供便捷的日志设置函数
def setup_logger(name=None, log_file=None, log_level=None):
    """设置日志
    
    Args:
        name (str): 日志名称
        log_file (str): 日志文件路径
        log_level (str): 日志级别
    
    Returns:
        logging.Logger: 日志实例
    """
    return LoggerUtil.get_logger(name, log_file, log_level)