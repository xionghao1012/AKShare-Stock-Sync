# -*- coding: utf-8 -*-
"""
智能股票同步脚本 - 支持断点续传和网络错误处理
"""
import sys
import time
import json
import os
from datetime import datetime
from batch_sync_stocks import BatchStockSync

class SmartStockSync:
    def __init__(self):
        self.syncer = BatchStockSync()
        self.progress_file = "sync_progress.json"
        self.failed_stocks_file = "failed_stocks.json"
        
    def save_progress(self, current_stock, success_count, failed_count, failed_stocks):
        """保存同步进度"""
        progress = {
            "current_stock": current_stock,
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_stocks": failed_stocks,
            "last_update": datetime.now().isoformat()
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def load_progress(self):
        """加载同步进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def sync_with_retry(self, stock_code, stock_name, list_date, max_retries=3):
        """带重试机制的同步"""
        for attempt in range(max_retries):
            try:
                print(f"  尝试 {attempt + 1}/{max_retries}: ", end="")
                if self.syncer.sync_single_stock(stock_code, stock_name, list_date):
                    print("成功")
                    return True
                else:
                    print("失败")
                    if attempt < max_retries - 1:
                        time.sleep(5)  # 等待5秒后重试
            except KeyboardInterrupt:
                print("\n用户中断同步")
                raise
            except Exception as e:
                print(f"异常: {str(e)[:50]}...")
                if attempt < max_retries - 1:
                    time.sleep(10)  # 网络异常等待更长时间
        
        return False
    
    def continue_sync_from_code(self, start_code, max_stocks=None):
        """从指定股票代码开始继续同步"""
        if not self.syncer.connect_database():
            print("数据库连接失败")
            return
        
        try:
            # 获取所有股票列表
            def _get_all_stocks(connection):
                cursor = connection.cursor()
                try:
                    cursor.execute("SELECT A股代码, A股简称, A股上市日期 FROM stock_stock_info ORDER BY A股代码")
                    stocks = cursor.fetchall()
                    return stocks
                finally:
                    cursor.close()
            
            all_stocks = self.syncer.safe_executor.safe_execute(
                _get_all_stocks, self.syncer.conn,
                default_return=[],
                context="获取所有股票列表"
            )
            
            if not all_stocks:
                print("获取股票列表失败")
                return
            
            # 找到起始位置
            start_index = -1
            for i, (stock_code, stock_name, list_date) in enumerate(all_stocks):
                if stock_code == start_code:
                    start_index = i
                    break
            
            if start_index == -1:
                print(f"未找到股票代码: {start_code}")
                return
            
            # 从起始位置开始同步
            remaining_stocks = all_stocks[start_index:]
            if max_stocks:
                remaining_stocks = remaining_stocks[:max_stocks]
            
            total_count = len(remaining_stocks)
            
            print(f"从股票 {start_code} 开始继续同步")
            print(f"计划同步 {total_count} 只股票")
            print("=" * 50)
            
            success_count = 0
            failed_count = 0
            failed_stocks = []
            
            for i, (stock_code, stock_name, list_date) in enumerate(remaining_stocks, 1):
                print(f"[{i}/{total_count}] {stock_code} ({stock_name})")
                
                try:
                    if self.sync_with_retry(stock_code, stock_name, list_date):
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
                    break
            
            print("\n" + "=" * 50)
            print(f"[完成] 同步完成 - 成功: {success_count}, 失败: {failed_count}")
            
            if failed_stocks:
                print(f"\n[失败] 失败的股票 ({len(failed_stocks)} 只):")
                for stock in failed_stocks:
                    print(f"  {stock['code']} ({stock['name']})")
                
                # 保存失败的股票列表
                with open(self.failed_stocks_file, 'w', encoding='utf-8') as f:
                    json.dump(failed_stocks, f, ensure_ascii=False, indent=2)
                print(f"\n失败的股票已保存到: {self.failed_stocks_file}")
            
        finally:
            self.syncer.close()
    
    def retry_failed_stocks(self):
        """重试失败的股票"""
        if not os.path.exists(self.failed_stocks_file):
            print("没有找到失败的股票记录")
            return
        
        try:
            with open(self.failed_stocks_file, 'r', encoding='utf-8') as f:
                failed_stocks = json.load(f)
        except:
            print("读取失败股票记录出错")
            return
        
        if not failed_stocks:
            print("没有失败的股票需要重试")
            return
        
        if not self.syncer.connect_database():
            print("数据库连接失败")
            return
        
        print(f"开始重试 {len(failed_stocks)} 只失败的股票")
        print("=" * 50)
        
        success_count = 0
        still_failed = []
        
        try:
            for i, stock in enumerate(failed_stocks, 1):
                stock_code = stock['code']
                stock_name = stock['name']
                list_date = stock['list_date']
                
                print(f"[{i}/{len(failed_stocks)}] 重试 {stock_code} ({stock_name})")
                
                if self.sync_with_retry(stock_code, stock_name, list_date):
                    success_count += 1
                    print(f"  [成功] 重试成功")
                else:
                    still_failed.append(stock)
                    print(f"  [失败] 重试仍然失败")
                
                # 每5只股票休息一下
                if i % 5 == 0:
                    time.sleep(5)
                    print(f"  [休息] 已重试 {i} 只股票，休息5秒...")
        
        except KeyboardInterrupt:
            print(f"\n[中断] 用户中断重试")
        
        finally:
            self.syncer.close()
        
        print("\n" + "=" * 50)
        print(f"[完成] 重试完成 - 成功: {success_count}, 仍然失败: {len(still_failed)}")
        
        if still_failed:
            # 更新失败股票列表
            with open(self.failed_stocks_file, 'w', encoding='utf-8') as f:
                json.dump(still_failed, f, ensure_ascii=False, indent=2)
            print(f"仍然失败的股票已更新到: {self.failed_stocks_file}")
        else:
            # 删除失败股票文件
            os.remove(self.failed_stocks_file)
            print("[完成] 所有股票都重试成功了！")

def main():
    sync_tool = SmartStockSync()
    
    if len(sys.argv) < 2:
        print("智能股票同步工具")
        print("用法:")
        print("  python smart_stock_sync.py continue <起始股票代码> [最大数量]")
        print("  python smart_stock_sync.py retry")
        print("  python smart_stock_sync.py status")
        print()
        print("例如:")
        print("  python smart_stock_sync.py continue 000786")
        print("  python smart_stock_sync.py continue 000786 100")
        print("  python smart_stock_sync.py retry")
        return
    
    command = sys.argv[1]
    
    if command == "continue":
        if len(sys.argv) < 3:
            print("请指定起始股票代码")
            return
        
        start_code = sys.argv[2]
        max_stocks = None
        
        if len(sys.argv) >= 4:
            try:
                max_stocks = int(sys.argv[3])
            except ValueError:
                print("最大数量必须是数字")
                return
        
        print(f"准备从股票 {start_code} 开始继续同步...")
        if max_stocks:
            print(f"最多同步 {max_stocks} 只股票")
        
        confirm = input("确认开始同步吗？(y/N): ")
        if confirm.lower() not in ['y', 'yes', '是']:
            print("操作已取消")
            return
        
        sync_tool.continue_sync_from_code(start_code, max_stocks)
    
    elif command == "retry":
        print("准备重试失败的股票...")
        confirm = input("确认开始重试吗？(y/N): ")
        if confirm.lower() not in ['y', 'yes', '是']:
            print("操作已取消")
            return
        
        sync_tool.retry_failed_stocks()
    
    elif command == "status":
        progress = sync_tool.load_progress()
        if progress:
            print("同步进度:")
            print(f"  当前股票: {progress.get('current_stock', 'N/A')}")
            print(f"  成功数量: {progress.get('success_count', 0)}")
            print(f"  失败数量: {progress.get('failed_count', 0)}")
            print(f"  最后更新: {progress.get('last_update', 'N/A')}")
        else:
            print("没有找到同步进度记录")
    
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()