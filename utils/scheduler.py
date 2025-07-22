"""
数据同步调度器
"""
import schedule
import time
import threading
from datetime import datetime
from controllers.akshare_sync_controller import AKShareSyncController
from config.sync_config import SyncConfig
import logging

logger = logging.getLogger(__name__)


class SyncScheduler:
    """同步调度器"""
    
    def __init__(self):
        self.controller = AKShareSyncController()
        self.config = SyncConfig()
        self.running = False
        self.thread = None
    
    def setup_schedules(self):
        """设置调度任务"""
        # 股票数据 - 每5分钟同步一次
        schedule.every(5).minutes.do(self._sync_category, 'stock')
        
        # 期货数据 - 每3分钟同步一次
        schedule.every(3).minutes.do(self._sync_category, 'futures')
        
        # 基金数据 - 每10分钟同步一次
        schedule.every(10).minutes.do(self._sync_category, 'fund')
        
        # 债券数据 - 每30分钟同步一次
        schedule.every(30).minutes.do(self._sync_category, 'bond')
        
        # 外汇数据 - 每1分钟同步一次
        schedule.every(1).minutes.do(self._sync_category, 'forex')
        
        # 宏观数据 - 每1小时同步一次
        schedule.every().hour.do(self._sync_category, 'macro')
        
        # 新闻数据 - 每15分钟同步一次
        schedule.every(15).minutes.do(self._sync_category, 'news')
        
        # 行业数据 - 每30分钟同步一次
        schedule.every(30).minutes.do(self._sync_category, 'industry')
        
        logger.info("调度任务设置完成")
    
    def _sync_category(self, category: str):
        """同步指定分类的数据"""
        try:
            logger.info(f"开始定时同步 {category} 数据")
            success = self.controller.sync_by_category(category)
            if success:
                logger.info(f"{category} 数据同步成功")
            else:
                logger.warning(f"{category} 数据同步失败")
        except Exception as e:
            logger.error(f"同步 {category} 数据时发生错误: {e}")
    
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行中")
            return
        
        if not self.controller.initialize():
            logger.error("控制器初始化失败，无法启动调度器")
            return
        
        self.setup_schedules()
        self.running = True
        
        def run_scheduler():
            logger.info("调度器已启动")
            while self.running:
                schedule.run_pending()
                time.sleep(1)
            logger.info("调度器已停止")
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join()
        schedule.clear()
        self.controller.cleanup()
        logger.info("调度器已停止")
    
    def get_next_runs(self) -> list:
        """获取下次运行时间"""
        jobs = schedule.get_jobs()
        return [
            {
                'job': str(job.job_func),
                'next_run': job.next_run.strftime('%Y-%m-%d %H:%M:%S') if job.next_run else 'N/A'
            }
            for job in jobs
        ]