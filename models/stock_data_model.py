"""
股票数据模型 - 负责数据的获取、清洗和存储
"""
import akshare as ak
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class StockDataModel:
    """股票数据模型类"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.engine = None
    
    def connect_database(self) -> bool:
        """建立数据库连接"""
        try:
            logger.info("正在连接数据库...")
            self.engine = create_engine(
                self.db_config.get_connection_string(),
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"成功连接到数据库 '{self.db_config.database}'")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def fetch_roll_yield_data(self, params: Dict[str, str]) -> Optional[pd.DataFrame]:
        """获取期货收益率数据"""
        try:
            var = params.get('var', 'RB')
            start_day = params.get('start_day', '20180618')
            end_day = params.get('end_day', '20180718')
            
            logger.info(f"正在获取 {var} 的期货收益率数据 ({start_day} 到 {end_day})...")
            
            # 验证日期格式
            self._validate_date_format(start_day)
            self._validate_date_format(end_day)
            
            df = ak.get_roll_yield_bar(
                type_method="date",
                var=var,
                start_day=start_day,
                end_day=end_day
            )
            
            if df is None or df.empty:
                logger.warning("获取的数据为空")
                return None
            
            logger.info(f"成功获取 {len(df)} 条数据记录")
            return df
            
        except ValueError as e:
            logger.error(f"日期格式错误: {e}")
            return None
        except Exception as e:
            logger.error(f"数据获取失败: {e}")
            return None
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗"""
        try:
            if df is None or df.empty:
                return df
            
            original_count = len(df)
            
            # 删除重复行
            df = df.drop_duplicates()
            if len(df) < original_count:
                logger.info(f"删除了 {original_count - len(df)} 条重复数据")
            
            # 处理空值
            null_counts = df.isnull().sum()
            if null_counts.sum() > 0:
                logger.warning(f"发现空值: {null_counts[null_counts > 0].to_dict()}")
                df = df.dropna()
            
            return df
            
        except Exception as e:
            logger.error(f"数据清洗失败: {e}")
            return df
    
    def save_data(self, df: pd.DataFrame, if_exists: str = 'replace') -> bool:
        """保存数据到数据库"""
        if df is None or df.empty:
            logger.error("没有数据可以保存")
            return False
        
        try:
            logger.info(f"正在将 {len(df)} 条记录写入表 '{self.db_config.table_name}'...")
            
            with self.engine.begin() as conn:
                df.to_sql(
                    name=self.db_config.table_name,
                    con=conn,
                    if_exists=if_exists,
                    index=False,
                    method='multi',
                    chunksize=1000
                )
            
            logger.info("数据成功写入MySQL数据库")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"数据库写入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"保存数据时发生未知错误: {e}")
            return False
    
    def get_data_count(self) -> Optional[int]:
        """获取数据库中的记录数"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {self.db_config.table_name}"))
                return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"查询数据数量失败: {e}")
            return None
    
    def get_data_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """获取数据信息"""
        if df is None or df.empty:
            return {}
        
        return {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum()
        }
    
    def _validate_date_format(self, date_str: str) -> None:
        """验证日期格式"""
        datetime.strptime(date_str, '%Y%m%d')
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")