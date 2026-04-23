import csv
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = BASE_DIR / "restaurants.csv"
OUTPUT_CSV = BASE_DIR / "restaurant_types.csv"


def extract_restaurant_types():
    if not INPUT_CSV.exists():
        print(f"❌ 错误：未找到文件 {INPUT_CSV}")
        return

    type_counter = Counter()
    type_details = {}

    with INPUT_CSV.open("r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            restaurant_type_raw = row.get("类型", "").strip()
            restaurant_name = row.get("名称", "").strip()

            if restaurant_type_raw:
                parts = restaurant_type_raw.split(";")
                if len(parts) >= 3:
                    restaurant_type = parts[2].strip()
                elif len(parts) == 2:
                    restaurant_type = parts[1].strip()
                else:
                    restaurant_type = parts[0].strip()

                if restaurant_type:
                    type_counter[restaurant_type] += 1

                    if restaurant_type not in type_details:
                        type_details[restaurant_type] = []
                    type_details[restaurant_type].append(restaurant_name)

    sorted_types = sorted(type_counter.items(), key=lambda x: x[1], reverse=True)

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["类型"])

        for restaurant_type, count in sorted_types:
            examples = "; ".join(type_details[restaurant_type][:3])
            writer.writerow([restaurant_type])

    print(f"✅ 成功提取 {len(sorted_types)} 种餐馆类型")
    print(f"📄 结果已保存到: {OUTPUT_CSV}")
    print(f"\n📊 前10种最常见的类型:")
    for i, (rtype, count) in enumerate(sorted_types[:10], 1):
        print(f"   {i}. {rtype}: {count}家")


if __name__ == "__main__":
    extract_restaurant_types()

