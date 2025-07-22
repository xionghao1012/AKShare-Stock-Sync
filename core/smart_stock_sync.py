#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能股票同步工具 - 推荐使用的核心同步模块
提供智能的断点续传、失败重试和状态管理功能
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.stock_data_model import StockDataModel
from utils.logger_util import LoggerUtil
from utils.error_handler import ErrorHandler

class SmartStockSync:
    """智能股票同步类"""
    
    def __init__(self):
        """初始化智能同步器"""
        self.logger = LoggerUtil().get_logger(__name__)
        self.stock_model = StockDataModel()
        self.error_handler = ErrorHandler()
        
        # 进度文件路径
        self.progress_file = project_root / 'sync_progress.json'
        self.progress_data = self._load_progress()
        
    def _load_progress(self) -> Dict:
        """加载同步进度"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"加载进度文件失败: {e}")
        
        return {
            'last_sync_time': None,
            'completed_stocks': [],
            'failed_stocks': [],
            'sync_status': {},
            'total_records': 0
        }
    
    def _save_progress(self):
        """保存同步进度"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存进度文件失败: {e}")
    
    def get_status(self) -> Dict:
        """获取同步状态"""
        return {
            'completed_count': len(self.progress_data['completed_stocks']),
            'failed_count': len(self.progress_data['failed_stocks']),
            'total_records': self.progress_data['total_records'],
            'last_sync': self.progress_data['last_sync_time'],
            'sync_status': self.progress_data['sync_status']
        }
    
    def sync_all_stocks(self, start_date: str, end_date: str) -> bool:
        """同步所有股票"""
        try:
            # 获取所有股票代码
            stock_codes = self.stock_model.get_all_stock_codes()
            self.logger.info(f"开始同步 {len(stock_codes)} 只股票的数据")
            
            for stock_code in stock_codes:
                if stock_code not in self.progress_data['completed_stocks']:
                    self.sync_single_stock(stock_code, start_date, end_date)
            
            self.logger.info("所有股票同步完成")
            return True
            
        except Exception as e:
            self.logger.error(f"同步所有股票失败: {e}")
            return False
    
    def sync_single_stock(self, stock_code: str, start_date: str, end_date: str) -> bool:
        """同步单个股票"""
        try:
            self.logger.info(f"开始同步股票 {stock_code} 的数据")
            
            # 检查是否已同步
            if stock_code in self.progress_data['completed_stocks']:
                self.logger.info(f"股票 {stock_code} 已同步，跳过")
                return True
            
            # 执行同步
            success = self.stock_model.sync_stock_data(stock_code, start_date, end_date)
            
            if success:
                self.progress_data['completed_stocks'].append(stock_code)
                if stock_code in self.progress_data['failed_stocks']:
                    self.progress_data['failed_stocks'].remove(stock_code)
                
                # 更新记录数
                count = self.stock_model.get_stock_record_count(stock_code)
                self.progress_data['total_records'] += count
                
                self.logger.info(f"股票 {stock_code} 同步成功，新增 {count} 条记录")
            else:
                if stock_code not in self.progress_data['failed_stocks']:
                    self.progress_data['failed_stocks'].append(stock_code)
                self.logger.warning(f"股票 {stock_code} 同步失败")
            
            # 更新状态
            self.progress_data['sync_status'][stock_code] = {
                'last_sync': datetime.now().isoformat(),
                'success': success,
                'records': count if success else 0
            }
            
            # 保存进度
            self._save_progress()
            
            return success
            
        except Exception as e:
            self.logger.error(f"同步股票 {stock_code} 时发生错误: {e}")
            return False
    
    def retry_failed_stocks(self, start_date: str, end_date: str) -> bool:
        """重试失败的股票"""
        try:
            failed_stocks = self.progress_data['failed_stocks'].copy()
            self.logger.info(f"开始重试 {len(failed_stocks)} 只失败的股票")
            
            success_count = 0
            for stock_code in failed_stocks:
                if self.sync_single_stock(stock_code, start_date, end_date):
                    success_count += 1
            
            self.logger.info(f"重试完成，成功 {success_count} 只，失败 {len(failed_stocks) - success_count} 只")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"重试失败股票时发生错误: {e}")
            return False
    
    def continue_sync(self, start_date: str, end_date: str) -> bool:
        """继续同步未完成的部分"""
        try:
            # 获取所有股票代码
            all_stocks = set(self.stock_model.get_all_stock_codes())
            completed_stocks = set(self.progress_data['completed_stocks'])
            pending_stocks = all_stocks - completed_stocks
            
            self.logger.info(f"继续同步 {len(pending_stocks)} 只未完成的股票")
            
            success_count = 0
            for stock_code in pending_stocks:
                if self.sync_single_stock(stock_code, start_date, end_date):
                    success_count += 1
            
            self.logger.info(f"继续同步完成，成功 {success_count} 只")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"继续同步时发生错误: {e}")
            return False
    
    def reset_progress(self):
        """重置同步进度"""
        try:
            self.progress_data = {
                'last_sync_time': None,
                'completed_stocks': [],
                'failed_stocks': [],
                'sync_status': {},
                'total_records': 0
            }
            self._save_progress()
            self.logger.info("同步进度已重置")
        except Exception as e:
            self.logger.error(f"重置进度失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='智能股票同步工具')
    parser.add_argument('--action', choices=['status', 'sync', 'retry', 'continue', 'reset'],
                        default='status', help='执行的操作')
    parser.add_argument('--start-date', type=str, help='开始日期 (YYYYMMDD)')
    parser.add_argument('--end-date', type=str, help='结束日期 (YYYYMMDD)')
    parser.add_argument('--stock', type=str, help='股票代码')
    
    args = parser.parse_args()
    
    sync_tool = SmartStockSync()
    
    if args.action == 'status':
        status = sync_tool.get_status()
        print("📊 同步状态")
        print(f"已完成: {status['completed_count']} 只股票")
        print(f"失败: {status['failed_count']} 只股票")
        print(f"总记录数: {status['total_records']} 条")
        print(f"最后同步: {status['last_sync']}")
    
    elif args.action == 'sync' and args.start_date and args.end_date:
        if args.stock:
            sync_tool.sync_single_stock(args.stock, args.start_date, args.end_date)
        else:
            sync_tool.sync_all_stocks(args.start_date, args.end_date)
    
    elif args.action == 'retry' and args.start_date and args.end_date:
        sync_tool.retry_failed_stocks(args.start_date, args.end_date)
    
    elif args.action == 'continue' and args.start_date and args.end_date:
        sync_tool.continue_sync(args.start_date, args.end_date)
    
    elif args.action == 'reset':
        sync_tool.reset_progress()
    
    else:
        print("请使用 --help 查看使用说明")

if __name__ == "__main__":
    main()