"""
AKShare数据同步模型 - 全面同步akshare数据到MySQL，优化错误处理
"""
import akshare as ak
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Float, Integer, DateTime, Text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging
import time
import json
from utils.error_handler import (
    ErrorHandler, SafeExecutor, DataValidator, 
    retry_on_error, RetryConfig, API_RETRY_CONFIG, DATABASE_RETRY_CONFIG
)

logger = logging.getLogger(__name__)


class AKShareSyncModel:
    """AKShare数据同步模型类"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.engine = None
        self.metadata = MetaData()
        self.error_handler = ErrorHandler(__name__)
        self.safe_executor = SafeExecutor(self.error_handler)
        
        # 定义数据源配置
        self.data_sources = {
            # 股票数据
            'stock': {
                'stock_info': {'func': 'stock_info_sz_name_code', 'params': {}, 'desc': '股票基本信息'},
                'stock_zh_a_hist': {'func': 'stock_zh_a_hist', 'params': {'symbol': '000001', 'period': 'daily'}, 'desc': 'A股历史数据'},
                'stock_individual_info_em': {'func': 'stock_individual_info_em', 'params': {'symbol': '000001'}, 'desc': '个股信息'},
                'stock_financial_abstract': {'func': 'stock_financial_abstract', 'params': {'symbol': '000001'}, 'desc': '财务摘要'},
            },
            
            # 期货数据
            'futures': {
                'futures_main_sina': {'func': 'futures_main_sina', 'params': {}, 'desc': '期货主力合约'},
                'futures_zh_spot': {'func': 'futures_zh_spot', 'params': {'symbol': 'RB'}, 'desc': '期货现货数据'},
                'get_roll_yield_bar': {'func': 'get_roll_yield_bar', 'params': {'type_method': 'date', 'var': 'RB'}, 'desc': '期货收益率'},
            },
            
            # 基金数据
            'fund': {
                'fund_etf_category_sina': {'func': 'fund_etf_category_sina', 'params': {'symbol': '股票型'}, 'desc': 'ETF分类'},
                'fund_open_fund_info_em': {'func': 'fund_open_fund_info_em', 'params': {}, 'desc': '开放式基金信息'},
            },
            
            # 债券数据
            'bond': {
                'bond_zh_us_rate': {'func': 'bond_zh_us_rate', 'params': {}, 'desc': '中美国债收益率'},
                'bond_china_yield': {'func': 'bond_china_yield', 'params': {}, 'desc': '中国国债收益率'},
            },
            
            # 外汇数据
            'forex': {
                'currency_boc_sina': {'func': 'currency_boc_sina', 'params': {}, 'desc': '中行外汇牌价'},
                'currency_latest': {'func': 'currency_latest', 'params': {}, 'desc': '实时汇率'},
            },
            
            # 宏观经济数据
            'macro': {
                'macro_china_gdp': {'func': 'macro_china_gdp', 'params': {}, 'desc': '中国GDP数据'},
                'macro_china_cpi': {'func': 'macro_china_cpi', 'params': {}, 'desc': '中国CPI数据'},
                'macro_china_ppi': {'func': 'macro_china_ppi', 'params': {}, 'desc': '中国PPI数据'},
                'macro_china_pmi': {'func': 'macro_china_pmi', 'params': {}, 'desc': '中国PMI数据'},
            },
            
            # 新闻舆情数据
            'news': {
                'stock_news_em': {'func': 'stock_news_em', 'params': {'symbol': '000001'}, 'desc': '股票新闻'},
                'news_cctv': {'func': 'news_cctv', 'params': {}, 'desc': '央视新闻'},
            },
            
            # 行业数据
            'industry': {
                'stock_board_industry_name_em': {'func': 'stock_board_industry_name_em', 'params': {}, 'desc': '行业板块'},
                'stock_board_concept_name_em': {'func': 'stock_board_concept_name_em', 'params': {}, 'desc': '概念板块'},
            }
        }
    
    @retry_on_error(DATABASE_RETRY_CONFIG)
    def connect_database(self) -> bool:
        """建立数据库连接，带重试机制"""
        try:
            logger.info("正在连接数据库...")
            self.engine = create_engine(
                self.db_config.get_connection_string(),
                **self.db_config.get_engine_config()
            )
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"成功连接到数据库 '{self.db_config.database}'")
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "数据库连接")
            return False
    
    def fetch_data_by_category(self, category: str) -> Dict[str, pd.DataFrame]:
        """按分类获取数据，带错误处理和重试机制"""
        results = {}
        
        if category not in self.data_sources:
            error_msg = f"未知的数据分类: {category}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        for data_name, config in self.data_sources[category].items():
            try:
                logger.info(f"正在获取 {config['desc']} 数据...")
                
                # 使用安全执行器调用API
                df = self.safe_executor.safe_api_call(
                    self._fetch_single_data_source,
                    config,
                    retry_config=API_RETRY_CONFIG
                )
                
                if df is not None and not df.empty:
                    # 验证数据
                    try:
                        DataValidator.validate_dataframe(df, min_rows=1)
                        results[data_name] = df
                        logger.info(f"成功获取 {len(df)} 条 {config['desc']} 数据")
                    except ValueError as e:
                        logger.warning(f"{config['desc']} 数据验证失败: {e}")
                        continue
                else:
                    logger.warning(f"{config['desc']} 数据为空")
                
                # 添加延时避免API限制
                time.sleep(1)
                
            except Exception as e:
                error_info = self.error_handler.handle_error(e, f"获取 {config['desc']} 数据")
                continue
        
        return results
    
    def _fetch_single_data_source(self, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """获取单个数据源的数据"""
        try:
            # 动态调用akshare函数
            func = getattr(ak, config['func'])
            df = func(**config['params'])
            return df
        except AttributeError as e:
            raise ValueError(f"未找到akshare函数: {config['func']}")
        except Exception as e:
            # 重新抛出异常，让重试机制处理
            raise e
    
    def sync_all_data(self) -> bool:
        """同步所有数据，带错误处理"""
        success_count = 0
        total_count = 0
        
        try:
            for category in self.data_sources.keys():
                logger.info(f"开始同步 {category} 类别数据...")
                
                # 安全获取分类数据
                data_dict = self.safe_executor.safe_execute(
                    self.fetch_data_by_category,
                    category,
                    default_return={},
                    context=f"获取 {category} 分类数据"
                )
                
                for data_name, df in data_dict.items():
                    total_count += 1
                    table_name = f"{category}_{data_name}"
                    
                    # 安全保存数据
                    save_result = self.safe_executor.safe_execute(
                        self.save_data_to_table,
                        df, table_name,
                        default_return=False,
                        context=f"保存 {table_name} 数据"
                    )
                    
                    if save_result:
                        success_count += 1
            
            logger.info(f"数据同步完成: {success_count}/{total_count} 成功")
            
            # 显示错误统计
            error_stats = self.error_handler.get_error_stats()
            if any(count > 0 for count in error_stats.values()):
                logger.info(f"错误统计: {error_stats}")
            
            return success_count == total_count
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, "同步所有数据")
            logger.error(f"同步所有数据失败: {error_info['message']}")
            return False
    
    @retry_on_error(DATABASE_RETRY_CONFIG)
    def save_data_to_table(self, df: pd.DataFrame, table_name: str) -> bool:
        """保存数据到指定表，带错误处理和重试机制"""
        try:
            # 验证输入数据
            DataValidator.validate_dataframe(df, min_rows=1)
            
            if not table_name or not isinstance(table_name, str):
                raise ValueError("表名不能为空且必须是字符串")
            
            logger.info(f"开始保存 {len(df)} 条数据到表 {table_name}")
            
            with self.engine.begin() as conn:
                df.to_sql(
                    name=table_name,
                    con=conn,
                    if_exists='replace',
                    index=False,
                    method='multi',
                    chunksize=1000
                )
            
            logger.info(f"数据成功保存到表 {table_name}")
            return True
            
        except Exception as e:
            error_info = self.error_handler.handle_error(e, f"保存数据到表 {table_name}")
            return False
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")
