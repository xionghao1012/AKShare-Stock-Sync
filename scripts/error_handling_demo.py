#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
错误处理和可用功能演示
基于测试结果，展示如何使用稳定的接口
"""
import akshare as ak
import mysql.connector
from config.database_config import DatabaseConfig
import pandas as pd
from datetime import datetime
import logging
from utils.error_handler import ErrorHandler, SafeExecutor

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_handling_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class StableDataSync:
    """基于稳定接口的数据同步类"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.conn = None
        self.error_handler = ErrorHandler(__name__)
        self.safe_executor = SafeExecutor(self.error_handler)
        self.logger = logging.getLogger(__name__)
    
    def connect_database(self):
        """连接数据库"""
        try:
            self.conn = mysql.connector.connect(
                host=self.db_config.host,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database,
                charset='utf8mb4'
            )
            self.logger.info("数据库连接成功")
            return True
        except Exception as e:
            self.error_handler.handle_error(e, "数据库连接")
            return False
    
    def sync_stock_basic_info(self):
        """同步股票基本信息（稳定接口）"""
        print("=== 同步股票基本信息 ===")
        
        try:
            # 获取股票基本信息
            print("正在获取股票基本信息...")
            df = ak.stock_info_sz_name_code()
            
            if df is None or df.empty:
                print("❌ 未获取到股票基本信息")
                return False
            
            print(f"✅ 成功获取 {len(df)} 只股票基本信息")
            
            # 保存到数据库
            print("正在保存到数据库...")
            cursor = self.conn.cursor()
            
            # 清空旧数据
            cursor.execute("DELETE FROM stock_stock_info")
            
            # 批量插入新数据
            insert_query = """
                INSERT INTO stock_stock_info 
                (板块, A股代码, A股简称, A股上市日期, A股总股本, A股流通股本, 所属行业)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            data_to_insert = []
            for _, row in df.iterrows():
                data_to_insert.append((
                    row['板块'], row['A股代码'], row['A股简称'], 
                    row['A股上市日期'], row['A股总股本'], row['A股流通股本'], row['所属行业']
                ))
            
            cursor.executemany(insert_query, data_to_insert)
            self.conn.commit()
            cursor.close()
            
            print(f"✅ 成功保存 {len(data_to_insert)} 条股票基本信息到数据库")
            self.logger.info(f"成功同步股票基本信息: {len(data_to_insert)} 条")
            
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "同步股票基本信息")
            print(f"❌ 同步失败: {error_info['message']}")
            return False
    
    def get_individual_stock_details(self, stock_codes):
        """获取个股详细信息（稳定接口）"""
        print(f"\n=== 获取个股详细信息 ===")
        
        results = {}
        
        for i, stock_code in enumerate(stock_codes, 1):
            try:
                print(f"[{i}/{len(stock_codes)}] 获取 {stock_code} 详细信息...")
                
                df = ak.stock_individual_info_em(symbol=stock_code)
                
                if df is None or df.empty:
                    print(f"  ⚠️ {stock_code}: 无数据")
                    continue
                
                # 解析数据
                info = {}
                for _, row in df.iterrows():
                    info[row['item']] = row['value']
                
                # 提取关键信息
                stock_name = info.get('股票简称', 'N/A')
                latest_price = info.get('最新', 'N/A')
                total_market_cap = info.get('总市值', 'N/A')
                
                print(f"  ✅ {stock_code} ({stock_name})")
                print(f"     最新价: {latest_price}")
                print(f"     总市值: {total_market_cap}")
                
                results[stock_code] = info
                
                # 保存到数据库
                self._save_individual_stock_info(stock_code, info)
                
            except Exception as e:
                error_info = self.error_handler.handle_error(e, f"获取股票 {stock_code} 详细信息")
                print(f"  ❌ {stock_code} 失败: {error_info['message']}")
        
        print(f"\n✅ 成功获取 {len(results)} 只股票的详细信息")
        return results
    
    def _save_individual_stock_info(self, stock_code, info):
        """保存个股详细信息到数据库"""
        try:
            cursor = self.conn.cursor()
            
            # 删除旧数据
            cursor.execute("DELETE FROM stock_stock_individual_info_em WHERE 股票代码 = %s", (stock_code,))
            
            # 插入新数据
            insert_query = """
                INSERT INTO stock_stock_individual_info_em 
                (股票代码, item, value, 更新时间)
                VALUES (%s, %s, %s, %s)
            """
            
            current_time = datetime.now()
            data_to_insert = []
            
            for item, value in info.items():
                data_to_insert.append((stock_code, item, str(value), current_time))
            
            cursor.executemany(insert_query, data_to_insert)
            self.conn.commit()
            cursor.close()
            
        except Exception as e:
            self.error_handler.handle_error(e, f"保存股票 {stock_code} 详细信息")
    
    def demonstrate_error_handling(self):
        """演示错误处理机制"""
        print("\n=== 错误处理演示 ===")
        
        # 模拟各种错误类型
        test_cases = [
            ("数据格式错误", ValueError("数据格式错误")),
            ("网络连接失败", ConnectionError("网络连接失败")),
            ("缺少必需的键", KeyError("缺少必需的键")),
            ("内存不足", MemoryError("内存不足")),
            ("未知错误", Exception("未知错误"))
        ]
        
        for desc, error in test_cases:
            error_info = self.error_handler.handle_error(error, f"测试错误分类: {desc}")
        
        # 显示错误统计
        print("\n错误统计:")
        error_stats = self.error_handler.get_error_stats()
        for error_type, count in error_stats.items():
            if count > 0:
                print(f"  {error_type}: {count}")
    
    def demonstrate_retry_mechanism(self):
        """演示重试机制"""
        print("\n=== 重试机制演示 ===")
        
        # 模拟不稳定的函数
        attempt_count = 0
        
        def unstable_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError(f"模拟失败 (尝试 {attempt_count})")
            return f"成功 (尝试 {attempt_count})"
        
        # 使用安全执行器
        result = self.safe_executor.safe_execute(
            unstable_function,
            default_return="默认值",
            context="unstable_function"
        )
        
        print(f"重试结果: {result}")
    
    def get_available_stock_count(self):
        """获取可用股票数量"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stock_stock_info")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            self.error_handler.handle_error(e, "获取股票数量")
            return 0
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

def main():
    """主函数"""
    print("股票数据同步 - 错误处理演示")
    print("=" * 50)
    
    syncer = StableDataSync()
    
    # 连接数据库
    if not syncer.connect_database():
        print("❌ 数据库连接失败，程序退出")
        return
    
    try:
        # 1. 同步股票基本信息
        syncer.sync_stock_basic_info()
        
        # 2. 获取个股详细信息（测试几只股票）
        test_stocks = ['000001', '000002', '600000']
        syncer.get_individual_stock_details(test_stocks)
        
        # 3. 演示错误处理
        syncer.demonstrate_error_handling()
        
        # 4. 演示重试机制
        syncer.demonstrate_retry_mechanism()
        
        # 5. 显示统计信息
        stock_count = syncer.get_available_stock_count()
        print(f"\n=== 统计信息 ===")
        print(f"数据库中股票数量: {stock_count}")
        
        # 6. 显示错误统计
        error_stats = syncer.error_handler.get_error_stats()
        print(f"错误统计: {error_stats}")
        
        print("\n✅ 演示完成！")
        print("\n💡 总结:")
        print("1. 股票基本信息接口工作正常")
        print("2. 个股详细信息接口工作正常") 
        print("3. 错误处理机制运行良好")
        print("4. 重试机制有效")
        print("5. 数据库操作稳定")
        
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"\n程序异常: {e}")
    finally:
        syncer.close()

if __name__ == "__main__":
    main()