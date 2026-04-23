# utils/logger.py
# 日志工具模块

import logging
import sys
from datetime import datetime
from typing import Optional


def setup_logger(name: str, level=logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    配置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）
    
    Returns:
        配置好的Logger对象
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = 'campus_dining') -> logging.Logger:
    """
    获取日志记录器（单例模式）
    
    Args:
        name: 日志记录器名称
    
    Returns:
        Logger对象
    """
    return setup_logger(name)


# 全局日志实例
app_logger = get_logger('campus_dining')


class LoggerContext:
    """
    日志上下文管理器
    
    使用示例:
        with LoggerContext('api', '处理推荐请求'):
            # 执行操作
            pass
    """
    def __init__(self, module: str, action: str, logger: logging.Logger = None):
        self.module = module
        self.action = action
        self.logger = logger or app_logger
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"[{self.module}] 开始: {self.action}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            self.logger.info(f"[{self.module}] 完成: {self.action} (耗时 {elapsed:.3f}s)")
        else:
            self.logger.error(f"[{self.module}] 失败: {self.action} (耗时 {elapsed:.3f}s) - {exc_val}")
        return False


def log_request(logger: logging.Logger = None):
    """
    装饰器：记录请求日志
    """
    def decorator(f):
        def wrapped(*args, **kwargs):
            lg = logger or app_logger
            lg.info(f"请求: {f.__name__}")
            try:
                result = f(*args, **kwargs)
                lg.info(f"响应: {f.__name__} - 成功")
                return result
            except Exception as e:
                lg.error(f"响应: {f.__name__} - 失败: {e}")
                raise
        return wrapped
    return decorator