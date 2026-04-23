"""
测试高德地图路径规划API - 详细版
"""
import requests
import json
from config import get_config

def test_amap_api_detailed():
    """测试高德API并打印完整响应"""
    
    config = get_config()
    api_key = config.AMAP_API_KEY
    
    print("=" * 60)
    print("高德地图API详细测试")
    print("=" * 60)
    print(f"API Key: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else api_key}")
    print(f"API Timeout: {config.API_TIMEOUT}秒")
    
    # 测试坐标（南京大学鼓楼校区 -> 附近餐厅）
    origin = "118.7835,32.0542"  # 经度,纬度
    destination = "118.7850,32.0560"
    
    print("\n【测试1】步行模式 (walking) - 详细数据结构")
    print("-" * 60)
    
    url = "https://restapi.amap.com/v3/direction/walking"
    params = {
        "origin": origin,
        "destination": destination,
        "key": api_key,
        "output": "JSON"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=config.API_TIMEOUT)
        data = resp.json()
        
        print(f"HTTP状态码: {resp.status_code}")
        print(f"返回状态: status={data.get('status')}, info={data.get('info')}")
        
        if data.get('status') == '1':
            route = data.get('route', {})
            paths = route.get('paths', [])
            
            print(f"✅ API调用成功")
            print(f"路径数量: {len(paths)}")
            
            if paths:
                path = paths[0]
                print(f"\n路径信息:")
                print(f"  距离: {path.get('distance')} 米")
                print(f"  时间: {path.get('duration')} 秒")
                
                # 查看polyline数据结构
                polyline = path.get('polyline', '')
                print(f"  polyline长度: {len(polyline)} 字符")
                
                if polyline:
                    # 显示polyline前200个字符
                    print(f"  polyline预览: {polyline[:200]}...")
                    
                    # 解析前几个点
                    points = polyline.split(';')[:5]
                    print(f"  前5个坐标点:")
                    for i, point in enumerate(points):
                        if ',' in point:
                            lng, lat = point.split(',')
                            print(f"    [{i}] 经度={lng}, 纬度={lat}")
                else:
                    print(f"  ⚠️ polyline为空！")
                    print(f"  路径keys: {list(path.keys())}")
                    
                    # 检查是否有steps
                    steps = path.get('steps', [])
                    print(f"  steps数量: {len(steps)}")
                    if steps:
                        print(f"  第一个step的keys: {list(steps[0].keys())}")
                        if 'polyline' in steps[0]:
                            step_polyline = steps[0]['polyline']
                            print(f"  step中有polyline: {len(step_polyline)} 字符")
                            if step_polyline:
                                print(f"  step polyline预览: {step_polyline[:100]}...")
            else:
                print("❌ 返回数据中没有路径信息")
        else:
            print(f"❌ API调用失败: {data.get('info')}")
            print(f"infocode: {data.get('infocode', 'N/A')}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print()
    
    # 测试2: 骑行模式
    print("【测试2】骑行模式 (bicycling)")
    print("-" * 60)
    try:
        url = "https://restapi.amap.com/v3/direction/bicycling"
        params = {
            "origin": origin,
            "destination": destination,
            "key": api_key,
            "output": "JSON"
        }
        
        resp = requests.get(url, params=params, timeout=config.API_TIMEOUT)
        data = resp.json()
        
        print(f"返回状态: status={data.get('status')}, info={data.get('info')}")
        
        if data.get('status') == '1':
            print("✅ 骑行服务可用")
        else:
            print(f"⚠️ 骑行服务不可用: {data.get('info')}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    print()
    
    # 测试3: 公交模式
    print("【公交模式测试】")
    print("-" * 60)
    
    url = "https://restapi.amap.com/v3/direction/transit/integrated"
    params = {
        "origin": origin,
        "destination": destination,
        "city": "南京",
        "cityd": "南京",
        "key": api_key,
        "output": "JSON"
    }
    
    resp = requests.get(url, params=params, timeout=config.API_TIMEOUT)
    data = resp.json()
    
    if data.get('status') == '1':
        route = data.get('route', {})
        print(f"✅ API调用成功")
        print(f"route keys: {list(route.keys())}")
        
        transits = route.get('transits', [])
        print(f"transits数量: {len(transits)}")
        
        if transits:
            transit = transits[0]
            print(f"\n第一个transit的keys: {list(transit.keys())}")
            
            distance = transit.get('distance', 0)
            duration = transit.get('duration', 0)
            print(f"距离: {distance} 米")
            print(f"时间: {duration} 秒")
            
            segments = transit.get('segments', [])
            print(f"segments数量: {len(segments)}")
            
            if segments:
                print(f"第一个segment的keys: {list(segments[0].keys())}")
        else:
            print("⚠️ 没有可用的公交线路")
    else:
        print(f"❌ API调用失败: {data.get('info')}")
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_amap_api_detailed()
