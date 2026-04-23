# 🛠️ NJU-for-eating 开发者指南

> 技术架构、API文档、部署说明和开发规范

---

## 📋 目录

- [技术架构](#技术架构)
- [数据库设计](#数据库设计)
- [API文档](#api文档)
- [核心算法](#核心算法)
- [坐标系统](#坐标系统)
- [开发环境配置](#开发环境配置)
- [部署指南](#部署指南)
- [常见问题](#常见问题)

---

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────┐
│          前端层 (Frontend)               │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Leaflet  │ │   HTML5  │ │   CSS3  │ │
│  │  Map     │ │   + JS   │ │         │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└──────────────┬──────────────────────────┘
               │ HTTP/JSON
               ↓
┌─────────────────────────────────────────┐
│         API层 (Flask Backend)            │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │recommend │ │restaurants│ │ route   │ │
│  │   API    │ │   API     │ │  API    │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└──────────────┬──────────────────────────┘
               │ Business Logic
               ↓
┌─────────────────────────────────────────┐
│        核心层 (Core Modules)             │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │Recommen- │ │  Route   │ │ Filter  │ │
│  │  der     │ │ Planner  │ │ Engine  │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└──────────────┬──────────────────────────┘
               │ Data Access
               ↓
┌─────────────────────────────────────────┐
│        数据层 (SQLite Database)          │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │restaur-  │ │  user_   │ │  users  │ │
│  │  ants    │ │ feedback │ │         │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└─────────────────────────────────────────┘
```

### 技术选型理由

| 组件 | 选择 | 理由 |
|------|------|------|
| Web框架 | Flask | 轻量级、易上手、RESTful API友好 |
| 数据库 | SQLite | 零配置、文件型、适合小型项目 |
| 地图引擎 | Leaflet | 开源免费、插件丰富、性能优秀 |
| 地图服务 | 高德API | 国内数据准确、路径规划可靠 |
| 前端框架 | 原生JS | 无构建工具依赖、易于理解 |

---

## 💾 数据库设计

### 表结构

#### 1. restaurants (餐厅信息表)

```sql
CREATE TABLE restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,              -- 餐厅名称
    lat REAL NOT NULL,               -- 纬度 (WGS-84)
    lng REAL NOT NULL,               -- 经度 (WGS-84)
    address TEXT,                    -- 地址
    cuisine TEXT,                    -- 菜系
    price INTEGER,                   -- 人均价格(元)
    rating REAL,                     -- 评分 (1-5)
    wait_time INTEGER,               -- 预计等待时间(分钟)
    phone TEXT,                      -- 电话
    hours TEXT,                      -- 营业时间
    tags TEXT                        -- 标签(逗号分隔)
);
```

**索引优化:**
```sql
CREATE INDEX idx_cuisine ON restaurants(cuisine);
CREATE INDEX idx_rating ON restaurants(rating DESC);
CREATE INDEX idx_price ON restaurants(price);
```

#### 2. user_feedback (用户反馈表)

```sql
CREATE TABLE user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    restaurant_id INTEGER,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);
```

#### 3. users (用户表)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. user_preferences (用户偏好表)

```sql
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY,
    max_price INTEGER DEFAULT 50,
    max_distance INTEGER DEFAULT 2000,
    preferred_cuisines TEXT,
    accept_waiting BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 数据初始化

首次启动时自动插入示例数据:
- **位置**: 南京大学鼓楼校区周边
- **数量**: 198家餐厅
- **来源**: 真实数据采集 + 人工补充

**修改初始数据:**
```python
# 编辑 backend/data/database.py
# 修改 sample_restaurants 列表
# 删除 backend/data/restaurants.db
# 重启服务自动生成新数据库
```

---

## 🔌 API文档

### 基础信息

**Base URL:** `http://127.0.0.1:5000/api`  
**Content-Type:** `application/json`  
**认证方式:** 暂无(后续可扩展JWT)

### 1. 推荐接口

#### GET /api/recommend

获取个性化餐厅推荐

**请求参数:**
```json
{
  "lat": 32.0542,           // 必填: 纬度
  "lng": 118.7835,          // 必填: 经度
  "max_price": 50,          // 可选: 最高价格
  "max_distance": 2000      // 可选: 最大距离(米)
}
```

**响应示例:**
```json
{
  "code": 200,
  "status": "success",
  "message": "推荐成功，共找到 10 家餐厅",
  "data": [
    {
      "id": 1,
      "name": "南芳园风味美食苑",
      "lat": 32.051371,
      "lng": 118.780808,
      "cuisine": "江浙菜",
      "price": 35,
      "rating": 4.5,
      "distance": 425,
      "score": 0.8567,
      "reason": "评分最高"
    }
  ],
  "timestamp": 1714000000000
}
```

### 2. 餐厅接口

#### GET /api/restaurants

获取所有餐厅(支持分页)

**查询参数:**
- `page`: 页码(默认1)
- `page_size`: 每页数量(默认20)

**响应:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 198,
    "total_pages": 10
  }
}
```

#### GET /api/restaurants/nearby

获取附近餐厅

**查询参数:**
- `lat`: 纬度(必填)
- `lng`: 经度(必填)
- `max_distance`: 最大距离(默认3000米)
- `page`: 页码
- `page_size`: 每页数量

#### POST /api/restaurants/filter

高级筛选餐厅

**请求体:**
```json
{
  "lat": 32.0542,
  "lng": 118.7835,
  "price_min": 20,
  "price_max": 50,
  "rating_min": 4.0,
  "max_distance": 2000,
  "cuisines": ["川菜", "西餐"],
  "sort_by": "distance"
}
```

#### GET /api/search

关键词搜索餐厅

**查询参数:**
- `keyword`: 搜索关键词(必填)
- `limit`: 返回数量(默认20)

**支持搜索:**
- 餐厅名称
- 菜系类型
- 地址信息
- 特色标签

### 3. 路径规划接口

#### POST /api/route

规划从起点到终点的路径

**请求体:**
```json
{
  "origin": {
    "lat": 32.0542,
    "lng": 118.7835
  },
  "destination": {
    "lat": 32.0560,
    "lng": 118.7850
  },
  "mode": "walking"  // walking/biking/transit
}
```

**响应:**
```json
{
  "code": 200,
  "status": "success",
  "data": {
    "distance": 450,
    "duration": 320,
    "polyline": [
      [32.0542, 118.7835],
      [32.0545, 118.7838],
      ...
    ],
    "mode": "walking",
    "provider": "amap"  // amap/simple
  }
}
```

**降级机制:**
- `provider: "amap"` - 使用高德API(真实路径)
- `provider: "simple"` - 使用直线路径(API失败时)

---

## 🧮 核心算法

### 1. 推荐算法

**加权评分模型:**

```python
score = w1 × rating_norm + w2 × price_norm + w3 × distance_norm + w4 × wait_time_norm
```

**权重配置:**
```python
WEIGHTS = {
    'rating': 0.40,      # 评分权重 40%
    'price': 0.25,       # 价格权重 25%
    'distance': 0.20,    # 距离权重 20%
    'wait_time': 0.15    # 等待时间权重 15%
}
```

**归一化方法:**
```python
def normalize(value, min_val, max_val):
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)
```

**推荐理由生成:**
```python
if rating > 4.5:
    reason = "评分最高"
elif distance < 500:
    reason = "距离最近"
elif score / price > threshold:
    reason = "性价比最优"
elif wait_time < 10:
    reason = "无需等待"
```

### 2. 距离计算

**Haversine公式:**

```python
def haversine_distance(lat1, lng1, lat2, lng2):
    R = 6371000  # 地球半径(米)
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
    c = 2 ⋅ atan2(√a, √(1−a))
    
    return R ⋅ c
```

**精度:** ±0.5% (适用于<100km的距离)

### 3. 时间估算

```python
def calculate_eta(distance_meters, mode):
    speeds = {
        'walking': 1.4,   # 5 km/h
        'biking': 4.0,    # 14.4 km/h
        'transit': 3.0    # 含等车时间
    }
    speed = speeds.get(mode, 1.4)
    return int(distance_meters / speed)
```

---

## 🗺️ 坐标系统

### 坐标系说明

| 坐标系 | 说明 | 使用场景 |
|--------|------|---------|
| WGS-84 | GPS标准坐标 | 数据库存储、GPS设备 |
| GCJ-02 | 中国加密坐标 | 高德地图、腾讯地图 |

### 转换策略

**原则:** 
- 数据库统一存储WGS-84
- 前端显示前转换为GCJ-02
- 距离计算使用WGS-84

**转换函数:**
```javascript
function wgs84ToGcj02(lat, lng) {
    // 国家测绘局发布的标准算法
    // 详见 frontend/js/map.js
}
```

**偏移量:**
- 南京地区: 纬度-228米, 经度+578米
- 总偏移: 约300-500米

### 常见问题

**Q: 为什么位置偏移?**

A: 未进行坐标转换。确保所有传入Leaflet的坐标都是GCJ-02。

**Q: 如何验证坐标准确性?**

A: 
```bash
cd backend
python verify_restaurant_coords.py
```

**Q: 如何批量更新坐标?**

A: 
```bash
cd backend
python update_coords_from_amap.py
```

详见 [UPDATE_COORDS_GUIDE.md](UPDATE_COORDS_GUIDE.md)

---

## 💻 开发环境配置

### 后端开发

**虚拟环境:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

**调试模式:**
```python
# backend/app.py
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**日志级别:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 前端开发

**代码规范:**
- 使用ES6+语法
- 模块化组织(js/目录下)
- 注释清晰,关键逻辑必注

**调试技巧:**
```javascript
// 浏览器控制台
console.log('当前位置:', mapManager.currentLocation);
console.log('餐厅数量:', app.restaurants.length);
```

**热重载:**
使用VS Code Live Server,修改后自动刷新

### 数据库管理

**可视化工具:**
- DB Browser for SQLite (推荐)
- SQLite Studio
- VS Code SQLite Explorer扩展

**常用查询:**
```sql
-- 查看所有餐厅
SELECT * FROM restaurants ORDER BY rating DESC;

-- 统计各菜系数量
SELECT cuisine, COUNT(*) as count 
FROM restaurants 
GROUP BY cuisine;

-- 查找异常坐标
SELECT * FROM restaurants 
WHERE lat < 32.0 OR lat > 32.1;
```

---

## 🚀 部署指南

### 本地部署

**步骤:**
1. 安装Python 3.8+
2. 克隆项目
3. 安装依赖
4. 配置`.env`
5. 启动服务

**验证:**
```bash
# 测试后端
curl http://127.0.0.1:5000/api/restaurants?page=1&page_size=5

# 访问前端
open http://localhost:8080
```

### 生产环境部署

**后端 (Gunicorn + Nginx):**

```bash
# 安装Gunicorn
pip install gunicorn

# 启动
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

**Nginx配置:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        root /path/to/frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

**前端 (静态资源托管):**

选项1: Nginx直接托管
```bash
cp -r frontend/* /var/www/html/
```

选项2: CDN加速
- 上传到阿里云OSS/腾讯云COS
- 配置CDN域名
- 修改HTML中的资源引用

**数据库备份:**
```bash
# 定时备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp backend/data/restaurants.db backup/restaurants_$DATE.db
```

### Docker部署 (可选)

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
EXPOSE 5000

CMD ["python", "app.py"]
```

**docker-compose.yml:**
```yaml
version: '3'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    volumes:
      - ./backend/data:/app/data
    environment:
      - AMAP_API_KEY=${AMAP_API_KEY}
  
  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend:/usr/share/nginx/html
```

---

## ❓ 常见问题

### 开发相关

**Q1: 修改.env后不生效?**

A: `.env`文件变化不会触发热重载,必须手动重启Flask服务。

**Q2: 数据库被锁定?**

A: 
1. 停止Flask服务
2. 关闭所有SQLite浏览器
3. 检查任务管理器是否有残留进程
4. 重新打开

**Q3: 导入错误 `attempted relative import`?**

A: 使用绝对导入代替相对导入:
```python
# ❌ 错误
from ..utils.geo import haversine_distance

# ✅ 正确
from utils.geo import haversine_distance
```

### 运行相关

**Q4: 高德API返回SERVICE_NOT_AVAILABLE?**

A: 
1. 确认使用Web服务类型的Key
2. 检查骑行模式是否开通(可能需单独申请)
3. 查看配额是否耗尽

**Q5: 定位一直失败?**

A:
1. 检查浏览器权限(地址栏锁图标)
2. 使用HTTPS协议(HTTP可能被阻止)
3. 到室外开阔地带测试
4. 查看控制台错误信息

**Q6: 地图瓦片加载缓慢?**

A:
1. 检查网络连接(需要访问高德CDN)
2. 清除浏览器缓存
3. 考虑使用本地瓦片服务器

### 数据相关

**Q7: 如何添加新餐厅?**

A: 三种方式:
1. 直接编辑数据库(SQLite浏览器)
2. 修改`database.py`中的示例数据
3. 编写导入脚本从CSV/Excel导入

**Q8: 餐厅坐标不准确?**

A: 使用高德地理编码API批量更新:
```bash
cd backend
python update_coords_from_amap.py
```

**Q9: 推荐结果不合理?**

A: 调整推荐算法权重:
```python
# backend/core/recommender.py
WEIGHTS = {
    'rating': 0.40,    # 提高评分权重
    'price': 0.25,
    'distance': 0.20,
    'wait_time': 0.15
}
```

---

## 📊 性能优化

### 后端优化

1. **数据库索引**
```sql
CREATE INDEX idx_cuisine ON restaurants(cuisine);
CREATE INDEX idx_rating ON restaurants(rating DESC);
```

2. **查询优化**
```python
# ❌ 低效: 全表扫描
all_restaurants = db.get_all_restaurants()
filtered = [r for r in all_restaurants if r['cuisine'] == '川菜']

# ✅ 高效: 利用索引
filtered = db.get_restaurants_by_cuisine('川菜')
```

3. **缓存策略**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_recommendations(lat, lng, max_price):
    # 缓存推荐结果
    pass
```

### 前端优化

1. **防抖节流**
```javascript
// 搜索框防抖
let timeout;
searchInput.addEventListener('input', (e) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
        performSearch(e.target.value);
    }, 300);
});
```

2. **懒加载**
```javascript
// 滚动加载更多
window.addEventListener('scroll', () => {
    if (isNearBottom()) {
        loadMoreRestaurants();
    }
});
```

3. **Canvas渲染**
```javascript
// Leaflet使用Canvas提升性能
L.map('map', {
    preferCanvas: true
});
```

---

## 🔐 安全建议

### API安全

1. **速率限制**
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/recommend')
@limiter.limit("100 per hour")
def recommend():
    pass
```

2. **输入验证**
```python
from utils.validator import validate_recommend_params

valid, error = validate_recommend_params(data)
if not valid:
    return jsonify({'error': error}), 400
```

3. **CORS配置**
```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8080"]
    }
})
```

### 数据安全

1. **敏感信息保护**
```env
# .env (不要提交到Git)
AMAP_API_KEY=secret_key
DATABASE_URL=sqlite:///data/restaurants.db
```

2. **SQL注入防护**
```python
# ❌ 危险: SQL注入风险
cursor.execute(f"SELECT * FROM restaurants WHERE name='{name}'")

# ✅ 安全: 参数化查询
cursor.execute("SELECT * FROM restaurants WHERE name=?", (name,))
```

3. **XSS防护**
```javascript
// 转义用户输入
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

---

## 📝 开发规范

### 代码风格

**Python:**
- 遵循PEP 8规范
- 使用4空格缩进
- 函数名使用snake_case
- 类名使用CamelCase

**JavaScript:**
- 使用ES6+语法
- 常量使用UPPER_CASE
- 变量使用camelCase
- 类名使用PascalCase

### 提交规范

```bash
git commit -m "feat: 添加餐厅收藏功能"
git commit -m "fix: 修复定位精度问题"
git commit -m "docs: 更新API文档"
git commit -m "refactor: 重构推荐算法模块"
```

**类型:**
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链

### 分支策略

```
main (生产环境)
  ↑
develop (开发主分支)
  ↑
feature/xxx (功能分支)
bugfix/xxx (修复分支)
```

---

## 🧪 测试

### 单元测试

```bash
cd backend
python -m pytest tests/
```

**示例测试:**
```python
def test_haversine_distance():
    dist = haversine_distance(32.0542, 118.7835, 32.0560, 118.7850)
    assert 400 < dist < 500  # 约450米
```

### API测试

```bash
# 测试推荐接口
curl -X POST http://127.0.0.1:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"lat": 32.0542, "lng": 118.7835}'

# 测试路径规划
curl -X POST http://127.0.0.1:5000/api/route \
  -H "Content-Type: application/json" \
  -d '{
    "origin": {"lat": 32.0542, "lng": 118.7835},
    "destination": {"lat": 32.0560, "lng": 118.7850},
    "mode": "walking"
  }'
```

---

## 📚 参考资料

- [Flask官方文档](https://flask.palletsprojects.com/)
- [Leaflet文档](https://leafletjs.com/reference.html)
- [高德地图API](https://lbs.amap.com/api/webservice/guide/create-project/get-key)
- [SQLite教程](https://www.sqlite.org/docs.html)

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request!

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: add some feature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

**最后更新**: 2026年4月23日
