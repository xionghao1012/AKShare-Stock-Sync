# -*- coding: utf-8 -*-
"""
数据库配置模块
提供数据库连接配置和连接池管理
"""

import os
import mysql.connector
from mysql.connector import pooling
from typing import Optional

class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        """初始化数据库配置"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '3306'))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'stock_data')
        self.charset = 'utf8mb4'
        
    def get_config(self) -> dict:
        """获取数据库配置字典"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset,
            'autocommit': True,
            'pool_name': 'stock_pool',
            'pool_size': 10,
            'pool_reset_session': True
        }
    
    def create_connection_pool(self) -> Optional[pooling.MySQLConnectionPool]:
        """创建数据库连接池"""
        try:
            config = self.get_config()
            pool = pooling.MySQLConnectionPool(**config)
            return pool
        except mysql.connector.Error as e:
            print(f"数据库连接池创建失败: {e}")
            return None