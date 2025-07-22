# -*- coding: utf-8 -*-
"""
每日股票数据定时同步调度器
考虑交易日历、节假日等因素的智能同步
"""
import schedule
import time
import sys
import os
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database_config import DatabaseConfig

class TradingCalendar:
    """交易日历管理"""
    
    def __init__(self):
        # 2025年节假日（需要根据实际情况更新）
        self.holidays_2025 = [
            # 元旦
            date(2025, 1, 1),
            # 春节
            date(2025, 1, 28), date(2025, 1, 29), date(2025, 1, 30), 
            date(2025, 1, 31), date(2025, 2, 3), date(2025, 2, 4), date(2025, 2, 5),
            # 清明节
            date(2025, 4, 5), date(2025, 4, 6), date(2025, 4, 7),
            # 劳动节
            date(2025, 5, 1), date(2025, 5, 2), date(2025, 5, 5),
            # 端午节
            date(2025, 5, 31), date(2025, 6, 2),
            # 中秋节
            date(2025, 10, 6), date(2025, 10, 7), date(2025, 10, 8),
            # 国庆节
            date(2025, 10, 1), date(2025, 10, 2), date(2025, 10, 3), 
            date(2025, 10, 4), date(2025, 10, 7), date(2025, 10, 8),
        ]
        
        # 调休工作日（周末但需要上班的日子）
        self.makeup_workdays_2025 = [
            date(2025, 1, 26),  # 春节调休
            date(2025, 2, 8),   # 春节调休
            date(2025, 4, 27),  # 劳动节调休
            date(2025, 9, 29),  # 国庆节调休
            date(2025, 10, 11), # 国庆节调休
        ]
    
    def is_trading_day(self, check_date: date) -> bool:
        """判断是否为交易日"""
        # 检查是否为节假日
        if check_date in self.holidays_2025:
            return False
        
        # 检查是否为周末（但排除调休工作日）
        if check_date.weekday() >= 5:  # 周六=5, 周日=6
            return check_date in self.makeup_workdays_2025
        
        return True
    
    def get_last_trading_day(self, from_date: Optional[date] = None) -> date:
        """获取最近的交易日"""
        if from_date is None:
            from_date = date.today()
        
        check_date = from_date - timedelta(days=1)
        
        # 向前查找最近的交易日（最多查找10天）
        for _ in range(10):
            if self.is_trading_day(check_date):
                return check_date
            check_date -= timedelta(days=1)
        
        # 如果10天内都没有交易日，返回一周前（保险起见）
        return from_date - timedelta(days=7)
    
    def get_next_trading_day(self, from_date: Optional[date] = None) -> date:
        """获取下一个交易日"""
        if from_date is None:
            from_date = date.today()
        
        check_date = from_date + timedelta(days=1)
        
        # 向后查找下一个交易日（最多查找10天）
        for _ in range(10):
            if self.is_trading_day(check_date):
                return check_date
            check_date += timedelta(days=1)
        
        # 如果10天内都没有交易日，返回一周后（保险起见）
        return from_date + timedelta(days=7)

class DailySyncScheduler:
    """每日同步调度器"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.calendar = TradingCalendar()
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/daily_sync.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_database_connection(self) -> bool:
        """检查数据库连接"""
        try:
            conn = mysql.connector.connect(
                host=self.db_config.host,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database,
                connection_timeout=10
            )
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            return False
    
    def get_stocks_need_update(self) -> List[Dict]:
        """获取需要更新的股票列表"""
        try:
            conn = mysql.connector.connect(
                host=self.db_config.host,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database,
                buffered=True
            )
            cursor = conn.cursor()
            
            # 获取所有股票的最新数据日期
            cursor.execute("""
                SELECT si.A股代码, si.A股简称, 
                       COALESCE(MAX(sh.日期), '1990-01-01') as latest_date,
                       COUNT(sh.日期) as record_count
                FROM stock_stock_info si
                LEFT JOIN stock_stock_zh_a_hist sh ON si.A股代码 = sh.股票代码
                GROUP BY si.A股代码, si.A股简称
                ORDER BY si.A股代码
            """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # 分析哪些股票需要更新
            last_trading_day = self.calendar.get_last_trading_day()
            needs_update = []
            
            for stock_code, stock_name, latest_date, record_count in results:
                # 转换日期格式
                if isinstance(latest_date, str):
                    latest_date = datetime.strptime(latest_date, '%Y-%m-%d').date()
                
                # 判断是否需要更新
                if latest_date < last_trading_day:
                    days_behind = (last_trading_day - latest_date).days
                    needs_update.append({
                        'code': stock_code,
                        'name': stock_name,
                        'latest_date': latest_date,
                        'days_behind': days_behind,
                        'record_count': record_count
                    })
            
            return needs_update
            
        except Exception as e:
            self.logger.error(f"获取需要更新的股票列表失败: {e}")
            return []
    
    def sync_stock_data(self, stock_code: str, stock_name: str) -> bool:
        """同步单只股票数据"""
        try:
            import subprocess
            
            # 调用现有的同步脚本
            cmd = [
                sys.executable, 
                'core/smart_stock_sync.py', 
                'continue', 
                stock_code
            ]
            
            self.logger.info(f"开始同步 {stock_code} ({stock_name})")
            
            # 执行同步命令
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,  # 5分钟超时
                input='y\n'  # 自动确认
            )
            
            if result.returncode == 0:
                self.logger.info(f"成功同步 {stock_code} ({stock_name})")
                return True
            else:
                self.logger.error(f"同步失败 {stock_code} ({stock_name}): {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"同步超时 {stock_code} ({stock_name})")
            return False
        except Exception as e:
            self.logger.error(f"同步异常 {stock_code} ({stock_name}): {e}")
            return False
    
    def run_daily_sync(self):
        """执行每日同步任务"""
        today = date.today()
        
        self.logger.info("=" * 60)
        self.logger.info(f"开始每日股票数据同步任务 - {today}")
        self.logger.info("=" * 60)
        
        # 检查今天是否需要同步
        if not self.should_sync_today():
            self.logger.info("今天不是交易日，跳过同步")
            return
        
        # 检查数据库连接
        if not self.check_database_connection():
            self.logger.error("数据库连接失败，终止同步任务")
            return
        
        # 获取需要更新的股票
        stocks_to_update = self.get_stocks_need_update()
        
        if not stocks_to_update:
            self.logger.info("所有股票数据都是最新的，无需同步")
            return
        
        self.logger.info(f"发现 {len(stocks_to_update)} 只股票需要更新")
        
        # 按落后天数排序，优先同步落后较多的股票
        stocks_to_update.sort(key=lambda x: x['days_behind'], reverse=True)
        
        # 执行同步
        success_count = 0
        failed_count = 0
        
        for i, stock in enumerate(stocks_to_update, 1):
            self.logger.info(f"[{i}/{len(stocks_to_update)}] 同步 {stock['code']} ({stock['name']}) - 落后 {stock['days_behind']} 天")
            
            if self.sync_stock_data(stock['code'], stock['name']):
                success_count += 1
            else:
                failed_count += 1
            
            # 每同步10只股票休息一下，避免过于频繁的请求
            if i % 10 == 0:
                self.logger.info("休息5秒...")
                time.sleep(5)
        
        # 同步结果统计
        self.logger.info("=" * 60)
        self.logger.info(f"每日同步任务完成")
        self.logger.info(f"成功: {success_count} 只, 失败: {failed_count} 只")
        self.logger.info("=" * 60)
    
    def should_sync_today(self) -> bool:
        """判断今天是否应该执行同步"""
        today = date.today()
        
        # 如果今天是交易日，检查昨天的数据
        if self.calendar.is_trading_day(today):
            return True
        
        # 如果今天不是交易日，但昨天是交易日，也需要同步
        yesterday = today - timedelta(days=1)
        if self.calendar.is_trading_day(yesterday):
            return True
        
        # 周一可能需要同步周五的数据
        if today.weekday() == 0:  # 周一
            friday = today - timedelta(days=3)
            if self.calendar.is_trading_day(friday):
                return True
        
        return False
    
    def start_scheduler(self):
        """启动定时调度器"""
        self.logger.info("启动每日股票数据同步调度器")
        
        # 设置定时任务
        # 工作日早上9:00执行（开盘前）
        schedule.every().monday.at("09:00").do(self.run_daily_sync)
        schedule.every().tuesday.at("09:00").do(self.run_daily_sync)
        schedule.every().wednesday.at("09:00").do(self.run_daily_sync)
        schedule.every().thursday.at("09:00").do(self.run_daily_sync)
        schedule.every().friday.at("09:00").do(self.run_daily_sync)
        
        # 工作日晚上18:00执行（收盘后）
        schedule.every().monday.at("18:00").do(self.run_daily_sync)
        schedule.every().tuesday.at("18:00").do(self.run_daily_sync)
        schedule.every().wednesday.at("18:00").do(self.run_daily_sync)
        schedule.every().thursday.at("18:00").do(self.run_daily_sync)
        schedule.every().friday.at("18:00").do(self.run_daily_sync)
        
        # 周末也检查一次（防止遗漏）
        schedule.every().saturday.at("10:00").do(self.run_daily_sync)
        
        self.logger.info("定时任务已设置:")
        self.logger.info("- 工作日 09:00 (开盘前同步)")
        self.logger.info("- 工作日 18:00 (收盘后同步)")
        self.logger.info("- 周六 10:00 (补充检查)")
        
        # 运行调度器
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                self.logger.info("收到停止信号，退出调度器")
                break
            except Exception as e:
                self.logger.error(f"调度器运行异常: {e}")
                time.sleep(300)  # 出错后等待5分钟再继续

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='每日股票数据同步调度器')
    parser.add_argument('--run-once', action='store_true', help='立即执行一次同步任务')
    parser.add_argument('--check-calendar', action='store_true', help='检查交易日历')
    
    args = parser.parse_args()
    
    scheduler = DailySyncScheduler()
    
    if args.check_calendar:
        # 检查交易日历
        today = date.today()
        print(f"今天 ({today}) 是否为交易日: {scheduler.calendar.is_trading_day(today)}")
        print(f"最近交易日: {scheduler.calendar.get_last_trading_day()}")
        print(f"下一交易日: {scheduler.calendar.get_next_trading_day()}")
        print(f"今天是否应该同步: {scheduler.should_sync_today()}")
        
    elif args.run_once:
        # 立即执行一次同步
        scheduler.run_daily_sync()
        
    else:
        # 启动定时调度器
        scheduler.start_scheduler()

if __name__ == "__main__":
    main()