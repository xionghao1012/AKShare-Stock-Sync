# -*- coding: utf-8 -*-
"""
自动继续同步脚本
从上次中断的地方继续同步股票数据
"""
import json
import os
from smart_stock_sync import SmartStockSync

def auto_continue_sync():
    """自动从上次中断的地方继续同步"""
    sync_tool = SmartStockSync()
    
    # 加载进度
    progress = sync_tool.load_progress()
    if not progress:
        print("没有找到同步进度，请手动指定起始股票代码")
        return
    
    current_stock = progress.get('current_stock')
    if not current_stock:
        print("进度文件中没有当前股票信息")
        return
    
    print(f"检测到上次同步到股票: {current_stock}")
    print(f"成功: {progress.get('success_count', 0)}, 失败: {progress.get('failed_count', 0)}")
    print(f"最后更新: {progress.get('last_update', 'N/A')}")
    
    # 计算下一个股票代码
    try:
        stock_num = int(current_stock)
        next_stock = f"{stock_num + 1:06d}"
        print(f"准备从下一个股票 {next_stock} 开始继续同步...")
    except ValueError:
        print(f"无法解析股票代码 {current_stock}，请手动指定")
        return
    
    # 开始同步，每次同步100只股票
    batch_size = 100
    print(f"将分批同步，每批 {batch_size} 只股票")
    
    try:
        sync_tool.continue_sync_from_code(next_stock, batch_size)
    except KeyboardInterrupt:
        print("\n用户中断同步")
    except Exception as e:
        print(f"同步过程中出现错误: {e}")

if __name__ == "__main__":
    auto_continue_sync()