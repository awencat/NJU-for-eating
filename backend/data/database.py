# data/database.py
# 数据库操作模块

import sqlite3
import os
import json
from contextlib import contextmanager
from typing import List, Dict, Any, Optional


class Database:
    """数据库操作类"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接（上下文管理器）
        自动处理提交和关闭
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典形式
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建餐厅表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS restaurants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lng REAL NOT NULL,
                    address TEXT,
                    cuisine TEXT,
                    price INTEGER DEFAULT 30,
                    rating REAL DEFAULT 3.5,
                    wait_time INTEGER DEFAULT 10,
                    phone TEXT,
                    hours TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建用户反馈表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    restaurant_id INTEGER,
                    user_id TEXT,
                    rating INTEGER,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
                )
            ''')
            
            # 创建用户表（可选，用于用户管理）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建用户偏好表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE,
                    max_price INTEGER DEFAULT 50,
                    max_distance INTEGER DEFAULT 1000,
                    cuisines TEXT,
                    accept_wait INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_location ON restaurants(lat, lng)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_cuisine ON restaurants(cuisine)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants(rating)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_restaurant ON user_feedback(restaurant_id)')
            
            # 检查是否需要插入初始数据
            cursor.execute('SELECT COUNT(*) FROM restaurants')
            count = cursor.fetchone()[0]
            if count == 0:
                self._insert_sample_data(conn)
    
    def _insert_sample_data(self, conn):
        """插入示例餐厅数据（南京大学鼓楼校区周边）"""
        sample_restaurants = [
            ("小四川菜馆", 32.0542, 118.7835, "鼓楼区汉口路22号", "川菜", 35, 4.5, 15, "025-83591234", "10:00-21:30", "辣,实惠,学生常去"),
            ("东北人家", 32.0560, 118.7850, "鼓楼区广州路5号", "东北菜", 40, 4.3, 10, "025-83592345", "09:30-22:00", "量大,实惠,炖菜"),
            ("轻食沙拉", 32.0520, 118.7800, "鼓楼区北京西路1号", "西餐", 45, 4.6, 5, "025-83593456", "10:00-20:00", "健康,低卡,素食"),
            ("湘味轩", 32.0550, 118.7820, "鼓楼区青岛路8号", "湘菜", 38, 4.4, 20, "025-83594567", "11:00-22:00", "辣,下饭,特色"),
            ("日式料理亭", 32.0530, 118.7840, "鼓楼区上海路12号", "日料", 68, 4.7, 25, "025-83595678", "11:30-21:30", "精致,刺身,寿司"),
            ("麦当劳", 32.0570, 118.7810, "鼓楼区中山路88号", "快餐", 28, 4.2, 8, "025-83596789", "00:00-24:00", "汉堡,薯条,24小时"),
            ("肯德基", 32.0510, 118.7860, "鼓楼区中央路1号", "快餐", 30, 4.3, 10, "025-83597890", "00:00-24:00", "炸鸡,蛋挞,24小时"),
            ("兰州拉面", 32.0545, 118.7838, "鼓楼区汉口路30号", "西北菜", 22, 4.1, 5, "025-83598901", "08:00-22:00", "面食,实惠,快速"),
            ("海底捞火锅", 32.0580, 118.7800, "鼓楼区中央路201号", "火锅", 120, 4.8, 45, "025-83599012", "10:00-03:00", "服务好,火锅,夜宵"),
            ("必胜客", 32.0500, 118.7870, "鼓楼区中山路150号", "西餐", 65, 4.4, 15, "025-83590123", "10:30-22:00", "披萨,意面,下午茶"),
            ("COCO都可", 32.0548, 118.7832, "鼓楼区汉口路15号", "饮品", 15, 4.3, 5, "025-83591235", "10:00-21:00", "奶茶,饮品,快速"),
            ("烤鸭店", 32.0555, 118.7845, "鼓楼区广州路10号", "烤鸭", 50, 4.5, 20, "025-83592346", "11:00-20:30", "烤鸭,北京风味"),
            ("新疆大盘鸡", 32.0565, 118.7825, "鼓楼区青岛路20号", "新疆菜", 45, 4.4, 15, "025-83593457", "11:00-22:00", "大盘鸡,羊肉串"),
            ("重庆小面", 32.0535, 118.7855, "鼓楼区上海路8号", "川菜", 20, 4.2, 8, "025-83594568", "07:00-21:00", "面食,辣,快速"),
            ("星巴克", 32.0590, 118.7790, "鼓楼区中央路100号", "咖啡", 35, 4.5, 10, "025-83595679", "08:00-22:00", "咖啡,甜点,休闲"),
            ("南京大牌档", 32.0685, 118.7805, "鼓楼区湖南路2号", "南京菜", 80, 4.6, 30, "025-83611234", "11:00-21:30", "特色,本地菜,老字号"),
            ("喜茶", 32.0555, 118.7820, "鼓楼区中山路50号", "饮品", 28, 4.7, 20, "025-83594578", "10:00-22:00", "奶茶,网红,排队"),
            ("绿茶餐厅", 32.0535, 118.7815, "鼓楼区北京西路4号", "杭帮菜", 55, 4.4, 25, "025-83595689", "10:30-21:30", "性价比,江浙菜"),
            ("西贝莜面村", 32.0600, 118.7820, "鼓楼区中央路210号", "西北菜", 85, 4.5, 35, "025-83596790", "11:00-21:30", "西北菜,面食,儿童餐"),
            ("探鱼", 32.0525, 118.7855, "鼓楼区上海路20号", "烤鱼", 75, 4.4, 40, "025-83597801", "11:00-22:00", "烤鱼,麻辣,夜宵"),
            ("呷哺呷哺", 32.0565, 118.7835, "鼓楼区广州路15号", "火锅", 60, 4.3, 25, "025-83598912", "10:00-22:00", "小火锅,性价比"),
            ("星巴克", 32.0590, 118.7790, "鼓楼区中央路100号", "咖啡", 35, 4.5, 10, "025-83595679", "08:00-22:00", "咖啡,甜点,休闲"),
            ("瑞幸咖啡", 32.0540, 118.7845, "鼓楼区汉口路25号", "咖啡", 15, 4.4, 5, "025-83591246", "08:00-20:00", "咖啡,外卖,优惠"),
            ("一点点", 32.0538, 118.7830, "鼓楼区青岛路5号", "饮品", 12, 4.2, 8, "025-83592357", "10:00-21:00", "奶茶,便宜,网红"),
            ("杨国福麻辣烫", 32.0552, 118.7828, "鼓楼区广州路8号", "麻辣烫", 25, 4.3, 15, "025-83593468", "10:00-22:00", "麻辣烫,自选,实惠"),
        ]
        
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO restaurants (name, lat, lng, address, cuisine, price, rating, wait_time, phone, hours, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_restaurants)
        
        print(f"已插入 {len(sample_restaurants)} 条示例餐厅数据")
    
    # ==================== 餐厅操作 ====================
    
    def get_all_restaurants(self) -> List[Dict]:
        """获取所有餐厅"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM restaurants ORDER BY rating DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_restaurant_by_id(self, restaurant_id: int) -> Optional[Dict]:
        """根据ID获取餐厅"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM restaurants WHERE id = ?', (restaurant_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_restaurants_by_cuisine(self, cuisine: str) -> List[Dict]:
        """根据菜系获取餐厅"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM restaurants WHERE cuisine = ? ORDER BY rating DESC', (cuisine,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_restaurants_by_price_range(self, min_price: int, max_price: int) -> List[Dict]:
        """根据价格区间获取餐厅"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM restaurants 
                WHERE price BETWEEN ? AND ? 
                ORDER BY price ASC
            ''', (min_price, max_price))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_top_rated_restaurants(self, limit: int = 10) -> List[Dict]:
        """获取评分最高的餐厅"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM restaurants 
                ORDER BY rating DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_restaurants(self, keyword: str) -> List[Dict]:
        """搜索餐厅（按名称或菜系）"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM restaurants 
                WHERE name LIKE ? OR cuisine LIKE ? OR tags LIKE ?
                ORDER BY rating DESC
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_restaurant(self, restaurant: Dict) -> int:
        """添加新餐厅"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO restaurants (name, lat, lng, address, cuisine, price, rating, wait_time, phone, hours, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                restaurant['name'],
                restaurant['lat'],
                restaurant['lng'],
                restaurant.get('address', ''),
                restaurant.get('cuisine', ''),
                restaurant.get('price', 30),
                restaurant.get('rating', 3.5),
                restaurant.get('wait_time', 10),
                restaurant.get('phone', ''),
                restaurant.get('hours', ''),
                restaurant.get('tags', '')
            ))
            return cursor.lastrowid
    
    def update_restaurant(self, restaurant_id: int, updates: Dict) -> bool:
        """更新餐厅信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            fields = []
            values = []
            for key, value in updates.items():
                if key in ['name', 'lat', 'lng', 'address', 'cuisine', 'price', 'rating', 'wait_time', 'phone', 'hours', 'tags']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return False
            
            values.append(restaurant_id)
            query = f"UPDATE restaurants SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            return cursor.rowcount > 0
    
    def delete_restaurant(self, restaurant_id: int) -> bool:
        """删除餐厅"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM restaurants WHERE id = ?', (restaurant_id,))
            return cursor.rowcount > 0
    
    # ==================== 反馈操作 ====================
    
    def add_feedback(self, restaurant_id: int, user_id: str, rating: int, comment: str = '') -> int:
        """添加用户反馈"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_feedback (restaurant_id, user_id, rating, comment)
                VALUES (?, ?, ?, ?)
            ''', (restaurant_id, user_id, rating, comment))
            return cursor.lastrowid
    
    def get_feedback_by_restaurant(self, restaurant_id: int) -> List[Dict]:
        """获取餐厅的所有反馈"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM user_feedback 
                WHERE restaurant_id = ? 
                ORDER BY created_at DESC
            ''', (restaurant_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_average_rating(self, restaurant_id: int) -> float:
        """获取餐厅的平均评分"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT AVG(rating) as avg_rating 
                FROM user_feedback 
                WHERE restaurant_id = ?
            ''', (restaurant_id,))
            row = cursor.fetchone()
            return round(row['avg_rating'], 1) if row['avg_rating'] else 0.0
    
    # ==================== 用户偏好操作 ====================
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """获取用户偏好"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                prefs = dict(row)
                # 解析菜系JSON
                if prefs.get('cuisines'):
                    try:
                        prefs['cuisines'] = json.loads(prefs['cuisines'])
                    except:
                        prefs['cuisines'] = ['全部']
                else:
                    prefs['cuisines'] = ['全部']
                return prefs
            return None
    
    def save_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """保存用户偏好"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cuisines_json = json.dumps(preferences.get('cuisines', ['全部']))
            
            cursor.execute('''
                INSERT INTO user_preferences (user_id, max_price, max_distance, cuisines, accept_wait, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    max_price = excluded.max_price,
                    max_distance = excluded.max_distance,
                    cuisines = excluded.cuisines,
                    accept_wait = excluded.accept_wait,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                user_id,
                preferences.get('max_price', 50),
                preferences.get('max_distance', 1000),
                cuisines_json,
                1 if preferences.get('accept_wait', True) else 0
            ))
            return True
    
    # ==================== 统计操作 ====================
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 餐厅总数
            cursor.execute('SELECT COUNT(*) as total FROM restaurants')
            total_restaurants = cursor.fetchone()['total']
            
            # 菜系列表
            cursor.execute('SELECT DISTINCT cuisine FROM restaurants')
            cuisines = [row['cuisine'] for row in cursor.fetchall()]
            
            # 平均价格
            cursor.execute('SELECT AVG(price) as avg_price FROM restaurants')
            avg_price = cursor.fetchone()['avg_price'] or 0
            
            # 平均评分
            cursor.execute('SELECT AVG(rating) as avg_rating FROM restaurants')
            avg_rating = cursor.fetchone()['avg_rating'] or 0
            
            # 反馈总数
            cursor.execute('SELECT COUNT(*) as total FROM user_feedback')
            total_feedback = cursor.fetchone()['total']
            
            return {
                'total_restaurants': total_restaurants,
                'cuisines': cuisines,
                'avg_price': round(avg_price, 1),
                'avg_rating': round(avg_rating, 1),
                'total_feedback': total_feedback
            }


# 全局数据库实例
_db_instance = None


def get_db(db_path: str = None) -> Database:
    """
    获取数据库单例
    
    Args:
        db_path: 数据库路径（仅在第一次调用时生效）
    
    Returns:
        Database实例
    """
    global _db_instance
    if _db_instance is None:
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'restaurants.db')
        _db_instance = Database(db_path)
    return _db_instance


def init_database(db_path: str = None) -> Database:
    """
    初始化数据库（别名函数）
    
    Args:
        db_path: 数据库路径
    
    Returns:
        Database实例
    """
    return get_db(db_path)