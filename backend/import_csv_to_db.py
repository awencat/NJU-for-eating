"""
批量导入CSV餐厅数据到数据库
使用方法: python import_csv_to_db.py
"""

import csv
import os
import sys
from data.database import Database


def clean_phone(phone_str):
    """清理电话号码格式"""
    if not phone_str or phone_str == '[]':
        return ''
    # 移除多余的分隔符，只保留第一个号码
    phones = phone_str.split(';')
    return phones[0].strip() if phones else ''


def clean_tags(poi_type):
    """从POI类型中提取标签"""
    if not poi_type:
        return ''
    # 例如: "餐饮服务;中餐厅;中餐厅" -> "餐饮服务,中餐厅"
    parts = poi_type.split(';')
    return ','.join([p.strip() for p in parts if p.strip()])


def import_restaurants_from_csv(csv_file='restaurants.csv', db_path='data/restaurants.db'):
    """
    从CSV文件导入餐厅数据到数据库
    
    Args:
        csv_file: CSV文件路径
        db_path: 数据库文件路径
    """
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_file):
        print(f"❌ 错误: 找不到文件 {csv_file}")
        print(f"当前工作目录: {os.getcwd()}")
        return False
    
    # 初始化数据库
    print(f"📊 正在连接数据库: {db_path}")
    db = Database(db_path)
    
    # 读取CSV文件
    print(f"📖 正在读取CSV文件: {csv_file}")
    restaurants = []
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # 提取字段
                name = row.get('名称', '').strip()
                address = row.get('地址', '').strip()
                lng = float(row.get('经度', 0))
                lat = float(row.get('纬度', 0))
                phone = clean_phone(row.get('电话', ''))
                poi_type = row.get('类型', '')
                tags = clean_tags(poi_type)
                
                # 跳过无效数据
                if not name or lat == 0 or lng == 0:
                    print(f"⚠️  跳过无效数据: {name or '未知餐厅'}")
                    continue
                
                # 简化菜系分类(从POI类型中提取)
                cuisine = '其他'
                if '川菜' in poi_type or '四川' in name:
                    cuisine = '川菜'
                elif '东北' in poi_type or '东北' in name:
                    cuisine = '东北菜'
                elif '西餐' in poi_type or '披萨' in name or '牛排' in name:
                    cuisine = '西餐'
                elif '日料' in poi_type or '日本' in poi_type or '寿司' in name:
                    cuisine = '日料'
                elif '火锅' in poi_type or '火锅' in name:
                    cuisine = '火锅'
                elif '快餐' in poi_type or '汉堡' in name or '炸鸡' in name:
                    cuisine = '快餐'
                elif '咖啡' in poi_type or '咖啡' in name:
                    cuisine = '咖啡'
                elif '奶茶' in poi_type or '饮品' in poi_type or '茶' in name:
                    cuisine = '饮品'
                elif '小吃' in poi_type or '烧烤' in poi_type:
                    cuisine = '小吃'
                elif '湘菜' in poi_type or '湖南' in name:
                    cuisine = '湘菜'
                elif '粤菜' in poi_type or '广东' in name:
                    cuisine = '粤菜'
                elif '西北' in poi_type or '兰州' in name:
                    cuisine = '西北菜'
                elif '新疆' in poi_type:
                    cuisine = '新疆菜'
                elif '面食' in poi_type or '面馆' in name:
                    cuisine = '面食'
                elif '食堂' in name or '餐厅' in name:
                    cuisine = '食堂'
                else:
                    cuisine = '中餐'
                
                # 生成默认值
                import random
                price = random.randint(15, 80)  # 随机价格
                rating = round(random.uniform(3.5, 4.8), 1)  # 随机评分
                wait_time = random.randint(5, 30)  # 随机等待时间
                hours = "10:00-22:00"  # 默认营业时间
                
                restaurant_data = {
                    'name': name,
                    'lat': lat,
                    'lng': lng,
                    'address': address,
                    'cuisine': cuisine,
                    'price': price,
                    'rating': rating,
                    'wait_time': wait_time,
                    'phone': phone,
                    'hours': hours,
                    'tags': tags
                }
                
                restaurants.append(restaurant_data)
                
            except Exception as e:
                print(f"❌ 处理行数据时出错: {e}")
                print(f"   数据: {row}")
                continue
    
    print(f"✅ 成功解析 {len(restaurants)} 条餐厅数据")
    
    # 插入数据库
    if not restaurants:
        print("⚠️  没有可导入的数据")
        return False
    
    print(f"💾 正在插入数据库...")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # 清空现有数据(可选,注释掉则追加数据)
        cursor.execute('DELETE FROM restaurants')
        print("🗑️  已清空现有餐厅数据")
        
        # 批量插入
        inserted = 0
        for r in restaurants:
            try:
                cursor.execute('''
                    INSERT INTO restaurants (name, lat, lng, address, cuisine, price, rating, wait_time, phone, hours, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    r['name'], r['lat'], r['lng'], r['address'],
                    r['cuisine'], r['price'], r['rating'], r['wait_time'],
                    r['phone'], r['hours'], r['tags']
                ))
                inserted += 1
            except Exception as e:
                print(f"❌ 插入失败: {r['name']} - {e}")
        
        print(f"✅ 成功导入 {inserted}/{len(restaurants)} 条餐厅数据")
    
    # 显示统计信息
    print("\n📊 数据统计:")
    all_restaurants = db.get_all_restaurants()
    
    from collections import Counter
    cuisines = [r['cuisine'] for r in all_restaurants]
    cuisine_count = Counter(cuisines)
    
    print(f"  总餐厅数: {len(all_restaurants)}")
    print(f"  菜系分布:")
    for cuisine, count in cuisine_count.most_common():
        print(f"    {cuisine}: {count}家")
    
    prices = [r['price'] for r in all_restaurants]
    ratings = [r['rating'] for r in all_restaurants]
    
    print(f"  价格区间: ¥{min(prices)} - ¥{max(prices)}")
    print(f"  平均价格: ¥{sum(prices)/len(prices):.0f}")
    print(f"  平均评分: {sum(ratings)/len(ratings):.1f}⭐")
    
    print("\n✨ 导入完成!")
    return True


if __name__ == '__main__':
    # 支持命令行参数
    import sys
    
    # 默认使用根目录的restaurants.csv
    csv_file = sys.argv[1] if len(sys.argv) > 1 else '../restaurants.csv'
    db_path = sys.argv[2] if len(sys.argv) > 2 else 'data/restaurants.db'
    
    print("=" * 60)
    print("🍽️  餐厅数据批量导入工具")
    print("=" * 60)
    print(f"CSV文件: {csv_file}")
    print(f"数据库: {db_path}")
    print("=" * 60)
    
    success = import_restaurants_from_csv(csv_file, db_path)
    
    if success:
        print("\n💡 提示:")
        print("  1. 请重启Flask服务以加载新数据")
        print("  2. 刷新浏览器页面查看更新后的餐厅")
        print("  3. 如需保留原有数据,请修改脚本中的DELETE语句")
    else:
        print("\n❌ 导入失败,请检查错误信息")
        sys.exit(1)
