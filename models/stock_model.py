# -*- coding: utf-8 -*-
"""
股票数据模型
定义股票数据结构和相关操作
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict

@dataclass
class StockData:
    """股票数据类"""
    code: str          # 股票代码
    date: str          # 日期 (YYYY-MM-DD)
    open: float        # 开盘价
    close: float       # 收盘价
    high: float        # 最高价
    low: float         # 最低价
    volume: int        # 成交量
    change: Optional[float] = None  # 涨跌幅
    turnover: Optional[float] = None # 换手率
    
    def __post_init__(self):
        """初始化后计算涨跌幅"""
        if self.change is None and hasattr(self, 'prev_close'):
            prev_close = getattr(self, 'prev_close', self.close)
            self.change = round((self.close - prev_close) / prev_close * 100, 2)
    
    def to_dict(self) -> Dict[str, any]:
        """转换为字典
        
        Returns:
            包含股票数据的字典
        """
        return {
            'code': self.code,
            'date': self.date,
            'open': self.open,
            'close': self.close,
            'high': self.high,
            'low': self.low,
            'volume': self.volume,
            'change': self.change,
            'turnover': self.turnover
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any], code: str = None) -> 'StockData':
        """从字典创建StockData实例
        
        Args:
            data: 包含股票数据的字典
            code: 股票代码
        
        Returns:
            StockData实例
        """
        # 处理不同数据源可能的字段名称差异
        field_mapping = {
            'trade_date': 'date',
            'vol': 'volume',
            'amount': 'turnover',
            'pct_chg': 'change'
        }
        
        # 标准化字段名称
        normalized_data = {}
        for key, value in data.items():
            normalized_key = field_mapping.get(key, key)
            normalized_data[normalized_key] = value
        
        # 如果字典中没有code且提供了code参数，则添加
        if 'code' not in normalized_data and code:
            normalized_data['code'] = code
        
        return cls(**normalized_data)

class StockModel:
    """股票数据模型类"""
    
    @staticmethod
    def convert_to_stock_data_list(raw_data: List[Dict[str, any]], code: str) -> List[StockData]:
        """将原始数据列表转换为StockData对象列表
        
        Args:
            raw_data: 原始数据列表
            code: 股票代码
        
        Returns:
            StockData对象列表
        """
        stock_data_list = []
        prev_close = None
        
        for item in raw_data:
            stock_data = StockData.from_dict(item, code)
            
            # 设置前收盘价用于计算涨跌幅
            if prev_close:
                stock_data.prev_close = prev_close
                stock_data.__post_init__()  # 重新计算涨跌幅
            
            stock_data_list.append(stock_data)
            prev_close = stock_data.close
            
        return stock_data_list
    
    @staticmethod
    def filter_by_date_range(data_list: List[StockData], start_date: str, end_date: str) -> List[StockData]:
        """按日期范围过滤股票数据
        
        Args:
            data_list: StockData对象列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            过滤后的StockData对象列表
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            # 如果日期格式错误，尝试另一种格式
            try:
                start_dt = datetime.strptime(start_date, '%Y%m%d')
                end_dt = datetime.strptime(end_date, '%Y%m%d')
            except ValueError:
                # 如果仍无法解析，返回原始列表
                return data_list
        
        filtered_list = []
        for item in data_list:
            try:
                item_dt = datetime.strptime(item.date, '%Y-%m-%d')
                if start_dt <= item_dt <= end_dt:
                    filtered_list.append(item)
            except ValueError:
                continue
        
        return filtered_list
    
    @staticmethod
    def calculate_technical_indicators(data_list: List[StockData]) -> List[Dict[str, any]]:
        """计算技术指标
        
        Args:
            data_list: StockData对象列表
        
        Returns:
            添加了技术指标的股票数据字典列表
        """
        result = []
        close_prices = [item.close for item in data_list]
        
        for i, item in enumerate(data_list):
            item_dict = item.to_dict()
            
            # 计算简单移动平均线 (SMA)
            if i >= 4:
                item_dict['sma5'] = round(sum(close_prices[i-4:i+1])/5, 2)
            if i >= 9:
                item_dict['sma10'] = round(sum(close_prices[i-9:i+1])/10, 2)
            
            result.append(item_dict)
        
        return result