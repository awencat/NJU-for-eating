# api/__init__.py
# API蓝图注册

from flask import Blueprint

# 创建蓝图
recommend_bp = Blueprint('recommend', __name__)
route_bp = Blueprint('route', __name__)
restaurants_bp = Blueprint('restaurants', __name__)

# 导入路由模块(只导入模块,不导入具体内容)
import api.recommend
import api.route
import api.restaurants