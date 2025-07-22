# -*- coding: utf-8 -*-
"""
数据验证测试用例
"""
import unittest
import time
from datetime import datetime, timedelta
from models.data_validator import DataValidator
from core.stock_data_fetcher import StockDataFetcher

class TestDataValidation(unittest.TestCase):
    """数据验证测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.validator = DataValidator()
        cls.fetcher = StockDataFetcher()
        cls.test_stock_code = '000001'
        
    def setUp(self):
        """每个测试用例执行前初始化"""
        self.sample_data = self._get_sample_stock_data()
        
    def _get_sample_stock_data(self):
        """获取样本股票数据用于测试"""
        try:
            # 获取真实股票数据作为测试样本
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            data = self.fetcher.fetch_stock_data(
                self.test_stock_code,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            # 如果获取真实数据失败，使用模拟数据
            print(f"获取真实数据失败，使用模拟数据: {str(e)}")
            return [{
                'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                'open': 10.0 + i * 0.1,
                'close': 10.1 + i * 0.1,
                'high': 10.2 + i * 0.1,
                'low': 9.9 + i * 0.1,
                'volume': 1000000 + i * 1000
            } for i in range(30)]
    
    def test_validate_stock_data(self):
        """测试股票数据验证"""
        result = self.validator.validate_stock_data(self.sample_data)
        self.assertTrue(result['valid'], "样本数据应该通过验证")
    
    def test_validate_missing_fields(self):
        """测试验证缺失字段的数据"""
        # 创建一个缺少字段的数据项
        invalid_data = self.sample_data.copy()
        del invalid_data[0]['close']  # 删除收盘价字段
        
        result = self.validator.validate_stock_data(invalid_data)
        self.assertFalse(result['valid'], "缺少字段的数据不应通过验证")
        self.assertIn('missing fields', result['error_message'].lower(), 
                     "错误消息应包含'缺少字段'信息")
    
    def test_validate_invalid_values(self):
        """测试验证包含无效值的数据"""
        # 创建一个包含无效值的数据项
        invalid_data = self.sample_data.copy()
        invalid_data[0]['open'] = -10.0  # 开盘价不能为负数
        
        result = self.validator.validate_stock_data(invalid_data)
        self.assertFalse(result['valid'], "包含无效值的数据不应通过验证")
    
    def test_validate_date_format(self):
        """测试验证日期格式"""
        # 创建一个日期格式无效的数据项
        invalid_data = self.sample_data.copy()
        invalid_data[0]['date'] = '2023/13/32'  # 无效的日期
        
        result = self.validator.validate_stock_data(invalid_data)
        self.assertFalse(result['valid'], "日期格式无效的数据不应通过验证")
    
    def test_data_consistency_check(self):
        """测试数据一致性检查"""
        # 创建一个价格不一致的数据项
        inconsistent_data = self.sample_data.copy()
        inconsistent_data[0]['high'] = 9.0
        inconsistent_data[0]['low'] = 10.0  # 最低价高于最高价，不一致
        
        result = self.validator.validate_stock_data(inconsistent_data)
        self.assertFalse(result['valid'], "价格不一致的数据不应通过验证")

if __name__ == '__main__':
    unittest.main(verbosity=2)