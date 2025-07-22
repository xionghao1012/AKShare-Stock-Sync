# -*- coding: utf-8 -*-
"""
错误处理工具类 - 提供统一的错误处理和重试机制
"""
import time
import logging
import traceback
from functools import wraps
from typing import Optional, Callable, Any, Dict, List
from enum import Enum
import requests.exceptions
import mysql.connector.errors
from sqlalchemy.exc import SQLAlchemyError


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = "网络错误"
    DATABASE_ERROR = "数据库错误"
    API_ERROR = "API错误"
    DATA_ERROR = "数据错误"
    SYSTEM_ERROR = "系统错误"
    UNKNOWN_ERROR = "未知错误"


class RetryConfig:
    """重试配置类"""
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff


class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
        self.error_stats = {
            ErrorType.NETWORK_ERROR: 0,
            ErrorType.DATABASE_ERROR: 0,
            ErrorType.API_ERROR: 0,
            ErrorType.DATA_ERROR: 0,
            ErrorType.SYSTEM_ERROR: 0,
            ErrorType.UNKNOWN_ERROR: 0
        }
    
    def classify_error(self, error: Exception) -> ErrorType:
        """分类错误类型"""
        if isinstance(error, (requests.exceptions.RequestException, 
                            requests.exceptions.ConnectionError,
                            requests.exceptions.Timeout,
                            requests.exceptions.HTTPError)):
            return ErrorType.NETWORK_ERROR
        
        elif isinstance(error, (mysql.connector.errors.Error,
                              SQLAlchemyError)):
            return ErrorType.DATABASE_ERROR
        
        elif isinstance(error, (ValueError, TypeError, KeyError)):
            return ErrorType.DATA_ERROR
        
        elif "akshare" in str(error).lower() or "api" in str(error).lower():
            return ErrorType.API_ERROR
        
        elif isinstance(error, (OSError, IOError, MemoryError)):
            return ErrorType.SYSTEM_ERROR
        
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def handle_error(self, error: Exception, context: str = "", 
                    log_traceback: bool = True) -> Dict[str, Any]:
        """处理错误并返回错误信息"""
        error_type = self.classify_error(error)
        self.error_stats[error_type] += 1
        
        error_info = {
            'type': error_type.value,
            'message': str(error),
            'context': context,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'recoverable': self._is_recoverable(error_type)
        }
        
        # 记录日志
        log_message = f"[{error_type.value}] {context}: {str(error)}"
        
        if error_type in [ErrorType.SYSTEM_ERROR, ErrorType.UNKNOWN_ERROR]:
            self.logger.error(log_message)
            if log_traceback:
                self.logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        elif error_type == ErrorType.DATABASE_ERROR:
            self.logger.error(log_message)
        elif error_type in [ErrorType.NETWORK_ERROR, ErrorType.API_ERROR]:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        return error_info
    
    def _is_recoverable(self, error_type: ErrorType) -> bool:
        """判断错误是否可恢复"""
        recoverable_errors = [
            ErrorType.NETWORK_ERROR,
            ErrorType.API_ERROR
        ]
        return error_type in recoverable_errors
    
    def get_error_stats(self) -> Dict[str, int]:
        """获取错误统计"""
        return {error_type.value: count for error_type, count in self.error_stats.items()}
    
    def reset_stats(self):
        """重置错误统计"""
        for error_type in self.error_stats:
            self.error_stats[error_type] = 0


def retry_on_error(retry_config: RetryConfig = None, 
                  error_handler: ErrorHandler = None):
    """重试装饰器"""
    if retry_config is None:
        retry_config = RetryConfig()
    
    if error_handler is None:
        error_handler = ErrorHandler()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    last_error = e
                    error_info = error_handler.handle_error(
                        e, 
                        context=f"执行 {func.__name__} (尝试 {attempt + 1}/{retry_config.max_retries + 1})",
                        log_traceback=(attempt == retry_config.max_retries)
                    )
                    
                    # 如果是最后一次尝试或错误不可恢复，直接抛出
                    if attempt == retry_config.max_retries or not error_info['recoverable']:
                        break
                    
                    # 等待后重试
                    delay = retry_config.delay * (retry_config.backoff ** attempt)
                    error_handler.logger.info(f"等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
            
            # 所有重试都失败，抛出最后的错误
            raise last_error
        
        return wrapper
    return decorator


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_dataframe(df, min_rows: int = 1, required_columns: List[str] = None) -> bool:
        """验证DataFrame"""
        if df is None:
            raise ValueError("DataFrame 不能为 None")
        
        if df.empty:
            raise ValueError("DataFrame 不能为空")
        
        if len(df) < min_rows:
            raise ValueError(f"DataFrame 行数不足，需要至少 {min_rows} 行，实际 {len(df)} 行")
        
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise ValueError(f"DataFrame 缺少必需的列: {missing_columns}")
        
        return True
    
    @staticmethod
    def validate_stock_code(stock_code: str) -> bool:
        """验证股票代码格式"""
        if not stock_code:
            raise ValueError("股票代码不能为空")
        
        if not isinstance(stock_code, str):
            raise ValueError("股票代码必须是字符串")
        
        if len(stock_code) != 6:
            raise ValueError("股票代码必须是6位数字")
        
        if not stock_code.isdigit():
            raise ValueError("股票代码必须是纯数字")
        
        return True
    
    @staticmethod
    def validate_date_format(date_str: str, format_str: str = '%Y%m%d') -> bool:
        """验证日期格式"""
        if not date_str:
            raise ValueError("日期不能为空")
        
        try:
            time.strptime(date_str, format_str)
            return True
        except ValueError:
            raise ValueError(f"日期格式错误，应为 {format_str} 格式")


class SafeExecutor:
    """安全执行器 - 提供安全的函数执行环境"""
    
    def __init__(self, error_handler: ErrorHandler = None):
        self.error_handler = error_handler or ErrorHandler()
    
    def safe_execute(self, func: Callable, *args, 
                    default_return=None, context: str = "", **kwargs) -> Any:
        """安全执行函数"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.error_handler.handle_error(e, context)
            return default_return
    
    def safe_database_operation(self, operation: Callable, 
                              connection, *args, **kwargs) -> bool:
        """安全执行数据库操作"""
        try:
            result = operation(connection, *args, **kwargs)
            if hasattr(connection, 'commit'):
                connection.commit()
            return True
        except Exception as e:
            self.error_handler.handle_error(e, "数据库操作")
            if hasattr(connection, 'rollback'):
                try:
                    connection.rollback()
                except:
                    pass
            return False
    
    def safe_api_call(self, api_func: Callable, *args, 
                     retry_config: RetryConfig = None, **kwargs) -> Optional[Any]:
        """安全执行API调用"""
        if retry_config is None:
            retry_config = RetryConfig(max_retries=3, delay=2.0)
        
        @retry_on_error(retry_config, self.error_handler)
        def _api_call():
            return api_func(*args, **kwargs)
        
        try:
            return _api_call()
        except Exception as e:
            self.error_handler.handle_error(e, f"API调用 {api_func.__name__}")
            return None


# 预定义的重试配置
NETWORK_RETRY_CONFIG = RetryConfig(max_retries=5, delay=2.0, backoff=1.5)
DATABASE_RETRY_CONFIG = RetryConfig(max_retries=3, delay=1.0, backoff=2.0)
API_RETRY_CONFIG = RetryConfig(max_retries=3, delay=3.0, backoff=1.5)