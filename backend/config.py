# config.py
# 配置文件

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """基础配置类"""
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/restaurants.db')
    
    # 高德地图API配置
    AMAP_API_KEY = os.getenv('AMAP_API_KEY', '')
    
    # API超时配置
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', 5))
    
    # CORS跨域配置
    # CORS跨域配置！！！！！！！！！！！！！！
    CORS_ORIGINS = os.getenv('CORS_ORIGINS',
                             'http://127.0.0.1:5500,http://localhost:5500,http://[::]:8080,http://127.0.0.1:8080,http://localhost:8080').split(
        ',')

    # 推荐算法权重
    WEIGHT_RATING = 0.5      # 评分权重（越高越好）
    WEIGHT_PRICE = 0.3       # 价格权重（越低越好）
    WEIGHT_WAIT = 0.2        # 排队权重（越短越好）
    
    # 默认筛选条件
    DEFAULT_MAX_PRICE = 50        # 默认最高价格（元）
    DEFAULT_MAX_DISTANCE = 1000   # 默认最大距离（米）
    DEFAULT_ACCEPT_WAIT = True    # 默认是否接受排队
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', None)
    
    @classmethod
    def is_amap_configured(cls) -> bool:
        """检查高德地图API是否已配置"""
        return bool(cls.AMAP_API_KEY)
    
    @classmethod
    def get_cors_origins(cls) -> list:
        """获取CORS允许的源列表"""
        return cls.CORS_ORIGINS
    
    @classmethod
    def get_weights(cls) -> dict:
        """获取推荐算法权重"""
        return {
            'rating': cls.WEIGHT_RATING,
            'price': cls.WEIGHT_PRICE,
            'wait': cls.WEIGHT_WAIT
        }
    
    @classmethod
    def get_default_filters(cls) -> dict:
        """获取默认筛选条件"""
        return {
            'max_price': cls.DEFAULT_MAX_PRICE,
            'max_distance': cls.DEFAULT_MAX_DISTANCE,
            'accept_wait': cls.DEFAULT_ACCEPT_WAIT
        }


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # 生产环境需要更严格的CORS
    @classmethod
    def get_cors_origins(cls) -> list:
        # 生产环境从环境变量读取，不允许通配符
        origins = os.getenv('CORS_ORIGINS', '')
        return [o.strip() for o in origins.split(',') if o.strip()]


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    DATABASE_PATH = 'data/test.db'
    LOG_LEVEL = 'ERROR'


# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """
    获取配置对象
    
    Args:
        env: 环境名称（development, production, testing）
    
    Returns:
        配置类实例
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()


# 创建全局配置实例
config = get_config()