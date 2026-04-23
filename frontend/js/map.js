// ==================== map.js ====================
// 地图管理模块 - 负责Leaflet地图的初始化、标记、路径绘制等

// WGS-84转GCJ-02坐标转换函数（用于高德地图）
function wgs84ToGcj02(lat, lng) {
    const PI = 3.1415926535897932384626;
    const a = 6378245.0;
    const ee = 0.00669342162296594323;
    
    function transformLat(x, y) {
        let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
        ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0;
        ret += (160.0 * Math.sin(y / 12.0 * PI) + 320 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0;
        return ret;
    }
    
    function transformLng(x, y) {
        let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
        ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0;
        ret += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0;
        return ret;
    }
    
    let dLat = transformLat(lng - 105.0, lat - 35.0);
    let dLng = transformLng(lng - 105.0, lat - 35.0);
    const radLat = lat / 180.0 * PI;
    let magic = Math.sin(radLat);
    magic = 1 - ee * magic * magic;
    const sqrtMagic = Math.sqrt(magic);
    dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * PI);
    dLng = (dLng * 180.0) / (a / sqrtMagic * Math.cos(radLat) * PI);
    
    return {
        lat: lat + dLat,
        lng: lng + dLng
    };
}

class MapManager {
    constructor() {
        this.map = null;
        this.userMarker = null;
        this.accuracyCircle = null;  // 定位精度圆圈
        this.restaurantMarkers = [];
        this.currentPath = null;
        this.currentLocation = null;
        this.defaultZoom = 15;
        this.markerCluster = null; // 标记聚类（优化性能）
        this.lastLocationUpdate = 0; // 上次位置更新时间戳
        this.locationUpdateInterval = 30000; // 位置更新最小间隔（30秒）
    }

    /**
     * 初始化地图
     * @param {number} lat - 纬度 (WGS-84)
     * @param {number} lng - 经度 (WGS-84)
     * @param {number} zoom - 缩放级别
     */
    init(lat, lng, zoom = 15) {
        // 确保地图容器有明确的高度
        const mapContainer = document.getElementById('map');
        if (mapContainer) {
            mapContainer.style.height = '100vh';
            mapContainer.style.width = '100%';
        }
        
        // ⚠️ 关键修复：将WGS-84坐标转换为GCJ-02（高德地图需要）
        const gcj02 = wgs84ToGcj02(lat, lng);
        console.log(`🗺️ 地图初始化 - WGS84: (${lat.toFixed(6)}, ${lng.toFixed(6)}) -> GCJ02: (${gcj02.lat.toFixed(6)}, ${gcj02.lng.toFixed(6)})`);
        
        this.map = L.map('map', {
            zoomControl: false,  // 禁用默认缩放控件，自定义位置
            attributionControl: true,
            preferCanvas: true,  // 使用Canvas渲染器提升性能
            fadeAnimation: true,  // 启用淡入淡出动画
            zoomAnimation: true   // 启用缩放动画
        }).setView([gcj02.lat, gcj02.lng], zoom);  // ✅ 使用GCJ-02坐标
        
        // 添加缩放控件到右上角
        L.control.zoom({
            position: 'topright'
        }).addTo(this.map);
        
        // 使用高德地图瓦片（国内访问更快）
        L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
            subdomains: ['1', '2', '3', '4'],
            attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
            maxZoom: 19,
            minZoom: 3,
            tileSize: 256,
            updateWhenIdle: true,
            updateWhenZooming: false,
            keepBuffer: 2
        }).addTo(this.map);
        
        console.log('✅ 地图初始化完成 (使用高德地图 - GCJ02坐标系)');
        
        // 添加用户位置标记（内部会再次转换，但因为传入的是WGS-84，所以正确）
        this.addUserMarker(lat, lng);
        
        // ⚠️ 重要：currentLocation存储原始WGS-84坐标，用于后续计算
        this.currentLocation = { lat, lng };
        
        // 添加比例尺
        L.control.scale({ metric: true, imperial: false }).addTo(this.map);
        
        // 监听窗口大小变化，自动调整地图
        window.addEventListener('resize', () => {
            setTimeout(() => {
                if (this.map) {
                    this.map.invalidateSize();
                }
            }, 200);
        });
        
        console.log('🎯 地图初始化完成，坐标系: WGS-84 -> GCJ-02');
    }

    /**
     * 添加用户位置标记
     * @param {number} lat - 纬度 (WGS-84)
     * @param {number} lng - 经度 (WGS-84)
     * @param {number} accuracy - 定位精度（米），可选
     */
    addUserMarker(lat, lng, accuracy = null) {
        if (this.userMarker) {
            this.map.removeLayer(this.userMarker);
        }
        
        // 转换为GCJ-02坐标（高德地图需要）
        const gcj02 = wgs84ToGcj02(lat, lng);
        
        // 如果有精度信息，添加精度圆圈
        if (accuracy && accuracy < 500) {  // 只显示精度<500米的圆圈
            if (this.accuracyCircle) {
                this.map.removeLayer(this.accuracyCircle);
            }
            
            this.accuracyCircle = L.circle([gcj02.lat, gcj02.lng], {
                radius: accuracy,
                color: '#2ecc71',
                fillColor: '#2ecc71',
                fillOpacity: 0.1,
                weight: 2,
                dashArray: '5, 10'
            }).addTo(this.map);
            
            console.log(`📏 已显示定位精度范围: ${accuracy.toFixed(0)}米`);
        }
        
        // 自定义用户图标
        const userIcon = L.divIcon({
            className: 'user-marker',
            html: `<div style="background: #2ecc71; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.2);"></div>`,
            iconSize: [24, 24],
            popupAnchor: [0, -12]
        });
        
        this.userMarker = L.marker([gcj02.lat, gcj02.lng], { icon: userIcon })
            .addTo(this.map)
            .bindPopup(`<strong>您的位置</strong><br>精度: ${accuracy ? accuracy.toFixed(0) + '米' : '未知'}`)
            .openPopup();
    }

    /**
     * 更新用户位置
     * @param {number} lat - 纬度
     * @param {number} lng - 经度
     * @param {number} accuracy - 定位精度（米），可选
     */
    updateUserLocation(lat, lng, accuracy = null) {
        const now = Date.now();
        
        // 首次定位或currentLocation为空时，强制更新（不受防抖限制）
        if (!this.currentLocation) {
            console.log('🎯 首次定位，强制更新位置');
            this.currentLocation = { lat, lng };
            this.addUserMarker(lat, lng, accuracy);  // 传递精度参数
            
            // 显示定位精度圆圈
            if (accuracy && accuracy < 100) {
                this.showAccuracyCircle(lat, lng, accuracy);
            }
            
            // ⚠️ 关键修复：将WGS-84转换为GCJ-02后再设置地图视图
            const gcj02 = wgs84ToGcj02(lat, lng);
            this.map.setView([gcj02.lat, gcj02.lng], this.defaultZoom);
            this.lastLocationUpdate = now;
            console.log(`✅ 位置已更新（首次）: WGS84(${lat.toFixed(6)}, ${lng.toFixed(6)}) -> GCJ02(${gcj02.lat.toFixed(6)}, ${gcj02.lng.toFixed(6)})`);
            return;
        }
        
        // 检查是否需要更新（避免频繁更新）
        if ((now - this.lastLocationUpdate) < this.locationUpdateInterval) {
            // 计算距离变化
            const distance = this.calculateDistance(lat, lng, this.currentLocation.lat, this.currentLocation.lng);
            
            // 如果移动距离小于30米，不更新位置（降低阈值以减少抖动）
            if (distance < 30) {
                console.log(`⏭️ 位置变化较小 (${distance.toFixed(0)}米)，跳过更新`);
                return;
            }
            
            // 如果移动距离较大，立即更新
            console.log(`🔄 位置变化较大 (${distance.toFixed(0)}米)，更新位置`);
        }
        
        this.currentLocation = { lat, lng };
        this.addUserMarker(lat, lng, accuracy);  // 传递精度参数
        
        // 更新定位精度圆圈
        if (accuracy && accuracy < 100) {
            this.showAccuracyCircle(lat, lng, accuracy);
        }
        
        // ⚠️ 关键修复：将WGS-84转换为GCJ-02后再设置地图视图
        const gcj02 = wgs84ToGcj02(lat, lng);
        this.map.setView([gcj02.lat, gcj02.lng], this.defaultZoom);
        this.lastLocationUpdate = now;
        console.log(`✅ 位置已更新: WGS84(${lat.toFixed(6)}, ${lng.toFixed(6)}) -> GCJ02(${gcj02.lat.toFixed(6)}, ${gcj02.lng.toFixed(6)})`);
    }

    /**
     * 显示定位精度圆圈
     * @param {number} lat - 纬度
     * @param {number} lng - 经度
     * @param {number} accuracy - 精度半径（米）
     */
    showAccuracyCircle(lat, lng, accuracy) {
        // 移除旧的精度圆圈
        if (this.accuracyCircle) {
            this.map.removeLayer(this.accuracyCircle);
        }
        
        // 转换为GCJ-02坐标
        const gcj02 = wgs84ToGcj02(lat, lng);
        
        // 添加新的精度圆圈
        this.accuracyCircle = L.circle([gcj02.lat, gcj02.lng], {
            radius: accuracy,
            color: '#2ecc71',
            fillColor: '#2ecc71',
            fillOpacity: 0.15,
            weight: 2,
            opacity: 0.6
        }).addTo(this.map);
        
        console.log(`🎯 显示定位精度范围: ${accuracy.toFixed(0)}米`);
    }

    /**
     * 添加餐厅标记
     * @param {Array} restaurants - 餐厅列表 (WGS-84坐标)
     * @param {Function} onMarkerClick - 点击回调
     */
    addRestaurantMarkers(restaurants, onMarkerClick) {
        this.clearRestaurantMarkers();
        
        // 限制显示的餐厅数量，避免过多标记导致卡顿
        const maxMarkers = 50;
        const displayRestaurants = restaurants.slice(0, maxMarkers);
        
        if (restaurants.length > maxMarkers) {
            console.warn(`餐厅数量过多(${restaurants.length})，仅显示前${maxMarkers}个`);
        }
        
        displayRestaurants.forEach(restaurant => {
            // 转换为GCJ-02坐标（高德地图需要）
            const gcj02 = wgs84ToGcj02(restaurant.lat, restaurant.lng);
            
            const ratingColor = this.getRatingColor(restaurant.rating);
            const restaurantIcon = L.divIcon({
                className: 'restaurant-marker',
                html: `<div style="background: ${ratingColor}; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 13px; font-weight: bold; box-shadow: 0 2px 8px rgba(0,0,0,0.2); cursor: pointer; transition: transform 0.2s;">${restaurant.rating.toFixed(1)}</div>`,
                iconSize: [34, 34],
                popupAnchor: [0, -17]
            });
            
            const marker = L.marker([gcj02.lat, gcj02.lng], { 
                icon: restaurantIcon,
                riseOnHover: true
            })
                .addTo(this.map)
                .bindPopup(`
                    <strong>${this.escapeHtml(restaurant.name)}</strong><br>
                    ⭐ ${restaurant.rating.toFixed(1)} | ¥${restaurant.price}<br>
                    📍 距离 ${restaurant.distance}米
                `, {
                    maxWidth: 250,
                    className: 'custom-popup'
                });
            
            marker.on('click', () => {
                if (onMarkerClick) onMarkerClick(restaurant);
            });
            
            this.restaurantMarkers.push(marker);
        });
    }

    /**
     * 根据评分获取颜色
     * @param {number} rating - 评分
     * @returns {string} 颜色代码
     */
    getRatingColor(rating) {
        if (rating >= 4.5) return '#f39c12';  // 金色
        if (rating >= 4.0) return '#f1c40f';  // 黄色
        if (rating >= 3.5) return '#95a5a6';  // 灰色
        return '#e74c3c';                      // 红色
    }

    /**
     * 调整地图视野以包含所有标记点
     * @param {Array} restaurants - 餐厅列表（需要有lat和lng字段）
     */
    fitBoundsToMarkers(restaurants) {
        if (!this.map || !restaurants || restaurants.length === 0) return;
        
        // 转换为GCJ-02坐标
        const gcj02Points = restaurants.map(r => wgs84ToGcj02(r.lat, r.lng));
        
        // 计算边界
        const bounds = L.latLngBounds(
            gcj02Points.map(p => [p.lat, p.lng])
        );
        
        // 调整地图视野，添加padding
        this.map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: 16,
            animate: true,
            duration: 0.5
        });
        
        console.log('🗺️  地图视野已调整至搜索结果范围');
    }

    /**
     * 清除所有餐厅标记
     */
    clearRestaurantMarkers() {
        if (this.restaurantMarkers) {
            this.restaurantMarkers.forEach(marker => {
                this.map.removeLayer(marker);
            });
            this.restaurantMarkers = [];
        }
        console.log('🗑️  已清除所有餐厅标记');
    }

    /**
     * 绘制路径
     * @param {Array} coordinates - 路径坐标数组 [[lat, lng], ...]
     * @param {string} mode - 出行方式 (walking, biking, transit)
     */
    drawPath(coordinates, mode = 'walking') {
        this.clearPath();
        
        if (!coordinates || coordinates.length === 0) {
            console.warn('路径坐标为空');
            return;
        }
        
        const colors = {
            walking: '#2ecc71',
            biking: '#3498db',
            transit: '#9b59b6',
            subway: '#e67e22'
        };
        
        const dashArrays = {
            walking: null,
            biking: null,
            transit: '10, 10',
            subway: '14, 8'
        };
        
        // 优化路径渲染
        this.currentPath = L.polyline(coordinates, {
            color: colors[mode] || '#2ecc71',
            weight: 5,
            opacity: 0.8,
            dashArray: dashArrays[mode],
            lineCap: 'round',
            lineJoin: 'round',
            smoothFactor: 1.5  // 平滑因子，提升性能
        }).addTo(this.map);
        
        // 添加起点和终点标记
        if (coordinates.length >= 2) {
            const startPoint = coordinates[0];
            const endPoint = coordinates[coordinates.length - 1];
            
            // 起点标记
            L.circleMarker(startPoint, {
                radius: 6,
                fillColor: '#2ecc71',
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            }).addTo(this.map).bindPopup('起点');
            
            // 终点标记
            L.circleMarker(endPoint, {
                radius: 6,
                fillColor: '#e74c3c',
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            }).addTo(this.map).bindPopup('终点');
        }
        
        // 调整地图视野，确保路径完全可见
        try {
            const bounds = L.latLngBounds(coordinates);
            if (bounds.isValid()) {
                this.map.fitBounds(bounds, { 
                    padding: [80, 80],
                    maxZoom: 17,  // 限制最大缩放，避免过近
                    animate: true,
                    duration: 0.5
                });
            }
        } catch (e) {
            console.error('调整地图视野失败:', e);
        }
    }

    /**
     * 清除路径
     */
    clearPath() {
        if (this.currentPath) {
            this.map.removeLayer(this.currentPath);
            this.currentPath = null;
        }
    }

    /**
     * 获取用户当前位置（优化版）
     * @param {Function} callback - 回调函数 (lat, lng) => void
     */
    locateUser(callback) {
        if (!navigator.geolocation) {
            console.warn('⚠️ 您的浏览器不支持地理定位，使用默认位置');
            if (callback) callback(32.0542, 118.7835);
            return;
        }
        
        console.log('📍 ========== 开始高精度定位 ==========');
        
        // 尝试多次定位以提高精度
        this._locateWithRetry(callback, 0, 3);
    }

    /**
     * 带重试的定位方法
     * @param {Function} callback - 回调函数
     * @param {number} attempt - 当前尝试次数
     * @param {number} maxAttempts - 最大尝试次数
     */
    _locateWithRetry(callback, attempt, maxAttempts) {
        const attemptNum = attempt + 1;
        console.log(`📍 第 ${attemptNum}/${maxAttempts} 次定位尝试...`);
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude, accuracy } = position.coords;
                
                console.log(`✅ 第${attemptNum}次定位成功:`);
                console.log(`   纬度: ${latitude.toFixed(6)}`);
                console.log(`   经度: ${longitude.toFixed(6)}`);
                console.log(`   精度: ${accuracy.toFixed(0)}米`);
                
                // 如果精度良好(<50米)或已达到最大尝试次数，接受结果
                if (accuracy <= 50 || attemptNum >= maxAttempts) {
                    console.log('✅ 定位精度可接受，更新地图位置');
                    this.updateUserLocation(latitude, longitude, accuracy);
                    if (callback) callback(latitude, longitude);
                    console.log('📍 ========== 定位完成 ==========');
                } else {
                    // 精度不佳，继续重试
                    console.warn(`⚠️ 精度较差(${accuracy.toFixed(0)}米)，继续重试...`);
                    setTimeout(() => {
                        this._locateWithRetry(callback, attempt + 1, maxAttempts);
                    }, 2000); // 等待2秒后重试
                }
            },
            (error) => {
                console.error(`❌ 第${attemptNum}次定位失败:`, error.message);
                
                // 如果是最后一次尝试，使用默认位置
                if (attemptNum >= maxAttempts) {
                    console.warn('⚠️ 所有定位尝试均失败，使用默认位置');
                    if (callback) callback(32.0542, 118.7835);
                } else {
                    // 继续重试
                    setTimeout(() => {
                        this._locateWithRetry(callback, attempt + 1, maxAttempts);
                    }, 2000);
                }
            },
            { 
                enableHighAccuracy: true,   // 启用GPS高精度
                timeout: 15000,             // 15秒超时
                maximumAge: 0               // 不使用缓存
            }
        );
    }

    /**
     * 手动触发重新定位
     * @param {Function} callback - 回调函数
     */
    refreshLocation(callback) {
        console.log('🔄 手动刷新位置...');
        // 重置上次更新时间，允许立即更新
        this.lastLocationUpdate = 0;
        this.locateUser(callback);
    }

    /**
     * 计算两点间距离（简化版）
     * @param {number} lat1 - 纬度1
     * @param {number} lng1 - 经度1
     * @param {number} lat2 - 纬度2
     * @param {number} lng2 - 经度2
     * @returns {number} 距离（米）
     */
    calculateDistance(lat1, lng1, lat2, lng2) {
        const R = 6371000; // 地球半径（米）
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLng = (lng2 - lng1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    /**
     * 缩放地图到所有标记
     */
    fitToMarkers() {
        const bounds = L.latLngBounds([]);
        
        if (this.userMarker) {
            bounds.extend(this.userMarker.getLatLng());
        }
        
        this.restaurantMarkers.forEach(marker => {
            bounds.extend(marker.getLatLng());
        });
        
        if (bounds.isValid()) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }

    /**
     * 设置地图视图中心
     * @param {number} lat - 纬度 (WGS-84)
     * @param {number} lng - 经度 (WGS-84)
     * @param {number} zoom - 缩放级别
     */
    setView(lat, lng, zoom = null) {
        // ⚠️ 关键修复：将WGS-84坐标转换为GCJ-02
        const gcj02 = wgs84ToGcj02(lat, lng);
        
        if (zoom) {
            this.map.setView([gcj02.lat, gcj02.lng], zoom);
        } else {
            this.map.panTo([gcj02.lat, gcj02.lng]);
        }
    }

    /**
     * 平移地图（指定方向和距离）
     * @param {string} direction - 方向: 'up', 'down', 'left', 'right'
     * @param {number} distance - 移动距离（米），默认200米
     */
    panMap(direction, distance = 200) {
        if (!this.currentLocation) {
            console.warn('⚠️ 当前位置未设置，无法平移');
            return;
        }
        
        const { lat, lng } = this.currentLocation;
        let newLat = lat;
        let newLng = lng;
        
        // 近似计算：1度纬度约111km，1度经度约111km*cos(lat)
        const latOffset = distance / 111000;  // 纬度偏移量
        const lngOffset = distance / (111000 * Math.cos(lat * Math.PI / 180));  // 经度偏移量
        
        switch(direction) {
            case 'up':
                newLat += latOffset;
                break;
            case 'down':
                newLat -= latOffset;
                break;
            case 'left':
                newLng -= lngOffset;
                break;
            case 'right':
                newLng += lngOffset;
                break;
        }
        
        // ⚠️ 关键修复：将新位置转换为GCJ-02后再设置地图视图
        const gcj02 = wgs84ToGcj02(newLat, newLng);
        this.map.panTo([gcj02.lat, gcj02.lng]);
        console.log(`🗺️ 地图向${direction}平移${distance}米 (WGS84: ${newLat.toFixed(6)}, ${newLng.toFixed(6)} -> GCJ02: ${gcj02.lat.toFixed(6)}, ${gcj02.lng.toFixed(6)})`);
    }

    /**
     * 添加地图控制按钮到界面
     */
    addMapControls() {
        // 创建控制面板容器
        const controlsDiv = L.DomUtil.create('div', 'map-controls-container');
        controlsDiv.innerHTML = `
            <div class="map-control-btn" id="panUpBtn" title="向上移动">
                <i class="fas fa-arrow-up"></i>
            </div>
            <div class="map-control-row">
                <div class="map-control-btn" id="panLeftBtn" title="向左移动">
                    <i class="fas fa-arrow-left"></i>
                </div>
                <div class="map-control-btn" id="refreshLocationBtn" title="重新定位">
                    <i class="fas fa-crosshairs"></i>
                </div>
                <div class="map-control-btn" id="panRightBtn" title="向右移动">
                    <i class="fas fa-arrow-right"></i>
                </div>
            </div>
            <div class="map-control-btn" id="panDownBtn" title="向下移动">
                <i class="fas fa-arrow-down"></i>
            </div>
        `;
        
        // 添加到地图右上角
        const control = L.control({ position: 'topright' });
        control.onAdd = () => controlsDiv;
        control.addTo(this.map);
        
        // 绑定事件
        setTimeout(() => {
            document.getElementById('panUpBtn')?.addEventListener('click', () => {
                this.panMap('up');
            });
            
            document.getElementById('panDownBtn')?.addEventListener('click', () => {
                this.panMap('down');
            });
            
            document.getElementById('panLeftBtn')?.addEventListener('click', () => {
                this.panMap('left');
            });
            
            document.getElementById('panRightBtn')?.addEventListener('click', () => {
                this.panMap('right');
            });
            
            document.getElementById('refreshLocationBtn')?.addEventListener('click', () => {
                if (window.app) {
                    window.app.refreshLocation();
                }
            });
        }, 100);
        
        console.log('🎮 地图控制按钮已添加');
    }

    /**
     * 转义HTML特殊字符
     * @param {string} text - 原始文本
     * @returns {string} 转义后的文本
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 创建全局单例
const mapManager = new MapManager();

