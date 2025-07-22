# -*- coding: utf-8 -*-
"""
AKShare同步控制器
处理股票数据同步的核心逻辑
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from models.akshare_sync_model import AKShareSyncModel
from models.stock_data_model import StockDataModel
from utils.error_handler import ErrorHandler

class AKShareSyncController:
    """AKShare同步控制器"""
    
    def __init__(self):
        """初始化控制器"""
        self.logger = logging.getLogger(__name__)
        self.sync_model = AKShareSyncModel()
        self.stock_model = StockDataModel()
        self.error_handler = ErrorHandler()
        
    def sync_market_data(self, market_type: str, start_date: str, end_date: str) -> bool:
        """同步指定市场板块的数据"""
        try:
            self.logger.info(f"开始同步{market_type}板块数据")
            
            # 获取股票列表
            stock_codes = self._get_stock_codes_by_market(market_type)
            if not stock_codes:
                self.logger.warning(f"未找到{market_type}板块的股票")
                return False
            
            success_count = 0
            for stock_code in stock_codes:
                if self.sync_single_stock(stock_code, start_date, end_date):
                    success_count += 1
            
            self.logger.info(f"{market_type}板块同步完成，成功{success_count}只，总计{len(stock_codes)}只")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"同步{market_type}板块数据失败: {e}")
            return False
    
    def sync_single_stock(self, stock_code: str, start_date: str, end_date: str) -> bool:
        """同步单个股票的数据"""
        try:
            # 验证日期格式
            self._validate_date_format(start_date)
            self._validate_date_format(end_date)
            
            # 获取股票数据
            stock_data = self.sync_model.get_stock_data(stock_code, start_date, end_date)
            if stock_data is None or stock_data.empty:
                self.logger.warning(f"股票{stock_code}无数据")
                return False
            
            # 保存到数据库
            success = self.stock_model.save_stock_data(stock_code, stock_data)
            if success:
                self.logger.info(f"股票{stock_code}数据同步成功，共{len(stock_data)}条记录")
            
            return success
            
        except Exception as e:
            self.logger.error(f"同步股票{stock_code}数据失败: {e}")
            return False
    
    def _get_stock_codes_by_market(self, market_type: str) -> List[str]:
        """根据市场类型获取股票代码列表"""
        market_map = {
            'RB': '主板',      # 主板
            'ZB': '中小板',    # 中小板
            'CYB': '创业板',   # 创业板
            'KCB': '科创板'    # 科创板
        }
        
        if market_type not in market_map:
            return []
        
        # 这里应该调用实际的API获取股票列表
        # 暂时返回示例数据
        return self.sync_model.get_stock_codes_by_market(market_type)
    
    def _validate_date_format(self, date_str: str) -> bool:
        """验证日期格式"""
        try:
            datetime.strptime(date_str, '%Y%m%d')
            return True
        except ValueError:
            raise ValueError(f"日期格式错误: {date_str}，应为YYYYMMDD格式")