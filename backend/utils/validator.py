# utils/validator.py
# 参数验证工具

from typing import Dict, Any, Tuple
from functools import wraps
from flask import request, jsonify


def validate_recommend_params(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    验证推荐接口参数
    
    Args:
        data: 请求数据
    
    Returns:
        (是否有效, 错误信息)
    """
    # 检查必需参数
    if 'lat' not in data or 'lng' not in data:
        return False, '缺少位置参数'
    
    try:
        lat = float(data['lat'])
        lng = float(data['lng'])
        
        # 验证经纬度范围
        if not (-90 <= lat <= 90):
            return False, '纬度范围应在 -90 到 90 之间'
        if not (-180 <= lng <= 180):
            return False, '经度范围应在 -180 到 180 之间'
    except (TypeError, ValueError):
        return False, '经纬度格式错误'
    
    # 验证可选参数
    if 'max_price' in data:
        try:
            max_price = float(data['max_price'])
            if max_price < 0:
                return False, 'max_price 必须大于等于0'
            if max_price > 1000:
                return False, 'max_price 不能超过1000'
        except (TypeError, ValueError):
            return False, 'max_price 格式错误'
    
    if 'max_distance' in data:
        try:
            max_distance = float(data['max_distance'])
            if max_distance < 0:
                return False, 'max_distance 必须大于等于0'
            if max_distance > 10000:
                return False, 'max_distance 不能超过10000米'
        except (TypeError, ValueError):
            return False, 'max_distance 格式错误'
    
    if 'cuisines' in data:
        if not isinstance(data['cuisines'], list):
            return False, 'cuisines 必须是数组'
    
    if 'accept_wait' in data:
        if not isinstance(data['accept_wait'], bool):
            return False, 'accept_wait 必须是布尔值'
    
    return True, ''


def validate_route_params(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    验证路径规划接口参数
    
    Args:
        data: 请求数据
    
    Returns:
        (是否有效, 错误信息)
    """
    # 检查必需参数
    if 'origin' not in data or 'destination' not in data:
        return False, '缺少起点或终点参数'
    
    origin = data['origin']
    destination = data['destination']
    
    # 验证起点
    if not isinstance(origin, dict):
        return False, '起点格式错误'
    if 'lat' not in origin or 'lng' not in origin:
        return False, '起点缺少坐标信息'
    
    try:
        lat = float(origin['lat'])
        lng = float(origin['lng'])
        if not (-90 <= lat <= 90):
            return False, '起点纬度范围错误'
        if not (-180 <= lng <= 180):
            return False, '起点经度范围错误'
    except (TypeError, ValueError):
        return False, '起点坐标格式错误'
    
    # 验证终点
    if not isinstance(destination, dict):
        return False, '终点格式错误'
    if 'lat' not in destination or 'lng' not in destination:
        return False, '终点缺少坐标信息'
    
    try:
        lat = float(destination['lat'])
        lng = float(destination['lng'])
        if not (-90 <= lat <= 90):
            return False, '终点纬度范围错误'
        if not (-180 <= lng <= 180):
            return False, '终点经度范围错误'
    except (TypeError, ValueError):
        return False, '终点坐标格式错误'
    
    # 验证出行模式
    mode = data.get('mode', 'walking')
    if mode not in ['walking', 'biking', 'transit']:
        return False, 'mode 必须是 walking, biking 或 transit'
    
    return True, ''


def validate_restaurant_id(restaurant_id: Any) -> Tuple[bool, str]:
    """
    验证餐厅ID
    
    Args:
        restaurant_id: 餐厅ID
    
    Returns:
        (是否有效, 错误信息)
    """
    try:
        rid = int(restaurant_id)
        if rid <= 0:
            return False, '餐厅ID必须大于0'
        return True, ''
    except (TypeError, ValueError):
        return False, '餐厅ID格式错误'


def validate_feedback_params(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    验证反馈接口参数
    
    Args:
        data: 请求数据
    
    Returns:
        (是否有效, 错误信息)
    """
    # 检查餐厅ID
    if 'restaurant_id' not in data:
        return False, '缺少餐厅ID'
    
    try:
        restaurant_id = int(data['restaurant_id'])
        if restaurant_id <= 0:
            return False, '餐厅ID必须大于0'
    except (TypeError, ValueError):
        return False, '餐厅ID格式错误'
    
    # 检查评分
    if 'rating' not in data:
        return False, '缺少评分'
    
    try:
        rating = int(data['rating'])
        if not 1 <= rating <= 5:
            return False, '评分必须在1-5之间'
    except (TypeError, ValueError):
        return False, '评分格式错误'
    
    # 检查评论（可选）
    if 'comment' in data and not isinstance(data['comment'], str):
        return False, '评论必须是字符串'
    
    return True, ''


def require_json(f):
    """
    装饰器：要求请求必须包含JSON数据
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'code': 400,
                'status': 'error',
                'message': '请求必须包含JSON数据'
            }), 400
        return f(*args, **kwargs)
    return decorated_function


def require_params(*params):
    """
    装饰器：要求请求必须包含指定参数
    
    Args:
        *params: 必需的参数名列表
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({
                    'code': 400,
                    'status': 'error',
                    'message': '请求体不能为空'
                }), 400
            
            missing = [p for p in params if p not in data]
            if missing:
                return jsonify({
                    'code': 400,
                    'status': 'error',
                    'message': f'缺少必要参数: {", ".join(missing)}'
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator