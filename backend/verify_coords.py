"""
验证餐厅坐标准确性
对比数据库坐标和高德地图API返回的坐标
"""

import sqlite3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

AMAP_API_KEY = os.getenv('AMAP_API_KEY', '')

def geocode_with_amap(address):
    """使用高德地理编码API获取准确坐标"""
    if not AMAP_API_KEY:
        print("⚠️  未配置高德API密钥,跳过验证")
        return None
    
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "address": address,
        "city": "南京",
        "key": AMAP_API_KEY,
        "output": "JSON"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data.get("status") == "1" and data.get("geocodes"):
            location = data["geocodes"][0]["location"]
            lng, lat = location.split(",")
            return {
                "lat": float(lat),
                "lng": float(lng),
                "formatted_address": data["geocodes"][0].get("formatted_address", "")
            }
        else:
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None


def verify_restaurant_coords():
    """验证餐厅坐标"""
    print("=" * 80)
    print("🗺️  餐厅坐标准确性验证")
    print("=" * 80)
    
    conn = sqlite3.connect('data/restaurants.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, address, lat, lng FROM restaurants LIMIT 10')
    restaurants = cursor.fetchall()
    conn.close()
    
    print(f"\n📋 验证前10家餐厅:\n")
    
    for i, (rid, name, address, db_lat, db_lng) in enumerate(restaurants, 1):
        print(f"{i}. {name}")
        print(f"   数据库坐标(WGS-84): {db_lat:.6f}, {db_lng:.6f}")
        
        # 使用高德API验证
        search_addr = f"{name} {address}"
        amap_result = geocode_with_amap(search_addr)
        
        if amap_result:
            api_lat = amap_result['lat']
            api_lng = amap_result['lng']
            
            # 计算差异(米)
            lat_diff_meters = abs(api_lat - db_lat) * 111000
            lng_diff_meters = abs(api_lng - db_lng) * 111000
            total_diff = (lat_diff_meters**2 + lng_diff_meters**2)**0.5
            
            print(f"   高德API坐标(GCJ-02): {api_lat:.6f}, {api_lng:.6f}")
            print(f"   差异: {total_diff:.0f}米")
            
            if total_diff > 100:
                print(f"   ⚠️  警告: 偏差超过100米,可能需要更新!")
            else:
                print(f"   ✅ 坐标准确")
        else:
            print(f"   ❌ 无法通过高德API验证")
        
        print()


if __name__ == '__main__':
    if not AMAP_API_KEY:
        print("❌ 错误: 请在 .env 文件中配置 AMAP_API_KEY")
        print("   或者手动检查数据库坐标是否准确")
    else:
        verify_restaurant_coords()
