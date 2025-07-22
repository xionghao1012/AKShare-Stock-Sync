# -*- coding: utf-8 -*-
"""
获取302系列股票列表
"""
import akshare as ak
import pandas as pd

def get_302_stocks():
    """获取302系列股票"""
    try:
        print("正在获取股票列表...")
        
        # 获取所有A股股票信息
        stock_info = ak.stock_info_a_code_name()
        
        # 筛选302开头的股票
        stocks_302 = stock_info[stock_info['code'].str.startswith('302')]
        
        print(f"找到 {len(stocks_302)} 只302系列股票:")
        print("-" * 60)
        
        for i, (_, row) in enumerate(stocks_302.iterrows(), 1):
            print(f"{i:3d}. {row['code']} - {row['name']}")
        
        return stocks_302
        
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        return pd.DataFrame()

def check_sync_status(stocks_302):
    """检查同步状态"""
    import mysql.connector
    from config.database_config import DatabaseConfig
    
    if stocks_302.empty:
        return
    
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
        
        print(f"\n检查同步状态:")
        print("-" * 60)
        
        synced_count = 0
        unsynced_stocks = []
        
        for _, row in stocks_302.iterrows():
            code = row['code']
            name = row['name']
            
            # 检查是否已有数据
            cursor.execute(f"SELECT COUNT(*) FROM stock_stock_zh_a_hist WHERE 股票代码 = %s", (code,))
            count = cursor.fetchone()[0]
            
            if count > 0:
                synced_count += 1
                print(f"✅ {code} ({name}) - 已同步 {count} 条记录")
            else:
                unsynced_stocks.append((code, name))
                print(f"❌ {code} ({name}) - 未同步")
        
        print(f"\n同步状态总结:")
        print(f"已同步: {synced_count} 只")
        print(f"未同步: {len(unsynced_stocks)} 只")
        
        if unsynced_stocks:
            print(f"\n需要同步的股票:")
            for code, name in unsynced_stocks:
                print(f"  {code} ({name})")
            
            return unsynced_stocks
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return []

if __name__ == "__main__":
    stocks_302 = get_302_stocks()
    if not stocks_302.empty:
        unsynced = check_sync_status(stocks_302)
        
        if unsynced:
            print(f"\n发现 {len(unsynced)} 只未同步的302系列股票")
        else:
            print(f"\n🎉 所有302系列股票都已同步完成！")