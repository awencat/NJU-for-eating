import requests
import json
import csv
import time
from typing import List, Dict

# ==================== 配置参数（请按实际情况修改）====================
API_KEY = "6c0106f59b6daeef09d31bceebe0de8c"                # 替换成你自己的Key
CENTER_LNG = 118.781366                   # 中心点经度（例如天安门）
CENTER_LAT = 32.051983                     # 中心点纬度
RADIUS = 2000                              # 搜索半径（米），最大50000
POI_TYPES = "050000"                       # 餐饮大类代码
OUTPUT_CSV = "restaurants.csv"             # 输出CSV文件名
# ===================================================================

def fetch_pois_by_page(page: int, page_size: int = 25) -> Dict:
    """
    获取一页的POI数据
    :param page: 页码（从1开始）
    :param page_size: 每页数量，最大25
    :return: API返回的JSON数据（字典）
    """
    url = "https://restapi.amap.com/v3/place/around"
    params = {
        "key": API_KEY,
        "location": f"{CENTER_LNG},{CENTER_LAT}",
        "radius": RADIUS,
        "types": POI_TYPES,
        "offset": page_size,
        "page": page,
        "output": "JSON"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        print(f"请求第{page}页时出错: {e}")
        return {"status": "0", "info": str(e)}

def get_all_pois() -> List[Dict]:
    """
    自动分页获取所有POI数据
    :return: 所有POI对象的列表
    """
    all_pois = []
    page = 1
    page_size = 25
    total_count = 0

    while True:
        print(f"正在获取第{page}页...")
        data = fetch_pois_by_page(page, page_size)

        if data.get("status") != "1":
            print(f"API返回错误: {data.get('info')}")
            break

        # 当前页的POI列表
        pois = data.get("pois", [])
        if not pois:
            break

        all_pois.extend(pois)

        # 获取总数（第一次请求时）
        if total_count == 0:
            total_count = int(data.get("count", 0))
            print(f"共找到 {total_count} 条记录")

        # 判断是否还有下一页
        if len(pois) < page_size:
            break

        page += 1
        time.sleep(0.1)  # 避免请求过快，礼貌一点

    print(f"实际获取到 {len(all_pois)} 条记录")
    return all_pois

def save_to_csv(pois: List[Dict], filename: str):
    """
    将POI数据保存为CSV文件，整理关键字段
    """
    if not pois:
        print("没有数据可保存")
        return

    # 定义要保存的字段及对应的JSON路径
    field_mapping = {
        "名称": "name",
        "地址": "address",
        "经度": lambda p: p.get("location", "").split(",")[0] if p.get("location") else "",
        "纬度": lambda p: p.get("location", "").split(",")[1] if p.get("location") else "",
        "电话": "tel",
        "类型": "type",
        "高德POI ID": "id",
        "所在省": "pname",
        "所在市": "cityname",
        "所在区": "adname"
    }

    rows = []
    for poi in pois:
        row = {}
        for col_name, source in field_mapping.items():
            if callable(source):
                value = source(poi)
            else:
                value = poi.get(source, "")
            row[col_name] = value
        rows.append(row)

    # 写入CSV
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=field_mapping.keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"数据已保存至 {filename}")

def main():
    print("开始获取餐饮POI数据...")
    pois = get_all_pois()
    if pois:
        save_to_csv(pois, OUTPUT_CSV)
        print("完成！")
    else:
        print("未获取到任何数据，请检查网络、API Key或参数设置。")

if __name__ == "__main__":
    main()