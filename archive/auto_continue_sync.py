# -*- coding: utf-8 -*-
"""
自动继续同步工具
用于从上次中断的位置继续股票数据同步
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from core.smart_stock_sync import SmartStockSync
from utils.logger_util import setup_logger
from config.sync_config import SyncConfig

class AutoContinueSync:
    """自动继续同步类"""
    
    def __init__(self):
        """初始化自动继续同步工具"""
        self.config = SyncConfig()
        self.logger = setup_logger(
            log_file=self.config.log_file,
            log_level=self.config.log_level
        )
        self.sync_manager = SmartStockSync()
        self.progress_file = 'sync_progress.json'
    
    def load_sync_progress(self):
        """加载同步进度
        
        Returns:
            dict: 同步进度信息，如果文件不存在则返回None
        """
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            self.logger.error(f"加载同步进度失败: {str(e)}")
            return None
    
    def save_sync_progress(self, progress_data):
        """保存同步进度
        
        Args:
            progress_data (dict): 同步进度数据
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 添加时间戳
            progress_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"保存同步进度失败: {str(e)}")
            return False
    
    def continue_sync(self):
        """继续上次的同步
        
        Returns:
            dict: 同步结果
        """
        self.logger.info("===== 自动继续同步工具 ====")
        
        # 加载进度
        progress = self.load_sync_progress()
        if not progress:
            self.logger.info("未找到同步进度记录，将从头开始同步")
            return self.start_new_sync()
        
        # 检查进度是否有效
        if 'last_sync_time' not in progress or 'last_synced_stock' not in progress:
            self.logger.warning("同步进度记录不完整，将从头开始同步")
            return self.start_new_sync()
        
        # 检查上次同步时间是否太旧（超过24小时）
        last_sync_time = datetime.strptime(progress['last_sync_time'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() - last_sync_time > timedelta(hours=24):
            self.logger.warning("上次同步时间超过24小时，将从头开始同步")
            return self.start_new_sync()
        
        # 继续同步
        self.logger.info(f"上次同步时间: {progress['last_sync_time']}")
        self.logger.info(f"上次同步到股票: {progress['last_synced_stock']}")
        
        # 获取股票列表
        stock_list = self.sync_manager.get_stock_list()
        if not stock_list:
            self.logger.error("未获取到股票列表，同步终止")
            return {'success': False, 'message': '未获取到股票列表'}
        
        # 找到上次同步位置
        try:
            last_index = stock_list.index(progress['last_synced_stock'])
            remaining_stocks = stock_list[last_index+1:]
            self.logger.info(f"继续同步剩余{len(remaining_stocks)}只股票")
            
            if not remaining_stocks:
                self.logger.info("所有股票已同步完成，将开始新一轮同步")
                return self.start_new_sync()
            
            # 执行同步
            result = self.sync_manager.sync_stock_batch(
                remaining_stocks,
                start_date=datetime.now().strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d'),
                batch_size=self.config.batch_size
            )
            
            # 更新进度
            if result['success_count'] > 0:
                progress['last_synced_stock'] = remaining_stocks[-1]
                progress['last_sync_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                progress['synced_count'] = progress.get('synced_count', 0) + result['success_count']
                self.save_sync_progress(progress)
            
            return {
                'success': True,
                'success_count': result['success_count'],
                'failed_count': result['failed_count'],
                'total_processed': len(remaining_stocks)
            }
            
        except ValueError:
            self.logger.warning(f"在股票列表中未找到上次同步的股票{progress['last_synced_stock']}，将从头开始同步")
            return self.start_new_sync()
    
    def start_new_sync(self):
        """开始新的同步
        
        Returns:
            dict: 同步结果
        """
        self.logger.info("开始新的股票数据同步...")
        
        # 获取股票列表
        stock_list = self.sync_manager.get_stock_list()
        if not stock_list:
            self.logger.error("未获取到股票列表，同步终止")
            return {'success': False, 'message': '未获取到股票列表'}
        
        # 初始化进度
        progress = {
            'last_sync_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_synced_stock': '',
            'synced_count': 0,
            'total_stocks': len(stock_list)
        }
        self.save_sync_progress(progress)
        
        # 执行同步
        result = self.sync_manager.sync_stock_batch(
            stock_list,
            start_date=datetime.now().strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d'),
            batch_size=self.config.batch_size
        )
        
        # 更新进度
        if result['success_count'] > 0:
            progress['last_synced_stock'] = stock_list[result['success_count']-1]
            progress['synced_count'] = result['success_count']
            self.save_sync_progress(progress)
        
        return {
            'success': True,
            'success_count': result['success_count'],
            'failed_count': result['failed_count'],
            'total_processed': len(stock_list)
        }

if __name__ == '__main__':
    auto_sync = AutoContinueSync()
    result = auto_sync.continue_sync()
    
    if result['success']:
        print(f"同步完成: 成功{result['success_count']}只, 失败{result['failed_count']}只, 共处理{result['total_processed']}只")
    else:
        print(f"同步失败: {result.get('message', '未知错误')}")