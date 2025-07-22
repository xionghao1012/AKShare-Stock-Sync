# -*- coding: utf-8 -*-
"""
检查302系列股票的同步状态
"""
import mysql.connector
from config.database_config import DatabaseConfig

def check_302_stocks():
    """检查302系列股票"""
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
        
        # 查询所有302开头的股票
        cursor.execute("""
            SELECT A股代码, A股简称, A股上市日期 
            FROM stock_stock_info 
            WHERE A股代码 LIKE '302%' 
            ORDER BY A股代码
        """)
        
        stocks_302 = cursor.fetchall()
        
        print(f"数据库中302系列股票总数: {len(stocks_302)}")
        print("\n302系列股票列表:")
        print("-" * 60)
        
        for i, (code, name, list_date) in enumerate(stocks_302, 1):
            print(f"{i:3d}. {code} ({name}) - 上市日期: {list_date}")
        
        # 检查哪些已经有数据
        print("\n检查数据同步状态...")
        print("-" * 60)
        
        synced_count = 0
        unsynced_stocks = []
        
        for code, name, list_date in stocks_302:
            # 检查是否已有数据
            cursor.execute(f"SELECT COUNT(*) FROM stock_stock_zh_a_hist WHERE 股票代码 = %s", (code,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                synced_count += 1
                print(f"✅ {code} ({name}) - 已同步 {count} 条记录")
            else:
                unsynced_stocks.append((code, name, list_date))
                print(f"❌ {code} ({name}) - 未同步")
        
        print(f"\n同步状态总结:")
        print(f"已同步: {synced_count} 只")
        print(f"未同步: {len(unsynced_stocks)} 只")
        
        if unsynced_stocks:
            print(f"\n需要同步的股票:")
            for code, name, list_date in unsynced_stocks:
                print(f"  {code} ({name}) - {list_date}")
        
        cursor.close()
        conn.close()
        
        return unsynced_stocks
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return []

if __name__ == "__main__":
    check_302_stocks()