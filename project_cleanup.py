# -*- coding: utf-8 -*-
"""
项目清理脚本 - 整理项目目录结构
"""
import os
import shutil
from pathlib import Path

def cleanup_project():
    """清理项目目录"""
    
    # 创建新的目录结构
    directories = {
        'core': '核心功能模块',
        'tools': '工具脚本',
        'docs': '文档',
        'logs': '日志文件',
        'scripts': '辅助脚本',
        'archive': '归档文件'
    }
    
    # 创建目录
    for dir_name in directories:
        os.makedirs(dir_name, exist_ok=True)
        print(f"创建目录: {dir_name}/")
    
    # 文件分类规则
    file_moves = {
        # 核心功能模块
        'core/': [
            'smart_stock_sync.py',  # 主要同步工具
            'batch_sync_stocks.py',  # 批量同步核心
            'gentle_sync.py',  # 温和同步
        ],
        
        # 工具脚本
        'tools/': [
            'optimize_database.py',  # 数据库优化
            'check_tables.py',  # 表检查
            'system_monitor.py',  # 系统监控
        ],
        
        # 辅助脚本
        'scripts/': [
            'check_302_stocks.py',
            'get_302_stocks.py', 
            'continue_sync.py',
            'test_available_apis.py',
            'test_error_handling.py',
            'error_handling_demo.py',
            'network_fix.py',
            'transform_data.py',
        ],
        
        # 文档
        'docs/': [
            'README.md',
            'USAGE_GUIDE.md',
            'ERROR_HANDLING_GUIDE.md',
            '优化完成报告.md',
            '网络问题解决方案.md',
            '项目总结.md',
            'mysql_config_fix.sql',
        ],
        
        # 日志文件
        'logs/': [
            'demo.log',
            'error_handling_test.log',
            'stock_data.log',
            'stock_sync.log',
        ],
        
        # 归档文件（重复或过时的）
        'archive/': [
            'akshare_sync_main.py',  # 旧版本
            'auto_continue_sync.py',  # 功能重复
            'data_manager_main.py',  # 功能重复
            'resume_stock_sync.py',  # 功能重复
            'scheduler_main.py',  # 功能重复
            'start.py',  # 功能重复
            'index.py',  # 旧版本
        ]
    }
    
    # 移动文件
    for target_dir, files in file_moves.items():
        for file_name in files:
            if os.path.exists(file_name):
                try:
                    shutil.move(file_name, target_dir + file_name)
                    print(f"移动: {file_name} -> {target_dir}")
                except Exception as e:
                    print(f"移动失败 {file_name}: {e}")
    
    print("\n项目清理完成！")
    print("\n新的目录结构:")
    for dir_name, desc in directories.items():
        print(f"  {dir_name}/  - {desc}")

if __name__ == "__main__":
    cleanup_project()