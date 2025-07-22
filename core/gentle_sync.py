# -*- coding: utf-8 -*-
"""
温和的股票同步工具
添加更多的检查点和恢复机制，避免卡死
"""
import sys
import os
import time
import json
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.smart_stock_sync import SmartStockSync

class GentleStockSyncTool(SmartStockSync):
    """温和的股票同步工具"""
    
    def __init__(self):
        super().__init__()
        self.heartbeat_file = "sync_heartbeat.json"
        self.max_no_progress_time = 300  # 5分钟没有进展就认为卡死
        
    def update_heartbeat(self, stock_code, message=""):
        """更新心跳文件"""
        heartbeat_data = {
            "timestamp": datetime.now().isoformat(),
            "stock_code": stock_code,
            "message": message,
            "pid": os.getpid()
        }
        
        try:
            with open(self.heartbeat_file, 'w', encoding='utf-8') as f:
                json.dump(heartbeat_data, f, ensure_ascii=False, indent=2)
        except:
            pass  # 忽略心跳文件写入错误
    
    def check_if_stuck(self):
        """检查是否卡死"""
        try:
            if not os.path.exists(self.heartbeat_file):
                return False
                
            with open(self.heartbeat_file, 'r', encoding='utf-8') as f:
                heartbeat_data = json.load(f)
            
            last_update = datetime.fromisoformat(heartbeat_data['timestamp'])
            time_diff = datetime.now() - last_update
            
            return time_diff.total_seconds() > self.max_no_progress_time
            
        except:
            return False
    
    def gentle_sync_single_stock(self, stock_code, stock_name, list_date, max_retries=3):
        """温和地同步单只股票"""
        for attempt in range(max_retries):
            try:
                self.update_heartbeat(stock_code, f"开始尝试 {attempt + 1}/{max_retries}")
                print(f"  尝试 {attempt + 1}/{max_retries}: 正在同步 {stock_code} ({stock_name}) 从 {list_date} 开始")
                
                # 分步骤执行，每步都更新心跳
                self.update_heartbeat(stock_code, "连接数据库")
                
                # 检查是否已经有最新数据
                if self.check_stock_up_to_date(stock_code):
                    print("  数据已是最新，跳过")
                    return True
                
                self.update_heartbeat(stock_code, "获取股票数据")
                
                # 执行同步
                if self.syncer.sync_stock_data(stock_code, stock_name, list_date):
                    self.update_heartbeat(stock_code, "同步成功")
                    print("成功")
                    return True
                else:
                    self.update_heartbeat(stock_code, f"同步失败，尝试 {attempt + 1}")
                    print("失败")
                    if attempt < max_retries - 1:
                        print("  等待5秒后重试...")
                        time.sleep(5)
                        
            except KeyboardInterrupt:
                print("\n用户中断同步")
                raise
                
            except Exception as e:
                error_msg = str(e)[:100]
                self.update_heartbeat(stock_code, f"异常: {error_msg}")
                print(f"异常: {error_msg}")
                if attempt < max_retries - 1:
                    print("  等待10秒后重试...")
                    time.sleep(10)
        
        self.update_heartbeat(stock_code, "所有尝试都失败")
        return False
    
    def check_stock_up_to_date(self, stock_code):
        """检查股票数据是否已经是最新的"""
        try:
            def _check_latest_date(connection):
                cursor = connection.cursor()
                try:
                    cursor.execute("""
                        SELECT MAX(日期) FROM stock_stock_zh_a_hist 
                        WHERE 股票代码 = %s
                    """, (stock_code,))
                    result = cursor.fetchone()
                    return result[0] if result and result[0] else None
                finally:
                    cursor.close()
            
            latest_date = self.syncer.safe_executor.safe_execute(
                _check_latest_date,
                self.syncer.conn,
                context="检查最新日期失败"
            )
            
            if latest_date:
                # 如果最新数据是最近3天内的，认为是最新的
                today = datetime.now().date()
                if isinstance(latest_date, str):
                    latest_date = datetime.strptime(latest_date, '%Y-%m-%d').date()
                
                days_diff = (today - latest_date).days
                return days_diff <= 3
            
            return False
            
        except:
            return False
    
    def gentle_continue_sync(self, start_code, max_stocks=None):
        """温和地继续同步"""
        if not self.syncer.connect_database():
            print("数据库连接失败")
            return
        
        try:
            print(f"准备从股票 {start_code} 开始温和同步...")
            self.update_heartbeat(start_code, "开始同步任务")
            
            # 获取股票列表
            print("获取股票列表...")
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
                self.syncer.conn,
                context="获取股票列表失败"
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
            progress = self.load_progress()
            if progress:
                success_count = progress.get('success_count', 0)
                failed_count = progress.get('failed_count', 0)
                failed_stocks = progress.get('failed_stocks', [])
            else:
                success_count = 0
                failed_count = 0
                failed_stocks = []
            
            print("=" * 50)
            
            try:
                for i, (stock_code, stock_name, list_date) in enumerate(stocks_to_sync, 1):
                    print(f"[{i}/{total_count}] {stock_code} ({stock_name})")
                    
                    # 使用温和的同步方法
                    if self.gentle_sync_single_stock(stock_code, stock_name, list_date):
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
                    
                    # 每5只股票休息一下（更频繁的休息）
                    if i % 5 == 0:
                        print(f"  [休息] 已处理 {i} 只股票，休息3秒...")
                        time.sleep(3)
                    
                    # 每20只股票显示进度
                    if i % 20 == 0:
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
            # 清理心跳文件
            try:
                if os.path.exists(self.heartbeat_file):
                    os.remove(self.heartbeat_file)
            except:
                pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='温和的股票数据同步工具')
    parser.add_argument('action', choices=['continue', 'retry', 'check'], help='操作类型')
    parser.add_argument('start_code', nargs='?', help='起始股票代码')
    parser.add_argument('--max-stocks', type=int, help='最大同步股票数量')
    
    args = parser.parse_args()
    
    tool = GentleStockSyncTool()
    
    if args.action == 'continue' and args.start_code:
        # 确认开始同步
        response = input("确认开始温和同步吗？(y/N): ")
        if response.lower() != 'y':
            print("取消同步")
            return
        
        tool.gentle_continue_sync(args.start_code, args.max_stocks)
        
    elif args.action == 'retry':
        tool.retry_failed_stocks()
        
    elif args.action == 'check':
        # 检查是否卡死
        if tool.check_if_stuck():
            print("检测到同步进程可能卡死")
            if os.path.exists(tool.heartbeat_file):
                with open(tool.heartbeat_file, 'r', encoding='utf-8') as f:
                    heartbeat_data = json.load(f)
                print(f"最后活动: {heartbeat_data['timestamp']}")
                print(f"处理股票: {heartbeat_data['stock_code']}")
                print(f"状态: {heartbeat_data['message']}")
        else:
            print("同步进程运行正常")
    else:
        print("请提供起始股票代码")

if __name__ == "__main__":
    main()