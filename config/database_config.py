"""
数据库配置管理
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '84694296')
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '3306')
        self.database = os.getenv('DB_NAME', 'stock')
        self.table_name = os.getenv('TABLE_NAME', 'roll_yield_bar')
        
        # 连接池配置
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '5'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '10'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    
    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        return f'mysql+mysqlconnector://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'
    
    def get_engine_config(self) -> dict:
        """获取数据库引擎配置"""
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': True,
            'echo': False
        }
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        required_fields = [self.user, self.password, self.host, self.database]
        return all(field for field in required_fields)
    
    def __str__(self) -> str:
        """字符串表示（隐藏密码）"""
        return f"DatabaseConfig(host={self.host}, database={self.database}, user={self.user})"