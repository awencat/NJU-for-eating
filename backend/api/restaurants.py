from flask import request, jsonify
from data.database import Database
import config

from api import restaurants_bp


def get_db():
    return Database(config.Config.DATABASE_PATH)


@restaurants_bp.route('/restaurants', methods=['GET'])
def get_all_restaurants():
    """
    获取所有餐厅
    
    Query参数:
    - page: 页码(从1开始,默认1)
    - page_size: 每页数量(默认20)
    
    返回:
    - 餐厅列表
    - 分页信息
    """
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        db = get_db()
        all_restaurants = db.get_all_restaurants()
        
        total = len(all_restaurants)
        total_pages = (total + page_size - 1) // page_size  # 向上取整
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = all_restaurants[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': paginated_results,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@restaurants_bp.route('/nearby', methods=['GET'])
def get_nearby_restaurants():
    """
    获取附近所有餐厅(支持分页)
    
    Query参数:
    - lat: 纬度(必填)
    - lng: 经度(必填)
    - max_distance: 最大距离(米,默认3000)
    - page: 页码(从1开始,默认1)
    - page_size: 每页数量(默认20)
    
    返回:
    - 按距离排序的餐厅列表
    - 分页信息
    """
    try:
        from utils.geo import haversine_distance
        
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
        max_distance = int(request.args.get('max_distance', 3000))
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        if not lat or not lng:
            return jsonify({
                'success': False,
                'message': '请提供经纬度坐标'
            }), 400
        
        db = get_db()
        
        # 获取所有餐厅
        all_restaurants = db.get_all_restaurants()
        
        # 计算距离并过滤
        nearby_restaurants = []
        for rest in all_restaurants:
            distance = haversine_distance(lat, lng, rest['lat'], rest['lng'])
            if distance <= max_distance:
                rest_with_distance = dict(rest)
                rest_with_distance['distance'] = round(distance)
                nearby_restaurants.append(rest_with_distance)
        
        # 按距离排序
        nearby_restaurants.sort(key=lambda x: x['distance'])
        
        # 分页处理
        total = len(nearby_restaurants)
        total_pages = (total + page_size - 1) // page_size  # 向上取整
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = nearby_restaurants[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': paginated_results,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@restaurants_bp.route('/filter', methods=['POST'])
def filter_restaurants():
    """
    高级筛选餐厅
    
    Body参数:
    - lat: 纬度(必填)
    - lng: 经度(必填)
    - price_min: 最低价格(可选)
    - price_max: 最高价格(可选)
    - rating_min: 最低评分(可选)
    - max_wait_time: 最大等待时间(可选)
    - max_distance: 最大距离(可选)
    - cuisines: 菜系列表(可选)
    - is_opening: 是否只显示营业中(可选)
    - sort_by: 排序方式(distance/rating/price/wait_time,默认distance)
    - page: 页码(默认1)
    - page_size: 每页数量(默认20)
    
    返回:
    - 筛选后的餐厅列表
    - 分页信息
    - 筛选条件统计
    """
    try:
        from utils.geo import haversine_distance
        from datetime import datetime
        
        data = request.get_json()
        
        lat = float(data.get('lat', 0))
        lng = float(data.get('lng', 0))
        
        # 筛选条件
        price_min = data.get('price_min')
        price_max = data.get('price_max')
        rating_min = data.get('rating_min')
        max_wait_time = data.get('max_wait_time')
        max_distance = data.get('max_distance', 3000)
        cuisines = data.get('cuisines', [])
        is_opening = data.get('is_opening', False)
        
        # 排序和分页
        sort_by = data.get('sort_by', 'distance')
        page = int(data.get('page', 1))
        page_size = int(data.get('page_size', 20))
        
        if not lat or not lng:
            return jsonify({
                'success': False,
                'message': '请提供经纬度坐标'
            }), 400
        
        db = get_db()
        all_restaurants = db.get_all_restaurants()
        
        # 应用筛选条件
        filtered = []
        for rest in all_restaurants:
            # 计算距离
            distance = haversine_distance(lat, lng, rest['lat'], rest['lng'])
            
            # 距离过滤
            if distance > max_distance:
                continue
            
            # 价格过滤
            if price_min and rest['price'] < price_min:
                continue
            if price_max and rest['price'] > price_max:
                continue
            
            # 评分过滤
            if rating_min and rest['rating'] < rating_min:
                continue
            
            # 等待时间过滤
            if max_wait_time and rest['wait_time'] > max_wait_time:
                continue
            
            # 菜系过滤
            if cuisines and rest['cuisine'] not in cuisines:
                continue
            
            # 营业状态过滤
            if is_opening and rest.get('hours'):
                now = datetime.now()
                current_time = now.strftime('%H:%M')
                hours = rest['hours'].split('-')
                if len(hours) == 2:
                    open_time = hours[0].strip()
                    close_time = hours[1].strip()
                    if current_time < open_time or current_time > close_time:
                        continue
            
            # 通过所有筛选
            rest_with_info = dict(rest)
            rest_with_info['distance'] = round(distance)
            filtered.append(rest_with_info)
        
        # 排序
        if sort_by == 'rating':
            filtered.sort(key=lambda x: x['rating'], reverse=True)
        elif sort_by == 'price':
            filtered.sort(key=lambda x: x['price'])
        elif sort_by == 'wait_time':
            filtered.sort(key=lambda x: x['wait_time'])
        else:  # distance
            filtered.sort(key=lambda x: x['distance'])
        
        # 分页
        total = len(filtered)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = filtered[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'data': paginated_results,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'filters_applied': {
                'price_range': f'¥{price_min or 0}-¥{price_max or "∞"}',
                'min_rating': rating_min or '无',
                'max_wait_time': f'{max_wait_time or "∞"}分钟',
                'max_distance': f'{max_distance}米',
                'cuisines': cuisines or ['全部'],
                'sort_by': sort_by
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@restaurants_bp.route('/restaurant/<int:restaurant_id>', methods=['GET'])
def get_restaurant_detail(restaurant_id):
    """获取单个餐厅详情"""
    try:
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM restaurants WHERE id = ?', (restaurant_id,))
            restaurant = cursor.fetchone()
            
            if not restaurant:
                return jsonify({
                    'success': False,
                    'message': '餐厅不存在'
                }), 404
            
            return jsonify({
                'success': True,
                'data': dict(restaurant)
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@restaurants_bp.route('/search', methods=['GET'])
def search_restaurants():
    """搜索餐厅（支持关键词模糊匹配）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        limit = request.args.get('limit', 20, type=int)
        
        if not keyword:
            return jsonify({
                'success': False,
                'message': '请输入搜索关键词'
            }), 400
        
        db = get_db()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # 模糊搜索：匹配名称、菜系、地址、标签
            search_pattern = f'%{keyword}%'
            query = '''
                SELECT * FROM restaurants 
                WHERE name LIKE ? 
                   OR cuisine LIKE ? 
                   OR address LIKE ? 
                   OR tags LIKE ?
                ORDER BY rating DESC, price ASC
                LIMIT ?
            '''
            
            cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern, limit))
            restaurants = cursor.fetchall()
            
            results = []
            for rest in restaurants:
                rest_dict = dict(rest)
                # 计算距离（如果有用户位置）
                user_lat = request.args.get('lat', type=float)
                user_lng = request.args.get('lng', type=float)
                
                if user_lat and user_lng:
                    distance = haversine_distance(user_lat, user_lng, rest_dict['lat'], rest_dict['lng'])
                    rest_dict['distance'] = round(distance)
                else:
                    rest_dict['distance'] = None
                
                results.append(rest_dict)
            
            return jsonify({
                'success': True,
                'data': results,
                'total': len(results),
                'keyword': keyword
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
