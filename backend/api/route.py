# api/route.py
# 路径规划接口

from datetime import datetime
from flask import request, jsonify
from api import route_bp
from core.route_planner import RoutePlanner
from utils.validator import validate_route_params
from config import get_config


@route_bp.route('/route', methods=['POST'])
def plan_route():
    """
    路径规划接口（使用高德地图API或降级为直线路径）
    
    请求体示例:
    {
        "origin": {"lat": 32.0542, "lng": 118.7835},
        "destination": {"lat": 32.0560, "lng": 118.7850},
        "mode": "walking"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 400,
                'status': 'error',
                'message': '请求体不能为空'
            }), 400
        
        # 验证参数
        is_valid, error_msg = validate_route_params(data)
        if not is_valid:
            return jsonify({
                'code': 400,
                'status': 'error',
                'message': error_msg
            }), 400
        
        # 提取参数
        origin = data.get('origin')
        destination = data.get('destination')
        mode = data.get('mode', 'walking')
        
        origin_lat = float(origin['lat'])
        origin_lng = float(origin['lng'])
        dest_lat = float(destination['lat'])
        dest_lng = float(destination['lng'])
        
        # 获取配置并初始化路径规划器
        config = get_config()
        planner = RoutePlanner(amap_api_key=config.AMAP_API_KEY, timeout=config.API_TIMEOUT)
        
        # 调用路径规划
        origin_coord = (origin_lat, origin_lng)
        dest_coord = (dest_lat, dest_lng)
        route_data = planner.plan(origin_coord, dest_coord, mode)
        
        return jsonify({
            'code': 200,
            'status': 'success',
            'message': '路径规划成功',
            'data': route_data,
            'timestamp': int(datetime.now().timestamp() * 1000)
        })
        
    except Exception as e:
        print(f"路径规划接口错误: {e}")
        return jsonify({
            'code': 500,
            'status': 'error',
            'message': f'服务器内部错误: {str(e)}'
        }), 500