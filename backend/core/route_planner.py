# core/route_planner.py
# 路径规划引擎

import requests
from typing import Any, Dict, Tuple

from utils.geo import calculate_eta, haversine_distance, wgs84_to_gcj02_tuple


class RoutePlanner:
    """路径规划引擎"""

    def __init__(self, amap_api_key: str = None, timeout: int = 5):
        self.amap_api_key = amap_api_key
        self.timeout = timeout
        self.use_amap = bool(amap_api_key)

    def _origin_to_gcj02(self, origin: Tuple[float, float, str]) -> Tuple[float, float]:
        lat, lng = origin[0], origin[1]
        coord_system = origin[2] if len(origin) > 2 else 'gcj02'
        if (coord_system or '').lower() == 'wgs84':
            return wgs84_to_gcj02_tuple(lat, lng)
        return lat, lng

    def plan(self, origin: Tuple[float, float, str],
             destination: Tuple[float, float],
             mode: str = 'walking') -> Dict[str, Any]:
        origin_gcj02 = self._origin_to_gcj02(origin)
        destination_gcj02 = destination

        if self.use_amap:
            return self._plan_with_amap(origin_gcj02, destination_gcj02, mode)
        return self._plan_simple(origin_gcj02, destination_gcj02, mode)

    def _plan_with_amap(self, origin_gcj02: Tuple[float, float],
                        destination_gcj02: Tuple[float, float],
                        mode: str) -> Dict[str, Any]:
        path_map = {
            'walking': 'walking',
            'biking': 'bicycling',
            'transit': 'transit/integrated',
            'subway': 'transit/integrated',
        }

        origin_str = f"{origin_gcj02[1]},{origin_gcj02[0]}"
        destination_str = f"{destination_gcj02[1]},{destination_gcj02[0]}"

        try:
            url = f"https://restapi.amap.com/v3/direction/{path_map.get(mode, 'walking')}"
            params = {
                "origin": origin_str,
                "destination": destination_str,
                "key": self.amap_api_key,
                "output": "JSON",
            }

            if mode in ('transit', 'subway'):
                params["city"] = "南京"
                params["cityd"] = "南京"
                if mode == 'subway':
                    params["strategy"] = 7

            resp = requests.get(url, params=params, timeout=self.timeout)
            data = resp.json()

            if data.get('status') == '1' and data.get('route'):
                return self._parse_amap_response(data, mode)

            error_info = data.get('info', '未知错误')
            error_code = data.get('infocode', 'N/A')
            print(f"[RoutePlanner] 高德API错误: {error_info} (infocode: {error_code})")
            return self._plan_simple(origin_gcj02, destination_gcj02, mode)
        except requests.RequestException as e:
            print(f"[RoutePlanner] 高德API请求失败: {e}")
            return self._plan_simple(origin_gcj02, destination_gcj02, mode)

    def _parse_amap_response(self, data: Dict, mode: str) -> Dict[str, Any]:
        route = data.get('route', {})
        paths = route.get('transits', []) if mode in ('transit', 'subway') else route.get('paths', [])

        if not paths:
            raise ValueError("无路径数据")

        path = paths[0]
        polyline = []

        if mode in ('transit', 'subway'):
            for segment in path.get('segments', []):
                for bus in segment.get('bus', {}).get('buslines', []):
                    self._append_polyline(polyline, bus.get('polyline', ''))
                self._append_polyline(polyline, segment.get('walking', {}).get('polyline', ''))
        else:
            for step in path.get('steps', []):
                self._append_polyline(polyline, step.get('polyline', ''))

        unique_polyline = []
        for point in polyline:
            if not unique_polyline or unique_polyline[-1] != point:
                unique_polyline.append(point)

        return {
            'distance': float(path.get('distance', 0)),
            'duration': float(path.get('duration', 0)),
            'polyline': unique_polyline,
            'mode': mode,
            'provider': 'amap',
        }

    @staticmethod
    def _append_polyline(polyline: list, polyline_str: str) -> None:
        if not polyline_str:
            return
        for point in polyline_str.split(';'):
            lng, lat = point.split(',')
            polyline.append([float(lat), float(lng)])

    def _plan_simple(self, origin: Tuple[float, float],
                     destination: Tuple[float, float],
                     mode: str) -> Dict[str, Any]:
        distance = haversine_distance(origin[0], origin[1], destination[0], destination[1])
        duration = calculate_eta(distance, mode)

        polyline = []
        for i in range(31):
            t = i / 30
            lat = origin[0] + (destination[0] - origin[0]) * t
            lng = origin[1] + (destination[1] - origin[1]) * t
            polyline.append([lat, lng])

        return {
            'distance': distance,
            'duration': duration,
            'polyline': polyline,
            'mode': mode,
            'provider': 'simple',
            'fallback': True,
        }

    def get_travel_time(self, origin: Tuple[float, float, str],
                        destination: Tuple[float, float],
                        mode: str = 'walking') -> int:
        route = self.plan(origin, destination, mode)
        return route.get('duration', 0)

    def get_travel_distance(self, origin: Tuple[float, float, str],
                            destination: Tuple[float, float],
                            mode: str = 'walking') -> float:
        route = self.plan(origin, destination, mode)
        return route.get('distance', 0)
