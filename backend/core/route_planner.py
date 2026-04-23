# core/route_planner.py
# 路径规划引擎

import requests
import math
from typing import Dict, Any, Tuple, List, Optional

from utils.geo import haversine_distance, calculate_eta


class RoutePlanner:
    """路径规划引擎"""
    
    def __init__(self, amap_api_key: str = None, timeout: int = 5):
        """
        初始化路径规划器
        
        Args:
            amap_api_key: 高德地图API密钥（可选，不配置则使用直线路径）
            timeout: API请求超时时间（秒）
        """
        self.amap_api_key = amap_api_key
        self.timeout = timeout
        self.use_amap = bool(amap_api_key)
    
    def plan(self, origin: Tuple[float, float], 
             destination: Tuple[float, float],
             mode: str = 'walking') -> Dict[str, Any]:
        """
        规划路径
        
        Args:
            origin: 起点坐标 (lat, lng)
            destination: 终点坐标 (lat, lng)
            mode: 出行方式 (walking, biking, transit)
        
        Returns:
            路径信息，包含 distance, duration, polyline, mode
        """
        if self.use_amap:
            return self._plan_with_amap(origin, destination, mode)
        else:
            return self._plan_simple(origin, destination, mode)
    
    def _plan_with_amap(self, origin: Tuple[float, float],
                        destination: Tuple[float, float],
                        mode: str) -> Dict[str, Any]:
        """使用高德地图API规划路径"""
        
        # 保存原始坐标用于fallback
        origin_lat, origin_lng = origin
        dest_lat, dest_lng = destination
        
        # 将WGS-84坐标转换为GCJ-02（高德API需要）
        from utils.geo import wgs84_to_gcj02
        origin_gcj02 = wgs84_to_gcj02(origin_lat, origin_lng)
        dest_gcj02 = wgs84_to_gcj02(dest_lat, dest_lng)
        
        print(f"[RoutePlanner] 坐标转换: WGS84({origin_lat:.6f},{origin_lng:.6f}) -> GCJ02({origin_gcj02['lat']:.6f},{origin_gcj02['lng']:.6f})")
        
        # 高德API路径映射（使用英文）
        path_map = {
            'walking': 'walking',
            'biking': 'bicycling',  # 注意：API使用bicycling而非biking
            'transit': 'transit/integrated'
        }
        
        # 高德API要求经度在前，纬度在后（使用转换后的GCJ-02坐标）
        origin_str = f"{origin_gcj02['lng']},{origin_gcj02['lat']}"
        dest_str = f"{dest_gcj02['lng']},{dest_gcj02['lat']}"
        
        try:
            # 构建API路径
            api_path = path_map.get(mode, 'walking')
            url = f"https://restapi.amap.com/v3/direction/{api_path}"
            
            # 构建请求参数
            params = {
                "origin": origin_str,
                "destination": dest_str,
                "key": self.amap_api_key,
                "output": "JSON"
            }
            
            # 公交模式需要额外参数
            if mode == 'transit':
                params["city"] = "南京"
                params["cityd"] = "南京"
            
            resp = requests.get(url, params=params, timeout=self.timeout)
            data = resp.json()
            
            # 检查是否服务不可用（特别是骑行模式）
            if data.get('status') == '0':
                error_info = data.get('info', '未知错误')
                error_code = data.get('infocode', 'N/A')
                
                # 如果是骑行模式且服务不可用，自动降级为步行
                if mode == 'biking' and 'SERVICE_NOT_AVAILABLE' in error_info:
                    print(f"[RoutePlanner] 骑行服务不可用，自动降级为步行模式")
                    return self._plan_with_amap(origin, destination, 'walking')
                
                print(f"[RoutePlanner] 高德API错误: {error_info} (infocode: {error_code})")
                return self._plan_simple(origin, destination, mode)
            
            if data.get('status') == '1' and data.get('route'):
                return self._parse_amap_response(data, mode)
            else:
                error_info = data.get('info', '未知错误')
                error_code = data.get('infocode', 'N/A')
                print(f"[RoutePlanner] 高德API错误: {error_info} (infocode: {error_code})")
                return self._plan_simple(origin, destination, mode)
                
        except requests.RequestException as e:
            print(f"[RoutePlanner] 高德API请求失败: {e}")
            return self._plan_simple(origin, destination, mode)
    
    def _parse_amap_response(self, data: Dict, mode: str) -> Dict[str, Any]:
        """解析高德API响应"""
        
        route = data.get('route', {})
        
        # 获取第一条路径
        if mode == 'transit':
            paths = route.get('transits', [])
        else:
            paths = route.get('paths', [])
        
        if not paths:
            raise ValueError("无路径数据")
        
        path = paths[0]
        
        # 提取距离和时间
        distance = float(path.get('distance', 0))
        duration = float(path.get('duration', 0))
        
        # 提取路径点 - 从steps中合并polyline
        polyline = []
        
        if mode == 'transit':
            # 公交模式：从segments中提取
            for segment in path.get('segments', []):
                # 公交车段
                bus_lines = segment.get('bus', {}).get('buslines', [])
                for bus in bus_lines:
                    polyline_str = bus.get('polyline', '')
                    if polyline_str:
                        points = polyline_str.split(';')
                        for point in points:
                            lng, lat = point.split(',')
                            polyline.append([float(lat), float(lng)])
                
                # 步行段
                walk_polyline = segment.get('walking', {}).get('polyline', '')
                if walk_polyline:
                    points = walk_polyline.split(';')
                    for point in points:
                        lng, lat = point.split(',')
                        polyline.append([float(lat), float(lng)])
        else:
            # 步行/骑行模式：从steps中合并polyline
            steps = path.get('steps', [])
            for step in steps:
                polyline_str = step.get('polyline', '')
                if polyline_str:
                    points = polyline_str.split(';')
                    for point in points:
                        lng, lat = point.split(',')
                        polyline.append([float(lat), float(lng)])
        
        # 去重（移除连续重复点）
        unique_polyline = []
        for point in polyline:
            if not unique_polyline or unique_polyline[-1] != point:
                unique_polyline.append(point)
        
        return {
            'distance': distance,
            'duration': duration,
            'polyline': unique_polyline,
            'mode': mode,
            'provider': 'amap'
        }
    
    def _plan_simple(self, origin: Tuple[float, float],
                     destination: Tuple[float, float],
                     mode: str) -> Dict[str, Any]:
        """简单直线路径规划（fallback）"""
        
        distance = haversine_distance(origin[0], origin[1], destination[0], destination[1])
        duration = calculate_eta(distance, mode)
        
        # 生成直线路径点
        steps = 30
        polyline = []
        for i in range(steps + 1):
            t = i / steps
            lat = origin[0] + (destination[0] - origin[0]) * t
            lng = origin[1] + (destination[1] - origin[1]) * t
            polyline.append([lat, lng])
        
        return {
            'distance': distance,
            'duration': duration,
            'polyline': polyline,
            'mode': mode,
            'provider': 'simple',
            'fallback': True
        }
    
    def get_travel_time(self, origin: Tuple[float, float],
                        destination: Tuple[float, float],
                        mode: str = 'walking') -> int:
        """
        获取预估旅行时间（秒）
        
        Args:
            origin: 起点坐标
            destination: 终点坐标
            mode: 出行方式
        
        Returns:
            预估时间（秒）
        """
        route = self.plan(origin, destination, mode)
        return route.get('duration', 0)
    
    def get_travel_distance(self, origin: Tuple[float, float],
                            destination: Tuple[float, float],
                            mode: str = 'walking') -> float:
        """
        获取预估旅行距离（米）
        
        Args:
            origin: 起点坐标
            destination: 终点坐标
            mode: 出行方式
        
        Returns:
            预估距离（米）
        """
        route = self.plan(origin, destination, mode)
        return route.get('distance', 0)