# -*- coding: utf-8 -*-
"""
AKShare股票数据同步主程序
"""

import logging
import time
from datetime import datetime
from core.smart_stock_sync import SmartStockSync
from utils.logger_util import setup_logger
from config.sync_config import SyncConfig
from tools.system_monitor import SystemMonitor

def main():
    """主函数"""
    # 初始化配置
    config = SyncConfig()
    
    # 设置日志
    logger = setup_logger(
        log_file=config.log_file,
        log_level=config.log_level
    )
    
    # 记录开始时间
    start_time = time.time()
    logger.info(f"===== AKShare股票数据同步系统启动 ===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 系统监控
    system_monitor = SystemMonitor()
    system_info = system_monitor.get_system_info()
    logger.info(f"系统信息: {system_info}")
    
    try:
        # 创建同步实例
        sync_manager = SmartStockSync()
        
        # 获取股票列表
        logger.info("获取股票列表...")
        stock_list = sync_manager.get_stock_list()
        logger.info(f"共获取到{len(stock_list)}只股票")
        
        if not stock_list:
            logger.error("未获取到股票列表，同步终止")
            return
        
        # 执行同步
        logger.info("开始同步股票数据...")
        result = sync_manager.sync_stock_batch(
            stock_list,
            start_date=datetime.now().strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d'),
            batch_size=config.batch_size
        )
        
        # 记录结果
        logger.info(f"同步完成: 成功{result['success_count']}只, 失败{result['failed_count']}只")
        if result['failed_stocks']:
            logger.warning(f"同步失败的股票: {', '.join(result['failed_stocks'][:10])}{'...' if len(result['failed_stocks'])>10 else ''}")
        
        # 优化数据库
        if config.enable_optimization:
            logger.info("开始优化数据库...")
            sync_manager.optimize_database()
            logger.info("数据库优化完成")
        
    except Exception as e:
        logger.error(f"同步过程中发生错误: {str(e)}", exc_info=True)
    finally:
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"===== AKShare股票数据同步系统结束 ===== 耗时: {duration:.2f}秒")

if __name__ == '__main__':
    main()