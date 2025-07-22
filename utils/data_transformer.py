"""
数据转换工具 - 将键值对表转换为单行表
"""
import pandas as pd
from sqlalchemy import create_engine, text
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataTransformer:
    """数据转换工具类"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.engine = create_engine(
            db_config.get_connection_string(),
            **db_config.get_engine_config()
        )
    
    def transform_key_value_to_row(self, source_table: str, target_table: str = None, 
                                  key_column: str = 'item', value_column: str = 'value') -> bool:
        """
        将键值对表转换为单行表
        
        Args:
            source_table: 源表名
            target_table: 目标表名，如果为None则使用源表名_transformed
            key_column: 键列名
            value_column: 值列名
        
        Returns:
            bool: 转换是否成功
        """
        try:
            if target_table is None:
                target_table = f"{source_table}_transformed"
            
            logger.info(f"开始转换表 {source_table} 为单行格式...")
            
            # 读取源数据
            with self.engine.connect() as conn:
                df = pd.read_sql(f"SELECT * FROM {source_table}", conn)
            
            if df.empty:
                logger.warning(f"表 {source_table} 为空")
                return False
            
            # 转换为单行格式
            transformed_data = {}
            for _, row in df.iterrows():
                key = str(row[key_column]).strip()
                value = str(row[value_column]).strip()
                transformed_data[key] = value
            
            # 创建单行DataFrame
            result_df = pd.DataFrame([transformed_data])
            
            logger.info(f"转换后的列: {list(result_df.columns)}")
            logger.info(f"数据预览: {result_df.iloc[0].to_dict()}")
            
            # 保存到目标表
            with self.engine.begin() as conn:
                result_df.to_sql(
                    name=target_table,
                    con=conn,
                    if_exists='replace',
                    index=False
                )
            
            logger.info(f"成功将 {source_table} 转换为单行格式并保存到 {target_table}")
            return True
            
        except Exception as e:
            logger.error(f"转换表 {source_table} 失败: {e}")
            return False
    
    def batch_transform_individual_info(self) -> bool:
        """批量转换个股信息表"""
        try:
            # 获取所有个股信息相关的表
            with self.engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES LIKE '%individual_info%'"))
                tables = [row[0] for row in result.fetchall()]
            
            success_count = 0
            for table in tables:
                if self.transform_key_value_to_row(table):
                    success_count += 1
            
            logger.info(f"批量转换完成: {success_count}/{len(tables)} 个表转换成功")
            return success_count == len(tables)
            
        except Exception as e:
            logger.error(f"批量转换失败: {e}")
            return False
    
    def get_transformed_data(self, table_name: str) -> Optional[pd.DataFrame]:
        """获取转换后的数据"""
        try:
            transformed_table = f"{table_name}_transformed"
            with self.engine.connect() as conn:
                df = pd.read_sql(f"SELECT * FROM {transformed_table}", conn)
                return df
        except Exception as e:
            logger.error(f"获取转换后数据失败: {e}")
            return None
    
    def compare_before_after(self, table_name: str):
        """对比转换前后的数据"""
        try:
            print(f"\n=== 表 {table_name} 转换对比 ===")
            
            # 原始数据
            with self.engine.connect() as conn:
                original_df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            
            print("\n原始数据 (键值对格式):")
            print(original_df.to_string(index=False))
            
            # 转换后数据
            transformed_df = self.get_transformed_data(table_name)
            if transformed_df is not None:
                print(f"\n转换后数据 (单行格式):")
                print(transformed_df.to_string(index=False))
                
                print(f"\n转换后列数: {len(transformed_df.columns)}")
                print(f"转换后行数: {len(transformed_df)}")
            else:
                print("转换后数据获取失败")
                
        except Exception as e:
            logger.error(f"对比数据失败: {e}")
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")