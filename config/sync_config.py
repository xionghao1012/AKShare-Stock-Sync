# -*- coding: utf-8 -*-
"""
同步配置模块
提供同步相关的配置参数
"""

import os

class SyncConfig:
    """同步配置类"""
    
    def __init__(self):
        """初始化同步配置"""
        # 网络配置
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '1'))
        
        # 同步配置
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.sync_interval = int(os.getenv('SYNC_INTERVAL', '3600'))  # 秒
        self.enable_gentle_mode = os.getenv('ENABLE_GENTLE_MODE', 'true').lower() == 'true'
        
        # 日志配置
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'logs/stock_sync.log')
        
        # 数据库配置
        self.enable_optimization = os.getenv('ENABLE_OPTIMIZATION', 'true').lower() == 'true'
        self.optimize_interval = int(os.getenv('OPTIMIZE_INTERVAL', '86400'))  # 秒
        
    def get_config(self) -> dict:
        """获取完整配置字典"""
        return {
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'batch_size': self.batch_size,
            'sync_interval': self.sync_interval,
            'enable_gentle_mode': self.enable_gentle_mode,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'enable_optimization': self.enable_optimization,
            'optimize_interval': self.optimize_interval
        }