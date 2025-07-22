"""
同步配置管理
"""
import os
from typing import Dict, List, Any


class SyncConfig:
    """同步配置类"""
    
    def __init__(self):
        # 同步间隔配置（秒）
        self.sync_intervals = {
            'stock': 300,      # 5分钟
            'futures': 180,    # 3分钟
            'fund': 600,       # 10分钟
            'bond': 1800,      # 30分钟
            'forex': 60,       # 1分钟
            'macro': 3600,     # 1小时
            'news': 900,       # 15分钟
            'industry': 1800   # 30分钟
        }
        
        # API调用限制配置
        self.api_limits = {
            'requests_per_minute': 60,
            'delay_between_calls': 1,
            'retry_attempts': 3,
            'retry_delay': 5
        }
        
        # 数据保存策略
        self.save_strategies = {
            'default': 'replace',
            'historical': 'append',
            'realtime': 'replace'
        }
    
    def get_sync_interval(self, category: str) -> int:
        """获取同步间隔"""
        return self.sync_intervals.get(category, 300)
    
    def get_api_delay(self) -> int:
        """获取API调用延迟"""
        return self.api_limits['delay_between_calls']
    
    def get_retry_config(self) -> Dict[str, int]:
        """获取重试配置"""
        return {
            'attempts': self.api_limits['retry_attempts'],
            'delay': self.api_limits['retry_delay']
        }