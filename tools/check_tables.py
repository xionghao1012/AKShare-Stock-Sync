# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""
import mysql.connector
from config.database_config import DatabaseConfig

def check_tables():
    """检查数据库表"""
    db_config = DatabaseConfig()
    
    try:
        # 连接数据库
        conn = mysql.connector.connect(
            host=db_config.host,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        # 查看所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("数据库中的所有表:")
        print("-" * 40)
        for table in tables:
            print(f"  {table[0]}")
        
        # 检查股票数据表
        stock_data_tables = [table[0] for table in tables if 'stock' in table[0].lower() and 'data' in table[0].lower()]
        
        if stock_data_tables:
            print(f"\n可能的股票数据表:")
            for table in stock_data_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} 条记录")
                
                # 查看表结构
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"    字段: {[col[0] for col in columns]}")
        
        # 检查stock_stock_zh_a_hist表的详细结构
        print(f"\n检查stock_stock_zh_a_hist表的详细结构:")
        cursor.execute("DESCRIBE stock_stock_zh_a_hist")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]} - {col[1]}")
        
        # 查看前几条数据
        print(f"\n查看前5条数据:")
        cursor.execute("SELECT * FROM stock_stock_zh_a_hist LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {row}")
        
        # 检查是否有302132的数据
        print(f"\n检查302132 (中航成飞) 的数据:")
        try:
            # 尝试不同的字段名
            possible_fields = ['stock_code', 'code', 'symbol', '股票代码']
            for field in possible_fields:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM stock_stock_zh_a_hist WHERE {field} = '302132'")
                    count = cursor.fetchone()[0]
                    print(f"  使用字段 {field}: {count} 条记录")
                    if count > 0:
                        break
                except:
                    continue
        except Exception as e:
            print(f"  检查时出错: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_tables()