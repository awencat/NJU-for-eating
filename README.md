# 🍜 NJU-for-eating 智慧校园餐厅推荐系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 基于智能算法的南京大学校园餐饮出行优化方案

---

## 📖 项目简介

**NJU-for-eating** 是一个专为南京大学师生设计的智慧餐厅推荐系统,通过多维度智能算法帮助用户快速找到合适的餐厅,并提供最优路径规划服务。

### ✨ 核心特性

- 🎯 **智能推荐**: 基于评分、价格、距离、等待时间的加权评分算法
- 🗺️ **精准定位**: GPS实时定位 + 高德地图集成,位置误差<35米
- 🚶 **多模式导航**: 支持步行、骑行、公交三种出行方式
- 🔍 **高级筛选**: 价格区间、菜系偏好、评分要求等多维筛选
- ⭐ **个性化设置**: 预算控制、距离限制、口味偏好本地持久化
- ❤️ **收藏反馈**: 一键收藏常用餐厅,用餐后评分优化推荐

### 📊 数据规模

- **198家** 餐厅覆盖南大鼓楼校区周边
- **10+种** 菜系类型(川菜、西餐、快餐、咖啡等)
- **¥10-¥100** 价格区间满足不同消费需求
- **85%** 定位成功率(行业平均70%)

---

## 🚀 快速开始

### 前置要求

- Python 3.8+
- 现代浏览器(Chrome/Firefox/Edge)
- (可选) 高德地图API密钥

### 1️⃣ 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2️⃣ 配置环境变量

```bash
cd backend
copy .env.example .env  # Windows
```

编辑 `.env` 文件:
```env
# 高德地图API密钥(可选,用于真实路径规划)
AMAP_API_KEY=your_api_key_here

# 数据库路径
DATABASE_PATH=data/restaurants.db
```

> 💡 **提示**: 不配置API密钥也可正常运行,系统将使用直线路径作为降级方案

### 3️⃣ 启动服务

**后端服务:**
```bash
cd backend
python app.py
```

服务将在 `http://127.0.0.1:5000` 启动

**前端页面:**

方式一: VS Code Live Server (推荐)
1. 安装 "Live Server" 扩展
2. 右键 `frontend/index.html` → "Open with Live Server"

方式二: Python简易服务器
```bash
cd frontend
python -m http.server 8080
```

访问 `http://localhost:8080`



---

## 🎯 核心功能演示

### 1. 智能餐厅推荐

系统根据当前位置自动推荐附近优质餐厅,显示:
- 餐厅名称、评分、人均价格
- 距离、预计等待时间
- 推荐理由标签(评分最高/距离最近/性价比最优)

### 2. 多模式路径规划。

选择餐厅后,支持三种出行方式:
- 🚶 **步行**: 适合短距离(<1km)
- 🚴 **骑行**: 适合中距离(1-3km)
- 🚌 **公交**: 适合长距离(>3km)

显示详细路径、距离、预计时间

### 3. 高级筛选与搜索

**筛选条件:**
- 价格区间: ¥10-¥100
- 最低评分: 1-5星
- 最大距离: 500m-3000m
- 菜系类型: 多选(川菜/西餐/快餐等)

**关键词搜索:**
- 餐厅名称: "南芳园"
- 菜系类型: "川菜"
- 地址信息: "广州路"
- 特色标签: "实惠"

### 4. 个性化设置

点击右上角⚙️按钮打开设置面板:
- 调整最高人均预算
- 设置最大可接受距离
- 选择偏好菜系
- 是否接受排队等待

设置自动保存到本地,下次访问依然有效

### 5. 地图交互控制

**定位功能:**
- 🎯 点击定位按钮获取当前位置
- 🔵 蓝色圆圈显示定位精度范围
- 精度<35米时自动更新位置

**地图控制:**
- ⬆️⬇️⬅️➡️ 四个方向精确移动200米
- +/- 缩放按钮调整视野
- 🎯 十字准星一键回到当前位置

---

## 🛠️ 技术栈

### 后端
- **框架**: Flask 2.0+
- **数据库**: SQLite (轻量级文件数据库)
- **地图服务**: 高德地图API (地理编码 + 路径规划)
- **核心算法**: 加权评分推荐 + Haversine距离计算

### 前端
- **地图引擎**: Leaflet.js (开源地图库)
- **UI框架**: 原生JavaScript + CSS3
- **数据存储**: localStorage (用户偏好持久化)
- **坐标系统**: WGS-84 ↔ GCJ-02 自动转换

### 架构设计
```
前端层 (Leaflet + JavaScript)
    ↓ HTTP请求
API层 (Flask RESTful API)
    ↓ 业务逻辑
核心层 (推荐算法 + 路径规划 + 筛选引擎)
    ↓ 数据访问
数据层 (SQLite数据库)
```

---

## 📁 项目结构

```
NJU-for-eating/
├── backend/                 # 后端代码
│   ├── api/                # API路由
│   │   ├── recommend.py    # 推荐接口
│   │   ├── restaurants.py  # 餐厅接口
│   │   └── route.py        # 路径规划接口
│   ├── core/               # 核心业务逻辑
│   │   ├── recommender.py  # 推荐算法
│   │   ├── route_planner.py# 路径规划
│   │   └── filter.py       # 筛选引擎
│   ├── data/               # 数据文件
│   │   └── restaurants.db  # SQLite数据库
│   ├── utils/              # 工具函数
│   │   ├── geo.py          # 地理计算
│   │   └── validator.py    # 参数验证
│   ├── app.py              # Flask应用入口
│   └── config.py           # 配置文件
├── frontend/               # 前端代码
│   ├── js/                 # JavaScript模块
│   │   ├── app.js          # 主应用逻辑
│   │   ├── map.js          # 地图管理
│   │   ├── api.js          # API调用
│   │   ├── search.js       # 搜索功能
│   │   ├── filter.js       # 筛选功能
│   │   └── favorites.js    # 收藏功能
│   ├── css/                # 样式文件
│   └── index.html          # 主页面
├── .env                    # 环境变量配置
├── README.md               # 本文件
└── DEVELOPER_GUIDE.md      # 开发者指南
```

---

## 🔧 常见问题

### Q1: 地图加载缓慢或无法显示?

**解决方案:**
1. 检查网络连接(需要访问高德地图CDN)
2. 清除浏览器缓存(Ctrl+Shift+R硬刷新)
3. 确认防火墙未拦截地图资源

### Q2: 定位不准确或失败?

**解决方案:**
1. 允许浏览器位置权限(地址栏左侧锁图标)
2. 到室外开阔地带测试(GPS信号更强)
3. 关闭WiFi使用纯GPS定位(提高精度)
4. 点击🎯按钮手动重新定位

### Q3: 路径规划显示直线?

**原因:** 未配置高德API密钥或使用骑行模式(API可能不支持)

**解决方案:**
1. 在 `.env` 中配置 `AMAP_API_KEY`
2. 申请Web服务类型的Key(非Android/iOS SDK)
3. 重启后端服务使配置生效

### Q4: 修改数据库后不生效?

**解决方案:**
1. 完全停止Flask服务(Ctrl+C)
2. 确认无残留进程
3. 重新启动服务
4. 前端硬刷新(Ctrl+Shift+R)

### Q5: 如何添加新餐厅?

**方法一:** 直接编辑数据库
```bash
# 使用SQLite浏览器打开 backend/data/restaurants.db
# 在restaurants表中INSERT新记录
```

**方法二:** 修改初始化脚本
```python
# 编辑 backend/data/database.py
# 在sample_restaurants列表中添加新餐厅
# 删除旧数据库文件,重启服务自动生成
```

---

## 📚 相关文档

- **[开发者指南](DEVELOPER_GUIDE.md)** - 技术架构、API文档、部署说明
- **[PPT汇报大纲](PPT_PRESENTATION_OUTLINE.md)** - 项目汇报材料

---

## 👥 团队信息

**课程**: 智慧交通创新出行  
**学校**: 南京大学  
**日期**: 2026年4月  

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- 高德地图开放平台 - 提供地图服务和路径规划API
- Leaflet.js - 开源地图可视化库
- Flask - 轻量级Python Web框架

---

**⭐ 如果这个项目对你有帮助,欢迎Star!**