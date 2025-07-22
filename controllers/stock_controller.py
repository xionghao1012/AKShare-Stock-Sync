# -*- coding: utf-8 -*-
"""
股票控制器
提供股票数据管理和查询功能
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from models.stock_data_model import StockDataModel

class StockController:
    """股票控制器"""
    
    def __init__(self):
        """初始化控制器"""
        self.logger = logging.getLogger(__name__)
        self.stock_model = StockDataModel()
        
    def get_sync_status(self) -> Dict:
        """获取同步状态"""
        try:
            total_stocks = self.stock_model.get_total_stock_count()
            synced_stocks = self.stock_model.get_synced_stock_count()
            total_records = self.stock_model.get_total_record_count()
            
            return {
                'total_stocks': total_stocks,
                'synced_stocks': synced_stocks,
                'pending_stocks': total_stocks - synced_stocks,
                'total_records': total_records,
                'sync_rate': (synced_stocks / total_stocks * 100) if total_stocks > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"获取同步状态失败: {e}")
            return {}
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """获取股票信息"""
        try:
            return self.stock_model.get_stock_info(stock_code)
        except Exception as e:
            self.logger.error(f"获取股票{stock_code}信息失败: {e}")
            return None
    
    def get_stock_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """获取股票数据"""
        try:
            return self.stock_model.get_stock_data(stock_code, start_date, end_date)
        except Exception as e:
            self.logger.error(f"获取股票{stock_code}数据失败: {e}")
            return None
    
    def optimize_database(self) -> bool:
        """优化数据库"""
        try:
            self.logger.info("开始优化数据库")
            success = self.stock_model.optimize_database()
            
            if success:
                self.logger.info("数据库优化完成")
            else:
                self.logger.error("数据库优化失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"优化数据库失败: {e}")
            return False
    
    def get_stock_list(self, market_type: Optional[str] = None) -> List[Dict]:
        """获取股票列表"""
        try:
            return self.stock_model.get_stock_list(market_type)
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return []