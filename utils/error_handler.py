# -*- coding: utf-8 -*-
"""
错误处理工具类
提供统一的错误处理和异常管理功能
"""
import logging
import traceback
from typing import Dict, Any, Optional

class ErrorHandler:
    """错误处理类"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """初始化错误处理器
        
        Args:
            logger: 日志记录器实例
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理异常并返回标准化错误信息
        
        Args:
            error: 捕获的异常
            context: 错误发生时的上下文信息
        
        Returns:
            包含错误信息的字典
        """
        # 记录完整异常堆栈
        error_traceback = traceback.format_exc()
        self.logger.error(f"发生错误: {str(error)}\n{error_traceback}")
        
        # 构建标准化错误响应
        error_response = {
            'success': False,
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'timestamp': self._get_current_timestamp()
        }
        
        # 添加上下文信息（如果提供）
        if context:
            error_response['context'] = context
        
        return error_response
    
    def handle_api_error(self, response: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理API调用错误
        
        Args:
            response: API响应
            context: 错误发生时的上下文信息
        
        Returns:
            包含错误信息的字典
        """
        error_msg = response.get('msg', 'API调用失败')
        error_code = response.get('code', -1)
        
        self.logger.error(f"API错误: 代码 {error_code}, 消息: {error_msg}")
        
        error_response = {
            'success': False,
            'error_type': 'APIError',
            'error_code': error_code,
            'error_message': error_msg,
            'timestamp': self._get_current_timestamp()
        }
        
        if context:
            error_response['context'] = context
        
        return error_response
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳
        
        Returns:
            格式化的时间戳字符串
        """
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def format_error_message(error: Exception) -> str:
        """格式化错误消息
        
        Args:
            error: 异常对象
        
        Returns:
            格式化的错误消息字符串
        """
        return f"{error.__class__.__name__}: {str(error)}"

# 创建全局错误处理器实例
global_error_handler = ErrorHandler()

def handle_exception(context: Optional[Dict[str, Any]] = None):
    """异常处理装饰器
    
    Args:
        context: 错误上下文信息
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return global_error_handler.handle_error(e, context)
        return wrapper
    return decorator