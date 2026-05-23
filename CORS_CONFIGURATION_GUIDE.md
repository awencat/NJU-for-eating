# 🔌 CORS跨域配置说明

> 解决前端无法连接后端API的问题

---

## 🎯 问题现象

**症状**:
- ✅ Live Server (端口5500) 可以正常访问后端
- ❌ Python HTTP Server (端口8080) 连接失败
- 浏览器控制台显示错误:
  ```
  Access to XMLHttpRequest at 'http://127.0.0.1:5000/api/xxx' 
  from origin 'http://localhost:8080' has been blocked by CORS policy
  ```

**原因**: 浏览器的**同源策略(Same-Origin Policy)**阻止了跨域请求

---

## 📋 什么是CORS?

**CORS (Cross-Origin Resource Sharing)** - 跨域资源共享

**同源定义**: 协议 + 域名 + 端口 三者完全相同

| 前端地址 | 后端地址 | 是否同源 | 是否需要CORS |
|---------|---------|---------|-------------|
| http://127.0.0.1:**5500** | http://127.0.0.1:**5000** | ❌ 端口不同 | ✅ 需要 |
| http://localhost:**8080** | http://127.0.0.1:**5000** | ❌ 域名+端口不同 | ✅ 需要 |
| http://127.0.0.1:**5000** | http://127.0.0.1:**5000** | ✅ 完全相同 | ❌ 不需要 |

---

## ✅ 解决方案

### 方案1: 修改后端CORS配置(推荐)

**编辑文件**: `backend/config.py`

```python
# CORS跨域配置 - 支持多种前端开发服务器端口
CORS_ORIGINS = os.getenv(
    'CORS_ORIGINS', 
    'http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8080,http://localhost:8080'
).split(',')
```

**支持的端口**:
- ✅ **5500** - VS Code Live Server 默认端口
- ✅ **8080** - Python HTTP Server 常用端口
- ✅ 可添加其他端口,用逗号分隔

**使用环境变量**(更灵活):

编辑 `backend/.env`:
```env
# 自定义CORS白名单
CORS_ORIGINS=http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8080,http://localhost:8080,http://192.168.1.100:5500
```

**重启服务生效**:
```bash
# 停止当前服务 (Ctrl+C)
cd backend
python app.py  # 重新启动
```

---

### 方案2: 临时禁用CORS(仅开发调试)

⚠️ **警告**: 仅用于快速测试,不要在生产环境使用!

**编辑**: `backend/app.py`

```python
# 临时禁用CORS检查
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

这会允许**所有来源**访问,包括恶意网站,**不安全**!

---

### 方案3: 使用代理(高级)

**配置前端开发服务器代理**:

如果使用Webpack/Vite等构建工具,可以配置代理:

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      }
    }
  }
})
```

这样前端请求 `/api/xxx` 会被自动转发到后端,避免跨域问题。

---

## 🔍 验证配置是否生效

### 方法1: 查看浏览器控制台

打开浏览器开发者工具(F12),切换到 **Network** 标签:

**成功标志**:
- ✅ 请求状态码: `200 OK`
- ✅ 响应头包含: `Access-Control-Allow-Origin: http://localhost:8080`

**失败标志**:
- ❌ 红色错误: `CORS policy`
- ❌ 状态码: `(failed)` 或 `0`

### 方法2: 测试健康检查接口

在浏览器访问:
```
http://127.0.0.1:5000/api/health
```

应该返回:
```json
{
  "code": 200,
  "status": "success",
  "message": "服务运行正常"
}
```

### 方法3: 使用curl测试

```bash
# Windows PowerShell
$headers = @{
  "Origin" = "http://localhost:8080"
}
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health" -Headers $headers

# Linux/Mac
curl -H "Origin: http://localhost:8080" http://127.0.0.1:5000/api/health -v
```

查看响应头中是否包含 `Access-Control-Allow-Origin`

---

## 📊 常见端口对照表

| 工具/框架 | 默认端口 | 说明 |
|----------|---------|------|
| **VS Code Live Server** | 5500 | 本项目推荐使用 |
| **Python HTTP Server** | 8000 | `python -m http.server` |
| **Python HTTP Server** | 8080 | 常用替代端口 |
| **Node.js http-server** | 8080 | npm包 |
| **Vue CLI** | 8080 | `npm run serve` |
| **React Dev Server** | 3000 | `npm start` |
| **Angular CLI** | 4200 | `ng serve` |
| **Flask Backend** | 5000 | 本项目后端 |
| **Django Backend** | 8000 | Python框架 |

---

## 🛠️ 故障排查

### Q1: 修改config.py后仍然报错?

**原因**: Flask缓存了配置,未重新加载

**解决**:
```bash
# 完全停止服务
# 按 Ctrl+C

# 确认进程已退出
tasklist | findstr python  # Windows
ps aux | grep python       # Linux/Mac

# 重新启动
cd backend
python app.py
```

### Q2: 添加了端口但还是被阻止?

**检查清单**:
- [ ] `.env` 文件中的 `CORS_ORIGINS` 是否正确
- [ ] 端口号是否拼写错误
- [ ] 是否有多余空格
- [ ] 是否重启了Flask服务

**调试方法**:
在 `backend/app.py` 中添加日志:
```python
@app.before_request
def log_cors():
    print(f"请求来源: {request.headers.get('Origin')}")
    print(f"CORS配置: {app.config['CORS_ORIGINS']}")
```

### Q3: 局域网访问也需要配置CORS吗?

**是的!** 

如果朋友通过 `http://192.168.1.100:5500` 访问你的前端,需要添加:

```env
CORS_ORIGINS=http://127.0.0.1:5500,http://localhost:5500,http://192.168.1.100:5500
```

### Q4: 生产环境如何配置?

**推荐做法**:
1. 使用环境变量管理CORS配置
2. 只允许特定域名访问
3. 不要使用通配符 `*`

```env
# .env.production
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

---

## 💡 最佳实践

### 开发环境

**灵活配置**:
```env
# backend/.env (不提交到Git)
CORS_ORIGINS=http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8080,http://localhost:8080
```

### 测试环境

**限制更多**:
```env
# .env.test
CORS_ORIGINS=https://test.your-domain.com
```

### 生产环境

**最严格**:
```env
# .env.production
CORS_ORIGINS=https://your-domain.com
```

---

## 📝 相关代码位置

**配置文件**:
- `backend/config.py` - CORS配置定义
- `backend/.env` - 环境变量(需手动创建)

**应用入口**:
- `backend/app.py` - Flask应用初始化,CORS注册

**前端调用**:
- `frontend/js/api.js` - API请求封装

---

## 🎓 技术原理

### 浏览器如何处理CORS?

1. **简单请求**: 直接发送,检查响应头
2. **预检请求**: 先发送 `OPTIONS` 请求,确认允许后再发送实际请求

**预检请求示例**:
```http
OPTIONS /api/recommend HTTP/1.1
Origin: http://localhost:8080
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type

HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:8080
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type
```

### Flask-CORS工作原理

```python
from flask_cors import CORS

# 自动为所有路由添加CORS响应头
CORS(app, origins=['http://localhost:8080'])

# 等价于手动添加:
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8080'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response
```

---

## 🔗 参考资料

- [MDN CORS文档](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)
- [Flask-CORS官方文档](https://flask-cors.readthedocs.io/)
- [同源策略详解](https://developer.mozilla.org/zh-CN/docs/Web/Security/Same-origin_policy)

---

**最后更新**: 2026年4月23日  
**相关文档**: [README.md](../README.md) | [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)
