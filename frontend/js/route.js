// ==================== route.js ====================
// 路径规划模块 - 负责出行方式切换和路径规划逻辑

class RouteManager {
    constructor() {
        this.currentMode = 'walking';
        this.destinationRestaurant = null;
        this.isPlanning = false;
        this.modeNames = {
            walking: { name: '步行', icon: 'fa-walking', speed: '约5km/h' },
            biking: { name: '骑行', icon: 'fa-bicycle', speed: '约14km/h' },
            transit: { name: '公交', icon: 'fa-bus', speed: '含换乘时间' }
        };
        this.unavailableModes = new Set(); // 记录不可用的模式
    }

    /**
     * 初始化路径规划管理器
     */
    init() {
        this.bindEvents();
        this.checkModeAvailability();
        console.log('路径规划管理器初始化完成');
    }

    /**
     * 检查各出行模式的可用性
     */
    async checkModeAvailability() {
        // 测试骑行模式是否可用
        try {
            const testData = {
                origin: mapManager.currentLocation || { lat: 32.0542, lng: 118.7835 },
                destination: { lat: 32.0560, lng: 118.7850 },
                mode: 'biking'
            };
            
            const response = await fetch(`${API_BASE_URL}/api/route`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(testData)
            });
            
            const result = await response.json();
            
            // 如果返回fallback=true，说明骑行服务不可用
            if (result.data && result.data.fallback) {
                this.unavailableModes.add('biking');
                console.log('⚠️ 骑行服务暂时不可用，已自动禁用');
                
                // 如果当前选中的是骑行，切换到步行
                if (this.currentMode === 'biking') {
                    this.setMode('walking');
                }
            } else {
                console.log('✅ 骑行服务可用');
            }
        } catch (error) {
            console.error('检查骑行服务失败:', error);
        }
        
        console.log('路径规划模式检查完成');
    }

    /**
     * 设置当前出行模式
     * @param {string} mode - 出行方式 (walking, biking, transit)
     */
    setMode(mode) {
        if (mode === this.currentMode) return;
        
        // 检查该模式是否可用
        if (this.unavailableModes.has(mode)) {
            this.showModeUnavailable(mode);
            return;
        }
        
        this.currentMode = mode;
        this.updateModeButtons();
        
        // 如果有选中的餐厅，重新规划路径
        if (this.destinationRestaurant && mapManager.currentLocation) {
            this.planRouteToDestination();
        }
        
        console.log(`出行模式切换为: ${mode}`);
    }

    /**
     * 显示模式不可用提示
     * @param {string} mode - 不可用的模式
     */
    showModeUnavailable(mode) {
        const modeName = this.modeNames[mode]?.name || mode;
        const errorDiv = document.getElementById('routeError');
        if (errorDiv) {
            errorDiv.innerHTML = `
                <div style="background: #f39c12; color: white; padding: 8px 16px; border-radius: 8px; font-size: 0.8rem; position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); z-index: 1000;">
                    <i class="fas fa-exclamation-circle"></i> ${modeName}路径规划服务暂不可用，已自动切换到步行模式
                </div>
            `;
            setTimeout(() => {
                errorDiv.innerHTML = '';
            }, 3000);
        }
        
        // 自动切换到步行模式
        this.setMode('walking');
    }

    /**
     * 更新UI按钮状态
     */
    updateModeButtons() {
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.mode === this.currentMode) {
                btn.classList.add('active');
            }
        });
    }

    /**
     * 导航到指定餐厅
     * @param {Object} restaurant - 餐厅对象
     */
    async navigateToRestaurant(restaurant) {
        if (!restaurant) {
            console.warn('未指定餐厅');
            return;
        }
        
        if (!mapManager.currentLocation) {
            alert('请先获取当前位置');
            return;
        }
        
        this.destinationRestaurant = restaurant;
        await this.planRouteToDestination();
    }

    /**
     * 规划到目标餐厅的路径
     */
    async planRouteToDestination() {
        if (!this.destinationRestaurant) return;
        
        if (!mapManager.currentLocation) {
            alert('无法获取当前位置，请刷新页面后重试');
            return;
        }
        
        if (this.isPlanning) {
            console.log('路径规划进行中，请稍后');
            return;
        }
        
        this.isPlanning = true;
        this.showRouteLoading(true);
        
        try {
            const params = {
                origin: {
                    lat: mapManager.currentLocation.lat,
                    lng: mapManager.currentLocation.lng
                },
                destination: {
                    lat: this.destinationRestaurant.lat,
                    lng: this.destinationRestaurant.lng
                },
                mode: this.currentMode
            };
            
            console.log(`开始路径规划: ${this.currentMode}模式`);
            const route = await apiService.getRoute(params);
            
            if (route && route.polyline && route.polyline.length > 0) {
                // 绘制路径
                mapManager.drawPath(route.polyline, this.currentMode);
                
                // 显示路径信息
                this.showRouteInfo(route);
                
                console.log(`路径规划成功: 距离${route.distance}m, 时间${route.duration}s, 提供者:${route.provider}`);
            } else {
                throw new Error('无路径数据');
            }
        } catch (error) {
            console.error('路径规划失败:', error);
            
            // 如果是骑行模式失败，标记为不可用并切换到步行
            if (this.currentMode === 'biking' && !this.unavailableModes.has('biking')) {
                console.warn('骑行路径规划失败，标记为不可用');
                this.unavailableModes.add('biking');
                
                // 自动切换到步行模式并重试
                this.currentMode = 'walking';
                this.updateModeButtons();
                
                setTimeout(() => {
                    this.planRouteToDestination();
                }, 500);
                
                return;
            }
            
            this.showRouteError(error.message);
        } finally {
            this.isPlanning = false;
            this.showRouteLoading(false);
        }
    }

    /**
     * 显示路径信息
     * @param {Object} route - 路径信息
     */
    showRouteInfo(route) {
        const durationMin = Math.round(route.duration / 60);
        const distanceKm = (route.distance / 1000).toFixed(1);
        const modeName = this.modeNames[this.currentMode]?.name || '步行';
        
        // 在终点显示信息弹窗
        const endPoint = route.polyline[route.polyline.length - 1];
        const infoPopup = L.popup()
            .setLatLng(endPoint)
            .setContent(`
                <div style="padding: 5px;">
                    <strong>${this.destinationRestaurant.name}</strong><br>
                    📍 距离：${distanceKm} km<br>
                    ⏱️ 预计：${durationMin} 分钟<br>
                    🚶 方式：${modeName}
                </div>
            `)
            .openOn(mapManager.map);
        
        // 可选：在底部显示一个小提示
        const routeInfoDiv = document.getElementById('routeInfo');
        if (routeInfoDiv) {
            routeInfoDiv.innerHTML = `
                <div style="background: #2ecc71; color: white; padding: 8px 16px; border-radius: 30px; font-size: 0.8rem;">
                    <i class="fas fa-route"></i> 距 ${this.destinationRestaurant.name} 还有 ${distanceKm}km，约 ${durationMin} 分钟
                </div>
            `;
            setTimeout(() => {
                routeInfoDiv.innerHTML = '';
            }, 5000);
        }
    }

    /**
     * 显示路径规划加载状态
     * @param {boolean} show - 是否显示
     */
    showRouteLoading(show) {
        const loadingDiv = document.getElementById('routeLoading');
        if (loadingDiv) {
            loadingDiv.style.display = show ? 'flex' : 'none';
        }
        
        if (show) {
            const statusDiv = document.getElementById('routeStatus');
            if (statusDiv) {
                statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在规划路径...';
            }
        } else {
            const statusDiv = document.getElementById('routeStatus');
            if (statusDiv && statusDiv.innerHTML.includes('正在规划')) {
                statusDiv.innerHTML = '';
            }
        }
    }

    /**
     * 显示路径规划错误
     * @param {string} message - 错误信息
     */
    showRouteError(message) {
        const errorDiv = document.getElementById('routeError');
        if (errorDiv) {
            errorDiv.innerHTML = `
                <div style="background: #e74c3c; color: white; padding: 8px 16px; border-radius: 8px; font-size: 0.8rem; position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); z-index: 1000;">
                    <i class="fas fa-exclamation-triangle"></i> 路径规划失败：${message}<br>
                    <small>将使用直线路径显示</small>
                </div>
            `;
            setTimeout(() => {
                errorDiv.innerHTML = '';
            }, 5000);
        } else {
            alert(`路径规划失败：${message}\n将使用直线路径显示`);
        }
    }

    /**
     * 清除当前路径
     */
    clearRoute() {
        mapManager.clearPath();
        this.destinationRestaurant = null;
    }

    /**
     * 获取当前出行模式信息
     * @returns {Object} 模式信息
     */
    getCurrentModeInfo() {
        return this.modeNames[this.currentMode] || this.modeNames.walking;
    }

    /**
     * 绑定UI事件
     */
    bindEvents() {
        // 绑定模式切换按钮
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.setMode(btn.dataset.mode);
            });
        });
        
        // 绑定导航按钮（在详情弹窗中）
        const navigateBtn = document.getElementById('navigateBtn');
        if (navigateBtn) {
            navigateBtn.addEventListener('click', () => {
                if (window.recommendManager && window.recommendManager.selectedRestaurant) {
                    this.navigateToRestaurant(window.recommendManager.selectedRestaurant);
                }
            });
        }
    }
}

// 创建全局单例
const routeManager = new RouteManager();