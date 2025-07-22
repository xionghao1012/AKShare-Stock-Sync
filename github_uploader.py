# -*- coding: utf-8 -*-
"""
GitHub上传工具
用于将项目文件批量上传到GitHub仓库
"""

import os
import json
import requests
from config.sync_config import SyncConfig

class GitHubUploader:
    """GitHub上传器类"""
    
    def __init__(self, token):
        """初始化GitHub上传器
        
        Args:
            token (str): GitHub访问令牌
        """
        self.config = SyncConfig()
        self.token = token
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def upload_file(self, owner, repo, branch, file_path, content, message):
        """上传单个文件到GitHub仓库
        
        Args:
            owner (str): 仓库所有者
            repo (str): 仓库名称
            branch (str): 分支名称
            file_path (str): 文件路径
            content (str): 文件内容
            message (str): 提交信息
        
        Returns:
            bool: 上传是否成功
        """
        try:
            # 获取文件SHA（如果已存在）
            sha = self._get_file_sha(owner, repo, file_path, branch)
            
            # 构建API URL
            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}'
            
            # 构建请求数据
            data = {
                'message': message,
                'content': content.encode('utf-8').hex(),
                'branch': branch
            }
            
            # 如果文件已存在，添加SHA进行更新
            if sha:
                data['sha'] = sha
            
            # 发送请求
            response = requests.put(url, headers=self.headers, json=data, timeout=self.config.timeout)
            response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"文件上传失败: {file_path}, 错误: {e}")
            return False
    
    def _get_file_sha(self, owner, repo, file_path, branch):
        """获取文件的SHA值（用于更新文件）
        
        Args:
            owner (str): 仓库所有者
            repo (str): 仓库名称
            file_path (str): 文件路径
            branch (str): 分支名称
        
        Returns:
            str: 文件SHA值，如果文件不存在则返回None
        """
        try:
            url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}'
            response = requests.get(url, headers=self.headers, timeout=self.config.timeout)
            
            if response.status_code == 200:
                return response.json().get('sha')
            return None
        except Exception as e:
            print(f"获取文件SHA失败: {file_path}, 错误: {e}")
            return None
    
    def batch_upload(self, owner, repo, branch, file_list, message):
        """批量上传文件
        
        Args:
            owner (str): 仓库所有者
            repo (str): 仓库名称
            branch (str): 分支名称
            file_list (list): 文件列表，每个元素是包含'path'和'content'的字典
            message (str): 提交信息
        
        Returns:
            dict: 上传结果，包含成功和失败的文件列表
        """
        result = {
            'success': [],
            'failed': []
        }
        
        for file_info in file_list:
            file_path = file_info['path']
            content = file_info['content']
            
            if self.upload_file(owner, repo, branch, file_path, content, message):
                result['success'].append(file_path)
            else:
                result['failed'].append(file_path)
        
        return result

if __name__ == '__main__':
    # 示例用法
    import sys
    if len(sys.argv) < 2:
        print("用法: python github_uploader.py <github_token>")
        sys.exit(1)
        
    token = sys.argv[1]
    uploader = GitHubUploader(token)
    
    # 这里只是示例，实际使用时应该动态获取文件列表
    example_files = [
        {'path': 'example.txt', 'content': '这是一个示例文件'}
    ]
    
    result = uploader.batch_upload('xionghao1012', 'AKShare-Stock-Sync', 'main', example_files, '示例文件上传')
    print(f"上传完成: 成功{len(result['success'])}个, 失败{len(result['failed'])}个")