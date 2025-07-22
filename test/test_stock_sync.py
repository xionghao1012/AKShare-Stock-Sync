# -*- coding: utf-8 -*-
"""
股票同步系统测试用例
"""
import unittest
import time
from datetime import datetime
from core.smart_stock_sync import SmartStockSync
from config.sync_config import SyncConfig

class TestStockSyncSystem(unittest.TestCase):
    """股票同步系统测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.config = SyncConfig()
        cls.sync_manager = SmartStockSync()
        cls.test_stock_code = '000001'
        
    def setUp(self):
        """每个测试用例执行前初始化"""
        self.start_time = time.time()
        
    def tearDown(self):
        """每个测试用例执行后清理"""
        end_time = time.time()
        print(f"测试用例执行时间: {end_time - self.start_time:.4f}秒")
    
    def test_get_stock_list(self):
        """测试获取股票列表"""
        stock_list = self.sync_manager.get_stock_list()
        self.assertIsInstance(stock_list, list, "股票列表应该是列表类型")
        self.assertGreater(len(stock_list), 0, "股票列表不应为空")
        self.assertIn(self.test_stock_code, stock_list, "测试股票代码应在列表中")
    
    def test_sync_single_stock(self):
        """测试同步单只股票数据"""
        result = self.sync_manager.sync_single_stock(
            self.test_stock_code,
            start_date=datetime.now().strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d')
        )
        self.assertTrue(result['success'], "单只股票同步应该成功")
        self.assertIsNotNone(result.get('data'), "同步结果应包含数据")
    
    def test_sync_small_batch(self):
        """测试小批量同步"""
        stock_list = [self.test_stock_code, '000002', '000004']
        result = self.sync_manager.sync_stock_batch(
            stock_list,
            start_date=datetime.now().strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d'),
            batch_size=2
        )
        self.assertIsInstance(result, dict, "批量同步结果应该是字典类型")
        self.assertGreater(result['success_count'], 0, "应该有成功同步的股票")
    
    def test_sync_progress_tracking(self):
        """测试同步进度跟踪"""
        # 假设存在同步进度文件
        import os
        progress_file = 'sync_progress.json'
        
        # 确保进度文件存在
        if not os.path.exists(progress_file):
            with open(progress_file, 'w', encoding='utf-8') as f:
                import json
                json.dump({
                    'last_synced_stock': self.test_stock_code,
                    'last_sync_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'synced_count': 1
                }, f)
        
        # 测试加载进度
        from archive.auto_continue_sync import AutoContinueSync
        auto_sync = AutoContinueSync()
        progress = auto_sync.load_sync_progress()
        self.assertIsNotNone(progress, "应该能加载同步进度")
        self.assertEqual(progress['last_synced_stock'], self.test_stock_code, "进度中的股票代码应该匹配")

if __name__ == '__main__':
    unittest.main(verbosity=2)