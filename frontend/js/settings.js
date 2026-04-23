// ==================== settings.js ====================
// 设置管理模块 - 负责用户偏好的存储、读取和UI交互

class SettingsManager {
    constructor() {
        this.storageKey = 'campus_dining_preferences';
        this.defaultPreferences = {
            maxPrice: 50,
            maxDistance: 1000,
            cuisines: ['全部'],
            acceptWait: true
        };
        this.preferences = null;
        this.listeners = [];
    }

    /**
     * 初始化设置管理器
     */
    init() {
        this.loadPreferences();
        this.bindEvents();
        console.log('设置管理器初始化完成');
    }

    /**
     * 加载用户偏好（从localStorage）
     */
    loadPreferences() {
        const stored = localStorage.getItem(this.storageKey);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                this.preferences = { ...this.defaultPreferences, ...parsed };
            } catch (e) {
                console.error('加载偏好设置失败:', e);
                this.preferences = { ...this.defaultPreferences };
            }
        } else {
            this.preferences = { ...this.defaultPreferences };
        }
    }

    /**
     * 保存用户偏好到localStorage
     */
    savePreferences() {
        localStorage.setItem(this.storageKey, JSON.stringify(this.preferences));
        this.notifyListeners();
    }

    /**
     * 获取用户偏好
     * @returns {Object} 用户偏好对象
     */
    getPreferences() {
        return { ...this.preferences };
    }

    /**
     * 获取单个偏好值
     * @param {string} key - 偏好键名
     * @returns {*} 偏好值
     */
    getPreference(key) {
        return this.preferences[key];
    }

    /**
     * 设置用户偏好
     * @param {string} key - 偏好键名
     * @param {*} value - 偏好值
     */
    setPreference(key, value) {
        this.preferences[key] = value;
        this.savePreferences();
    }

    /**
     * 批量设置用户偏好
     * @param {Object} newPreferences - 新的偏好对象
     */
    setPreferences(newPreferences) {
        this.preferences = { ...this.preferences, ...newPreferences };
        this.savePreferences();
    }

    /**
     * 重置为默认偏好
     */
    resetToDefault() {
        this.preferences = { ...this.defaultPreferences };
        this.savePreferences();
        this.updateUIFromPreferences();
    }

    /**
     * 从UI获取偏好设置
     * @returns {Object} 偏好对象
     */
    getPreferencesFromUI() {
        const maxPrice = parseInt(document.getElementById('priceRange')?.value || 50);
        const maxDistance = parseInt(document.getElementById('distanceRange')?.value || 1000);
        const acceptWait = document.getElementById('acceptWait')?.checked || true;
        
        const selectedCuisines = [];
        document.querySelectorAll('#cuisineGroup input:checked').forEach(cb => {
            selectedCuisines.push(cb.value);
        });
        const cuisines = selectedCuisines.length > 0 ? selectedCuisines : ['全部'];
        
        return { maxPrice, maxDistance, cuisines, acceptWait };
    }

    /**
     * 将偏好设置应用到UI
     */
    updateUIFromPreferences() {
        const priceRange = document.getElementById('priceRange');
        const priceValue = document.getElementById('priceValue');
        const distanceRange = document.getElementById('distanceRange');
        const distanceValue = document.getElementById('distanceValue');
        const acceptWait = document.getElementById('acceptWait');
        
        if (priceRange) {
            priceRange.value = this.preferences.maxPrice;
            if (priceValue) priceValue.textContent = this.preferences.maxPrice;
        }
        
        if (distanceRange) {
            distanceRange.value = this.preferences.maxDistance;
            if (distanceValue) distanceValue.textContent = this.preferences.maxDistance;
        }
        
        if (acceptWait) {
            acceptWait.checked = this.preferences.acceptWait;
        }
        
        // 更新菜系复选框
        document.querySelectorAll('#cuisineGroup input').forEach(cb => {
            cb.checked = this.preferences.cuisines.includes(cb.value);
        });
        
        // 如果没有选中任何菜系，选中"全部"
        const anyChecked = Array.from(document.querySelectorAll('#cuisineGroup input:checked')).length > 0;
        if (!anyChecked) {
            const allCheckbox = document.querySelector('#cuisineGroup input[value="全部"]');
            if (allCheckbox) allCheckbox.checked = true;
        }
    }

    /**
     * 显示设置弹窗
     */
    openModal() {
        this.updateUIFromPreferences();
        const modal = document.getElementById('settingsModal');
        if (modal) modal.style.display = 'flex';
    }

    /**
     * 关闭设置弹窗
     */
    closeModal() {
        const modal = document.getElementById('settingsModal');
        if (modal) modal.style.display = 'none';
    }

    /**
     * 保存设置（从UI读取并保存）
     * @returns {Object} 保存后的偏好
     */
    saveFromUI() {
        const newPreferences = this.getPreferencesFromUI();
        this.setPreferences(newPreferences);
        this.closeModal();
        return this.getPreferences();
    }

    /**
     * 绑定UI事件
     */
    bindEvents() {
        // 价格滑块
        const priceRange = document.getElementById('priceRange');
        const priceValue = document.getElementById('priceValue');
        if (priceRange && priceValue) {
            priceRange.addEventListener('input', (e) => {
                priceValue.textContent = e.target.value;
            });
        }
        
        // 距离滑块
        const distanceRange = document.getElementById('distanceRange');
        const distanceValue = document.getElementById('distanceValue');
        if (distanceRange && distanceValue) {
            distanceRange.addEventListener('input', (e) => {
                distanceValue.textContent = e.target.value;
            });
        }
        
        // 保存按钮
        const saveBtn = document.getElementById('saveSettings');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveFromUI();
            });
        }
        
        // 取消按钮
        const cancelBtn = document.getElementById('cancelSettings');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closeModal();
            });
        }
        
        // 关闭按钮
        const closeBtn = document.querySelector('#settingsModal .close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeModal();
            });
        }
        
        // 菜系"全部"联动
        const allCheckbox = document.querySelector('#cuisineGroup input[value="全部"]');
        if (allCheckbox) {
            allCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    document.querySelectorAll('#cuisineGroup input').forEach(cb => {
                        if (cb.value !== '全部') cb.checked = false;
                    });
                }
            });
            
            // 其他菜系被选中时取消"全部"
            document.querySelectorAll('#cuisineGroup input:not([value="全部"])').forEach(cb => {
                cb.addEventListener('change', () => {
                    if (cb.checked && allCheckbox.checked) {
                        allCheckbox.checked = false;
                    }
                });
            });
        }
        
        // 点击弹窗外关闭
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal();
                }
            });
        }
    }

    /**
     * 添加偏好变化监听器
     * @param {Function} listener - 回调函数
     */
    addListener(listener) {
        this.listeners.push(listener);
    }

    /**
     * 移除监听器
     * @param {Function} listener - 要移除的回调函数
     */
    removeListener(listener) {
        const index = this.listeners.indexOf(listener);
        if (index > -1) {
            this.listeners.splice(index, 1);
        }
    }

    /**
     * 通知所有监听器偏好已变化
     */
    notifyListeners() {
        this.listeners.forEach(listener => {
            try {
                listener(this.getPreferences());
            } catch (e) {
                console.error('监听器执行错误:', e);
            }
        });
    }
}

// 创建全局单例
const settingsManager = new SettingsManager();