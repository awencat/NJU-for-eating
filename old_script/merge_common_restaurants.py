import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

SOURCE_CANDIDATES = {
    "amap": ["restruant.csv", "restaurant.csv", "restaurants.csv"],
    "combined": [
        "all_combined_resturant.csv",
        "all_combined_restaurant.csv",
        "all_restaurants_combined.csv",
    ],
}

OUTPUT_CSV = BASE_DIR / "common_restaurants_merged.csv"


def find_existing_file(candidates: list[str]) -> Path:
    for filename in candidates:
        path = BASE_DIR / filename
        if path.exists():
            return path
    raise FileNotFoundError(f"未找到文件，尝试过：{', '.join(candidates)}")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def normalize_name(name: str) -> str:
    return "".join((name or "").split()).strip().lower()


def choose_best_combined_row(rows: list[dict[str, str]]) -> dict[str, str]:
    def review_count(row: dict[str, str]) -> int:
        digits = "".join(ch for ch in row.get("review_count", "") if ch.isdigit())
        return int(digits) if digits else 0

    def rating(row: dict[str, str]) -> float:
        text = row.get("rating", "").replace("星", "").strip()
        try:
            return float(text)
        except ValueError:
            return 0.0

    return max(rows, key=lambda row: (review_count(row), rating(row)))


def build_combined_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        key = normalize_name(row.get("name", ""))
        if not key:
            continue
        grouped.setdefault(key, []).append(row)

    return {key: choose_best_combined_row(group) for key, group in grouped.items()}


def merge_rows(
    amap_rows: list[dict[str, str]], combined_index: dict[str, dict[str, str]]
) -> list[dict[str, str]]:
    merged_rows: list[dict[str, str]] = []

    for amap_row in amap_rows:
        name = amap_row.get("名称", "").strip()
        key = normalize_name(name)
        combined_row = combined_index.get(key)
        if not combined_row:
            continue

        merged_rows.append(
            {
                "名称": name,
                "地址": amap_row.get("地址", "").strip(),
                "电话": amap_row.get("电话", "").strip(),
                "评论数": combined_row.get("review_count", "").strip(),
                "评分": combined_row.get("rating", "").strip(),
                "代表菜品": combined_row.get("recommended_dishes", "").strip(),
                "类型": combined_row.get("category", "").strip(),
                "经度": amap_row.get("经度", "").strip(),
                "纬度": amap_row.get("纬度", "").strip(),
            }
        )

    return merged_rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = ["名称", "地址", "电话", "评论数", "评分", "代表菜品", "类型", "经度", "纬度"]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    amap_path = find_existing_file(SOURCE_CANDIDATES["amap"])
    combined_path = find_existing_file(SOURCE_CANDIDATES["combined"])

    amap_rows = read_csv_rows(amap_path)
    combined_rows = read_csv_rows(combined_path)
    combined_index = build_combined_index(combined_rows)
    merged_rows = merge_rows(amap_rows, combined_index)

    write_csv(OUTPUT_CSV, merged_rows)

    print(f"Amap数据文件：{amap_path.name}")
    print(f"综合数据文件：{combined_path.name}")
    print(f"共同餐馆数量：{len(merged_rows)}")
    print(f"导出文件：{OUTPUT_CSV.name}")


if __name__ == "__main__":
    main()
