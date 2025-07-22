#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国股票数据同步系统 - 主程序入口
基于MVC架构的股票数据同步工具

@author: xionghao1012
@version: 2.0.0
@date: 2025-07-22
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from controllers.akshare_sync_controller import AKShareSyncController
from controllers.stock_controller import StockController
from views.console_view import ConsoleView
from utils.logger_util import LoggerUtil
from config.sync_config import SyncConfig

class StockSyncSystem:
    """股票数据同步系统主类"""
    
    def __init__(self):
        """初始化系统"""
        self.logger = LoggerUtil().get_logger(__name__)
        self.controller = AKShareSyncController()
        self.stock_controller = StockController()
        self.view = ConsoleView()
        self.config = SyncConfig()
        
    def interactive_mode(self):
        """交互模式"""
        self.view.show_welcome()
        
        while True:
            choice = self.view.show_main_menu()
            
            if choice == '1':
                self.sync_by_market()
            elif choice == '2':
                self.sync_by_stock_code()
            elif choice == '3':
                self.check_sync_status()
            elif choice == '4':
                self.optimize_database()
            elif choice == '5':
                self.view.show_goodbye()
                break
            else:
                self.view.show_error("无效选择，请重试")
    
    def sync_by_market(self):
        """按市场板块同步"""
        market_type = self.view.select_market_type()
        start_date = self.view.get_date_input("开始日期 (YYYYMMDD): ")
        end_date = self.view.get_date_input("结束日期 (YYYYMMDD): ")
        
        try:
            self.controller.sync_market_data(
                market_type=market_type,
                start_date=start_date,
                end_date=end_date
            )
            self.view.show_success("同步完成！")
        except Exception as e:
            self.view.show_error(f"同步失败: {str(e)}")
    
    def sync_by_stock_code(self):
        """按股票代码同步"""
        stock_code = self.view.get_stock_code()
        start_date = self.view.get_date_input("开始日期 (YYYYMMDD): ")
        end_date = self.view.get_date_input("结束日期 (YYYYMMDD): ")
        
        try:
            self.controller.sync_single_stock(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date
            )
            self.view.show_success("同步完成！")
        except Exception as e:
            self.view.show_error(f"同步失败: {str(e)}")
    
    def check_sync_status(self):
        """检查同步状态"""
        try:
            status = self.stock_controller.get_sync_status()
            self.view.show_sync_status(status)
        except Exception as e:
            self.view.show_error(f"获取状态失败: {str(e)}")
    
    def optimize_database(self):
        """优化数据库"""
        try:
            self.stock_controller.optimize_database()
            self.view.show_success("数据库优化完成！")
        except Exception as e:
            self.view.show_error(f"优化失败: {str(e)}")
    
    def batch_sync_mode(self, market_type, start_day, end_day):
        """批量同步模式"""
        try:
            self.controller.sync_market_data(
                market_type=market_type,
                start_date=start_day,
                end_date=end_day
            )
            return True
        except Exception as e:
            self.logger.error(f"批量同步失败: {str(e)}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='中国股票数据同步系统')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='启用交互模式')
    parser.add_argument('--var', type=str, choices=['RB', 'ZB', 'CYB', 'KCB'],
                        help='市场板块: RB(主板), ZB(中小板), CYB(创业板), KCB(科创板)')
    parser.add_argument('--start-day', type=str,
                        help='开始日期 (YYYYMMDD格式)')
    parser.add_argument('--end-day', type=str,
                        help='结束日期 (YYYYMMDD格式)')
    parser.add_argument('--stock', type=str,
                        help='单个股票代码')
    parser.add_argument('--optimize', action='store_true',
                        help='优化数据库')
    parser.add_argument('--status', action='store_true',
                        help='查看同步状态')
    
    args = parser.parse_args()
    
    system = StockSyncSystem()
    
    try:
        if args.interactive:
            system.interactive_mode()
        elif args.optimize:
            system.optimize_database()
        elif args.status:
            system.check_sync_status()
        elif args.stock and args.start_day and args.end_day:
            system.controller.sync_single_stock(
                stock_code=args.stock,
                start_date=args.start_day,
                end_date=args.end_day
            )
            print("✅ 单个股票同步完成")
        elif args.var and args.start_day and args.end_day:
            success = system.batch_sync_mode(
                market_type=args.var,
                start_day=args.start_day,
                end_day=args.end_day
            )
            if success:
                print("✅ 批量同步完成")
            else:
                print("❌ 批量同步失败")
                sys.exit(1)
        else:
            print("请使用 --help 查看使用说明")
            print("或直接运行: python main.py --interactive")
            
    except KeyboardInterrupt:
        print("\n\n👋 用户中断操作")
    except Exception as e:
        print(f"❌ 系统错误: {str(e)}")
        system.logger.error(f"系统错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()