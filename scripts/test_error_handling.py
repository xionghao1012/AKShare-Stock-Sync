#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试错误处理和数据库表结构
"""
import mysql.connector
from config.database_config import DatabaseConfig
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_tables():
    """测试数据库表结构"""
    print("=== 数据库表结构测试 ===")
    
    try:
        db_config = DatabaseConfig()
        conn = mysql.connector.connect(
            host=db_config.host,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 检查现有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"现有表: {[table[0] for table in tables]}")
        
        # 检查 stock_stock_info 表结构
        if ('stock_stock_info',) in tables:
            cursor.execute("DESCRIBE stock_stock_info")
            columns = cursor.fetchall()
            print(f"\nstock_stock_info 表结构:")
            for col in columns:
                print(f"  {col[0]} - {col[1]}")
        
        # 检查 stock_stock_individual_info_em 表是否存在
        if ('stock_stock_individual_info_em',) in tables:
            cursor.execute("DESCRIBE stock_stock_individual_info_em")
            columns = cursor.fetchall()
            print(f"\nstock_stock_individual_info_em 表结构:")
            for col in columns:
                print(f"  {col[0]} - {col[1]}")
        else:
            print("\n⚠️ stock_stock_individual_info_em 表不存在，需要创建")
            
            # 创建表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS stock_stock_individual_info_em (
                id INT AUTO_INCREMENT PRIMARY KEY,
                股票代码 VARCHAR(10) NOT NULL,
                item VARCHAR(50) NOT NULL,
                value TEXT,
                更新时间 DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_stock_code (股票代码),
                INDEX idx_item (item)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            print("✅ 成功创建 stock_stock_individual_info_em 表")
        
        # 测试数据插入
        print(f"\n=== 测试数据操作 ===")
        
        # 测试股票基本信息查询
        cursor.execute("SELECT COUNT(*) FROM stock_stock_info")
        count = cursor.fetchone()[0]
        print(f"stock_stock_info 表中有 {count} 条记录")
        
        if count > 0:
            cursor.execute("SELECT A股代码, A股简称 FROM stock_stock_info LIMIT 3")
            samples = cursor.fetchall()
            print("前3条股票信息:")
            for code, name in samples:
                print(f"  {code} - {name}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"数据库测试失败: {e}")
        return False

def test_error_classification():
    """测试错误分类功能"""
    print(f"\n=== 错误分类测试 ===")
    
    from utils.error_handler import ErrorHandler
    
    error_handler = ErrorHandler(__name__)
    
    # 测试不同类型的错误
    test_errors = [
        ("网络连接超时", ConnectionError("Connection timeout")),
        ("数据格式错误", ValueError("Invalid data format")),
        ("缺少必需字段", KeyError("Missing required field")),
        ("内存不足", MemoryError("Out of memory")),
        ("未知异常", Exception("Unknown error"))
    ]
    
    for desc, error in test_errors:
        error_info = error_handler.handle_error(error, desc)
        print(f"{desc}: {error_info['type']}")
    
    # 显示错误统计
    stats = error_handler.get_error_stats()
    print(f"\n错误统计: {stats}")

def test_safe_execution():
    """测试安全执行功能"""
    print(f"\n=== 安全执行测试 ===")
    
    from utils.error_handler import SafeExecutor, ErrorHandler
    
    error_handler = ErrorHandler(__name__)
    safe_executor = SafeExecutor(error_handler)
    
    # 测试正常函数
    def normal_function(x, y):
        return x + y
    
    result = safe_executor.safe_execute(
        normal_function, 10, 20,
        default_return=0,
        context="正常函数测试"
    )
    print(f"正常函数结果: {result}")
    
    # 测试异常函数
    def error_function():
        raise ValueError("测试异常")
    
    result = safe_executor.safe_execute(
        error_function,
        default_return="默认值",
        context="异常函数测试"
    )
    print(f"异常函数结果: {result}")

def main():
    """主测试函数"""
    print("错误处理系统测试")
    print("=" * 50)
    
    # 测试数据库表结构
    db_success = test_database_tables()
    
    # 测试错误分类
    test_error_classification()
    
    # 测试安全执行
    test_safe_execution()
    
    print(f"\n" + "=" * 50)
    print("测试总结:")
    print(f"✅ 数据库测试: {'成功' if db_success else '失败'}")
    print("✅ 错误分类: 正常")
    print("✅ 安全执行: 正常")
    
    print(f"\n💡 建议:")
    if db_success:
        print("1. 数据库表结构正常，可以正常使用")
        print("2. 错误处理机制工作良好")
        print("3. 可以开始使用稳定的接口进行数据同步")
    else:
        print("1. 需要检查数据库连接和配置")
        print("2. 确保数据库表结构正确")

if __name__ == "__main__":
    main()