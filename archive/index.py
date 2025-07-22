import akshare as ak
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging
import os
from datetime import datetime
from typing import Optional

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_data.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- 数据库配置 ---
class DatabaseConfig:
    def __init__(self):
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '84694296')
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '3306')
        self.database = os.getenv('DB_NAME', 'stock')
        self.table_name = os.getenv('TABLE_NAME', 'roll_yield_bar')
    
    def get_connection_string(self) -> str:
        return f'mysql+mysqlconnector://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'

# --- 数据获取和处理类 ---
class StockDataProcessor:
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.engine = None
    
    def create_database_connection(self) -> bool:
        """创建数据库连接"""
        try:
            logger.info("正在连接数据库...")
            self.engine = create_engine(
                self.db_config.get_connection_string(),
                pool_pre_ping=True,  # 连接池预检查
                pool_recycle=3600,   # 连接回收时间
                echo=False           # 设置为True可以看到SQL语句
            )
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"成功连接到数据库 '{self.db_config.database}'")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def fetch_roll_yield_data(self, var: str = "RB", start_day: str = "20180618", 
                             end_day: str = "20180718") -> Optional[pd.DataFrame]:
        """获取期货收益率数据"""
        try:
            logger.info(f"正在获取 {var} 的期货收益率数据 ({start_day} 到 {end_day})...")
            
            # 验证日期格式
            datetime.strptime(start_day, '%Y%m%d')
            datetime.strptime(end_day, '%Y%m%d')
            
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
            logger.info(f"数据列: {list(df.columns)}")
            
            # 数据清洗
            df = self.clean_data(df)
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
            # 删除重复行
            original_count = len(df)
            df = df.drop_duplicates()
            if len(df) < original_count:
                logger.info(f"删除了 {original_count - len(df)} 条重复数据")
            
            # 处理空值
            null_counts = df.isnull().sum()
            if null_counts.sum() > 0:
                logger.warning(f"发现空值: {null_counts[null_counts > 0].to_dict()}")
                # 可以根据需要选择填充或删除空值
                df = df.dropna()
            
            return df
            
        except Exception as e:
            logger.error(f"数据清洗失败: {e}")
            return df
    
    def save_to_database(self, df: pd.DataFrame, if_exists: str = 'replace') -> bool:
        """保存数据到数据库"""
        if df is None or df.empty:
            logger.error("没有数据可以保存")
            return False
        
        try:
            logger.info(f"正在将 {len(df)} 条记录写入表 '{self.db_config.table_name}'...")
            
            # 使用事务确保数据一致性
            with self.engine.begin() as conn:
                df.to_sql(
                    name=self.db_config.table_name,
                    con=conn,
                    if_exists=if_exists,
                    index=False,
                    method='multi',  # 批量插入优化
                    chunksize=1000   # 分批处理大数据集
                )
            
            logger.info("数据成功写入MySQL数据库")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"数据库写入失败: {e}")
            return False
        except Exception as e:
            logger.error(f"保存数据时发生未知错误: {e}")
            return False
    
    def verify_data_integrity(self) -> bool:
        """验证数据完整性"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {self.db_config.table_name}"))
                count = result.scalar()
                logger.info(f"数据库中共有 {count} 条记录")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"数据验证失败: {e}")
            return False
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")

# --- 主程序 ---
def main():
    """主程序入口"""
    processor = None
    
    try:
        # 初始化配置和处理器
        db_config = DatabaseConfig()
        processor = StockDataProcessor(db_config)
        
        # 创建数据库连接
        if not processor.create_database_connection():
            logger.error("无法连接到数据库，程序退出")
            return False
        
        # 获取数据
        df = processor.fetch_roll_yield_data(
            var="RB", 
            start_day="20180618", 
            end_day="20180718"
        )
        
        if df is None:
            logger.error("数据获取失败，程序退出")
            return False
        
        # 显示数据预览
        logger.info("数据预览:")
        logger.info(f"\n{df.head()}")
        logger.info(f"数据形状: {df.shape}")
        
        # 保存到数据库
        if processor.save_to_database(df):
            # 验证数据完整性
            processor.verify_data_integrity()
            logger.info("程序执行成功完成")
            return True
        else:
            logger.error("数据保存失败")
            return False
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        return False
    except Exception as e:
        logger.error(f"程序执行过程中发生未预期的错误: {e}")
        return False
    finally:
        # 确保资源清理
        if processor:
            processor.close_connection()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)