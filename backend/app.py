# app.py - Flask应用主入口

import os
import sys

# 确保当前目录在Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from config import get_config
from data import init_database
from api import recommend_bp, route_bp, restaurants_bp


def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name: 配置环境名称
    
    Returns:
        Flask应用实例
    """
    # 获取配置
    config = get_config(config_name)
    
    # 创建Flask应用
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY
    
    # 配置CORS
    CORS(app, origins=config.get_cors_origins())
    
    # 注册蓝图
    app.register_blueprint(recommend_bp, url_prefix='/api')
    app.register_blueprint(route_bp, url_prefix='/api')
    app.register_blueprint(restaurants_bp, url_prefix='/api')
    
    # 健康检查接口
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            'code': 200,
            'status': 'success',
            'message': '服务运行正常',
            'timestamp': int(__import__('time').time() * 1000)
        })
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'status': 'error',
            'message': '接口不存在'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'code': 500,
            'status': 'error',
            'message': '服务器内部错误'
        }), 500
    
    # 初始化数据库
    with app.app_context():
        init_database(config.DATABASE_PATH)
    
    return app


# ==================== 启动应用 ====================

if __name__ == '__main__':
    config = get_config()
    app = create_app()
    
    print("\n" + "=" * 50)
    print("  智慧校园餐厅推荐系统 - 后端服务")
    print("=" * 50)
    print(f"  服务地址: http://{config.HOST}:{config.PORT}")
    print(f"  健康检查: http://{config.HOST}:{config.PORT}/api/health")
    print(f"  推荐接口: POST http://{config.HOST}:{config.PORT}/api/recommend")
    print(f"  路径规划: POST http://{config.HOST}:{config.PORT}/api/route")
    print(f"  高德API: {'已配置' if config.is_amap_configured() else '未配置(使用直线路径)'}")
    print("=" * 50)
    print("  按 Ctrl+C 停止服务\n")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )