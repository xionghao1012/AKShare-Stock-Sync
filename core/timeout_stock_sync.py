# -*- coding: utf-8 -*-
"""
带超时处理的股票同步工具
解决同步过程中可能出现的卡死问题
"""
import signal
import sys
import os
import time
import threading
from contextlib import contextmanager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.smart_stock_sync import SmartStockSyncTool

class TimeoutError(Exception):
    """超时异常"""
    pass

@contextmanager
def timeout_handler(seconds):
    """超时上下文管理器"""
    def timeout_signal_handler(signum, frame):
        raise TimeoutError(f"操作超时 ({seconds}秒)")
    
    # 设置信号处理器
    old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # 恢复原来的信号处理器
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

class TimeoutStockSyncTool(SmartStockSyncTool):
    """带超时处理的股票同步工具"""
    
    def __init__(self):
        super().__init__()
        self.sync_timeout = 60  # 单只股票同步超时时间（秒）
        self.db_timeout = 30    # 数据库操作超时时间（秒）
    
    def sync_with_retry_timeout(self, stock_code, stock_name, list_date, max_retries=3):
        """带超时的重试同步"""
        for attempt in range(max_retries):
            try:
                print(f"  尝试 {attempt + 1}/{max_retries}: 正在同步 {stock_code} ({stock_name}) 从 {list_date} 开始")
                
                # 使用超时处理
                with timeout_handler(self.sync_timeout):
                    if self.syncer.sync_stock_data(stock_code, stock_name, list_date):
                        print("成功")
                        return True
                    else:
                        print("失败")
                        if attempt < max_retries - 1:
                            time.sleep(5)  # 等待5秒后重试
                            
            except TimeoutError as e:
                print(f"超时: {e}")
                if attempt < max_retries - 1:
                    print("等待10秒后重试...")
                    time.sleep(10)
                    
            except KeyboardInterrupt:
                print("\n用户中断同步")
                raise
                
            except Exception as e:
                print(f"异常: {str(e)[:50]}...")
                if attempt < max_retries - 1:
                    time.sleep(10)  # 网络异常等待更长时间
        
        return False
    
    def continue_sync_from_code_with_timeout(self, start_code, max_stocks=None):
        """带超时的继续同步"""
        if not self.syncer.connect_database():
            print("数据库连接失败")
            return
        
        try:
            print(f"准备从股票 {start_code} 开始继续同步...")
            
            # 获取所有股票列表（带超时）
            print("获取股票列表...")
            with timeout_handler(self.db_timeout):
                def _get_all_stocks(connection):
                    cursor = connection.cursor()
                    try:
                        cursor.execute("SELECT A股代码, A股简称, A股上市日期 FROM stock_stock_info ORDER BY A股代码")
                        stocks = cursor.fetchall()
                        return stocks
                    finally:
                        cursor.close()
                
                all_stocks = self.syncer.safe_executor.safe_execute(
                    _get_all_stocks, 
                    self.syncer.connection,
                    error_msg="获取股票列表失败"
                )
            
            if not all_stocks:
                print("无法获取股票列表")
                return
            
            # 找到起始位置
            start_index = 0
            for i, (code, name, list_date) in enumerate(all_stocks):
                if code >= start_code:
                    start_index = i
                    break
            
            stocks_to_sync = all_stocks[start_index:]
            if max_stocks:
                stocks_to_sync = stocks_to_sync[:max_stocks]
            
            total_count = len(stocks_to_sync)
            print(f"计划同步 {total_count} 只股票")
            
            # 加载进度
            success_count, failed_count, failed_stocks = self.load_progress()
            
            print("=" * 50)
            
            try:
                for i, (stock_code, stock_name, list_date) in enumerate(stocks_to_sync, 1):
                    print(f"[{i}/{total_count}] {stock_code} ({stock_name})")
                    
                    # 使用带超时的同步方法
                    if self.sync_with_retry_timeout(stock_code, stock_name, list_date):
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_stocks.append({
                            "code": stock_code,
                            "name": stock_name,
                            "list_date": list_date
                        })
                        print(f"  [X] 失败: {stock_code} ({stock_name})")
                    
                    # 保存进度
                    self.save_progress(stock_code, success_count, failed_count, failed_stocks)
                    
                    # 每10只股票休息一下
                    if i % 10 == 0:
                        time.sleep(3)
                        print(f"  [休息] 已处理 {i} 只股票，休息3秒...")
                    
                    # 每50只股票显示进度
                    if i % 50 == 0:
                        progress = i / total_count * 100
                        print(f"  [进度] 进度: {i}/{total_count} ({progress:.1f}%)")
                        print(f"  [统计] 成功: {success_count}, 失败: {failed_count}")
                
            except KeyboardInterrupt:
                print(f"\n[中断] 用户中断，已处理 {i} 只股票")
                print(f"[统计] 成功: {success_count}, 失败: {failed_count}")
                self.save_progress(stock_code, success_count, failed_count, failed_stocks)
                return
            
            print("\n" + "=" * 50)
            print(f"[完成] 同步完成 - 成功: {success_count}, 失败: {failed_count}")
            
            if failed_stocks:
                print(f"\n[失败] 失败的股票 ({len(failed_stocks)} 只):")
                for stock in failed_stocks:
                    print(f"  {stock['code']} ({stock['name']})")
        
        finally:
            self.syncer.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='带超时处理的股票数据同步工具')
    parser.add_argument('action', choices=['continue', 'retry'], help='操作类型')
    parser.add_argument('start_code', nargs='?', help='起始股票代码')
    parser.add_argument('--max-stocks', type=int, help='最大同步股票数量')
    parser.add_argument('--timeout', type=int, default=60, help='单只股票同步超时时间（秒）')
    
    args = parser.parse_args()
    
    # 检查是否在Windows上（Windows不支持signal.SIGALRM）
    if os.name == 'nt':
        print("警告: Windows系统不支持信号超时，将使用普通同步模式")
        # 在Windows上使用原来的工具
        tool = SmartStockSyncTool()
        if args.action == 'continue' and args.start_code:
            tool.continue_sync_from_code(args.start_code, args.max_stocks)
        elif args.action == 'retry':
            tool.retry_failed_stocks()
        return
    
    # Unix/Linux系统使用超时版本
    tool = TimeoutStockSyncTool()
    tool.sync_timeout = args.timeout
    
    if args.action == 'continue' and args.start_code:
        # 确认开始同步
        response = input("确认开始同步吗？(y/N): ")
        if response.lower() != 'y':
            print("取消同步")
            return
        
        tool.continue_sync_from_code_with_timeout(args.start_code, args.max_stocks)
    elif args.action == 'retry':
        tool.retry_failed_stocks()
    else:
        print("请提供起始股票代码")

if __name__ == "__main__":
    main()