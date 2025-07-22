# -*- coding: utf-8 -*-
"""
增强版股票数据同步状态检查工具
包含索引检查、数据一致性验证、批量同步命令生成等功能
"""
import mysql.connector
import sys
import os
import time
import argparse
from collections import defaultdict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database_config import DatabaseConfig
from datetime import datetime, date, timedelta

class EnhancedSyncChecker:
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
    
    def is_stock_fully_synced(self, stock_code, stock_name, list_date, record_count, earliest_date, latest_date):
        """智能判断股票是否完全同步"""
        today = date.today()
        recent_threshold = today - timedelta(days=10)  # 10天内有更新就算正常
        
        # 检查1: 完全没有数据
        if record_count == 0:
            return False
        
        # 检查2: 对于新上市股票（上市不到3个月），记录数过少才需要同步
        if list_date and isinstance(list_date, date):
            days_since_listing = (today - list_date).days
            
            if days_since_listing <= 90:  # 上市不到3个月的新股
                # 新股的合理记录数应该大约是交易天数（约每月20个交易日）
                expected_records = max(10, days_since_listing * 0.7)  # 考虑周末和节假日
                if record_count < expected_records * 0.5:  # 少于预期的一半才认为需要同步
                    return False
            else:
                # 老股票：记录数太少（少于100条明显异常）
                if record_count < 100:
                    return False
                
                # 检查是否缺少早期数据
                if earliest_date > list_date + timedelta(days=60):
                    return False
        
        # 检查3: 数据时效性（只对有足够历史数据的股票检查）
        if record_count >= 100:
            if latest_date < recent_threshold:
                return False
        
        return True
    
    def check_database_indexes(self):
        """检查数据库索引状态"""
        print("🔍 检查数据库索引状态...")
        print("-" * 60)
        
        # 检查股票信息表索引
        self.cursor.execute("""
            SHOW INDEX FROM stock_stock_info
        """)
        info_indexes = self.cursor.fetchall()
        
        # 检查历史数据表索引
        self.cursor.execute("""
            SHOW INDEX FROM stock_stock_zh_a_hist
        """)
        hist_indexes = self.cursor.fetchall()
        
        print("📊 stock_stock_info 表索引:")
        for idx in info_indexes:
            print(f"  - {idx[2]} ({idx[4]})")
        
        print("\n📊 stock_stock_zh_a_hist 表索引:")
        for idx in hist_indexes:
            print(f"  - {idx[2]} ({idx[4]})")
        
        # 检查是否有推荐的索引
        hist_code_indexed = any('股票代码' in str(idx[4]) for idx in hist_indexes)
        hist_date_indexed = any('日期' in str(idx[4]) for idx in hist_indexes)
        
        print(f"\n💡 索引建议:")
        if not hist_code_indexed:
            print("  ⚠️  建议在 stock_stock_zh_a_hist.股票代码 上创建索引")
            print("     CREATE INDEX idx_stock_code ON stock_stock_zh_a_hist(股票代码);")
        else:
            print("  ✅ 股票代码索引已存在")
            
        if not hist_date_indexed:
            print("  ⚠️  建议在 stock_stock_zh_a_hist.日期 上创建索引")
            print("     CREATE INDEX idx_date ON stock_stock_zh_a_hist(日期);")
        else:
            print("  ✅ 日期索引已存在")
    
    def check_data_consistency(self):
        """检查数据一致性"""
        print("\n🔍 检查数据一致性...")
        print("-" * 60)
        
        # 检查重复数据
        self.cursor.execute("""
            SELECT 股票代码, 日期, COUNT(*) as cnt
            FROM stock_stock_zh_a_hist
            GROUP BY 股票代码, 日期
            HAVING COUNT(*) > 1
            LIMIT 10
        """)
        
        duplicates = self.cursor.fetchall()
        if duplicates:
            print(f"⚠️  发现重复数据 ({len(duplicates)} 组):")
            for dup in duplicates[:5]:
                print(f"  - {dup[0]} {dup[1]}: {dup[2]} 条重复记录")
            if len(duplicates) > 5:
                print(f"  ... 还有 {len(duplicates) - 5} 组重复数据")
        else:
            print("✅ 未发现重复数据")
        
        # 检查数据完整性（价格为0或负数的异常数据）
        self.cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM stock_stock_zh_a_hist
            WHERE 开盘 <= 0 OR 收盘 <= 0 OR 最高 <= 0 OR 最低 <= 0
        """)
        
        invalid_price = self.cursor.fetchone()[0]
        if invalid_price > 0:
            print(f"⚠️  发现异常价格数据: {invalid_price:,} 条记录")
        else:
            print("✅ 价格数据正常")
        
        # 检查日期连续性（抽样检查几只股票）
        self.cursor.execute("""
            SELECT 股票代码 FROM stock_stock_zh_a_hist 
            GROUP BY 股票代码 
            HAVING COUNT(*) > 1000 
            ORDER BY RAND() 
            LIMIT 3
        """)
        
        sample_stocks = [row[0] for row in self.cursor.fetchall()]
        
        print(f"\n📅 日期连续性检查 (抽样 {len(sample_stocks)} 只股票):")
        for stock_code in sample_stocks:
            self.cursor.execute("""
                SELECT 日期 FROM stock_stock_zh_a_hist 
                WHERE 股票代码 = %s 
                ORDER BY 日期
            """, (stock_code,))
            
            dates = [row[0] for row in self.cursor.fetchall()]
            if len(dates) > 1:
                # 计算日期间隔
                gaps = []
                for i in range(1, len(dates)):
                    gap = (dates[i] - dates[i-1]).days
                    if gap > 7:  # 超过7天的间隔可能是异常
                        gaps.append(gap)
                
                if gaps:
                    avg_gap = sum(gaps) / len(gaps)
                    print(f"  {stock_code}: 发现 {len(gaps)} 个较大日期间隔，平均 {avg_gap:.1f} 天")
                else:
                    print(f"  {stock_code}: 日期连续性良好")
    
    def analyze_sync_patterns(self, synced_stocks, partial_synced, unsynced_stocks):
        """分析同步模式和趋势"""
        print("\n📈 同步模式分析:")
        print("-" * 60)
        
        # 按上市年份分析
        year_stats = defaultdict(lambda: {'total': 0, 'synced': 0, 'partial': 0, 'unsynced': 0})
        
        all_stocks_data = []
        for stock in synced_stocks:
            all_stocks_data.append(('synced', stock))
        for stock in partial_synced:
            all_stocks_data.append(('partial', stock))
        for stock in unsynced_stocks:
            all_stocks_data.append(('unsynced', stock))
        
        for status, stock in all_stocks_data:
            if 'list_date' in stock and stock['list_date']:
                year = stock['list_date'].year if hasattr(stock['list_date'], 'year') else int(str(stock['list_date'])[:4])
                year_stats[year]['total'] += 1
                year_stats[year][status] += 1
        
        print("📊 按上市年份统计:")
        recent_years = sorted([y for y in year_stats.keys() if y >= 2020], reverse=True)
        for year in recent_years[:10]:  # 显示最近10年
            stats = year_stats[year]
            total = stats['total']
            synced_rate = (stats['synced'] + stats['partial']) / total * 100 if total > 0 else 0
            status_icon = "✅" if synced_rate == 100 else "⚠️" if synced_rate >= 90 else "❌"
            print(f"  {status_icon} {year}年: {stats['synced']+stats['partial']:3d}/{total:3d} ({synced_rate:5.1f}%)")
        
        # 分析部分同步股票的特征
        if partial_synced:
            print(f"\n⚠️  部分同步股票特征分析:")
            record_counts = [s['record_count'] for s in partial_synced]
            avg_records = sum(record_counts) / len(record_counts)
            min_records = min(record_counts)
            max_records = max(record_counts)
            
            print(f"  平均记录数: {avg_records:.0f} 条")
            print(f"  记录数范围: {min_records} - {max_records} 条")
            
            # 按记录数分组
            very_low = len([r for r in record_counts if r < 30])
            low = len([r for r in record_counts if 30 <= r < 100])
            
            print(f"  记录数 < 30: {very_low} 只 (可能是新上市)")
            print(f"  记录数 30-99: {low} 只 (数据不完整)")
    
    def generate_sync_scripts(self, unsynced_stocks, partial_synced):
        """生成同步脚本"""
        print(f"\n🚀 生成同步脚本:")
        print("-" * 60)
        
        # 生成批量同步脚本
        script_content = "#!/bin/bash\n"
        script_content += "# 股票数据批量同步脚本\n"
        script_content += f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if unsynced_stocks:
            script_content += "echo '开始同步未同步的股票...'\n"
            for stock in unsynced_stocks:
                script_content += f"python core/smart_stock_sync.py continue {stock['code']}  # {stock['name']}\n"
            script_content += "\n"
        
        if partial_synced:
            script_content += "echo '开始补充部分同步的股票数据...'\n"
            # 优先同步记录数很少的股票
            sorted_partial = sorted(partial_synced, key=lambda x: x['record_count'])
            for stock in sorted_partial:
                script_content += f"python core/smart_stock_sync.py continue {stock['code']}  # {stock['name']} ({stock['record_count']}条)\n"
        
        script_content += "\necho '同步完成！'\n"
        
        # 保存脚本文件
        with open('scripts/batch_sync.sh', 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 生成Windows批处理文件
        bat_content = script_content.replace('#!/bin/bash', '@echo off')
        bat_content = bat_content.replace('echo ', 'echo ')
        bat_content = bat_content.replace("echo '", 'echo ')
        bat_content = bat_content.replace("'", '')
        
        with open('scripts/batch_sync.bat', 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        print(f"✅ 批量同步脚本已生成:")
        print(f"  - Linux/Mac: scripts/batch_sync.sh")
        print(f"  - Windows: scripts/batch_sync.bat")
        
        # 显示优先级建议
        if unsynced_stocks or partial_synced:
            print(f"\n📋 同步优先级建议:")
            print(f"  1. 优先同步完全未同步的股票 ({len(unsynced_stocks)} 只)")
            print(f"  2. 补充记录数很少的股票 (< 30条记录)")
            print(f"  3. 补充其他部分同步的股票")
    
    def run_full_check(self, check_indexes=True, check_consistency=True):
        """运行完整检查"""
        start_time = time.time()
        
        if not self.connect_db():
            return None
        
        try:
            print("🔍 正在执行增强版股票数据同步检查...")
            print("=" * 80)
            
            # 1. 检查索引（可选）
            if check_indexes:
                self.check_database_indexes()
            
            # 2. 获取股票信息
            print(f"\n📊 获取股票信息表数据...")
            self.cursor.execute("""
                SELECT A股代码, A股简称, A股上市日期 
                FROM stock_stock_info 
                ORDER BY A股代码
            """)
            
            all_stocks = self.cursor.fetchall()
            total_stocks = len(all_stocks)
            print(f"📈 股票信息表总数: {total_stocks} 只股票")
            
            # 3. 批量获取历史数据统计
            print(f"\n🔍 检查历史数据同步情况...")
            print("  正在执行批量查询，请稍候...")
            
            self.cursor.execute("""
                SELECT 股票代码,
                       COUNT(*) as record_count,
                       MIN(日期) as earliest_date,
                       MAX(日期) as latest_date
                FROM stock_stock_zh_a_hist 
                GROUP BY 股票代码
            """)
            
            hist_data = {}
            total_records = 0
            for row in self.cursor.fetchall():
                stock_code, record_count, earliest_date, latest_date = row
                hist_data[stock_code] = {
                    'record_count': record_count,
                    'earliest_date': earliest_date,
                    'latest_date': latest_date
                }
                total_records += record_count
            
            print(f"  已获取 {len(hist_data)} 只股票的历史数据统计")
            
            # 4. 分析同步状态
            synced_stocks = []
            unsynced_stocks = []
            partial_synced = []
            
            for stock_code, stock_name, list_date in all_stocks:
                if stock_code in hist_data:
                    data = hist_data[stock_code]
                    record_count = data['record_count']
                    
                    stock_info = {
                        'code': stock_code,
                        'name': stock_name,
                        'list_date': list_date,
                        'record_count': record_count,
                        'earliest_date': data['earliest_date'],
                        'latest_date': data['latest_date']
                    }
                    
                    # 使用智能判断逻辑
                    if self.is_stock_fully_synced(stock_code, stock_name, list_date, 
                                                record_count, data['earliest_date'], data['latest_date']):
                        synced_stocks.append(stock_info)
                    else:
                        partial_synced.append(stock_info)
                else:
                    unsynced_stocks.append({
                        'code': stock_code,
                        'name': stock_name,
                        'list_date': list_date
                    })
            
            # 5. 显示统计结果
            print(f"\n" + "=" * 80)
            print("📊 同步状态统计报告")
            print("=" * 80)
            
            print(f"📈 股票总数: {total_stocks:,} 只")
            print(f"✅ 已同步股票: {len(synced_stocks):,} 只 ({len(synced_stocks)/total_stocks*100:.1f}%)")
            print(f"⚠️  部分同步股票: {len(partial_synced):,} 只 ({len(partial_synced)/total_stocks*100:.1f}%)")
            print(f"❌ 未同步股票: {len(unsynced_stocks):,} 只 ({len(unsynced_stocks)/total_stocks*100:.1f}%)")
            print(f"📊 历史数据总记录数: {total_records:,} 条")
            
            # 6. 数据一致性检查（可选）
            if check_consistency:
                self.check_data_consistency()
            
            # 7. 同步模式分析
            self.analyze_sync_patterns(synced_stocks, partial_synced, unsynced_stocks)
            
            # 8. 生成同步脚本
            if unsynced_stocks or partial_synced:
                self.generate_sync_scripts(unsynced_stocks, partial_synced)
            
            # 9. 执行时间统计
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"\n⏱️  执行时间统计:")
            print("-" * 60)
            print(f"  总执行时间: {execution_time:.2f} 秒")
            print(f"  平均处理速度: {total_stocks/execution_time:.0f} 只股票/秒")
            
            return {
                'total_stocks': total_stocks,
                'synced_count': len(synced_stocks),
                'partial_count': len(partial_synced),
                'unsynced_count': len(unsynced_stocks),
                'total_records': total_records,
                'execution_time': execution_time
            }
            
        finally:
            self.close_db()

def main():
    parser = argparse.ArgumentParser(description='增强版股票数据同步状态检查工具')
    parser.add_argument('--no-indexes', action='store_true', help='跳过索引检查')
    parser.add_argument('--no-consistency', action='store_true', help='跳过数据一致性检查')
    parser.add_argument('--quick', action='store_true', help='快速模式（跳过索引和一致性检查）')
    
    args = parser.parse_args()
    
    checker = EnhancedSyncChecker()
    
    check_indexes = not (args.no_indexes or args.quick)
    check_consistency = not (args.no_consistency or args.quick)
    
    result = checker.run_full_check(
        check_indexes=check_indexes,
        check_consistency=check_consistency
    )
    
    if result:
        print(f"\n🎉 检查完成！")
        if result['unsynced_count'] == 0 and result['partial_count'] == 0:
            print("所有股票数据已完全同步！")
        else:
            print(f"还需要同步 {result['unsynced_count'] + result['partial_count']} 只股票")

if __name__ == "__main__":
    main()