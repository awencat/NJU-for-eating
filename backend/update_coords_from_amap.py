"""
通过高德地图地理编码API获取餐厅准确坐标
使用餐厅名称和地址进行地理编码,获取精确的GCJ-02坐标
"""

import requests
import sqlite3
import time
from typing import Dict, List, Optional


class AMapGeocoder:
    """高德地图地理编码器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/geocode/geo"
    
    def geocode(self, address: str, city: str = "南京") -> Optional[Dict]:
        """
        地理编码：将地址转换为坐标
        
        Args:
            address: 地址字符串
            city: 城市名称
        
        Returns:
            {'lat': float, 'lng': float} 或 None
        """
        try:
            params = {
                "address": address,
                "city": city,
                "key": self.api_key,
                "output": "JSON"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "1" and data.get("geocodes"):
                geocode = data["geocodes"][0]
                location = geocode["location"]  # 格式: "经度,纬度"
                lng, lat = location.split(",")
                
                return {
                    "lat": float(lat),
                    "lng": float(lng),
                    "formatted_address": geocode.get("formatted_address", ""),
                    "confidence": geocode.get("level", "")
                }
            else:
                print(f"❌ 地理编码失败: {data.get('info', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    def batch_geocode(self, addresses: List[str], city: str = "南京", delay: float = 0.5) -> List[Optional[Dict]]:
        """
        批量地理编码
        
        Args:
            addresses: 地址列表
            city: 城市名称
            delay: 每次请求间隔(秒),避免频率限制
        
        Returns:
            坐标结果列表
        """
        results = []
        for i, address in enumerate(addresses, 1):
            print(f"[{i}/{len(addresses)}] 正在查询: {address}")
            result = self.geocode(address, city)
            results.append(result)
            
            if result:
                print(f"   ✅ {result['lat']:.6f}, {result['lng']:.6f}")
            else:
                print(f"   ❌ 未找到坐标")
            
            # 延迟避免频率限制
            if i < len(addresses):
                time.sleep(delay)
        
        return results


def update_restaurant_coordinates(api_key: str, limit: int = 50):
    """
    更新数据库中餐厅的坐标
    
    Args:
        api_key: 高德地图API密钥
        limit: 处理的餐厅数量限制
    """
    print("=" * 80)
    print("🗺️  开始更新餐厅坐标")
    print("=" * 80)
    
    # 初始化地理编码器
    geocoder = AMapGeocoder(api_key)
    
    # 读取数据库
    conn = sqlite3.connect('data/restaurants.db')
    cursor = conn.cursor()
    
    # 获取所有餐厅
    cursor.execute('SELECT id, name, address FROM restaurants LIMIT ?', (limit,))
    restaurants = cursor.fetchall()
    
    print(f"\n📋 共需处理 {len(restaurants)} 家餐厅\n")
    
    updated_count = 0
    failed_count = 0
    
    for restaurant_id, name, address in restaurants:
        # 构建搜索地址（餐厅名 + 地址）
        search_address = f"{name} {address}"
        
        print(f"🔍 [{updated_count + failed_count + 1}/{len(restaurants)}] {name}")
        print(f"   地址: {address}")
        
        # 地理编码
        result = geocoder.geocode(search_address, "南京")
        
        if result:
            new_lat = result['lat']
            new_lng = result['lng']
            
            # 更新数据库
            cursor.execute(
                'UPDATE restaurants SET lat = ?, lng = ? WHERE id = ?',
                (new_lat, new_lng, restaurant_id)
            )
            conn.commit()
            
            print(f"   ✅ 更新成功: ({new_lat:.6f}, {new_lng:.6f})")
            print(f"   📍 格式化地址: {result['formatted_address']}")
            updated_count += 1
        else:
            print(f"   ⚠️  跳过(未找到坐标)")
            failed_count += 1
        
        # 延迟避免频率限制
        time.sleep(0.5)
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 坐标更新完成!")
    print(f"   成功: {updated_count} 家")
    print(f"   失败: {failed_count} 家")
    print("=" * 80)


if __name__ == '__main__':
    # 从环境变量或配置文件获取API密钥
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    AMAP_API_KEY = os.getenv('AMAP_API_KEY', '')
    
    if not AMAP_API_KEY:
        print("❌ 错误: 未找到高德地图API密钥")
        print("请在 .env 文件中设置 AMAP_API_KEY")
        exit(1)
    
    print(f"🔑 使用API密钥: {AMAP_API_KEY[:8]}...")
    print()
    
    # 询问用户
    print("⚠️  警告: 此操作将修改数据库中的餐厅坐标!")
    print("建议先备份数据库文件: backend/data/restaurants.db")
    print()
    
    confirm = input("是否继续? (yes/no): ")
    if confirm.lower() != 'yes':
        print("已取消操作")
        exit(0)
    
    # 执行更新
    limit = int(input("请输入要处理的餐厅数量 (默认50): ") or "50")
    update_restaurant_coordinates(AMAP_API_KEY, limit)
