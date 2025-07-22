# -*- coding: utf-8 -*-
"""
数据库优化工具
创建推荐的索引以提升查询性能
"""
import mysql.connector
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database_config import DatabaseConfig

def optimize_database():
    """优化数据库性能"""
    db_config = DatabaseConfig()
    
    try:
        conn = mysql.connector.connect(
            host=db_config.host,
            user=db_config.user,
            password=db_config.password,
            database=db_config.database,
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        print("🔧 正在优化数据库性能...")
        print("=" * 60)
        
        # 检查现有索引
        cursor.execute("SHOW INDEX FROM stock_stock_zh_a_hist")
        existing_indexes = [row[2] for row in cursor.fetchall()]
        
        print(f"📊 现有索引: {existing_indexes}")
        
        # 创建推荐的索引
        indexes_to_create = [
            {
                'name': 'idx_stock_code',
                'sql': 'CREATE INDEX idx_stock_code ON stock_stock_zh_a_hist(股票代码(10))',
                'description': '股票代码索引 - 提升按股票查询性能'
            },
            {
                'name': 'idx_date',
                'sql': 'CREATE INDEX idx_date ON stock_stock_zh_a_hist(日期)',
                'description': '日期索引 - 提升按日期查询性能'
            },
            {
                'name': 'idx_stock_date',
                'sql': 'CREATE INDEX idx_stock_date ON stock_stock_zh_a_hist(股票代码(10), 日期)',
                'description': '复合索引 - 提升股票+日期组合查询性能'
            }
        ]
        
        created_count = 0
        for index_info in indexes_to_create:
            if index_info['name'] not in existing_indexes:
                try:
                    print(f"🔨 创建索引: {index_info['name']}")
                    print(f"   描述: {index_info['description']}")
                    cursor.execute(index_info['sql'])
                    print(f"   ✅ 创建成功")
                    created_count += 1
                except Exception as e:
                    print(f"   ❌ 创建失败: {e}")
            else:
                print(f"⏭️  索引 {index_info['name']} 已存在，跳过")
        
        print(f"\n📊 优化结果:")
        print(f"  成功创建 {created_count} 个索引")
        
        if created_count > 0:
            print(f"\n💡 建议:")
            print(f"  - 索引创建后，查询性能将显著提升")
            print(f"  - 可以重新运行同步检查工具验证性能改善")
            print(f"  - 定期运行 ANALYZE TABLE 命令更新统计信息")
        
        # 显示表统计信息
        cursor.execute("SELECT COUNT(*) FROM stock_stock_zh_a_hist")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT 股票代码) FROM stock_stock_zh_a_hist")
        unique_stocks = cursor.fetchone()[0]
        
        print(f"\n📈 表统计信息:")
        print(f"  总记录数: {total_records:,}")
        print(f"  股票数量: {unique_stocks:,}")
        print(f"  平均每股记录数: {total_records/unique_stocks:.0f}")
        
        cursor.close()
        conn.close()
        
        return created_count
        
    except Exception as e:
        print(f"❌ 优化失败: {e}")
        return 0

if __name__ == "__main__":
    result = optimize_database()
    if result > 0:
        print(f"\n🎉 数据库优化完成！创建了 {result} 个索引")
    else:
        print(f"\n✅ 数据库已经是最优状态")