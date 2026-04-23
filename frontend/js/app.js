// ==================== app.js ====================
// 应用主入口模块 - 负责初始化所有模块和协调各模块交互

class App {
    constructor() {
        this.isInitialized = false;
        this.defaultLocation = { lat: 32.0542, lng: 118.7835 }; // 南京大学鼓楼校区
        this.lastLocateTime = 0;  // 上次定位时间戳
        this.locateCooldown = 10000;  // 定位冷却时间（10秒）
    }

    /**
     * 初始化应用
     */
    async init() {
        if (this.isInitialized) return;
        
        console.log('正在初始化智慧校园餐厅推荐系统...');
        
        // 初始化各模块
        settingsManager.init();
        filterManager.init();  // 初始化筛选管理器
        favoritesManager.init();  // 初始化收藏管理器
        searchManager.init();  // 初始化搜索管理器
        routeManager.init();
        
        // 初始化地图（默认位置）
        mapManager.init(this.defaultLocation.lat, this.defaultLocation.lng, 15);
        
        // 添加地图控制按钮
        mapManager.addMapControls();
        
        // 绑定全局事件
        this.bindGlobalEvents();
        
        // 检查后端服务
        const isHealthy = await this.checkBackendHealth();
        if (!isHealthy) {
            this.showBackendWarning();
        }
        
        // 获取用户位置并加载推荐
        this.locateAndRecommend();
        
        this.isInitialized = true;
        console.log('应用初始化完成');
    }

    /**
     * 刷新当前位置
     */
    refreshLocation() {
        this.showNotification('正在重新定位...', 'info');
        mapManager.refreshLocation(async (lat, lng) => {
            console.log(`位置已刷新: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
            this.showNotification('位置已更新', 'success');
            // 重新加载推荐
            await this.loadRecommendations(lat, lng);
        });
    }

    /**
     * 获取用户位置并加载推荐
     */
    locateAndRecommend() {
        // 检查定位冷却时间
        const now = Date.now();
        if (now - this.lastLocateTime < this.locateCooldown) {
            const remaining = Math.ceil((this.locateCooldown - (now - this.lastLocateTime)) / 1000);
            console.log(`定位冷却中，请等待 ${remaining} 秒`);
            
            // 显示提示
            this.showNotification(`请等待 ${remaining} 秒后再试`, 'warning');
            return;
        }
        
        this.lastLocateTime = now;
        
        let locationLoaded = false;
        
        // 检查是否在短时间内已经定位过
        if (mapManager.lastLocationUpdate && (now - mapManager.lastLocationUpdate) < 15000) {
            console.log('最近已定位过，使用当前位置');
            if (mapManager.currentLocation) {
                this.loadRecommendations(mapManager.currentLocation.lat, mapManager.currentLocation.lng);
                return;
            }
        }
        
        // 显示定位中提示
        this.showNotification('正在获取您的位置...', 'info');
        
        mapManager.locateUser(async (lat, lng) => {
            if (!locationLoaded) {
                locationLoaded = true;
                console.log(`开始加载推荐，位置: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
                this.showNotification('定位成功，正在加载推荐...', 'success');
                await this.loadRecommendations(lat, lng);
            }
        });
        
        // 如果20秒内没有获取到位置，强制使用默认位置
        setTimeout(async () => {
            if (!locationLoaded) {
                locationLoaded = true;
                console.log('定位超时，使用默认位置（南京大学鼓楼校区）');
                this.showNotification('定位超时，使用默认位置', 'warning');
                await this.loadRecommendations(this.defaultLocation.lat, this.defaultLocation.lng);
            }
        }, 20000);
    }

    /**
     * 加载推荐餐厅
     * @param {number} lat - 纬度
     * @param {number} lng - 经度
     */
    async loadRecommendations(lat, lng) {
        const preferences = settingsManager.getPreferences();
        
        this.showLoading(true);
        
        try {
            const params = {
                lat, lng,
                max_price: preferences.maxPrice,
                max_distance: preferences.maxDistance,
                cuisines: preferences.cuisines,
                accept_wait: preferences.acceptWait
            };
            
            console.log('发送推荐请求:', params);
            const restaurants = await apiService.getRecommendations(params);
            
            console.log('收到推荐结果:', restaurants?.length || 0, '家餐厅');
            
            if (restaurants && restaurants.length > 0) {
                this.displayRecommendations(restaurants);
                mapManager.addRestaurantMarkers(restaurants, (restaurant) => {
                    this.showRestaurantDetail(restaurant);
                });
            } else {
                this.showEmptyResult();
            }
        } catch (error) {
            console.error('加载推荐失败:', error);
            this.showError('加载失败：' + (error.response?.data?.message || error.message || '请检查后端服务是否正常运行'));
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 显示推荐列表
     * @param {Array} restaurants - 餐厅列表
     */
    displayRecommendations(restaurants) {
        const container = document.getElementById('restaurantList');
        if (!container) return;
        
        window.recommendManager = { currentRecommendations: restaurants, selectedRestaurant: null };
        
        const html = restaurants.map((rest, index) => `
            <div class="restaurant-card" data-id="${rest.id}" data-index="${index}">
                <div class="card-header">
                    <span class="card-name">${this.escapeHtml(rest.name)}</span>
                    <span class="card-rating">⭐ ${rest.rating.toFixed(1)}</span>
                </div>
                <div class="card-info">
                    <span><i class="fas fa-location-dot"></i> ${rest.distance}米</span>
                    <span><i class="fas fa-yen-sign"></i> ¥${rest.price}/人</span>
                    <span><i class="fas fa-clock"></i> 排队 ${rest.wait_time}分钟</span>
                </div>
                <div>
                    <span class="card-cuisine"><i class="fas fa-utensils"></i> ${rest.cuisine}</span>
                </div>
                ${rest.reason ? `<div class="card-reason"><i class="fas fa-lightbulb"></i> ${rest.reason}</div>` : ''}
            </div>
        `).join('');
        
        container.innerHTML = html;
        
        // 绑定卡片点击事件
        document.querySelectorAll('.restaurant-card').forEach(card => {
            card.addEventListener('click', () => {
                const index = parseInt(card.dataset.index);
                this.selectRestaurant(index, restaurants);
            });
        });
    }

    /**
     * 选择餐厅
     * @param {number} index - 餐厅索引
     * @param {Array} restaurants - 餐厅列表
     */
    selectRestaurant(index, restaurants) {
        // 移除其他卡片的高亮
        document.querySelectorAll('.restaurant-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // 高亮当前卡片
        const cards = document.querySelectorAll('.restaurant-card');
        if (cards[index]) {
            cards[index].classList.add('selected');
        }
        
        const restaurant = restaurants[index];
        if (restaurant) {
            window.recommendManager.selectedRestaurant = restaurant;
            this.showRestaurantDetail(restaurant);
        }
    }

    /**
     * 显示餐厅详情弹窗
     * @param {Object} restaurant - 餐厅对象
     */
    showRestaurantDetail(restaurant) {
        const modal = document.getElementById('detailModal');
        const nameSpan = document.getElementById('detailName');
        const bodyDiv = document.getElementById('detailBody');
        
        if (!modal || !nameSpan || !bodyDiv) return;
        
        nameSpan.textContent = restaurant.name;
        bodyDiv.innerHTML = `
            <div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <span><i class="fas fa-star" style="color: #f39c12;"></i> 评分：${restaurant.rating}</span>
                    <span><i class="fas fa-yen-sign"></i> 人均：¥${restaurant.price}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <span><i class="fas fa-location-dot"></i> 距离：${restaurant.distance}米</span>
                    <span><i class="fas fa-clock"></i> 排队：${restaurant.wait_time}分钟</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <span class="card-cuisine"><i class="fas fa-utensils"></i> ${restaurant.cuisine}</span>
                </div>
                <div class="detail-address">
                    <i class="fas fa-map-pin"></i> 地址：${restaurant.address || '待补充'}<br>
                    <i class="fas fa-phone"></i> 电话：${restaurant.phone || '待补充'}<br>
                    <i class="fas fa-clock"></i> 营业时间：${restaurant.hours || '10:00-21:30'}
                </div>
                ${restaurant.reason ? `<div class="detail-reason">
                    <i class="fas fa-lightbulb"></i> 推荐理由：${restaurant.reason}
                </div>` : ''}
            </div>
        `;
        
        modal.style.display = 'flex';
        
        // 绑定导航按钮
        const navigateBtn = document.getElementById('navigateBtn');
        if (navigateBtn) {
            const newBtn = navigateBtn.cloneNode(true);
            navigateBtn.parentNode.replaceChild(newBtn, navigateBtn);
            newBtn.addEventListener('click', () => {
                modal.style.display = 'none';
                routeManager.navigateToRestaurant(restaurant);
            });
        }
    }

    /**
     * 显示空结果
     */
    showEmptyResult() {
        const container = document.getElementById('restaurantList');
        if (container) {
            container.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fas fa-search"></i><br>
                    未找到符合条件的餐厅<br>
                    <small style="color: #999;">请尝试放宽筛选条件</small>
                </div>
            `;
        }
    }

    /**
     * 显示加载状态
     * @param {boolean} show - 是否显示
     */
    showLoading(show) {
        const container = document.getElementById('restaurantList');
        if (container && show) {
            container.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fas fa-spinner fa-spin"></i> 正在推荐餐厅...
                </div>
            `;
        }
    }

    /**
     * 显示错误信息
     * @param {string} message - 错误信息
     */
    showError(message) {
        const container = document.getElementById('restaurantList');
        if (container) {
            container.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fas fa-exclamation-triangle"></i><br>
                    ${message}
                </div>
            `;
        }
    }

    /**
     * 显示后端服务警告
     */
    showBackendWarning() {
        const warningDiv = document.createElement('div');
        warningDiv.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: #e74c3c;
            color: white;
            padding: 10px 20px;
            border-radius: 30px;
            font-size: 0.85rem;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        `;
        warningDiv.innerHTML = '<i class="fas fa-server"></i> 后端服务未连接，请确保服务已启动';
        document.body.appendChild(warningDiv);
        
        setTimeout(() => {
            warningDiv.remove();
        }, 5000);
    }

    /**
     * 应用高级筛选
     * @param {Object} filters - 筛选条件
     */
    async applyAdvancedFilter(filters) {
        if (!mapManager.currentLocation) {
            this.showNotification('请先定位', 'warning');
            return;
        }
        
        this.showLoading(true);
        
        try {
            const result = await apiService.filterRestaurants({
                lat: mapManager.currentLocation.lat,
                lng: mapManager.currentLocation.lng,
                ...filters,
                page: 1,
                page_size: 20
            });
            
            console.log('🔍 筛选结果:', result.pagination);
            
            if (result.data && result.data.length > 0) {
                this.displayFilteredRestaurants(result.data, result.pagination, result.filters_applied);
                mapManager.addRestaurantMarkers(result.data, (restaurant) => {
                    this.showRestaurantDetail(restaurant);
                });
                
                this.showNotification(`筛选完成: 找到 ${result.pagination.total} 家餐厅`, 'success');
            } else {
                this.showEmptyResult('没有找到符合条件的餐厅');
            }
        } catch (error) {
            console.error('筛选失败:', error);
            this.showError('筛选失败：' + (error.response?.data?.message || error.message));
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 显示筛选后的餐厅列表
     * @param {Array} restaurants - 餐厅列表
     * @param {Object} pagination - 分页信息
     * @param {Object} filtersApplied - 应用的筛选条件
     */
    displayFilteredRestaurants(restaurants, pagination, filtersApplied) {
        const container = document.getElementById('restaurantList');
        if (!container) return;
        
        window.recommendManager = { 
            currentRecommendations: restaurants, 
            selectedRestaurant: null,
            isFilteredMode: true,
            pagination: pagination,
            filters: filtersApplied
        };
        
        // 生成筛选条件显示
        const filterInfoHtml = `
            <div class="filter-info-bar">
                <i class="fas fa-filter"></i>
                <span>筛选: ${filtersApplied.price_range} | ⭐${filtersApplied.min_rating}+ | ⏱️${filtersApplied.max_wait_time}</span>
            </div>
        `;
        
        // 生成分页HTML
        const paginationHtml = `
            <div class="pagination-bar">
                <button class="page-btn ${!pagination.has_prev ? 'disabled' : ''}" 
                        onclick="app.goToFilteredPage(${pagination.page - 1})"
                        ${!pagination.has_prev ? 'disabled' : ''}>
                    <i class="fas fa-chevron-left"></i> 上一页
                </button>
                <span class="page-info">第 ${pagination.page}/${pagination.total_pages} 页 (共${pagination.total}家)</span>
                <button class="page-btn ${!pagination.has_next ? 'disabled' : ''}" 
                        onclick="app.goToFilteredPage(${pagination.page + 1})"
                        ${!pagination.has_next ? 'disabled' : ''}>
                    下一页 <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
        
        const html = filterInfoHtml + paginationHtml + restaurants.map((rest, index) => `
            <div class="restaurant-card" data-id="${rest.id}" data-index="${index}">
                <div class="card-header">
                    <span class="card-name">${this.escapeHtml(rest.name)}</span>
                    <span class="card-rating">⭐ ${rest.rating.toFixed(1)}</span>
                </div>
                <div class="card-info">
                    <span><i class="fas fa-location-dot"></i> ${rest.distance}米</span>
                    <span><i class="fas fa-utensils"></i> ${this.escapeHtml(rest.cuisine)}</span>
                </div>
                <div class="card-footer">
                    <span class="price-tag">¥${rest.price}</span>
                    <span class="wait-time">⏱️ ${rest.wait_time}分钟</span>
                    <button class="btn-favorite-small ${favoritesManager.isFavorited(rest.id) ? 'favorited' : ''}" 
                            onclick="event.stopPropagation(); app.toggleFavorite(${rest.id})">
                        <i class="fas fa-heart"></i>
                    </button>
                    <button class="btn-detail-small" onclick="app.showRestaurantDetailById(${rest.id})">详情</button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
        
        // 绑定卡片点击事件
        container.querySelectorAll('.restaurant-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = parseInt(card.dataset.id);
                const restaurant = restaurants.find(r => r.id === id);
                if (restaurant) {
                    this.showRestaurantDetail(restaurant);
                }
            });
        });
    }

    /**
     * 跳转到筛选结果的指定页
     * @param {number} page - 目标页码
     */
    async goToFilteredPage(page) {
        const manager = window.recommendManager;
        if (!manager || !manager.isFilteredMode) {
            this.showNotification('当前不在筛选模式', 'warning');
            return;
        }
        
        if (page < 1 || page > manager.pagination.total_pages) {
            return;
        }
        
        const filters = filterManager.getFilters();
        filters.page = page;
        filters.page_size = 20;
        filters.lat = mapManager.currentLocation.lat;
        filters.lng = mapManager.currentLocation.lng;
        
        await this.applyAdvancedFilter(filters);
        
        // 滚动到顶部
        const container = document.getElementById('restaurantList');
        if (container) {
            container.scrollTop = 0;
        }
    }

    /**
     * 加载附近所有餐厅(支持分页)
     * @param {number} lat - 纬度
     * @param {number} lng - 经度
     * @param {number} page - 页码
     */
    async loadNearbyRestaurants(lat, lng, page = 1) {
        const preferences = settingsManager.getPreferences();
        
        this.showLoading(true);
        
        try {
            const result = await apiService.getNearbyRestaurants({
                lat,
                lng,
                max_distance: preferences.maxDistance,
                page: page,
                page_size: 20
            });
            
            console.log('获取附近餐厅:', result.pagination);
            
            if (result.data && result.data.length > 0) {
                this.displayNearbyRestaurants(result.data, result.pagination);
                mapManager.addRestaurantMarkers(result.data, (restaurant) => {
                    this.showRestaurantDetail(restaurant);
                });
            } else {
                this.showEmptyResult('附近没有餐厅');
            }
        } catch (error) {
            console.error('加载附近餐厅失败:', error);
            this.showError('加载失败：' + (error.response?.data?.message || error.message));
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 显示附近餐厅列表(带分页)
     * @param {Array} restaurants - 餐厅列表
     * @param {Object} pagination - 分页信息
     */
    displayNearbyRestaurants(restaurants, pagination) {
        const container = document.getElementById('restaurantList');
        if (!container) return;
        
        window.recommendManager = { 
            currentRecommendations: restaurants, 
            selectedRestaurant: null,
            isNearbyMode: true,
            pagination: pagination
        };
        
        // 生成分页HTML
        const paginationHtml = `
            <div class="pagination-bar">
                <button class="page-btn ${!pagination.has_prev ? 'disabled' : ''}" 
                        onclick="app.goToPage(${pagination.page - 1})"
                        ${!pagination.has_prev ? 'disabled' : ''}>
                    <i class="fas fa-chevron-left"></i> 上一页
                </button>
                <span class="page-info">第 ${pagination.page}/${pagination.total_pages} 页 (共${pagination.total}家)</span>
                <button class="page-btn ${!pagination.has_next ? 'disabled' : ''}" 
                        onclick="app.goToPage(${pagination.page + 1})"
                        ${!pagination.has_next ? 'disabled' : ''}>
                    下一页 <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
        
        const html = paginationHtml + restaurants.map((rest, index) => `
            <div class="restaurant-card" data-id="${rest.id}" data-index="${index}">
                <div class="card-header">
                    <span class="card-name">${this.escapeHtml(rest.name)}</span>
                    <span class="card-rating">⭐ ${rest.rating.toFixed(1)}</span>
                </div>
                <div class="card-info">
                    <span><i class="fas fa-location-dot"></i> ${rest.distance}米</span>
                    <span><i class="fas fa-utensils"></i> ${this.escapeHtml(rest.cuisine)}</span>
                </div>
                <div class="card-footer">
                    <span class="price-tag">¥${rest.price}</span>
                    <span class="wait-time">⏱️ ${rest.wait_time}分钟</span>
                    <button class="btn-detail-small" onclick="app.showRestaurantDetailById(${rest.id})">详情</button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
        
        // 绑定卡片点击事件
        container.querySelectorAll('.restaurant-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = parseInt(card.dataset.id);
                const restaurant = restaurants.find(r => r.id === id);
                if (restaurant) {
                    this.showRestaurantDetail(restaurant);
                }
            });
        });
    }

    /**
     * 跳转到指定页
     * @param {number} page - 目标页码
     */
    async goToPage(page) {
        if (!mapManager.currentLocation) {
            this.showNotification('请先定位', 'warning');
            return;
        }
        
        const manager = window.recommendManager;
        if (!manager || !manager.isNearbyMode) {
            this.showNotification('当前不在附近餐厅模式', 'warning');
            return;
        }
        
        // 检查页码范围
        if (page < 1 || page > manager.pagination.total_pages) {
            return;
        }
        
        console.log(`📄 跳转到第 ${page} 页`);
        await this.loadNearbyRestaurants(
            mapManager.currentLocation.lat,
            mapManager.currentLocation.lng,
            page
        );
        
        // 滚动到顶部
        const container = document.getElementById('restaurantList');
        if (container) {
            container.scrollTop = 0;
        }
    }

    /**
     * 处理搜索结果
     * @param {Array} results - 搜索结果列表
     * @param {string} keyword - 搜索关键词
     */
    handleSearchResults(results, keyword) {
        console.log(`📊 处理搜索结果: ${results.length} 个餐厅`);
        
        // 清除现有标记
        mapManager.clearRestaurantMarkers();
        
        if (results.length === 0) {
            // 显示无结果提示
            this.showEmptyResult(`未找到"${keyword}"相关餐厅`);
            return;
        }
        
        // 添加搜索结果标记到地图
        mapManager.addRestaurantMarkers(results, (restaurant) => {
            this.showRestaurantDetail(restaurant);
        });
        
        // 在侧边栏显示搜索结果
        this.displaySearchResults(results, keyword);
        
        // 调整地图视野以包含所有结果
        if (results.length > 0) {
            mapManager.fitBoundsToMarkers(results);
        }
        
        // 显示成功提示
        this.showNotification(`找到 ${results.length} 个相关餐厅`, 'success');
    }

    /**
     * 显示搜索结果列表
     * @param {Array} restaurants - 餐厅列表
     * @param {string} keyword - 搜索关键词
     */
    displaySearchResults(restaurants, keyword) {
        const container = document.getElementById('restaurantList');
        if (!container) return;
        
        window.recommendManager = { 
            currentRecommendations: restaurants, 
            selectedRestaurant: null,
            isSearchResults: true,
            searchKeyword: keyword
        };
        
        const html = `
            <div class="search-header">
                <i class="fas fa-search"></i>
                <span>搜索结果: "${this.escapeHtml(keyword)}" (${restaurants.length}个)</span>
            </div>
        ` + restaurants.map((rest, index) => `
            <div class="restaurant-card" data-id="${rest.id}" data-index="${index}">
                <div class="card-header">
                    <span class="card-name">${this.escapeHtml(rest.name)}</span>
                    <span class="card-rating">⭐ ${rest.rating.toFixed(1)}</span>
                </div>
                <div class="card-info">
                    <span><i class="fas fa-location-dot"></i> ${rest.address || '未知地址'}</span>
                    <span><i class="fas fa-utensils"></i> ${this.escapeHtml(rest.cuisine || '未知')}</span>
                </div>
                <div class="card-footer">
                    <span class="price-tag">¥${rest.price}</span>
                    <button class="btn-detail-small" onclick="app.showRestaurantDetailById(${rest.id})">详情</button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
        
        // 绑定卡片点击事件
        container.querySelectorAll('.restaurant-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = parseInt(card.dataset.id);
                const restaurant = restaurants.find(r => r.id === id);
                if (restaurant) {
                    this.showRestaurantDetail(restaurant);
                }
            });
        });
    }

    /**
     * 清除搜索，恢复推荐状态
     */
    clearSearch() {
        console.log('🔄 清除搜索，恢复推荐');
        
        // 如果有当前位置，重新加载推荐
        if (mapManager.currentLocation) {
            this.loadRecommendations(mapManager.currentLocation.lat, mapManager.currentLocation.lng);
        } else {
            // 否则使用默认位置
            this.loadRecommendations(this.defaultLocation.lat, this.defaultLocation.lng);
        }
    }

    /**
     * 根据ID显示餐厅详情
     * @param {number} id - 餐厅ID
     */
    async showRestaurantDetailById(id) {
        try {
            const restaurant = await apiService.getRestaurantDetail(id);
            if (restaurant) {
                this.showRestaurantDetail(restaurant);
            }
        } catch (error) {
            console.error('获取餐厅详情失败:', error);
            this.showNotification('获取详情失败', 'error');
        }
    }

    /**
     * 显示收藏列表
     */
    showFavorites() {
        const favorites = favoritesManager.getFavorites();
        const modal = document.getElementById('favoritesModal');
        const listContainer = document.getElementById('favoritesList');
        const countHeader = document.getElementById('favoritesCountHeader');
        
        if (!modal || !listContainer) return;
        
        // 更新收藏数量
        const count = favoritesManager.getCount();
        countHeader.textContent = count;
        document.getElementById('favoritesCount').textContent = count;
        
        if (count === 0) {
            listContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #999;">
                    <i class="fas fa-heart-broken" style="font-size: 3rem; margin-bottom: 15px;"></i>
                    <p>还没有收藏任何餐厅</p>
                    <p style="font-size: 0.85rem; margin-top: 10px;">点击餐厅卡片上的 ❤️ 按钮即可收藏</p>
                </div>
            `;
        } else {
            listContainer.innerHTML = favorites.map(rest => `
                <div class="favorite-item" data-id="${rest.id}">
                    <div class="favorite-info">
                        <div class="favorite-name">${this.escapeHtml(rest.name)}</div>
                        <div class="favorite-details">
                            <span>⭐ ${rest.rating.toFixed(1)}</span>
                            <span>💰 ¥${rest.price}</span>
                            <span>🍜 ${this.escapeHtml(rest.cuisine)}</span>
                        </div>
                        <div class="favorite-address">${this.escapeHtml(rest.address || '')}</div>
                    </div>
                    <div class="favorite-actions">
                        <button class="btn-navigate" onclick="app.navigateToFavorite(${rest.id})">
                            <i class="fas fa-location-arrow"></i> 导航
                        </button>
                        <button class="btn-remove-favorite" onclick="app.removeFavorite(${rest.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }
        
        modal.style.display = 'flex';
    }

    /**
     * 切换收藏状态
     * @param {number} restaurantId - 餐厅ID
     */
    async toggleFavorite(restaurantId) {
        // 查找餐厅信息
        let restaurant = null;
        const manager = window.recommendManager;
        if (manager && manager.currentRecommendations) {
            restaurant = manager.currentRecommendations.find(r => r.id === restaurantId);
        }
        
        if (!restaurant) {
            // 如果当前列表中没有，尝试从API获取
            try {
                restaurant = await apiService.getRestaurantDetail(restaurantId);
            } catch (error) {
                console.error('获取餐厅信息失败:', error);
                this.showNotification('操作失败', 'error');
                return;
            }
        }
        
        if (!restaurant) {
            this.showNotification('餐厅不存在', 'error');
            return;
        }
        
        // 切换收藏
        const isFavorited = favoritesManager.toggleFavorite(restaurant);
        
        // 更新UI
        this.updateFavoriteButtonUI(restaurantId, isFavorited);
        
        // 更新收藏数量显示
        const count = favoritesManager.getCount();
        document.getElementById('favoritesCount').textContent = count;
        
        // 显示提示
        if (isFavorited) {
            this.showNotification(`已收藏: ${restaurant.name}`, 'success');
        } else {
            this.showNotification(`已取消收藏: ${restaurant.name}`, 'info');
        }
    }

    /**
     * 更新收藏按钮UI
     * @param {number} restaurantId - 餐厅ID
     * @param {boolean} isFavorited - 是否已收藏
     */
    updateFavoriteButtonUI(restaurantId, isFavorited) {
        const buttons = document.querySelectorAll(`[onclick*="toggleFavorite(${restaurantId})"]`);
        buttons.forEach(btn => {
            if (isFavorited) {
                btn.classList.add('favorited');
            } else {
                btn.classList.remove('favorited');
            }
        });
    }

    /**
     * 移除收藏
     * @param {number} restaurantId - 餐厅ID
     */
    removeFavorite(restaurantId) {
        const result = favoritesManager.removeFavorite(restaurantId);
        if (result) {
            // 重新显示收藏列表
            this.showFavorites();
            this.showNotification('已取消收藏', 'info');
        }
    }

    /**
     * 清空所有收藏
     */
    clearFavorites() {
        if (confirm('确定要清空所有收藏吗？')) {
            favoritesManager.clearAll();
            this.showFavorites();
            this.showNotification('已清空所有收藏', 'info');
        }
    }

    /**
     * 导航到收藏的餐厅
     * @param {number} restaurantId - 餐厅ID
     */
    async navigateToFavorite(restaurantId) {
        const favorites = favoritesManager.getFavorites();
        const restaurant = favorites.find(f => f.id === restaurantId);
        
        if (!restaurant) {
            this.showNotification('餐厅不存在', 'error');
            return;
        }
        
        // 关闭收藏弹窗
        document.getElementById('favoritesModal').style.display = 'none';
        
        // 显示餐厅详情并导航
        this.showRestaurantDetail(restaurant);
        
        // 自动开始导航
        setTimeout(() => {
            const navBtn = document.querySelector('#detailModal .btn-navigate');
            if (navBtn) {
                navBtn.click();
            }
        }, 500);
    }

    /**
     * 检查后端服务健康状态
     * @returns {Promise<boolean>} 是否健康
     */
    async checkBackendHealth() {
        try {
            return await apiService.healthCheck();
        } catch (error) {
            return false;
        }
    }

    /**
     * 绑定全局事件
     */
    bindGlobalEvents() {
        // 定位按钮
        const locateBtn = document.getElementById('locateBtn');
        if (locateBtn) {
            locateBtn.addEventListener('click', () => {
                this.locateAndRecommend();
            });
        }
        
        // 偏好设置按钮
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                settingsManager.openModal();
            });
        }
        
        // 推荐餐厅按钮
        const recommendBtn = document.getElementById('recommendBtn');
        if (recommendBtn) {
            recommendBtn.addEventListener('click', () => {
                if (mapManager.currentLocation) {
                    this.loadRecommendations(
                        mapManager.currentLocation.lat,
                        mapManager.currentLocation.lng
                    );
                    this.showNotification('正在加载推荐餐厅...', 'info');
                } else {
                    this.showNotification('请先定位您的位置', 'warning');
                }
            });
        }
        
        // 附近餐厅按钮
        const nearbyBtn = document.getElementById('nearbyBtn');
        if (nearbyBtn) {
            nearbyBtn.addEventListener('click', () => {
                if (mapManager.currentLocation) {
                    this.loadNearbyRestaurants(
                        mapManager.currentLocation.lat,
                        mapManager.currentLocation.lng,
                        1  // 第一页
                    );
                    this.showNotification('正在加载附近餐厅...', 'info');
                } else {
                    this.showNotification('请先定位您的位置', 'warning');
                }
            });
        }
        
        // 筛选按钮
        const filterBtn = document.getElementById('filterBtn');
        if (filterBtn) {
            filterBtn.addEventListener('click', () => {
                filterManager.openModal();
            });
        }
        
        // 收藏按钮
        const favoritesBtn = document.getElementById('favoritesBtn');
        if (favoritesBtn) {
            favoritesBtn.addEventListener('click', () => {
                this.showFavorites();
            });
        }
        
        // 刷新按钮
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                if (mapManager.currentLocation) {
                    this.loadRecommendations(mapManager.currentLocation.lat, mapManager.currentLocation.lng);
                } else {
                    this.locateAndRecommend();
                }
            });
        }
        
        // 关于按钮
        const aboutBtn = document.getElementById('aboutBtn');
        const aboutModal = document.getElementById('aboutModal');
        if (aboutBtn && aboutModal) {
            aboutBtn.addEventListener('click', () => {
                aboutModal.style.display = 'flex';
            });
            
            const closeAbout = document.querySelector('.close-about-modal');
            if (closeAbout) {
                closeAbout.addEventListener('click', () => {
                    aboutModal.style.display = 'none';
                });
            }
            
            const closeAboutBtn = document.getElementById('closeAboutBtn');
            if (closeAboutBtn) {
                closeAboutBtn.addEventListener('click', () => {
                    aboutModal.style.display = 'none';
                });
            }
            
            aboutModal.addEventListener('click', (e) => {
                if (e.target === aboutModal) {
                    aboutModal.style.display = 'none';
                }
            });
        }
        
        // 详情弹窗关闭
        const closeDetail = document.querySelector('.close-detail-modal');
        const detailModal = document.getElementById('detailModal');
        if (closeDetail && detailModal) {
            closeDetail.addEventListener('click', () => {
                detailModal.style.display = 'none';
            });
            
            detailModal.addEventListener('click', (e) => {
                if (e.target === detailModal) {
                    detailModal.style.display = 'none';
                }
            });
        }
        
        // 收藏弹窗关闭
        const closeFavorites = document.getElementById('closeFavoritesBtn');
        const favoritesModal = document.getElementById('favoritesModal');
        if (closeFavorites && favoritesModal) {
            closeFavorites.addEventListener('click', () => {
                favoritesModal.style.display = 'none';
            });
        }
        
        // 清空收藏按钮
        const clearFavorites = document.getElementById('clearFavoritesBtn');
        if (clearFavorites) {
            clearFavorites.addEventListener('click', () => {
                this.clearFavorites();
            });
        }
        
        // 收藏弹窗点击背景关闭
        if (favoritesModal) {
            favoritesModal.addEventListener('click', (e) => {
                if (e.target === favoritesModal) {
                    favoritesModal.style.display = 'none';
                }
            });
        }
    }

    /**
     * 显示通知提示
     * @param {string} message - 提示信息
     * @param {string} type - 类型 (info, success, warning, error)
     */
    showNotification(message, type = 'info') {
        // 移除旧的通知
        const oldNotification = document.querySelector('.locate-notification');
        if (oldNotification) {
            oldNotification.remove();
        }
        
        const colors = {
            info: '#3498db',
            success: '#2ecc71',
            warning: '#f39c12',
            error: '#e74c3c'
        };
        
        const icons = {
            info: 'fa-info-circle',
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle'
        };
        
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'locate-notification';
        notificationDiv.style.cssText = `
            position: fixed;
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: ${colors[type]};
            color: white;
            padding: 12px 24px;
            border-radius: 30px;
            font-size: 0.9rem;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            animation: slideUp 0.3s ease;
        `;
        notificationDiv.innerHTML = `<i class="fas ${icons[type]}"></i> ${message}`;
        document.body.appendChild(notificationDiv);
        
        // 添加动画样式
        if (!document.getElementById('notification-style')) {
            const style = document.createElement('style');
            style.id = 'notification-style';
            style.textContent = `
                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translateX(-50%) translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(-50%) translateY(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        // 3秒后自动消失
        setTimeout(() => {
            notificationDiv.style.opacity = '0';
            notificationDiv.style.transition = 'opacity 0.3s';
            setTimeout(() => notificationDiv.remove(), 300);
        }, 3000);
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

// 等待DOM加载完成后启动应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();  // 将app实例暴露到全局
    window.app.init();
});