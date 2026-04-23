# core/filter.py
# 偏好过滤器

from typing import List, Dict, Any, Optional
from utils.geo import haversine_distance


class PreferenceFilter:
    """用户偏好过滤器"""
    
    @staticmethod
    def filter_by_price(restaurants: List[Dict], max_price: float) -> List[Dict]:
        """
        按价格过滤
        
        Args:
            restaurants: 餐厅列表
            max_price: 最高价格
        
        Returns:
            过滤后的餐厅列表
        """
        return [r for r in restaurants if r['price'] <= max_price]
    
    @staticmethod
    def filter_by_min_price(restaurants: List[Dict], min_price: float) -> List[Dict]:
        """
        按最低价格过滤
        
        Args:
            restaurants: 餐厅列表
            min_price: 最低价格
        
        Returns:
            过滤后的餐厅列表
        """
        return [r for r in restaurants if r['price'] >= min_price]
    
    @staticmethod
    def filter_by_cuisine(restaurants: List[Dict], cuisines: List[str]) -> List[Dict]:
        """
        按菜系过滤
        
        Args:
            restaurants: 餐厅列表
            cuisines: 菜系列表（如果包含'全部'则不过滤）
        
        Returns:
            过滤后的餐厅列表
        """
        if not cuisines or '全部' in cuisines:
            return restaurants
        return [r for r in restaurants if r['cuisine'] in cuisines]
    
    @staticmethod
    def filter_by_distance(restaurants: List[Dict], lat: float, lng: float,
                           max_distance: float) -> List[Dict]:
        """
        按距离过滤，并添加距离字段
        
        Args:
            restaurants: 餐厅列表
            lat, lng: 参考点坐标
            max_distance: 最大距离（米）
        
        Returns:
            过滤后的餐厅列表（每个餐厅添加了distance字段）
        """
        filtered = []
        for r in restaurants:
            distance = haversine_distance(lat, lng, r['lat'], r['lng'])
            if distance <= max_distance:
                r['distance'] = round(distance)
                filtered.append(r)
        return filtered
    
    @staticmethod
    def filter_by_wait_time(restaurants: List[Dict], accept_wait: bool,
                            max_wait: int = 15) -> List[Dict]:
        """
        按排队时间过滤
        
        Args:
            restaurants: 餐厅列表
            accept_wait: 是否接受排队
            max_wait: 最大可接受排队时间（分钟）
        
        Returns:
            过滤后的餐厅列表
        """
        if accept_wait:
            return restaurants
        return [r for r in restaurants if r['wait_time'] <= max_wait]
    
    @staticmethod
    def filter_by_rating(restaurants: List[Dict], min_rating: float = 3.0) -> List[Dict]:
        """
        按最低评分过滤
        
        Args:
            restaurants: 餐厅列表
            min_rating: 最低评分
        
        Returns:
            过滤后的餐厅列表
        """
        return [r for r in restaurants if r['rating'] >= min_rating]
    
    @staticmethod
    def filter_by_tags(restaurants: List[Dict], tags: List[str]) -> List[Dict]:
        """
        按标签过滤
        
        Args:
            restaurants: 餐厅列表
            tags: 需要包含的标签列表
        
        Returns:
            过滤后的餐厅列表
        """
        if not tags:
            return restaurants
        
        filtered = []
        for r in restaurants:
            restaurant_tags = r.get('tags', '')
            if isinstance(restaurant_tags, str):
                restaurant_tags = restaurant_tags.split(',')
            if any(tag in restaurant_tags for tag in tags):
                filtered.append(r)
        return filtered
    
    @staticmethod
    def sort_by_rating(restaurants: List[Dict], ascending: bool = False) -> List[Dict]:
        """
        按评分排序
        
        Args:
            restaurants: 餐厅列表
            ascending: 是否升序（默认降序）
        
        Returns:
            排序后的列表
        """
        return sorted(restaurants, key=lambda x: x['rating'], reverse=not ascending)
    
    @staticmethod
    def sort_by_price(restaurants: List[Dict], ascending: bool = True) -> List[Dict]:
        """
        按价格排序
        
        Args:
            restaurants: 餐厅列表
            ascending: 是否升序（默认升序，价格从低到高）
        
        Returns:
            排序后的列表
        """
        return sorted(restaurants, key=lambda x: x['price'], reverse=not ascending)
    
    @staticmethod
    def sort_by_distance(restaurants: List[Dict], ascending: bool = True) -> List[Dict]:
        """
        按距离排序（需要先调用filter_by_distance添加distance字段）
        
        Args:
            restaurants: 餐厅列表
            ascending: 是否升序（默认升序，距离从近到远）
        
        Returns:
            排序后的列表
        """
        return sorted(restaurants, key=lambda x: x.get('distance', float('inf')), 
                     reverse=not ascending)
    
    @staticmethod
    def sort_by_wait_time(restaurants: List[Dict], ascending: bool = True) -> List[Dict]:
        """
        按排队时间排序
        
        Args:
            restaurants: 餐厅列表
            ascending: 是否升序（默认升序，排队从短到长）
        
        Returns:
            排序后的列表
        """
        return sorted(restaurants, key=lambda x: x['wait_time'], reverse=not ascending)
    
    @staticmethod
    def apply_all_filters(restaurants: List[Dict],
                          lat: float = None, lng: float = None,
                          max_price: float = None,
                          max_distance: float = None,
                          cuisines: List[str] = None,
                          accept_wait: bool = True,
                          min_rating: float = None,
                          sort_by: str = 'score') -> List[Dict]:
        """
        应用所有过滤器
        
        Args:
            restaurants: 餐厅列表
            lat, lng: 用户位置（用于距离过滤）
            max_price: 最高价格
            max_distance: 最大距离
            cuisines: 菜系偏好
            accept_wait: 是否接受排队
            min_rating: 最低评分
            sort_by: 排序方式 ('score', 'rating', 'price', 'distance', 'wait')
        
        Returns:
            过滤并排序后的餐厅列表
        """
        result = restaurants.copy()
        
        # 价格过滤
        if max_price is not None:
            result = PreferenceFilter.filter_by_price(result, max_price)
        
        # 菜系过滤
        if cuisines:
            result = PreferenceFilter.filter_by_cuisine(result, cuisines)
        
        # 距离过滤（同时添加distance字段）
        if lat is not None and lng is not None and max_distance is not None:
            result = PreferenceFilter.filter_by_distance(result, lat, lng, max_distance)
        
        # 排队过滤
        if not accept_wait:
            result = PreferenceFilter.filter_by_wait_time(result, accept_wait)
        
        # 评分过滤
        if min_rating is not None:
            result = PreferenceFilter.filter_by_rating(result, min_rating)
        
        # 排序
        if sort_by == 'rating':
            result = PreferenceFilter.sort_by_rating(result)
        elif sort_by == 'price':
            result = PreferenceFilter.sort_by_price(result)
        elif sort_by == 'distance':
            result = PreferenceFilter.sort_by_distance(result)
        elif sort_by == 'wait':
            result = PreferenceFilter.sort_by_wait_time(result)
        # 默认按score排序（需要在外部计算）
        
        return result