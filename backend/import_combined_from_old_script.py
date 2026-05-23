"""
使用 old_script/all_restaurants_combined.csv 重建数据库。

能力：
1. 读取大众点评整理后的餐厅列表
2. 使用高德 Place Text API 补齐地址、电话、经纬度
3. 生成一份 enriched CSV 方便人工复核
4. 清空并重建 restaurants 表数据

优先使用 `.env` 中的 AMAP_API_KEY；
如果未配置，则回退读取 old_script/main.py 中遗留的 API_KEY。
"""

from __future__ import annotations

import csv
import os
import random
import re
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional, Any

import requests
from dotenv import load_dotenv

from data.database import Database


ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCE_CSV = ROOT_DIR / "old_script" / "all_restaurants_combined.csv"
ENRICHED_CSV = ROOT_DIR / "old_script" / "all_restaurants_combined_enriched.csv"
UNMATCHED_CSV = ROOT_DIR / "old_script" / "all_restaurants_unmatched.csv"
DEFAULT_DB_PATH = ROOT_DIR / "backend" / "data" / "restaurants.db"
CITY_NAME = "南京"


AREA_HINTS = {
    "珠江路沿线": "玄武区珠江路",
    "新街口/德基广场": "秦淮区新街口",
    "新街口地区": "秦淮区新街口",
    "南大/南师大": "鼓楼区广州路",
    "夫子庙地区": "秦淮区夫子庙",
    "夫子庙/水游城": "秦淮区水游城",
    "升州路/集庆路": "秦淮区升州路",
    "山西路/湖南路": "鼓楼区湖南路",
    "火车站/玄武湖": "玄武区玄武湖",
    "莫愁湖/水西门": "建邺区水西门",
    "瑞金路沿线": "秦淮区瑞金路",
    "奥体中心": "建邺区奥体中心",
}


@dataclass
class MatchResult:
    name: str
    address: str
    lat: float
    lng: float
    phone: str
    poi_id: str
    poi_name: str
    poi_type: str
    score: float
    query: str


def normalize_name(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[·•・!！'\"“”‘’\s\-_/]+", "", text)
    text = re.sub(r"[()（）\[\]【】]", "", text)
    return text


def strip_branch(text: str) -> str:
    return re.sub(r"[（(].*?[）)]", "", (text or "")).strip()


def extract_branch(text: str) -> str:
    match = re.search(r"[（(](.*?)[）)]", text or "")
    return match.group(1).strip() if match else ""


def parse_price(text: str) -> int:
    digits = "".join(ch for ch in (text or "") if ch.isdigit())
    if not digits:
        return 35
    return max(5, min(int(digits), 500))


def parse_rating(text: str) -> float:
    cleaned = (text or "").replace("星", "").strip()
    try:
        value = float(cleaned)
    except ValueError:
        value = 3.8
    return max(1.0, min(value, 5.0))


def parse_review_count(text: str) -> int:
    digits = "".join(ch for ch in (text or "") if ch.isdigit())
    return int(digits) if digits else 0


def estimate_wait_time(price: int, rating: float, review_count: int) -> int:
    wait = 8
    wait += min(review_count // 2500, 4) * 4
    wait += 6 if price >= 100 else 0
    wait += 4 if rating >= 4.5 else 0
    return max(5, min(wait, 45))


def get_api_key() -> str:
    load_dotenv(ROOT_DIR / ".env")
    key = os.getenv("AMAP_API_KEY", "").strip()
    if key:
        return key

    legacy_script = ROOT_DIR / "old_script" / "main.py"
    if legacy_script.exists():
        text = legacy_script.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r'API_KEY\s*=\s*"([^"]+)"', text)
        if match:
            return match.group(1).strip()

    return ""


class AMapTextSearcher:
    def __init__(self, api_key: str, timeout: int = 10):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://restapi.amap.com/v3/place/text"
        self.session = requests.Session()

    def search(self, keywords: str) -> list[dict[str, Any]]:
        params = {
            "key": self.api_key,
            "keywords": keywords,
            "city": CITY_NAME,
            "citylimit": "true",
            "offset": 10,
            "page": 1,
            "extensions": "all",
            "output": "JSON",
        }
        response = self.session.get(self.base_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "1":
            raise RuntimeError(f"AMap API error: {data.get('info', 'unknown')}")
        return data.get("pois", [])


def build_queries(name: str, area: str) -> list[str]:
    area_hint = AREA_HINTS.get(area, area or "")
    branch = extract_branch(name)
    plain = strip_branch(name)

    queries = [
        name,
        plain,
        f"{name} {area_hint}".strip(),
        f"{plain} {area_hint}".strip(),
    ]

    if branch and plain:
        queries.append(f"{plain} {branch}")
        queries.append(f"{plain} {branch} {area_hint}".strip())

    unique_queries: list[str] = []
    for query in queries:
        query = query.strip()
        if query and query not in unique_queries:
            unique_queries.append(query)
    return unique_queries


def score_poi(source_row: dict[str, str], poi: dict[str, Any], query: str) -> float:
    source_name = source_row["name"].strip()
    source_plain = strip_branch(source_name)
    source_branch = extract_branch(source_name)
    area_hint = AREA_HINTS.get(source_row.get("area", ""), source_row.get("area", ""))

    poi_name = (poi.get("name") or "").strip()
    poi_address = (poi.get("address") or "").strip()
    poi_type = (poi.get("type") or "").strip()
    poi_city = (poi.get("cityname") or "").strip()

    if not poi_name or not poi.get("location"):
        return -1.0

    score = 0.0
    name_exact = normalize_name(source_name) == normalize_name(poi_name)
    plain_exact = normalize_name(source_plain) == normalize_name(strip_branch(poi_name))
    similarity = SequenceMatcher(None, normalize_name(source_plain), normalize_name(strip_branch(poi_name))).ratio()

    if poi_city and CITY_NAME not in poi_city:
        score -= 80
    else:
        score += 10

    if name_exact:
        score += 120
    if plain_exact:
        score += 80

    score += similarity * 60

    if normalize_name(source_plain) in normalize_name(poi_name):
        score += 20
    if normalize_name(poi_name) in normalize_name(source_plain):
        score += 20

    if source_branch:
        branch_norm = normalize_name(source_branch)
        if branch_norm and (
            branch_norm in normalize_name(poi_name)
            or branch_norm in normalize_name(poi_address)
            or branch_norm in normalize_name(query)
        ):
            score += 35

    if area_hint:
        hint_norm = normalize_name(area_hint)
        if hint_norm and (
            hint_norm in normalize_name(poi_address)
            or hint_norm in normalize_name(poi.get("adname", ""))
            or hint_norm in normalize_name(poi.get("business_area", ""))
        ):
            score += 20

    category = (source_row.get("category") or "").strip()
    if category and category in poi_type:
        score += 10

    return score


def find_best_match(searcher: AMapTextSearcher, row: dict[str, str]) -> Optional[MatchResult]:
    best: Optional[MatchResult] = None

    for query in build_queries(row["name"], row.get("area", "")):
        try:
            pois = searcher.search(query)
        except Exception as exc:
            print(f"⚠️ 搜索失败: {row['name']} | {query} | {exc}")
            time.sleep(0.25)
            continue

        for poi in pois:
            score = score_poi(row, poi, query)
            if score < 70:
                continue

            location = (poi.get("location") or "").split(",")
            if len(location) != 2:
                continue

            try:
                lng = float(location[0])
                lat = float(location[1])
            except ValueError:
                continue

            result = MatchResult(
                name=row["name"].strip(),
                address=(poi.get("address") or "").strip(),
                lat=lat,
                lng=lng,
                phone=(poi.get("tel") or "").strip(),
                poi_id=(poi.get("id") or "").strip(),
                poi_name=(poi.get("name") or "").strip(),
                poi_type=(poi.get("type") or "").strip(),
                score=score,
                query=query,
            )

            if best is None or result.score > best.score:
                best = result

        if best and best.score >= 120:
            break

        time.sleep(0.15)

    return best


def build_db_row(source_row: dict[str, str], match: MatchResult) -> dict[str, Any]:
    price = parse_price(source_row.get("avg_price", ""))
    rating = parse_rating(source_row.get("rating", ""))
    review_count = parse_review_count(source_row.get("review_count", ""))
    wait_time = estimate_wait_time(price, rating, review_count)

    tags = [
        source_row.get("category", "").strip(),
        source_row.get("area", "").strip(),
        source_row.get("recommended_dishes", "").strip(),
        f"review_count:{review_count}",
        f"shop_id:{source_row.get('shop_id', '').strip()}",
        f"source:{source_row.get('source_file', '').strip()}",
    ]

    if source_row.get("has_group_buy") == "是":
        tags.append("团购")
    if source_row.get("has_promotion") == "是":
        tags.append("促销")

    tags = [tag for tag in tags if tag]

    return {
        "name": source_row["name"].strip(),
        "lat": match.lat,
        "lng": match.lng,
        "address": match.address,
        "cuisine": source_row.get("category", "").strip() or "其他",
        "price": price,
        "rating": rating,
        "wait_time": wait_time,
        "phone": match.phone,
        "hours": "",
        "tags": ",".join(tags),
        "review_count": review_count,
        "amap_poi_id": match.poi_id,
        "matched_poi_name": match.poi_name,
        "matched_query": match.query,
        "match_score": round(match.score, 2),
        "detail_url": source_row.get("detail_url", "").strip(),
    }


def export_enriched_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    fieldnames = [
        "name",
        "address",
        "lat",
        "lng",
        "phone",
        "cuisine",
        "price",
        "rating",
        "wait_time",
        "review_count",
        "amap_poi_id",
        "matched_poi_name",
        "matched_query",
        "match_score",
        "tags",
        "detail_url",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_unmatched_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    if not rows:
        if output_path.exists():
            output_path.unlink()
        return

    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def replace_database(rows: list[dict[str, Any]], db_path: Path) -> None:
    db = Database(str(db_path))
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM restaurants")
        for row in rows:
            cursor.execute(
                """
                INSERT INTO restaurants
                (name, lat, lng, address, cuisine, price, rating, wait_time, phone, hours, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["name"],
                    row["lat"],
                    row["lng"],
                    row["address"],
                    row["cuisine"],
                    row["price"],
                    row["rating"],
                    row["wait_time"],
                    row["phone"],
                    row["hours"],
                    row["tags"],
                ),
            )


def main() -> int:
    if not SOURCE_CSV.exists():
        print(f"❌ 未找到源文件: {SOURCE_CSV}")
        return 1

    api_key = get_api_key()
    if not api_key:
        print("❌ 未找到高德 API Key，无法补齐地址和坐标。")
        print("请在 .env 中设置 AMAP_API_KEY，或确认 old_script/main.py 中的 API_KEY 仍可用。")
        return 1

    searcher = AMapTextSearcher(api_key)
    source_rows = list(csv.DictReader(SOURCE_CSV.open("r", encoding="utf-8-sig", newline="")))

    enriched_rows: list[dict[str, Any]] = []
    unmatched_rows: list[dict[str, str]] = []

    total = len(source_rows)
    print(f"📍 开始补齐 {total} 条餐厅数据...")

    for index, row in enumerate(source_rows, 1):
        match = find_best_match(searcher, row)
        if not match:
            unmatched_rows.append(row)
            print(f"[{index:03d}/{total}] ❌ 未匹配: {row['name']}")
            continue

        enriched_row = build_db_row(row, match)
        enriched_rows.append(enriched_row)
        print(
            f"[{index:03d}/{total}] ✅ {row['name']} -> {match.poi_name} | "
            f"{match.address} | score={match.score:.1f}"
        )

    export_enriched_csv(enriched_rows, ENRICHED_CSV)
    export_unmatched_csv(unmatched_rows, UNMATCHED_CSV)

    if not enriched_rows:
        print("❌ 没有任何有效匹配，数据库未修改。")
        return 1

    backup_path = DEFAULT_DB_PATH.with_suffix(".backup.db")
    if DEFAULT_DB_PATH.exists():
        backup_path.write_bytes(DEFAULT_DB_PATH.read_bytes())
        print(f"🛟 已备份旧数据库到: {backup_path}")

    replace_database(enriched_rows, DEFAULT_DB_PATH)

    print("\n🎉 导入完成")
    print(f"   成功导入: {len(enriched_rows)}")
    print(f"   未匹配: {len(unmatched_rows)}")
    print(f"   Enriched CSV: {ENRICHED_CSV}")
    if unmatched_rows:
        print(f"   Unmatched CSV: {UNMATCHED_CSV}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
