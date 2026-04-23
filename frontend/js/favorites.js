// 收藏管理模块 - 负责餐厅收藏功能

class FavoritesManager {
    constructor() {
        this.storageKey = 'campus_dining_favorites';
        this.favorites = [];
    }

    /**
     * 初始化收藏管理器
     */
    init() {
        this.loadFavorites();
        console.log(`❤️ 收藏管理器初始化完成,已加载 ${this.favorites.length} 个收藏`);
    }

    /**
     * 从localStorage加载收藏
     */
    loadFavorites() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                this.favorites = JSON.parse(stored);
            } else {
                this.favorites = [];
            }
        } catch (error) {
            console.error('加载收藏失败:', error);
            this.favorites = [];
        }
    }

    /**
     * 保存收藏到localStorage
     */
    saveFavorites() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.favorites));
        } catch (error) {
            console.error('保存收藏失败:', error);
        }
    }

    /**
     * 添加收藏
     * @param {Object} restaurant - 餐厅对象
     * @returns {boolean} 是否添加成功
     */
    addFavorite(restaurant) {
        // 检查是否已收藏
        if (this.isFavorited(restaurant.id)) {
            console.log('该餐厅已在收藏中');
            return false;
        }

        // 添加收藏(只保存必要信息)
        const favorite = {
            id: restaurant.id,
            name: restaurant.name,
            lat: restaurant.lat,
            lng: restaurant.lng,
            address: restaurant.address,
            cuisine: restaurant.cuisine,
            price: restaurant.price,
            rating: restaurant.rating,
            wait_time: restaurant.wait_time,
            phone: restaurant.phone,
            hours: restaurant.hours,
            tags: restaurant.tags,
            favoritedAt: new Date().toISOString()
        };

        this.favorites.push(favorite);
        this.saveFavorites();
        
        console.log(`❤️ 已收藏: ${restaurant.name}`);
        return true;
    }

    /**
     * 取消收藏
     * @param {number} restaurantId - 餐厅ID
     * @returns {boolean} 是否取消成功
     */
    removeFavorite(restaurantId) {
        const index = this.favorites.findIndex(f => f.id === restaurantId);
        if (index === -1) {
            console.log('该餐厅不在收藏中');
            return false;
        }

        const removed = this.favorites.splice(index, 1)[0];
        this.saveFavorites();
        
        console.log(`💔 已取消收藏: ${removed.name}`);
        return true;
    }

    /**
     * 切换收藏状态
     * @param {Object} restaurant - 餐厅对象
     * @returns {boolean} true表示已收藏,false表示已取消
     */
    toggleFavorite(restaurant) {
        if (this.isFavorited(restaurant.id)) {
            this.removeFavorite(restaurant.id);
            return false;
        } else {
            this.addFavorite(restaurant);
            return true;
        }
    }

    /**
     * 检查是否已收藏
     * @param {number} restaurantId - 餐厅ID
     * @returns {boolean}
     */
    isFavorited(restaurantId) {
        return this.favorites.some(f => f.id === restaurantId);
    }

    /**
     * 获取所有收藏
     * @returns {Array} 收藏列表
     */
    getFavorites() {
        return this.favorites;
    }

    /**
     * 获取收藏数量
     * @returns {number}
     */
    getCount() {
        return this.favorites.length;
    }

    /**
     * 清空所有收藏
     */
    clearAll() {
        this.favorites = [];
        this.saveFavorites();
        console.log('🗑️ 已清空所有收藏');
    }
}

// 创建全局实例
const favoritesManager = new FavoritesManager();
