"""
AKShare数据同步主程序
"""
import sys
import argparse
from controllers.akshare_sync_controller import AKShareSyncController


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AKShare数据同步系统')
    parser.add_argument('--category', '-c', 
                       choices=['stock', 'futures', 'fund', 'bond', 'forex', 'macro', 'news', 'industry'],
                       help='指定同步的数据分类')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='启用交互模式')
    parser.add_argument('--all', '-a', action='store_true',
                       help='同步所有数据')
    
    return parser.parse_args()


def main():
    """主程序"""
    controller = None
    
    try:
        args = parse_arguments()
        controller = AKShareSyncController()
        
        if not controller.initialize():
            return False
        
        if args.interactive:
            success = controller.interactive_sync()
        elif args.all:
            success = controller.sync_all_data()
        elif args.category:
            success = controller.sync_by_category(args.category)
        else:
            # 默认交互模式
            success = controller.interactive_sync()
        
        controller.view.show_completion_message(success)
        return success
        
    except KeyboardInterrupt:
        if controller:
            controller.view.show_info("程序被用户中断")
        return False
    except Exception as e:
        if controller:
            controller.view.show_error(f"程序执行错误: {e}")
        return False
    finally:
        if controller:
            controller.cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)