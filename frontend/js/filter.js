// 筛选管理模块 - 负责高级筛选功能

class FilterManager {
    constructor() {
        this.modal = null;
        this.filters = {
            price_min: 0,
            price_max: 100,
            rating_min: 0,
            max_wait_time: 60,
            max_distance: 3000,
            cuisines: [],
            is_opening: false,
            sort_by: 'distance'
        };
    }

    /**
     * 初始化筛选管理器
     */
    init() {
        this.modal = document.getElementById('filterModal');
        if (!this.modal) {
            console.error('筛选弹窗未找到');
            return;
        }
        
        this.bindEvents();
        this.loadFilters();
        console.log('🔍 筛选管理器初始化完成');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 价格滑块
        const priceMin = document.getElementById('filterPriceMin');
        const priceMax = document.getElementById('filterPriceMax');
        const priceMinValue = document.getElementById('filterPriceMinValue');
        const priceMaxValue = document.getElementById('filterPriceMaxValue');
        
        if (priceMin && priceMinValue) {
            priceMin.addEventListener('input', (e) => {
                priceMinValue.textContent = e.target.value;
                this.filters.price_min = parseInt(e.target.value);
            });
        }
        
        if (priceMax && priceMaxValue) {
            priceMax.addEventListener('input', (e) => {
                priceMaxValue.textContent = e.target.value;
                this.filters.price_max = parseInt(e.target.value);
            });
        }
        
        // 评分滑块
        const rating = document.getElementById('filterRating');
        const ratingValue = document.getElementById('filterRatingValue');
        if (rating && ratingValue) {
            rating.addEventListener('input', (e) => {
                ratingValue.textContent = e.target.value;
                this.filters.rating_min = parseFloat(e.target.value);
            });
        }
        
        // 等待时间滑块
        const waitTime = document.getElementById('filterWaitTime');
        const waitTimeValue = document.getElementById('filterWaitTimeValue');
        if (waitTime && waitTimeValue) {
            waitTime.addEventListener('input', (e) => {
                waitTimeValue.textContent = e.target.value;
                this.filters.max_wait_time = parseInt(e.target.value);
            });
        }
        
        // 距离滑块
        const distance = document.getElementById('filterDistance');
        const distanceValue = document.getElementById('filterDistanceValue');
        if (distance && distanceValue) {
            distance.addEventListener('input', (e) => {
                distanceValue.textContent = e.target.value;
                this.filters.max_distance = parseInt(e.target.value);
            });
        }
        
        // 营业状态复选框
        const isOpening = document.getElementById('filterIsOpening');
        if (isOpening) {
            isOpening.addEventListener('change', (e) => {
                this.filters.is_opening = e.target.checked;
            });
        }
        
        // 排序方式
        const sortBy = document.getElementById('filterSortBy');
        if (sortBy) {
            sortBy.addEventListener('change', (e) => {
                this.filters.sort_by = e.target.value;
            });
        }
        
        // 菜系多选框
        const cuisineGroup = document.getElementById('filterCuisineGroup');
        if (cuisineGroup) {
            cuisineGroup.addEventListener('change', (e) => {
                if (e.target.type === 'checkbox') {
                    this.updateCuisineFilters();
                }
            });
        }
        
        // 应用筛选按钮
        const applyBtn = document.getElementById('applyFilterBtn');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                this.applyFilters();
            });
        }
        
        // 重置按钮
        const resetBtn = document.getElementById('resetFilterBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetFilters();
            });
        }
        
        // 关闭按钮
        const closeButtons = this.modal.querySelectorAll('.close-modal');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeModal();
            });
        });
        
        // 点击背景关闭
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
    }

    /**
     * 更新菜系筛选条件
     */
    updateCuisineFilters() {
        const checkboxes = document.querySelectorAll('#filterCuisineGroup input[type="checkbox"]');
        const allCheckbox = document.querySelector('#filterCuisineGroup input[value="全部"]');
        
        // 如果勾选了"全部",取消其他所有
        if (allCheckbox && allCheckbox.checked) {
            checkboxes.forEach(cb => {
                if (cb.value !== '全部') cb.checked = false;
            });
            this.filters.cuisines = [];
        } else {
            // 取消"全部"的勾选
            if (allCheckbox) allCheckbox.checked = false;
            
            // 收集所有选中的菜系
            this.filters.cuisines = Array.from(checkboxes)
                .filter(cb => cb.checked && cb.value !== '全部')
                .map(cb => cb.value);
        }
    }

    /**
     * 显示筛选弹窗
     */
    openModal() {
        this.updateUIFromFilters();
        this.modal.style.display = 'flex';
    }

    /**
     * 关闭筛选弹窗
     */
    closeModal() {
        this.modal.style.display = 'none';
    }

    /**
     * 从filters更新UI
     */
    updateUIFromFilters() {
        // 更新滑块值
        document.getElementById('filterPriceMin').value = this.filters.price_min;
        document.getElementById('filterPriceMinValue').textContent = this.filters.price_min;
        document.getElementById('filterPriceMax').value = this.filters.price_max;
        document.getElementById('filterPriceMaxValue').textContent = this.filters.price_max;
        document.getElementById('filterRating').value = this.filters.rating_min;
        document.getElementById('filterRatingValue').textContent = this.filters.rating_min;
        document.getElementById('filterWaitTime').value = this.filters.max_wait_time;
        document.getElementById('filterWaitTimeValue').textContent = this.filters.max_wait_time;
        document.getElementById('filterDistance').value = this.filters.max_distance;
        document.getElementById('filterDistanceValue').textContent = this.filters.max_distance;
        document.getElementById('filterIsOpening').checked = this.filters.is_opening;
        document.getElementById('filterSortBy').value = this.filters.sort_by;
        
        // 更新菜系复选框
        const checkboxes = document.querySelectorAll('#filterCuisineGroup input[type="checkbox"]');
        checkboxes.forEach(cb => {
            if (cb.value === '全部') {
                cb.checked = this.filters.cuisines.length === 0;
            } else {
                cb.checked = this.filters.cuisines.includes(cb.value);
            }
        });
    }

    /**
     * 应用筛选
     */
    async applyFilters() {
        if (!mapManager.currentLocation) {
            if (window.app) {
                window.app.showNotification('请先定位您的位置', 'warning');
            }
            return;
        }
        
        console.log('🔍 应用筛选:', this.filters);
        
        // 保存筛选条件
        this.saveFilters();
        
        // 关闭弹窗
        this.closeModal();
        
        // 调用应用层的筛选方法
        if (window.app && typeof window.app.applyAdvancedFilter === 'function') {
            await window.app.applyAdvancedFilter(this.filters);
        }
    }

    /**
     * 重置筛选
     */
    resetFilters() {
        this.filters = {
            price_min: 0,
            price_max: 100,
            rating_min: 0,
            max_wait_time: 60,
            max_distance: 3000,
            cuisines: [],
            is_opening: false,
            sort_by: 'distance'
        };
        
        this.updateUIFromFilters();
        console.log('🔄 已重置筛选条件');
    }

    /**
     * 保存筛选条件到localStorage
     */
    saveFilters() {
        try {
            localStorage.setItem('campus_dining_filters', JSON.stringify(this.filters));
        } catch (error) {
            console.error('保存筛选条件失败:', error);
        }
    }

    /**
     * 从localStorage加载筛选条件
     */
    loadFilters() {
        try {
            const stored = localStorage.getItem('campus_dining_filters');
            if (stored) {
                this.filters = { ...this.filters, ...JSON.parse(stored) };
            }
        } catch (error) {
            console.error('加载筛选条件失败:', error);
        }
    }

    /**
     * 获取当前筛选条件
     * @returns {Object}
     */
    getFilters() {
        return { ...this.filters };
    }
}

// 创建全局实例
const filterManager = new FilterManager();
