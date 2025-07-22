# -*- coding: utf-8 -*-
"""
智能同步管理器
精确识别需要同步的股票，避免重复同步
"""
import mysql.connector
import sys
import os
import time
import argparse
from datetime import datetime, date, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database_config import DatabaseConfig

class SmartSyncManager:
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """连接数据库"""
        try:
            self.conn = mysql.connector.connect(
                host=self.db_config.host,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database,
                autocommit=True,
                buffered=True,
                use_unicode=True,
                charset='utf8mb4'
            )
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def close_db(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def analyze_sync_needs(self):
        """分析同步需求"""
        print("🔍 分析股票同步需求...")
        print("=" * 60)
        
        # 获取所有股票信息
        self.cursor.execute("""
            SELECT A股代码, A股简称, A股上市日期 
            FROM stock_stock_info 
            ORDER BY A股代码
        """)
        all_stocks = self.cursor.fetchall()
        
        # 获取历史数据统计
        self.cursor.execute("""
            SELECT 股票代码,
                   COUNT(*) as record_count,
                   MIN(日期) as earliest_date,
                   MAX(日期) as latest_date
            FROM stock_stock_zh_a_hist 
            GROUP BY 股票代码
        """)
        
        hist_data = {}
        for row in self.cursor.fetchall():
            stock_code, record_count, earliest_date, latest_date = row
            hist_data[stock_code] = {
                'record_count': record_count,
                'earliest_date': earliest_date,
                'latest_date': latest_date
            }
        
        # 分析同步需求
        needs_sync = []
        fully_synced = []
        
        today = date.today()
        # 更合理的时间阈值：工作日考虑，周末+节假日可能有3-5天没更新
        recent_threshold = today - timedelta(days=10)  # 10天内有更新就算正常
        
        for stock_code, stock_name, list_date in all_stocks:
            if stock_code not in hist_data:
                # 完全未同步
                needs_sync.append({
                    'code': stock_code,
                    'name': stock_name,
                    'list_date': list_date,
                    'reason': '完全未同步',
                    'priority': 1,
                    'record_count': 0
                })
            else:
                data = hist_data[stock_code]
                record_count = data['record_count']
                latest_date = data['latest_date']
                earliest_date = data['earliest_date']
                
                # 判断是否需要同步
                needs_update = False
                reason = ""
                priority = 3
                
                # 检查1: 完全没有数据（理论上不会到这里，但保险起见）
                if record_count == 0:
                    needs_update = True
                    reason = "无历史数据"
                    priority = 1
                
                # 检查2: 对于新上市股票（上市不到3个月），记录数过少才需要同步
                elif list_date and isinstance(list_date, date):
                    days_since_listing = (today - list_date).days
                    
                    if days_since_listing <= 90:  # 上市不到3个月的新股
                        # 新股的合理记录数应该大约是交易天数（约每月20个交易日）
                        expected_records = max(10, days_since_listing * 0.7)  # 考虑周末和节假日
                        if record_count < expected_records * 0.5:  # 少于预期的一半才认为需要同步
                            needs_update = True
                            reason = f"新股数据不足({record_count}条,预期>{expected_records:.0f}条)"
                            priority = 2
                    else:
                        # 老股票：记录数太少（少于100条明显异常）
                        if record_count < 100:
                            needs_update = True
                            reason = f"历史数据过少({record_count}条)"
                            priority = 2
                        
                        # 检查是否缺少早期数据
                        if earliest_date > list_date + timedelta(days=60):
                            needs_update = True
                            reason = f"缺少早期数据(上市:{list_date}, 最早:{earliest_date})"
                            priority = 2
                
                # 检查3: 数据时效性（只对有足够历史数据的股票检查）
                if not needs_update and record_count >= 100:
                    if latest_date < recent_threshold:
                        needs_update = True
                        reason = f"数据过旧(最新:{latest_date})"
                        priority = 3
                
                if needs_update:
                    needs_sync.append({
                        'code': stock_code,
                        'name': stock_name,
                        'list_date': list_date,
                        'reason': reason,
                        'priority': priority,
                        'record_count': record_count,
                        'latest_date': latest_date
                    })
                else:
                    fully_synced.append({
                        'code': stock_code,
                        'name': stock_name,
                        'record_count': record_count,
                        'latest_date': latest_date
                    })
        
        return needs_sync, fully_synced
    
    def generate_smart_sync_plan(self, needs_sync):
        """生成智能同步计划"""
        if not needs_sync:
            print("🎉 所有股票都已完全同步！")
            return
        
        print(f"\n📋 智能同步计划 ({len(needs_sync)} 只股票需要同步)")
        print("=" * 60)
        
        # 按优先级排序
        needs_sync.sort(key=lambda x: (x['priority'], x['record_count']))
        
        # 按优先级分组
        priority_groups = {1: [], 2: [], 3: []}
        for stock in needs_sync:
            priority_groups[stock['priority']].append(stock)
        
        # 显示同步计划
        priority_names = {
            1: "🔴 高优先级 - 完全未同步",
            2: "🟡 中优先级 - 数据不完整/过旧", 
            3: "🟢 低优先级 - 其他"
        }
        
        total_commands = 0
        sync_commands = []
        
        for priority in [1, 2, 3]:
            stocks = priority_groups[priority]
            if not stocks:
                continue
                
            print(f"\n{priority_names[priority]} ({len(stocks)} 只)")
            print("-" * 40)
            
            for i, stock in enumerate(stocks, 1):
                print(f"  {i:2d}. {stock['code']} ({stock['name']}) - {stock['reason']}")
                sync_commands.append(f"python core/smart_stock_sync.py continue {stock['code']}  # {stock['name']} - {stock['reason']}")
                total_commands += 1
        
        # 生成批量同步脚本
        self.generate_batch_script(sync_commands, needs_sync)
        
        return sync_commands
    
    def generate_batch_script(self, sync_commands, needs_sync):
        """生成批量同步脚本"""
        if not sync_commands:
            return
        
        # Windows批处理脚本
        bat_content = f"""@echo off
REM 智能股票数据同步脚本
REM 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
REM 需要同步的股票数量: {len(needs_sync)}

echo 开始智能股票数据同步...
echo 总共需要同步 {len(needs_sync)} 只股票
echo.

"""
        
        # 按优先级分组执行
        priority_groups = {1: [], 2: [], 3: []}
        for stock in needs_sync:
            priority_groups[stock['priority']].append(stock)
        
        priority_names = {
            1: "高优先级股票(完全未同步)",
            2: "中优先级股票(数据不完整/过旧)",
            3: "低优先级股票(其他)"
        }
        
        for priority in [1, 2, 3]:
            stocks = priority_groups[priority]
            if not stocks:
                continue
            
            bat_content += f"""echo ========================================
echo 开始同步{priority_names[priority]}
echo 数量: {len(stocks)} 只
echo ========================================

"""
            
            for stock in stocks:
                bat_content += f'python core/smart_stock_sync.py continue {stock["code"]}  REM {stock["name"]} - {stock["reason"]}\n'
            
            bat_content += "\necho.\n"
        
        bat_content += """echo ========================================
echo 智能同步完成！
echo ========================================
pause
"""
        
        # 保存脚本
        with open('scripts/smart_sync.bat', 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        # Linux脚本
        sh_content = bat_content.replace('@echo off', '#!/bin/bash')
        sh_content = sh_content.replace('REM ', '# ')
        sh_content = sh_content.replace('echo.', 'echo')
        sh_content = sh_content.replace('pause', 'read -p "按回车键继续..."')
        
        with open('scripts/smart_sync.sh', 'w', encoding='utf-8') as f:
            f.write(sh_content)
        
        print(f"\n🚀 智能同步脚本已生成:")
        print(f"  - Windows: scripts/smart_sync.bat")
        print(f"  - Linux/Mac: scripts/smart_sync.sh")
    
    def run_analysis(self):
        """运行完整分析"""
        start_time = time.time()
        
        if not self.connect_db():
            return None
        
        try:
            needs_sync, fully_synced = self.analyze_sync_needs()
            
            print(f"\n📊 同步需求分析结果:")
            print("=" * 60)
            print(f"✅ 已完全同步: {len(fully_synced):,} 只股票")
            print(f"⚠️  需要同步: {len(needs_sync):,} 只股票")
            print(f"📈 同步完成率: {len(fully_synced)/(len(fully_synced)+len(needs_sync))*100:.1f}%")
            
            if needs_sync:
                sync_commands = self.generate_smart_sync_plan(needs_sync)
                
                print(f"\n💡 执行建议:")
                print("-" * 40)
                print(f"1. 运行智能同步脚本: scripts/smart_sync.bat")
                print(f"2. 或者手动执行优先级高的股票同步")
                print(f"3. 同步完成后重新运行检查")
            else:
                print(f"\n🎉 恭喜！所有股票数据都已完全同步！")
            
            end_time = time.time()
            print(f"\n⏱️  分析耗时: {end_time - start_time:.2f} 秒")
            
            return {
                'needs_sync': needs_sync,
                'fully_synced': fully_synced,
                'sync_rate': len(fully_synced)/(len(fully_synced)+len(needs_sync))*100
            }
            
        finally:
            self.close_db()

def main():
    parser = argparse.ArgumentParser(description='智能股票同步管理器')
    parser.add_argument('--execute', action='store_true', help='执行同步计划')
    
    args = parser.parse_args()
    
    manager = SmartSyncManager()
    result = manager.run_analysis()
    
    if result and args.execute and result['needs_sync']:
        print(f"\n🚀 开始执行同步...")
        # 这里可以添加自动执行同步的逻辑
        pass

if __name__ == "__main__":
    main()