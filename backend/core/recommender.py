# core/recommender.py
# 推荐算法引擎

import math
from typing import List, Dict, Any, Tuple

from utils.geo import haversine_distance


def normalize(value: float, min_val: float, max_val: float) -> float:
    """
    最小-最大归一化
    
    Args:
        value: 待归一化值
        min_val: 最小值
        max_val: 最大值
    
    Returns:
        归一化后的值 [0, 1]
    """
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)


def calculate_restaurant_score(restaurant: Dict, distance: float, 
                                max_price: float, max_distance: float,
                                config) -> Tuple[float, str]:
    """
    计算餐厅综合得分
    
    Args:
        restaurant: 餐厅信息字典
        distance: 距离（米）
        max_price: 用户最高接受价格
        max_distance: 用户最大接受距离
        config: 配置对象（包含权重参数）
    
    Returns:
        (score, reason): 得分和推荐理由
    """
    reasons = []
    
    # 距离过滤
    if distance > max_distance:
        return -float('inf'), reasons
    
    # 价格过滤
    if restaurant['price'] > max_price:
        return -float('inf'), reasons
    
    # 归一化评分（越高越好）
    norm_rating = restaurant['rating'] / 5.0
    
    # 归一化价格（越低越好）
    norm_price = 1 - normalize(restaurant['price'], 0, max_price)
    
    # 归一化排队时间（越短越好）
    max_wait = 60
    norm_wait = 1 - normalize(restaurant['wait_time'], 0, max_wait)
    
    # 加权计算
    score = (config.WEIGHT_RATING * norm_rating +
             config.WEIGHT_PRICE * norm_price +
             config.WEIGHT_WAIT * norm_wait)
    
    # 距离奖励：500米内加分
    if distance < 500:
        score += 0.1
        reasons.append("距离很近")
    
    # 生成推荐理由
    if norm_rating > 0.85:
        reasons.append("评分很高")
    elif norm_rating > 0.7:
        reasons.append("评分较高")
    
    if norm_price > 0.8:
        reasons.append("价格实惠")
    
    if norm_wait > 0.8:
        reasons.append("排队时间短")
    elif norm_wait < 0.3:
        reasons.append("排队可能较长")
    
    if not reasons:
        reasons.append("综合推荐")
    
    return score, ", ".join(reasons)


class RecommenderEngine:
    """推荐算法引擎"""
    
    def __init__(self, config):
        """
        初始化推荐引擎
        
        Args:
            config: 配置对象，需包含以下属性:
                - WEIGHT_RATING: 评分权重
                - WEIGHT_PRICE: 价格权重
                - WEIGHT_WAIT: 排队权重
                - DEFAULT_MAX_PRICE: 默认最高价格
                - DEFAULT_MAX_DISTANCE: 默认最大距离
                - DEFAULT_ACCEPT_WAIT: 默认是否接受排队
        """
        self.config = config
    
    def recommend(self, restaurants: List[Dict], user_lat: float, user_lng: float,
                  max_price: float = None, max_distance: float = None,
                  cuisines: List[str] = None, accept_wait: bool = None) -> List[Dict]:
        """
        获取推荐餐厅列表
        
        Args:
            restaurants: 餐厅列表
            user_lat, user_lng: 用户位置
            max_price: 最高价格（默认使用配置值）
            max_distance: 最大距离（默认使用配置值）
            cuisines: 菜系偏好（默认全部）
            accept_wait: 是否接受排队（默认使用配置值）
        
        Returns:
            推荐餐厅列表（已排序）
        """
        # 使用默认值
        if max_price is None:
            max_price = self.config.DEFAULT_MAX_PRICE
        if max_distance is None:
            max_distance = self.config.DEFAULT_MAX_DISTANCE
        if cuisines is None:
            cuisines = ['全部']
        if accept_wait is None:
            accept_wait = self.config.DEFAULT_ACCEPT_WAIT
        
        # haversine_distance已在文件顶部导入
        scored_restaurants = []
        
        for restaurant in restaurants:
            # 计算距离
            distance = haversine_distance(
                user_lat, user_lng,
                restaurant['lat'], restaurant['lng']
            )
            
            # 菜系过滤
            if cuisines and '全部' not in cuisines:
                if restaurant['cuisine'] not in cuisines:
                    continue
            
            # 排队过滤
            if not accept_wait and restaurant['wait_time'] > 15:
                continue
            
            # 计算得分
            score, reason = calculate_restaurant_score(
                restaurant, distance, max_price, max_distance, self.config
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
        
        # 按得分排序
        scored_restaurants.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_restaurants[:10]
    
    def get_recommendation_reason(self, restaurant: Dict, distance: float,
                                   max_price: float, max_distance: float) -> str:
        """
        获取单个餐厅的推荐理由
        
        Args:
            restaurant: 餐厅信息
            distance: 距离
            max_price: 最高价格
            max_distance: 最大距离
        
        Returns:
            推荐理由字符串
        """
        _, reason = calculate_restaurant_score(
            restaurant, distance, max_price, max_distance, self.config
        )
        return reason