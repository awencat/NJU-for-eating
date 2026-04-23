// 搜索管理模块 - 负责餐厅搜索功能

class SearchManager {
    constructor() {
        this.searchInput = null;
        this.searchClearBtn = null;
        this.debounceTimer = null;
        this.currentResults = [];
        this.isSearching = false;
    }

    /**
     * 初始化搜索管理器
     */
    init() {
        this.searchInput = document.getElementById('searchInput');
        this.searchClearBtn = document.getElementById('searchClear');
        
        if (!this.searchInput) {
            console.error('搜索输入框未找到');
            return;
        }
        
        this.bindEvents();
        console.log('搜索管理器初始化完成');
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 输入事件(防抖)
        this.searchInput.addEventListener('input', (e) => {
            const keyword = e.target.value.trim();
            
            // 显示/隐藏清除按钮
            if (keyword) {
                this.searchClearBtn?.classList.add('visible');
            } else {
                this.searchClearBtn?.classList.remove('visible');
                this.clearSearch();
                return;
            }
            
            // 防抖处理(500ms)
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.performSearch(keyword);
            }, 500);
        });
        
        // 回车搜索
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                clearTimeout(this.debounceTimer);
                const keyword = e.target.value.trim();
                if (keyword) {
                    this.performSearch(keyword);
                }
            }
        });
        
        // 清除搜索
        if (this.searchClearBtn) {
            this.searchClearBtn.addEventListener('click', () => {
                this.clearSearch();
            });
        }
        
        // 点击外部关闭搜索结果(可选)
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                // 可以在这里添加关闭搜索结果的逻辑
            }
        });
    }

    /**
     * 执行搜索
     * @param {string} keyword - 搜索关键词
     */
    async performSearch(keyword) {
        if (!keyword || this.isSearching) return;
        
        this.isSearching = true;
        console.log('🔍 开始搜索:', keyword);
        
        try {
            // 确保apiService已定义
            if (typeof apiService === 'undefined') {
                throw new Error('API服务未初始化');
            }
            
            const results = await apiService.searchRestaurants(keyword, 20);
            
            this.currentResults = results;
            console.log(`✅ 搜索完成: 找到 ${results.length} 个结果`);
            
            // 通知应用层更新UI
            if (window.app && typeof window.app.handleSearchResults === 'function') {
                window.app.handleSearchResults(results, keyword);
            }
            
        } catch (error) {
            console.error('❌ 搜索失败:', error);
            
            // 显示错误提示
            if (window.app && typeof window.app.showNotification === 'function') {
                window.app.showNotification('搜索失败: ' + error.message, 'error');
            } else {
                alert('搜索失败: ' + error.message);
            }
        } finally {
            this.isSearching = false;
        }
    }

    /**
     * 清除搜索
     */
    clearSearch() {
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        
        if (this.searchClearBtn) {
            this.searchClearBtn.classList.remove('visible');
        }
        
        this.currentResults = [];
        
        // 通知应用层恢复默认状态
        if (window.app && typeof window.app.clearSearch === 'function') {
            window.app.clearSearch();
        }
        
        console.log('🗑️ 搜索已清除');
    }

    /**
     * 获取当前搜索结果
     * @returns {Array} 搜索结果列表
     */
    getResults() {
        return this.currentResults;
    }

    /**
     * 设置搜索框值(编程方式)
     * @param {string} value - 要设置的值
     */
    setSearchValue(value) {
        if (this.searchInput) {
            this.searchInput.value = value;
            
            if (value) {
                this.searchClearBtn?.classList.add('visible');
            } else {
                this.searchClearBtn?.classList.remove('visible');
            }
        }
    }
}

// 创建全局实例
const searchManager = new SearchManager();
