# -*- coding: utf-8 -*-
"""
检查股票数据同步状态
对比stock_stock_info表和stock_stock_zh_a_hist表，判断同步完成情况
"""
import mysql.connector
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database_config import DatabaseConfig
import pandas as pd
from datetime import datetime, date

def check_sync_status():
    """检查同步状态"""
    start_time = time.time()
    db_config = DatabaseConfig()
    
    try:
        # 连接数据库（优化连接参数）
        conn = mysql.connector.connect(
            host=db_config.host,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            autocommit=True,
            buffered=True,  # 启用缓冲，提高查询性能
            use_unicode=True,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        print("🔍 正在检查股票数据同步状态...")
        print("=" * 80)
        
        # 1. 获取所有股票信息
        print("📊 获取股票信息表数据...")
        cursor.execute("""
            SELECT A股代码, A股简称, A股上市日期 
            FROM stock_stock_info 
            ORDER BY A股代码
        """)
        
        all_stocks = cursor.fetchall()
        total_stocks = len(all_stocks)
        
        print(f"📈 股票信息表总数: {total_stocks} 只股票")
        
        # 2. 一次性获取所有股票的历史数据统计（优化性能）
        print("\n🔍 检查历史数据同步情况...")
        print("  正在执行批量查询，请稍候...")
        
        # 使用一次查询获取所有股票的统计信息
        cursor.execute("""
            SELECT 股票代码,
                   COUNT(*) as record_count,
                   MIN(日期) as earliest_date,
                   MAX(日期) as latest_date
            FROM stock_stock_zh_a_hist 
            GROUP BY 股票代码
        """)
        
        # 将结果转换为字典，便于快速查找
        hist_data = {}
        total_records = 0
        for row in cursor.fetchall():
            stock_code, record_count, earliest_date, latest_date = row
            hist_data[stock_code] = {
                'record_count': record_count,
                'earliest_date': earliest_date,
                'latest_date': latest_date
            }
            total_records += record_count
        
        print(f"  已获取 {len(hist_data)} 只股票的历史数据统计")
        
        # 3. 对比股票信息表和历史数据表
        synced_stocks = []
        unsynced_stocks = []
        partial_synced = []
        synced_count = 0
        
        print("  正在分析同步状态...")
        for i, (stock_code, stock_name, list_date) in enumerate(all_stocks, 1):
            # 显示进度
            if i % 1000 == 0 or i == total_stocks:
                print(f"  进度: {i}/{total_stocks} ({i/total_stocks*100:.1f}%)")
            
            if stock_code in hist_data:
                synced_count += 1
                data = hist_data[stock_code]
                record_count = data['record_count']
                
                # 检查数据完整性（简单检查：是否有足够的历史数据）
                if record_count >= 100:  # 假设正常股票应该有至少100条历史记录
                    synced_stocks.append({
                        'code': stock_code,
                        'name': stock_name,
                        'list_date': list_date,
                        'record_count': record_count,
                        'earliest_date': data['earliest_date'],
                        'latest_date': data['latest_date']
                    })
                else:
                    partial_synced.append({
                        'code': stock_code,
                        'name': stock_name,
                        'list_date': list_date,
                        'record_count': record_count,
                        'earliest_date': data['earliest_date'],
                        'latest_date': data['latest_date']
                    })
            else:
                unsynced_stocks.append({
                    'code': stock_code,
                    'name': stock_name,
                    'list_date': list_date
                })
        
        # 3. 生成统计报告
        print("\n" + "=" * 80)
        print("📊 同步状态统计报告")
        print("=" * 80)
        
        print(f"📈 股票总数: {total_stocks:,} 只")
        print(f"✅ 已同步股票: {len(synced_stocks):,} 只 ({len(synced_stocks)/total_stocks*100:.1f}%)")
        print(f"⚠️  部分同步股票: {len(partial_synced):,} 只 ({len(partial_synced)/total_stocks*100:.1f}%)")
        print(f"❌ 未同步股票: {len(unsynced_stocks):,} 只 ({len(unsynced_stocks)/total_stocks*100:.1f}%)")
        print(f"📊 历史数据总记录数: {total_records:,} 条")
        
        # 4. 按股票代码段分析（优化：一次遍历完成统计）
        print(f"\n📋 按股票代码段分析:")
        print("-" * 60)
        
        code_segments = {}
        # 一次遍历完成所有统计
        for stock_code, stock_name, list_date in all_stocks:
            segment = stock_code[:3]  # 取前3位作为代码段
            if segment not in code_segments:
                code_segments[segment] = {'total': 0, 'synced': 0}
            code_segments[segment]['total'] += 1
            
            # 同时检查是否已同步
            if stock_code in hist_data:
                code_segments[segment]['synced'] += 1
        
        for segment in sorted(code_segments.keys()):
            total = code_segments[segment]['total']
            synced = code_segments[segment]['synced']
            rate = synced/total*100 if total > 0 else 0
            status = "✅" if rate == 100 else "⚠️" if rate >= 90 else "❌"
            print(f"  {status} {segment}xxx: {synced:4d}/{total:4d} ({rate:5.1f}%)")
        
        # 5. 显示未同步的股票（如果数量不多）
        if len(unsynced_stocks) > 0:
            print(f"\n❌ 未同步的股票 ({len(unsynced_stocks)} 只):")
            print("-" * 60)
            
            if len(unsynced_stocks) <= 50:  # 如果不超过50只，全部显示
                for stock in unsynced_stocks:
                    print(f"  {stock['code']} ({stock['name']}) - 上市日期: {stock['list_date']}")
            else:  # 否则只显示前20只
                for stock in unsynced_stocks[:20]:
                    print(f"  {stock['code']} ({stock['name']}) - 上市日期: {stock['list_date']}")
                print(f"  ... 还有 {len(unsynced_stocks) - 20} 只股票未显示")
        
        # 6. 显示部分同步的股票
        if len(partial_synced) > 0:
            print(f"\n⚠️  部分同步的股票 ({len(partial_synced)} 只):")
            print("-" * 60)
            
            if len(partial_synced) <= 20:
                for stock in partial_synced:
                    print(f"  {stock['code']} ({stock['name']}) - 记录数: {stock['record_count']}")
            else:
                for stock in partial_synced[:10]:
                    print(f"  {stock['code']} ({stock['name']}) - 记录数: {stock['record_count']}")
                print(f"  ... 还有 {len(partial_synced) - 10} 只股票未显示")
        
        # 7. 数据质量分析
        if synced_stocks:
            print(f"\n📊 数据质量分析:")
            print("-" * 60)
            
            # 计算平均记录数
            avg_records = sum(s['record_count'] for s in synced_stocks) / len(synced_stocks)
            print(f"  平均历史记录数: {avg_records:.0f} 条/股票")
            
            # 找出记录数最多和最少的股票
            max_stock = max(synced_stocks, key=lambda x: x['record_count'])
            min_stock = min(synced_stocks, key=lambda x: x['record_count'])
            
            print(f"  记录数最多: {max_stock['code']} ({max_stock['name']}) - {max_stock['record_count']:,} 条")
            print(f"  记录数最少: {min_stock['code']} ({min_stock['name']}) - {min_stock['record_count']:,} 条")
            
            # 数据时间范围
            earliest_dates = [s['earliest_date'] for s in synced_stocks if s['earliest_date']]
            latest_dates = [s['latest_date'] for s in synced_stocks if s['latest_date']]
            
            if earliest_dates and latest_dates:
                overall_earliest = min(earliest_dates)
                overall_latest = max(latest_dates)
                print(f"  数据时间范围: {overall_earliest} 至 {overall_latest}")
        
        # 8. 生成建议
        print(f"\n💡 建议:")
        print("-" * 60)
        
        if len(unsynced_stocks) > 0:
            print(f"  1. 需要同步 {len(unsynced_stocks)} 只未同步的股票")
            print(f"     可以使用: python core/smart_stock_sync.py continue <股票代码>")
        
        if len(partial_synced) > 0:
            print(f"  2. 需要补充 {len(partial_synced)} 只部分同步股票的数据")
            print(f"     建议重新同步这些股票")
        
        if len(unsynced_stocks) == 0 and len(partial_synced) == 0:
            print(f"  🎉 所有股票数据已完全同步！")
        
        # 9. 保存详细报告到文件
        save_detailed_report(synced_stocks, partial_synced, unsynced_stocks, total_stocks, total_records)
        
        # 10. 显示执行时间统计
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"\n⏱️  执行时间统计:")
        print("-" * 60)
        print(f"  总执行时间: {execution_time:.2f} 秒")
        print(f"  平均处理速度: {total_stocks/execution_time:.0f} 只股票/秒")
        if total_records > 0:
            print(f"  数据处理速度: {total_records/execution_time:.0f} 条记录/秒")
        
        cursor.close()
        conn.close()
        
        return {
            'total_stocks': total_stocks,
            'synced_count': len(synced_stocks),
            'partial_count': len(partial_synced),
            'unsynced_count': len(unsynced_stocks),
            'total_records': total_records,
            'unsynced_stocks': unsynced_stocks,
            'execution_time': execution_time
        }
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return None

def save_detailed_report(synced_stocks, partial_synced, unsynced_stocks, total_stocks, total_records):
    """保存详细报告到文件"""
    try:
        report_content = f"""# 股票数据同步状态详细报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 总体统计

- 股票总数: {total_stocks:,} 只
- 已同步股票: {len(synced_stocks):,} 只 ({len(synced_stocks)/total_stocks*100:.1f}%)
- 部分同步股票: {len(partial_synced):,} 只 ({len(partial_synced)/total_stocks*100:.1f}%)
- 未同步股票: {len(unsynced_stocks):,} 只 ({len(unsynced_stocks)/total_stocks*100:.1f}%)
- 历史数据总记录数: {total_records:,} 条

## 未同步股票详细列表

"""
        
        if unsynced_stocks:
            report_content += "| 股票代码 | 股票名称 | 上市日期 |\n"
            report_content += "|----------|----------|----------|\n"
            for stock in unsynced_stocks:
                report_content += f"| {stock['code']} | {stock['name']} | {stock['list_date']} |\n"
        else:
            report_content += "🎉 所有股票都已同步！\n"
        
        if partial_synced:
            report_content += "\n## 部分同步股票详细列表\n\n"
            report_content += "| 股票代码 | 股票名称 | 记录数 | 最早日期 | 最新日期 |\n"
            report_content += "|----------|----------|--------|----------|----------|\n"
            for stock in partial_synced:
                report_content += f"| {stock['code']} | {stock['name']} | {stock['record_count']} | {stock['earliest_date']} | {stock['latest_date']} |\n"
        
        # 保存到logs目录
        with open('logs/sync_status_report.md', 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📄 详细报告已保存到: logs/sync_status_report.md")
        
    except Exception as e:
        print(f"⚠️  保存报告失败: {e}")

def generate_sync_commands(unsynced_stocks):
    """生成同步命令"""
    if not unsynced_stocks:
        return
    
    print(f"\n🚀 生成同步命令:")
    print("-" * 60)
    
    # 按代码段分组
    segments = {}
    for stock in unsynced_stocks:
        segment = stock['code'][:3]
        if segment not in segments:
            segments[segment] = []
        segments[segment].append(stock)
    
    for segment in sorted(segments.keys()):
        stocks = segments[segment]
        if len(stocks) == 1:
            stock = stocks[0]
            print(f"# 同步 {segment}xxx 系列 (1只)")
            print(f"python core/smart_stock_sync.py continue {stock['code']}")
        else:
            first_stock = min(stocks, key=lambda x: x['code'])
            print(f"# 同步 {segment}xxx 系列 ({len(stocks)}只)")
            print(f"python core/smart_stock_sync.py continue {first_stock['code']}")
        print()

if __name__ == "__main__":
    result = check_sync_status()
    
    if result and result['unsynced_count'] > 0:
        print(f"\n" + "=" * 80)
        generate_sync_commands(result['unsynced_stocks'])