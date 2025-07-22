"""
系统监控工具
"""
import time
import psutil
import mysql.connector
from datetime import datetime
from config.database_config import DatabaseConfig
from utils.data_manager import DataManager
from views.console_view import ConsoleView
import logging

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统监控类"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.data_manager = DataManager(self.db_config)
        self.view = ConsoleView()
    
    def get_system_info(self) -> dict:
        """获取系统信息"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_database_status(self) -> dict:
        """获取数据库状态"""
        try:
            conn = mysql.connector.connect(
                host=self.db_config.host,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database
            )
            
            cursor = conn.cursor()
            
            # 获取数据库大小
            cursor.execute(f"""
                SELECT 
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size (MB)'
                FROM information_schema.tables 
                WHERE table_schema = '{self.db_config.database}'
            """)
            db_size = cursor.fetchone()[0]
            
            # 获取表数量
            cursor.execute("SHOW TABLES")
            table_count = len(cursor.fetchall())
            
            # 获取连接数
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            connections = cursor.fetchone()[1]
            
            cursor.close()
            conn.close()
            
            return {
                'status': 'connected',
                'database_size_mb': db_size,
                'table_count': table_count,
                'connections': connections
            }
            
        except Exception as e:
            logger.error(f"获取数据库状态失败: {e}")
            return {'status': 'disconnected', 'error': str(e)}
    
    def get_table_statistics(self) -> list:
        """获取表统计信息"""
        tables = self.data_manager.get_table_list()
        stats = []
        
        for table in tables:
            info = self.data_manager.get_table_info(table)
            if info:
                stats.append({
                    'table_name': table,
                    'record_count': info.get('record_count', 0),
                    'last_updated': info.get('last_updated', 'N/A')
                })
        
        return sorted(stats, key=lambda x: x['record_count'], reverse=True)
    
    def display_dashboard(self):
        """显示监控面板"""
        while True:
            try:
                # 清屏
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("🖥️  AKShare数据同步系统监控面板")
                print("=" * 60)
                
                # 系统信息
                sys_info = self.get_system_info()
                print(f"⏰ 时间: {sys_info['timestamp']}")
                print(f"💻 CPU使用率: {sys_info['cpu_percent']:.1f}%")
                print(f"🧠 内存使用率: {sys_info['memory_percent']:.1f}%")
                print(f"💾 磁盘使用率: {sys_info['disk_percent']:.1f}%")
                
                print("\n" + "=" * 60)
                
                # 数据库状态
                db_status = self.get_database_status()
                if db_status['status'] == 'connected':
                    print("🗄️  数据库状态: ✅ 已连接")
                    print(f"📊 数据库大小: {db_status['database_size_mb']:.2f} MB")
                    print(f"📋 表数量: {db_status['table_count']}")
                    print(f"🔗 连接数: {db_status['connections']}")
                else:
                    print("🗄️  数据库状态: ❌ 连接失败")
                    print(f"❗ 错误: {db_status.get('error', 'Unknown')}")
                
                print("\n" + "=" * 60)
                
                # 表统计
                print("📈 数据表统计 (按记录数排序):")
                table_stats = self.get_table_statistics()
                for i, stat in enumerate(table_stats[:10], 1):  # 显示前10个表
                    print(f"{i:2d}. {stat['table_name']:<30} {stat['record_count']:>10,} 条")
                
                print("\n按 Ctrl+C 退出监控")
                time.sleep(5)  # 每5秒刷新一次
                
            except KeyboardInterrupt:
                print("\n👋 监控已停止")
                break
            except Exception as e:
                logger.error(f"监控面板错误: {e}")
                time.sleep(5)


def main():
    """主程序"""
    monitor = SystemMonitor()
    monitor.display_dashboard()


if __name__ == "__main__":
    main()