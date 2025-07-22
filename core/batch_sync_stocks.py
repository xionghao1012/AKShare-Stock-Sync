# -*- coding: utf-8 -*-
import akshare as ak
import mysql.connector
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database_config import DatabaseConfig
import time
from datetime import datetime
import logging
from utils.error_handler import (
    ErrorHandler, SafeExecutor, DataValidator, 
    retry_on_error, RetryConfig, API_RETRY_CONFIG, DATABASE_RETRY_CONFIG
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class BatchStockSync:
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.conn = None
        self.success_count = 0
        self.failed_count = 0
        self.error_handler = ErrorHandler(__name__)
        self.safe_executor = SafeExecutor(self.error_handler)
        self.logger = logging.getLogger(__name__)
    
    @retry_on_error(DATABASE_RETRY_CONFIG)
    def connect_database(self):
        """连接数据库，带重试机制"""
        try:
            self.conn = mysql.connector.connect(
                host=self.db_config.host,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database,
                autocommit=False,
                charset='utf8mb4',
                connect_timeout=30,
                pool_reset_session=True
            )
            self.logger.info("数据库连接成功")
            print("数据库连接成功")
            return True
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "数据库连接")
            print(f"数据库连接失败: {error_info['message']}")
            return False
    
    def get_stock_list(self, limit=50):
        """获取股票列表，带错误处理"""
        def _get_stocks(connection):
            cursor = connection.cursor()
            try:
                cursor.execute(f"SELECT A股代码, A股简称, A股上市日期 FROM stock_stock_info LIMIT {limit}")
                stocks = cursor.fetchall()
                self.logger.info(f"成功获取到 {len(stocks)} 只股票")
                print(f"获取到 {len(stocks)} 只股票")
                return stocks
            finally:
                cursor.close()
        
        result = self.safe_executor.safe_execute(
            _get_stocks, self.conn, 
            default_return=[], 
            context="获取股票列表"
        )
        return result if result is not None else []
    
    def sync_single_stock(self, stock_code, stock_name, list_date=None):
        """同步单只股票数据，带完整错误处理和数据验证"""
        try:
            # 验证股票代码
            DataValidator.validate_stock_code(stock_code)
            
            # 处理上市日期
            start_date = self._process_list_date(list_date)
            
            self.logger.info(f"开始同步股票 {stock_code} ({stock_name}) 从 {start_date}")
            print(f"正在同步 {stock_code} ({stock_name}) 从 {start_date} 开始")
            
            # 获取股票数据，带重试机制
            df = self._fetch_stock_data_with_retry(stock_code, start_date)
            if df is None:
                return False
            
            # 验证数据
            try:
                DataValidator.validate_dataframe(
                    df, 
                    min_rows=1,
                    required_columns=['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额']
                )
            except ValueError as e:
                self.error_handler.handle_error(e, f"数据验证失败 - {stock_code}")
                print(f"股票 {stock_code} 数据验证失败: {e}")
                return False
            
            # 保存数据到数据库
            if self._save_stock_data_to_db(stock_code, df):
                self.logger.info(f"成功同步股票 {stock_code}: {len(df)} 条记录")
                print(f"成功同步 {stock_code}: {len(df)} 条记录")
                return True
            else:
                return False
                
        except Exception as e:
            error_info = self.error_handler.handle_error(e, f"同步股票 {stock_code}")
            print(f"同步 {stock_code} 失败: {error_info['message']}")
            return False
    
    def _process_list_date(self, list_date):
        """处理上市日期格式"""
        if list_date:
            try:
                # 将日期格式从YYYY-MM-DD转换为YYYYMMDD
                if isinstance(list_date, str) and len(list_date) == 10:
                    start_date = list_date.replace('-', '')
                else:
                    start_date = str(list_date).replace('-', '')
                
                # 验证日期格式
                DataValidator.validate_date_format(start_date)
                return start_date
            except ValueError:
                self.logger.warning(f"日期格式错误: {list_date}，使用默认日期")
                return "19900101"
        else:
            return "19900101"  # 默认开始日期
    
    def _fetch_stock_data_with_retry(self, stock_code, start_date):
        """获取股票数据，带网络优化的重试机制"""
        # 网络优化配置
        retry_config = RetryConfig(max_retries=5, delay=3.0, backoff=1.5)
        
        @retry_on_error(retry_config)
        def _fetch_with_network_fix():
            try:
                # 临时禁用代理
                import os
                original_proxies = {}
                proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
                
                # 保存原始代理设置
                for var in proxy_vars:
                    if var in os.environ:
                        original_proxies[var] = os.environ[var]
                        del os.environ[var]
                
                try:
                    # 设置无代理环境
                    os.environ['NO_PROXY'] = '*'
                    
                    # 调用akshare接口
                    df = ak.stock_zh_a_hist(
                        symbol=stock_code,
                        period="daily", 
                        start_date=start_date,
                        end_date=datetime.now().strftime('%Y%m%d'),
                        adjust=""
                    )
                    
                    return df
                    
                finally:
                    # 恢复原始代理设置
                    for var, value in original_proxies.items():
                        os.environ[var] = value
                    if 'NO_PROXY' in os.environ:
                        del os.environ['NO_PROXY']
                        
            except Exception as e:
                # 重新抛出异常让重试机制处理
                raise e
        
        try:
            df = _fetch_with_network_fix()
            
            if df is None or df.empty:
                self.logger.warning(f"股票 {stock_code} 没有数据")
                print(f"股票 {stock_code} 没有数据")
                return None
            
            return df
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, f"获取股票数据 {stock_code}")
            print(f"获取股票 {stock_code} 数据失败: {error_info['message']}")
            return None
    
    def _save_stock_data_to_db(self, stock_code, df):
        """保存股票数据到数据库，带事务处理"""
        def _db_operation(connection):
            cursor = connection.cursor()
            try:
                # 删除旧数据
                cursor.execute("DELETE FROM stock_stock_zh_a_hist WHERE 股票代码 = %s", (stock_code,))
                
                # 批量插入新数据
                insert_query = """
                    INSERT INTO stock_stock_zh_a_hist 
                    (日期, 股票代码, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # 准备批量插入数据
                data_to_insert = []
                for _, row in df.iterrows():
                    data_to_insert.append((
                        row['日期'], stock_code, row['开盘'], row['收盘'], 
                        row['最高'], row['最低'], row['成交量'], row['成交额'],
                        row['振幅'], row['涨跌幅'], row['涨跌额'], row['换手率']
                    ))
                
                # 批量执行插入
                cursor.executemany(insert_query, data_to_insert)
                return True
                
            finally:
                cursor.close()
        
        return self.safe_executor.safe_database_operation(_db_operation, self.conn)
    
    def sync_by_stock_code(self, stock_code):
        """根据股票代码同步单只股票，带错误处理"""
        try:
            # 验证股票代码格式
            DataValidator.validate_stock_code(stock_code)
            
            def _get_stock_info(connection):
                cursor = connection.cursor()
                try:
                    cursor.execute("SELECT A股代码, A股简称, A股上市日期 FROM stock_stock_info WHERE A股代码 = %s", (stock_code,))
                    result = cursor.fetchone()
                    return result
                finally:
                    cursor.close()
            
            result = self.safe_executor.safe_execute(
                _get_stock_info, self.conn,
                default_return=None,
                context=f"查询股票信息 {stock_code}"
            )
            
            if not result:
                self.logger.warning(f"未找到股票代码: {stock_code}")
                print(f"未找到股票代码: {stock_code}")
                return False
            
            stock_code, stock_name, list_date = result
            self.logger.info(f"找到股票: {stock_code} ({stock_name})")
            print(f"找到股票: {stock_code} ({stock_name})")
            
            return self.sync_single_stock(stock_code, stock_name, list_date)
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, f"根据股票代码同步 {stock_code}")
            print(f"根据股票代码同步失败: {error_info['message']}")
            return False
    
    def sync_all_by_date(self, target_date):
        """按指定日期同步所有股票的当日数据，带完整错误处理"""
        try:
            # 验证日期格式
            DataValidator.validate_date_format(target_date)
            
            self.logger.info(f"开始按日期同步所有股票 {target_date} 的数据")
            print(f"开始同步所有股票 {target_date} 的数据")
            print("=" * 50)
            
            # 获取所有股票列表
            all_stocks = self._get_all_stocks_for_date_sync()
            if not all_stocks:
                return False
            
            print(f"共有 {len(all_stocks)} 只股票需要同步")
            self.logger.info(f"共有 {len(all_stocks)} 只股票需要同步")
            
            # 重置计数器
            self.success_count = 0
            self.failed_count = 0
            
            # 批量同步股票
            for i, (stock_code, stock_name) in enumerate(all_stocks, 1):
                success = self._sync_single_stock_by_date(
                    stock_code, stock_name, target_date, i, len(all_stocks)
                )
                
                if success:
                    self.success_count += 1
                else:
                    self.failed_count += 1
                
                # 进度控制和API限制处理
                self._handle_sync_progress(i, len(all_stocks))
            
            # 显示最终结果
            self._show_sync_summary()
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "按日期同步所有股票")
            print(f"按日期同步失败: {error_info['message']}")
            return False
    
    def _get_all_stocks_for_date_sync(self):
        """获取所有股票列表用于日期同步"""
        def _get_stocks(connection):
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT A股代码, A股简称 FROM stock_stock_info")
                stocks = cursor.fetchall()
                return stocks
            finally:
                cursor.close()
        
        return self.safe_executor.safe_execute(
            _get_stocks, self.conn,
            default_return=[],
            context="获取所有股票列表"
        )
    
    def _sync_single_stock_by_date(self, stock_code, stock_name, target_date, current_index, total_count):
        """同步单只股票的指定日期数据"""
        try:
            print(f"[{current_index}/{total_count}] 同步 {stock_code} ({stock_name}) {target_date} 数据")
            
            # 获取指定日期的数据，带重试机制
            df = self.safe_executor.safe_api_call(
                ak.stock_zh_a_hist,
                symbol=stock_code,
                period="daily",
                start_date=target_date,
                end_date=target_date,
                adjust="",
                retry_config=RetryConfig(max_retries=2, delay=1.0)
            )
            
            if df is None or df.empty:
                print(f"  {stock_code} 在 {target_date} 无数据")
                return True  # 无数据不算失败
            
            # 验证数据
            try:
                DataValidator.validate_dataframe(df, min_rows=1)
            except ValueError as e:
                print(f"  {stock_code} 数据验证失败: {e}")
                return False
            
            # 保存数据到数据库
            if self._save_single_date_data(stock_code, target_date, df):
                print(f"  成功同步 {len(df)} 条记录")
                return True
            else:
                return False
                
        except Exception as e:
            error_info = self.error_handler.handle_error(e, f"同步股票 {stock_code} 日期 {target_date}")
            print(f"  同步 {stock_code} 失败: {error_info['message']}")
            return False
    
    def _save_single_date_data(self, stock_code, target_date, df):
        """保存单只股票的单日数据"""
        def _db_operation(connection):
            cursor = connection.cursor()
            try:
                # 检查数据是否已存在
                cursor.execute(
                    "SELECT COUNT(*) FROM stock_stock_zh_a_hist WHERE 股票代码 = %s AND 日期 = %s",
                    (stock_code, target_date)
                )
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # 删除现有数据
                    cursor.execute(
                        "DELETE FROM stock_stock_zh_a_hist WHERE 股票代码 = %s AND 日期 = %s",
                        (stock_code, target_date)
                    )
                
                # 插入新数据
                insert_query = """
                    INSERT INTO stock_stock_zh_a_hist 
                    (日期, 股票代码, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                for _, row in df.iterrows():
                    cursor.execute(insert_query, (
                        row['日期'], stock_code, row['开盘'], row['收盘'],
                        row['最高'], row['最低'], row['成交量'], row['成交额'],
                        row['振幅'], row['涨跌幅'], row['涨跌额'], row['换手率']
                    ))
                
                return True
                
            finally:
                cursor.close()
        
        return self.safe_executor.safe_database_operation(_db_operation, self.conn)
    
    def _handle_sync_progress(self, current_index, total_count):
        """处理同步进度和API限制"""
        # 每10只股票休息一下，避免API限制
        if current_index % 10 == 0:
            time.sleep(2)
            print(f"  已处理 {current_index} 只股票，休息2秒...")
        
        # 每100只股票显示进度
        if current_index % 100 == 0:
            progress = current_index / total_count * 100
            print(f"  进度: {current_index}/{total_count} ({progress:.1f}%)")
            print(f"  成功: {self.success_count}, 失败: {self.failed_count}")
            self.logger.info(f"同步进度: {progress:.1f}%, 成功: {self.success_count}, 失败: {self.failed_count}")
    
    def _show_sync_summary(self):
        """显示同步结果摘要"""
        print("\n" + "=" * 50)
        print(f"按日期同步完成 - 成功: {self.success_count}, 失败: {self.failed_count}")
        
        # 显示错误统计
        error_stats = self.error_handler.get_error_stats()
        if any(count > 0 for count in error_stats.values()):
            print("\n错误统计:")
            for error_type, count in error_stats.items():
                if count > 0:
                    print(f"  {error_type}: {count}")
        
        self.logger.info(f"按日期同步完成 - 成功: {self.success_count}, 失败: {self.failed_count}")
        self.logger.info(f"错误统计: {error_stats}")

    def batch_sync(self, count=5):
        print("开始批量同步股票数据")
        print("=" * 40)
        
        stocks = self.get_stock_list(count)
        if not stocks:
            return False
        
        for i, (stock_code, stock_name, list_date) in enumerate(stocks, 1):
            print(f"[{i}/{len(stocks)}] ", end="")
            
            if self.sync_single_stock(stock_code, stock_name, list_date):
                self.success_count += 1
            else:
                self.failed_count += 1
            
            if i < len(stocks):
                time.sleep(2)
        
        print("\n" + "=" * 40)
        print(f"同步完成 - 成功: {self.success_count}, 失败: {self.failed_count}")
        return True
    
    def close(self):
        if self.conn:
            self.conn.close()

def main():
    import sys
    
    syncer = BatchStockSync()
    
    if not syncer.connect_database():
        return
    
    try:
        if len(sys.argv) == 1:
            # 交互模式
            interactive_mode(syncer)
        elif len(sys.argv) == 2:
            # 批量同步模式
            try:
                count = int(sys.argv[1])
                print(f"设置同步股票数量: {count}")
                if count > 20:
                    confirm = input(f"确认要同步 {count} 只股票吗？(y/N): ")
                    if confirm.lower() not in ['y', 'yes', '是']:
                        print("操作已取消")
                        return
                syncer.batch_sync(count)
            except ValueError:
                print("参数错误，进入交互模式")
                interactive_mode(syncer)
        elif len(sys.argv) == 3:
            # 特殊模式
            mode = sys.argv[1]
            param = sys.argv[2]
            
            if mode == "--code":
                # 根据股票代码同步
                print(f"根据股票代码同步: {param}")
                syncer.sync_by_stock_code(param)
            elif mode == "--date":
                # 按日期同步所有股票
                print(f"按日期同步所有股票: {param}")
                confirm = input(f"确认要同步所有股票在 {param} 的数据吗？这可能需要很长时间！(y/N): ")
                if confirm.lower() in ['y', 'yes', '是']:
                    syncer.sync_all_by_date(param)
                else:
                    print("操作已取消")
            else:
                print("未知模式，进入交互模式")
                interactive_mode(syncer)
        else:
            print("参数过多，进入交互模式")
            interactive_mode(syncer)
            
    finally:
        syncer.close()


def interactive_mode(syncer):
    """交互模式"""
    try:
        while True:
            print("\n" + "="*50)
            print("批量股票同步工具")
            print("="*50)
            print("1. 批量同步股票 (指定数量)")
            print("2. 根据股票代码同步")
            print("3. 按日期同步所有股票")
            print("4. 显示使用帮助")
            print("0. 退出")
            
            try:
                choice = input("\n请选择操作: ").strip()
            except EOFError:
                print("\n程序被中断，退出交互模式")
                break
            
            if choice == '0':
                break
            elif choice == '1':
                count = input("请输入要同步的股票数量 (默认10): ").strip()
                if not count:
                    count = 10
                else:
                    try:
                        count = int(count)
                    except ValueError:
                        print("输入无效，使用默认值10")
                        count = 10
                
                if count > 50:
                    confirm = input(f"确认要同步 {count} 只股票吗？(y/N): ")
                    if confirm.lower() not in ['y', 'yes', '是']:
                        continue
                
                syncer.batch_sync(count)
            
            elif choice == '2':
                stock_code = input("请输入股票代码 (如: 000001): ").strip()
                if stock_code:
                    syncer.sync_by_stock_code(stock_code)
                else:
                    print("股票代码不能为空")
                    
            elif choice == '3':
                date = input("请输入日期 (格式: YYYYMMDD, 如: 20241201): ").strip()
                if date and len(date) == 8:
                    try:
                        datetime.strptime(date, '%Y%m%d')
                        confirm = input(f"确认要同步所有股票在 {date} 的数据吗？这可能需要很长时间！(y/N): ")
                        if confirm.lower() in ['y', 'yes', '是']:
                            syncer.sync_all_by_date(date)
                        else:
                            print("操作已取消")
                    except ValueError:
                        print("日期格式错误，请使用 YYYYMMDD 格式")
                else:
                    print("日期格式错误，请使用 YYYYMMDD 格式")
                    
            elif choice == '4':
                show_help()
            else:
                print("无效的选择")
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"交互模式发生错误: {e}")
    
    print("退出交互模式")


def show_help():
    """显示帮助信息"""
    print("\n" + "="*60)
    print("批量股票同步工具使用说明")
    print("="*60)
    print("命令行用法:")
    print("  python batch_sync_stocks.py                    # 交互模式")
    print("  python batch_sync_stocks.py 10                 # 同步前10只股票")
    print("  python batch_sync_stocks.py --code 000001      # 同步指定股票")
    print("  python batch_sync_stocks.py --date 20241201    # 按日期同步所有股票")
    print()
    print("功能说明:")
    print("1. 批量同步: 按顺序同步指定数量的股票完整历史数据")
    print("2. 代码同步: 根据股票代码同步单只股票完整历史数据")
    print("3. 日期同步: 同步所有股票在指定日期的数据")
    print()
    print("注意事项:")
    print("- 历史数据从股票上市日期开始同步")
    print("- 大量同步时会自动添加延时避免API限制")
    print("- 数据会自动去重，重复同步会覆盖旧数据")


if __name__ == "__main__":
    main()
