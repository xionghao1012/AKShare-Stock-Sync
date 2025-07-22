"""
主程序入口 - MVC架构版本
"""
import sys
import argparse
from controllers.stock_controller import StockDataController
import logging

logger = logging.getLogger(__name__)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='中国股票数据收集系统')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='启用交互模式')
    parser.add_argument('--var', default='RB', 
                       help='品种代码 (默认: RB)')
    parser.add_argument('--start-day', default='20180618', 
                       help='开始日期 YYYYMMDD (默认: 20180618)')
    parser.add_argument('--end-day', default='20180718', 
                       help='结束日期 YYYYMMDD (默认: 20180718)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='日志级别')
    
    return parser.parse_args()


def main():
    """主程序入口"""
    controller = None
    
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 创建控制器
        controller = StockDataController()
        
        # 初始化系统
        if not controller.initialize():
            logger.error("系统初始化失败")
            return False
        
        # 根据参数选择运行模式
        if args.interactive:
            # 交互模式
            success = controller.interactive_mode()
        else:
            # 自动模式
            params = {
                'var': args.var,
                'start_day': args.start_day,
                'end_day': args.end_day
            }
            success = controller.fetch_and_process_data(params)
        
        # 显示完成信息
        controller.view.show_completion_message(success)
        return success
        
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        if controller:
            controller.view.show_info("程序被用户中断")
        return False
        
    except Exception as e:
        logger.error(f"程序执行过程中发生未预期的错误: {e}")
        if controller:
            controller.view.show_error(f"未预期的错误: {e}")
        return False
        
    finally:
        # 清理资源
        if controller:
            controller.cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)