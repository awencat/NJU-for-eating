# data/__init__.py
# 数据层模块初始化

from data.database import Database, get_db, init_database

__all__ = [
    'Database',
    'get_db',
    'init_database'
]