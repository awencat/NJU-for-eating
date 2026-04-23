# ==================== geo.py ====================
# 地理计算工具函数

import math
from typing import Tuple, Dict


def wgs84_to_gcj02(lat: float, lng: float) -> Dict[str, float]:
    """
    WGS-84坐标系转GCJ-02坐标系（火星坐标）
    用于高德地图API调用
    
    Args:
        lat: WGS-84纬度
        lng: WGS-84经度
    
    Returns:
        {'lat': GCJ-02纬度, 'lng': GCJ-02经度}
    """
    PI = 3.1415926535897932384626
    a = 6378245.0
    ee = 0.00669342162296594323
    
    def transform_lat(x: float, y: float) -> float:
        ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
        ret += (160.0 * math.sin(y / 12.0 * PI) + 320 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
        return ret
    
    def transform_lng(x: float, y: float) -> float:
        ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
        ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
        return ret
    
    d_lat = transform_lat(lng - 105.0, lat - 35.0)
    d_lng = transform_lng(lng - 105.0, lat - 35.0)
    
    rad_lat = lat / 180.0 * PI
    magic = math.sin(rad_lat)
    magic = 1 - ee * magic * magic
    sqrt_magic = math.sqrt(magic)
    
    d_lat = (d_lat * 180.0) / ((a * (1 - ee)) / (magic * sqrt_magic) * PI)
    d_lng = (d_lng * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * PI)
    
    return {
        'lat': lat + d_lat,
        'lng': lng + d_lng
    }


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    使用Haversine公式计算两点间球面距离
    
    Args:
        lat1, lng1: 第一个点的纬度和经度
        lat2, lng2: 第二个点的纬度和经度
    
    Returns:
        距离（米）
    """
    R = 6371000  # 地球平均半径（米）
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def euclidean_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    计算欧几里得距离（近似，适用于小范围）
    
    Args:
        lat1, lng1: 第一个点的纬度和经度
        lat2, lng2: 第二个点的纬度和经度
    
    Returns:
        距离（米）
    """
    # 纬度每度约111km，经度每度约85km（南京纬度约32度）
    lat_scale = 111000
    lng_scale = 111000 * math.cos(math.radians((lat1 + lat2) / 2))
    
    dx = (lng2 - lng1) * lng_scale
    dy = (lat2 - lat1) * lat_scale
    
    return math.sqrt(dx ** 2 + dy ** 2)


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


def calculate_eta(distance_meters: float, mode: str = 'walking') -> int:
    """
    根据距离和出行方式估算到达时间
    
    Args:
        distance_meters: 距离（米）
        mode: 出行方式（walking, biking, transit）
    
    Returns:
        预估时间（秒）
    """
    speeds = {
        'walking': 1.4,   # 米/秒，约5km/h
        'biking': 4.0,    # 米/秒，约14.4km/h
        'transit': 3.0    # 米/秒，包含等车时间估算
    }
    
    speed = speeds.get(mode, 1.4)
    return int(distance_meters / speed)


def is_point_in_bounds(lat: float, lng: float, 
                       center_lat: float, center_lng: float, 
                       radius_meters: float) -> bool:
    """
    判断点是否在指定半径范围内
    
    Args:
        lat, lng: 待判断点坐标
        center_lat, center_lng: 中心点坐标
        radius_meters: 半径（米）
    
    Returns:
        是否在范围内
    """
    distance = haversine_distance(lat, lng, center_lat, center_lng)
    return distance <= radius_meters


def get_bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    计算从点1到点2的方位角（度数）
    
    Args:
        lat1, lng1: 起点坐标
        lat2, lng2: 终点坐标
    
    Returns:
        方位角（0-360度，0为正北）
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lng2 - lng1)
    
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - \
        math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing


def interpolate_point(lat1: float, lng1: float, 
                      lat2: float, lng2: float, 
                      fraction: float) -> Tuple[float, float]:
    """
    在线段上插值获取中间点
    
    Args:
        lat1, lng1: 起点坐标
        lat2, lng2: 终点坐标
        fraction: 插值比例（0-1）
    
    Returns:
        插值点坐标 (lat, lng)
    """
    fraction = max(0, min(1, fraction))
    lat = lat1 + (lat2 - lat1) * fraction
    lng = lng1 + (lng2 - lng1) * fraction
    return (lat, lng)