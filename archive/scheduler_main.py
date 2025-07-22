"""
调度器主程序 - 自动定时同步数据
"""
import sys
import signal
import time
from utils.scheduler import SyncScheduler
from utils.logger_util import setup_logger
import logging

logger = logging.getLogger(__name__)


class SchedulerManager:
    """调度器管理器"""
    
    def __init__(self):
        self.scheduler = SyncScheduler()
        self.running = False
    
    def start(self):
        """启动调度器"""
        try:
            setup_logger()
            logger.info("正在启动AKShare数据同步调度器...")
            
            # 设置信号处理
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # 启动调度器
            self.scheduler.start()
            self.running = True
            
            print("🚀 AKShare数据同步调度器已启动")
            print("📊 调度任务:")
            next_runs = self.scheduler.get_next_runs()
            for job in next_runs:
                print(f"  - {job['job']}: {job['next_run']}")
            
            print("\n按 Ctrl+C 停止调度器")
            
            # 保持程序运行
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止调度器...")
        except Exception as e:
            logger.error(f"调度器运行错误: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止调度器"""
        if self.running:
            self.running = False
            self.scheduler.stop()
            print("🛑 调度器已停止")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在停止调度器...")
        self.stop()
        sys.exit(0)


def main():
    """主程序"""
    manager = SchedulerManager()
    manager.start()


if __name__ == "__main__":
    main()