# api/recommend.py
# 餐厅推荐接口

import math
from datetime import datetime
from flask import request, jsonify
from api import recommend_bp
from utils.geo import haversine_distance
from utils.validator import validate_recommend_params
from core.recommender import calculate_restaurant_score
from data.database import get_db
from config import get_config


@recommend_bp.route('/recommend', methods=['POST'])
def recommend_restaurants():
    """
    餐厅推荐接口
    
    请求体示例:
    {
        "lat": 32.0542,
        "lng": 118.7835,
        "max_price": 50,
        "max_distance": 1000,
        "cuisines": ["川菜", "西餐"],
        "accept_wait": true
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
        is_valid, error_msg = validate_recommend_params(data)
        if not is_valid:
            return jsonify({
                'code': 400,
                'status': 'error',
                'message': error_msg
            }), 400
        
        # 获取参数
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        
        config = get_config()
        max_price = float(data.get('max_price', config.DEFAULT_MAX_PRICE))
        max_distance = float(data.get('max_distance', config.DEFAULT_MAX_DISTANCE))
        accept_wait = data.get('accept_wait', config.DEFAULT_ACCEPT_WAIT)
        cuisines = data.get('cuisines', ['全部'])
        
        # 获取数据库中的餐厅（使用正确的上下文管理器）
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM restaurants')
            rows = cursor.fetchall()
        
        restaurants = [dict(row) for row in rows]
        
        print(f"[DEBUG] 从数据库获取 {len(restaurants)} 家餐厅")
        print(f"[DEBUG] 用户位置: lat={lat}, lng={lng}")
        print(f"[DEBUG] 筛选条件: max_price={max_price}, max_distance={max_distance}, cuisines={cuisines}, accept_wait={accept_wait}")
        
        # 计算得分并过滤
        scored_restaurants = []
        
        for restaurant in restaurants:
            # 计算距离
            distance = haversine_distance(
                lat, lng,
                restaurant['lat'], restaurant['lng']
            )
            
            # 菜系过滤
            if cuisines and '全部' not in cuisines:
                if restaurant['cuisine'] not in cuisines:
                    print(f"[DEBUG] 餐厅 {restaurant['name']} 被菜系过滤: {restaurant['cuisine']}")
                    continue
            
            # 排队过滤
            if not accept_wait and restaurant['wait_time'] > 15:
                print(f"[DEBUG] 餐厅 {restaurant['name']} 被排队时间过滤: {restaurant['wait_time']}分钟")
                continue
            
            # 计算得分
            score, reason = calculate_restaurant_score(
                restaurant, distance, max_price, max_distance, config
            )
            
            if score > -float('inf'):
                scored_restaurants.append({
                    'id': restaurant['id'],
                    'name': restaurant['name'],
                    'lat': restaurant['lat'],
                    'lng': restaurant['lng'],
                    'address': restaurant.get('address', ''),
                    'cuisine': restaurant['cuisine'],
                    'price': restaurant['price'],
                    'rating': restaurant['rating'],
                    'wait_time': restaurant['wait_time'],
                    'distance': round(distance),
                    'score': round(score, 4),
                    'reason': reason,
                    'phone': restaurant.get('phone', ''),
                    'hours': restaurant.get('hours', ''),
                    'tags': restaurant.get('tags', '').split(',') if restaurant.get('tags') else []
                })
                print(f"[DEBUG] 餐厅 {restaurant['name']} 通过筛选，得分: {score:.4f}, 距离: {distance:.0f}米")
            else:
                print(f"[DEBUG] 餐厅 {restaurant['name']} 被评分过滤（距离:{distance:.0f}m, 价格:{restaurant['price']}）")
        
        # 按得分排序
        scored_restaurants.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回前10个
        result = scored_restaurants[:10]
        
        return jsonify({
            'code': 200,
            'status': 'success',
            'message': f'推荐成功，共找到 {len(result)} 家餐厅',
            'data': result,
            'timestamp': int(datetime.now().timestamp() * 1000)
        })
        
    except Exception as e:
        print(f"推荐接口错误: {e}")
        return jsonify({
            'code': 500,
            'status': 'error',
            'message': f'服务器内部错误: {str(e)}'
        }), 500
