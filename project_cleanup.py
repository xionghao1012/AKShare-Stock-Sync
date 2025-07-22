# -*- coding: utf-8 -*-
"""
项目清理工具
用于清理项目中生成的临时文件、缓存和日志
"""

import os
import shutil
import logging
from datetime import datetime, timedelta

class ProjectCleanup:
    """项目清理类"""
    
    def __init__(self):
        """初始化清理工具"""
        self.logger = logging.getLogger(__name__)
        # 定义需要清理的目录和文件模式
        self.cleanup_patterns = {
            'pycache': {'pattern': '__pycache__', 'type': 'dir'}, 
            'logs': {'pattern': 'logs', 'type': 'dir', 'keep_days': 7}, 
            'temp_files': {'pattern': '.tmp', 'type': 'file'}, 
            'pyc_files': {'pattern': '.pyc', 'type': 'file'}, 
            'log_files': {'pattern': '.log', 'type': 'file', 'keep_days': 7}, 
            'dist_dir': {'pattern': 'dist', 'type': 'dir'}, 
            'build_dir': {'pattern': 'build', 'type': 'dir'}, 
            'egg_info': {'pattern': '.egg-info', 'type': 'dir'}
        }
    
    def clean_project(self, root_dir, dry_run=False):
        """清理项目中的临时文件和目录
        
        Args:
            root_dir (str): 项目根目录
            dry_run (bool): 是否模拟清理，不实际删除文件
        
        Returns:
            dict: 清理结果统计
        """
        stats = {
            'deleted_files': 0,
            'deleted_dirs': 0,
            'kept_files': 0,
            'kept_dirs': 0,
            'errors': []
        }
        
        self.logger.info(f"开始{'模拟' if dry_run else ''}清理项目: {root_dir}")
        
        # 遍历所有清理模式
        for pattern_name, pattern_info in self.cleanup_patterns.items():
            try:
                if pattern_info['type'] == 'dir':
                    dir_stats = self._clean_directories(
                        root_dir, pattern_info['pattern'], 
                        pattern_info.get('keep_days'), dry_run
                    )
                    stats['deleted_dirs'] += dir_stats['deleted']
                    stats['kept_dirs'] += dir_stats['kept']
                else:
                    file_stats = self._clean_files(
                        root_dir, pattern_info['pattern'], 
                        pattern_info.get('keep_days'), dry_run
                    )
                    stats['deleted_files'] += file_stats['deleted']
                    stats['kept_files'] += file_stats['kept']
            except Exception as e:
                error_msg = f"清理{pattern_name}时出错: {str(e)}"
                self.logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        self.logger.info(f"{'模拟' if dry_run else ''}清理完成: 删除文件{stats['deleted_files']}个, 删除目录{stats['deleted_dirs']}个, 保留文件{stats['kept_files']}个, 保留目录{stats['kept_dirs']}个, 错误{len(stats['errors'])}个")
        return stats
    
    def _clean_directories(self, root_dir, dir_name, keep_days=None, dry_run=False):
        """清理指定名称的目录
        
        Args:
            root_dir (str): 根目录
            dir_name (str): 要清理的目录名称
            keep_days (int): 保留最近几天的目录，None表示全部清理
            dry_run (bool): 是否模拟清理
        
        Returns:
            dict: 清理统计
        """
        stats = {'deleted': 0, 'kept': 0}
        
        for dirpath, dirnames, _ in os.walk(root_dir):
            if dir_name in dirnames:
                dir_path = os.path.join(dirpath, dir_name)
                
                # 检查是否需要保留
                if keep_days is not None:
                    modified_time = datetime.fromtimestamp(os.path.getmtime(dir_path))
                    if datetime.now() - modified_time < timedelta(days=keep_days):
                        stats['kept'] += 1
                        continue
                
                # 执行删除
                self.logger.debug(f"将{'模拟' if dry_run else ''}删除目录: {dir_path}")
                if not dry_run:
                    try:
                        shutil.rmtree(dir_path)
                        stats['deleted'] += 1
                    except Exception as e:
                        self.logger.error(f"删除目录失败: {dir_path}, 错误: {e}")
                else:
                    stats['deleted'] += 1
        
        return stats
    
    def _clean_files(self, root_dir, file_ext, keep_days=None, dry_run=False):
        """清理指定扩展名的文件
        
        Args:
            root_dir (str): 根目录
            file_ext (str): 文件扩展名
            keep_days (int): 保留最近几天的文件，None表示全部清理
            dry_run (bool): 是否模拟清理
        
        Returns:
            dict: 清理统计
        """
        stats = {'deleted': 0, 'kept': 0}
        
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith(file_ext):
                    file_path = os.path.join(dirpath, filename)
                    
                    # 检查是否需要保留
                    if keep_days is not None:
                        modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if datetime.now() - modified_time < timedelta(days=keep_days):
                            stats['kept'] += 1
                            continue
                    
                    # 执行删除
                    self.logger.debug(f"将{'模拟' if dry_run else ''}删除文件: {file_path}")
                    if not dry_run:
                        try:
                            os.remove(file_path)
                            stats['deleted'] += 1
                        except Exception as e:
                            self.logger.error(f"删除文件失败: {file_path}, 错误: {e}")
                    else:
                        stats['deleted'] += 1
        
        return stats

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取当前脚本所在目录作为项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 创建清理实例并执行清理
    cleaner = ProjectCleanup()
    result = cleaner.clean_project(project_root, dry_run=False)
    
    # 打印结果
    print("清理结果:")
    print(f"删除文件: {result['deleted_files']}个")
    print(f"删除目录: {result['deleted_dirs']}个")
    print(f"保留文件: {result['kept_files']}个")
    print(f"保留目录: {result['kept_dirs']}个")
    if result['errors']:
        print(f"错误: {len(result['errors'])}个")
        for error in result['errors']:
            print(f"- {error}")