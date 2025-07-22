# -*- coding: utf-8 -*-
"""
股票数据测试工具
用于验证股票数据同步功能和数据完整性
"""

import unittest
import logging
import time
import pandas as pd
from datetime import datetime, timedelta
from core.smart_stock_sync import SmartStockSync
from models.stock_data_model import StockDataModel
from config.sync_config import SyncConfig

# 配置日志
logging.basicConfig(level=logging.INFO)

class TestStockDataSync(unittest.TestCase):
    """股票数据同步测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化，只执行一次"""
        cls.config = SyncConfig()
        cls.sync = SmartStockSync()
        cls.model = StockDataModel()
        cls.test_stock_codes = [
            'sh600000',  # 浦发银行 - 沪市
            'sz000001',  # 平安银行 - 深市
            'sz300001',  # 特锐德 - 创业板
            'sh688001'   # 华兴源创 - 科创板
        ]
        cls.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        cls.end_date = datetime.now().strftime('%Y%m%d')
        
    def setUp(self):
        """每个测试方法执行前初始化"""
        self.test_start_time = time.time()
        
    def tearDown(self):
        """每个测试方法执行后清理"""
        test_duration = time.time() - self.test_start_time
        self.logger.info(f"测试耗时: {test_duration:.2f}秒")
    
    def test_single_stock_sync(self):
        """测试单个股票数据同步功能"""
        for stock_code in self.test_stock_codes:
            with self.subTest(stock_code=stock_code):
                # 同步股票数据
                result = self.sync.sync_single_stock(stock_code, self.start_date, self.end_date)
                self.assertTrue(result['success'], f"股票{stock_code}同步失败: {result.get('error', '未知错误')}")
                
                # 验证数据是否已保存
                data = self.model.get_stock_data(stock_code, self.start_date, self.end_date)
                self.assertIsNotNone(data, f"未找到股票{stock_code}的同步数据")
                self.assertGreater(len(data), 0, f"股票{stock_code}同步数据为空")
    
    def test_batch_stock_sync(self):
        """测试批量股票数据同步功能"""
        result = self.sync.sync_stock_batch(
            self.test_stock_codes, self.start_date, self.end_date, batch_size=2
        )
        
        self.assertTrue(result['success'], f"批量同步失败: {result.get('error', '未知错误')}")
        self.assertEqual(len(result['synced_stocks']), len(self.test_stock_codes), 
                         f"批量同步股票数量不匹配: 预期{len(self.test_stock_codes)}, 实际{len(result['synced_stocks'])}")
        self.assertEqual(result['failed_stocks'], 0, f"批量同步中有{len(result['failed_stocks'])}个股票失败")
    
    def test_data_integrity(self):
        """测试同步数据的完整性"""
        stock_code = self.test_stock_codes[0]
        
        # 获取同步后的数据
        db_data = self.model.get_stock_data(stock_code, self.start_date, self.end_date)
        self.assertIsNotNone(db_data, f"未找到股票{stock_code}的同步数据")
        
        # 验证数据字段完整性
        required_fields = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount']
        for record in db_data[:5]:  # 只检查前5条记录
            for field in required_fields:
                self.assertIn(field, record, f"数据记录缺少字段: {field}")
                self.assertIsNotNone(record[field], f"字段{field}的值为空")
    
    def test_sync_performance(self):
        """测试同步性能"""
        stock_code = self.test_stock_codes[0]
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行同步
        result = self.sync.sync_single_stock(stock_code, self.start_date, self.end_date)
        
        # 计算耗时
        sync_duration = time.time() - start_time
        
        # 验证同步成功
        self.assertTrue(result['success'], f"股票{stock_code}同步失败: {result.get('error', '未知错误')}")
        
        # 验证性能指标
        data_count = len(self.model.get_stock_data(stock_code, self.start_date, self.end_date))
        self.assertGreater(data_count, 0, "未获取到股票数据")
        
        # 计算每秒处理记录数
        records_per_second = data_count / sync_duration
        self.logger.info(f"同步性能: {records_per_second:.2f}条记录/秒")
        
        # 假设我们期望至少每秒处理10条记录
        self.assertGreater(records_per_second, 10, f"同步性能不达标: {records_per_second:.2f}条记录/秒")
    
    def test_error_handling(self):
        """测试错误处理机制"""
        invalid_stock_code = 'invalid_code_123'
        
        # 尝试同步无效股票代码
        result = self.sync.sync_single_stock(invalid_stock_code, self.start_date, self.end_date)
        
        # 验证错误处理
        self.assertFalse(result['success'], "无效股票代码应该同步失败")
        self.assertIsNotNone(result.get('error'), "应该返回错误信息")
        self.logger.info(f"错误处理测试: {result['error']}")

if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)

# 为了方便单独运行测试，添加命令行支持
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        # 如果提供了股票代码参数，则只测试指定股票
        test_stock_code = sys.argv[1]
        print(f"只测试股票代码: {test_stock_code}")
        
        # 创建测试套件
        suite = unittest.TestSuite()
        test_case = TestStockDataSync()
        test_case.test_stock_codes = [test_stock_code]
        suite.addTest(test_case.test_single_stock_sync)
        suite.addTest(test_case.test_data_integrity)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    else:
        # 运行所有测试
        unittest.main(verbosity=2)