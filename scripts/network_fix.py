# -*- coding: utf-8 -*-
"""
网络问题修复工具 - 解决akshare接口连接问题
"""
import os
import requests
import akshare as ak
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import logging

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NetworkFixer:
    """网络连接修复器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        
    def disable_proxy(self):
        """禁用代理设置"""
        try:
            # 清除环境变量中的代理设置
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
            for var in proxy_vars:
                if var in os.environ:
                    del os.environ[var]
                    print(f"已清除代理环境变量: {var}")
            
            # 设置requests不使用代理
            os.environ['NO_PROXY'] = '*'
            print("已禁用所有代理设置")
            return True
            
        except Exception as e:
            print(f"禁用代理失败: {e}")
            return False
    
    def setup_robust_session(self):
        """设置健壮的网络会话"""
        try:
            # 创建会话
            self.session = requests.Session()
            
            # 设置重试策略
            retry_strategy = Retry(
                total=5,  # 总重试次数
                backoff_factor=2,  # 退避因子
                status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]  # 允许重试的方法
            )
            
            # 创建适配器
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=20
            )
            
            # 挂载适配器
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            
            # 设置超时和头部
            self.session.timeout = (10, 30)  # 连接超时10秒，读取超时30秒
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            })
            
            # 禁用代理
            self.session.proxies = {}
            
            print("网络会话配置完成")
            return True
            
        except Exception as e:
            print(f"设置网络会话失败: {e}")
            return False
    
    def test_network_connectivity(self):
        """测试网络连通性"""
        test_urls = [
            'https://push2his.eastmoney.com',
            'https://www.baidu.com',
            'https://httpbin.org/get'
        ]
        
        results = {}
        
        for url in test_urls:
            try:
                if self.session:
                    response = self.session.get(url, timeout=10, verify=False)
                else:
                    response = requests.get(url, timeout=10, verify=False, proxies={})
                
                results[url] = {
                    'status': 'success',
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
                print(f"✓ {url} - 状态码: {response.status_code}, 响应时间: {response.elapsed.total_seconds():.2f}s")
                
            except Exception as e:
                results[url] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"✗ {url} - 连接失败: {e}")
        
        return results
    
    def fix_akshare_network(self):
        """修复akshare网络问题"""
        try:
            print("开始修复akshare网络问题...")
            print("=" * 50)
            
            # 步骤1: 禁用代理
            print("步骤1: 禁用代理设置")
            self.disable_proxy()
            
            # 步骤2: 设置健壮的网络会话
            print("\n步骤2: 配置网络会话")
            self.setup_robust_session()
            
            # 步骤3: 测试网络连通性
            print("\n步骤3: 测试网络连通性")
            connectivity_results = self.test_network_connectivity()
            
            # 步骤4: 测试akshare接口
            print("\n步骤4: 测试akshare接口")
            self.test_akshare_apis()
            
            print("\n" + "=" * 50)
            print("网络修复完成！")
            
            return True
            
        except Exception as e:
            print(f"网络修复失败: {e}")
            return False
    
    def test_akshare_apis(self):
        """测试akshare接口（Windows兼容版本）"""
        test_apis = [
            {
                'name': '股票基本信息',
                'func': lambda: ak.stock_info_sz_name_code(),
                'expected_columns': ['A股代码', 'A股简称']
            },
            {
                'name': '股票历史数据',
                'func': lambda: ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20241201", end_date="20241201"),
                'expected_columns': ['日期', '开盘', '收盘']
            }
        ]
        
        for api_test in test_apis:
            try:
                print(f"测试 {api_test['name']}...")
                
                # Windows兼容的超时处理
                import threading
                import time
                
                result = {'data': None, 'error': None, 'completed': False}
                
                def api_call_thread():
                    try:
                        result['data'] = api_test['func']()
                        result['completed'] = True
                    except Exception as e:
                        result['error'] = e
                        result['completed'] = True
                
                # 启动线程
                thread = threading.Thread(target=api_call_thread)
                thread.daemon = True
                thread.start()
                
                # 等待最多10秒
                thread.join(timeout=10)
                
                if not result['completed']:
                    print(f"  ✗ API调用超时（10秒）")
                    continue
                
                if result['error']:
                    print(f"  ✗ 测试失败: {result['error']}")
                    continue
                
                df = result['data']
                if df is not None and not df.empty:
                    print(f"  ✓ 成功获取 {len(df)} 条数据")
                    
                    # 检查必需列
                    missing_cols = set(api_test['expected_columns']) - set(df.columns)
                    if missing_cols:
                        print(f"  ⚠ 缺少列: {missing_cols}")
                    else:
                        print(f"  ✓ 数据结构正确")
                        
                    # 显示前几行数据
                    print(f"  📊 数据预览:")
                    print(f"     列名: {list(df.columns)[:5]}")
                    if len(df) > 0:
                        print(f"     首行: {df.iloc[0].to_dict()}")
                else:
                    print(f"  ⚠ 返回数据为空")
                    
            except Exception as e:
                print(f"  ✗ 测试失败: {e}")
    
    def apply_akshare_patches(self):
        """应用akshare补丁"""
        try:
            print("应用akshare网络补丁...")
            
            # 修改akshare的默认请求设置
            import akshare.tool.tushare.cons as cons
            
            # 设置更长的超时时间
            if hasattr(cons, 'TIMEOUT'):
                cons.TIMEOUT = 30
            
            # 禁用代理
            if hasattr(cons, 'PROXIES'):
                cons.PROXIES = {}
            
            print("akshare补丁应用完成")
            return True
            
        except Exception as e:
            print(f"应用补丁失败: {e}")
            return False


def main():
    """主函数"""
    print("AKShare网络问题修复工具")
    print("=" * 50)
    
    fixer = NetworkFixer()
    
    try:
        # 执行修复
        success = fixer.fix_akshare_network()
        
        if success:
            print("\n修复建议:")
            print("1. 重新运行你的股票同步程序")
            print("2. 如果仍有问题，尝试更换网络环境")
            print("3. 考虑使用移动热点或其他网络连接")
            print("4. 检查防火墙和安全软件设置")
        else:
            print("\n修复失败，请检查:")
            print("1. 网络连接是否正常")
            print("2. 是否有防火墙阻止连接")
            print("3. DNS设置是否正确")
            print("4. 是否需要配置代理")
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"\n程序异常: {e}")


if __name__ == "__main__":
    main()