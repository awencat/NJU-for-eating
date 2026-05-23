// 收藏管理模块 - 负责餐厅收藏功能

class FavoritesManager {
    constructor() {
        this.storageKey = 'campus_dining_favorites';
        this.favorites = [];
    }

    init() {
        this.loadFavorites();
        this.notifyChange('init');
        console.log(`❤️ 收藏管理器初始化完成，已加载 ${this.favorites.length} 个收藏`);
    }

    loadFavorites() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            const parsed = stored ? JSON.parse(stored) : [];
            this.favorites = this.normalizeFavorites(parsed);
        } catch (error) {
            console.error('加载收藏失败:', error);
            this.favorites = [];
        }
    }

    saveFavorites(source = 'save') {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.favorites));
            this.notifyChange(source);
        } catch (error) {
            console.error('保存收藏失败:', error);
        }
    }

    normalizeFavorites(list) {
        if (!Array.isArray(list)) return [];

        const unique = new Map();
        list.forEach(item => {
            const normalized = this.normalizeFavorite(item);
            if (!normalized) return;

            const existing = unique.get(normalized.id);
            if (!existing) {
                unique.set(normalized.id, normalized);
                return;
            }

            const existingTime = new Date(existing.favoritedAt || 0).getTime();
            const newTime = new Date(normalized.favoritedAt || 0).getTime();
            unique.set(normalized.id, newTime >= existingTime ? normalized : existing);
        });

        return Array.from(unique.values()).sort((a, b) => {
            return new Date(b.favoritedAt).getTime() - new Date(a.favoritedAt).getTime();
        });
    }

    normalizeFavorite(restaurant) {
        if (!restaurant || restaurant.id == null) return null;

        const id = Number(restaurant.id);
        if (!Number.isFinite(id)) return null;

        return {
            id,
            name: restaurant.name || '未命名餐厅',
            lat: Number(restaurant.lat) || 0,
            lng: Number(restaurant.lng) || 0,
            address: restaurant.address || '',
            cuisine: restaurant.cuisine || '未知',
            price: Number(restaurant.price) || 0,
            rating: Number(restaurant.rating) || 0,
            wait_time: Number(restaurant.wait_time) || 0,
            phone: restaurant.phone || '',
            hours: restaurant.hours || '',
            tags: Array.isArray(restaurant.tags) ? restaurant.tags : (restaurant.tags || ''),
            favoritedAt: restaurant.favoritedAt || new Date().toISOString()
        };
    }

    addFavorite(restaurant) {
        const favorite = this.normalizeFavorite(restaurant);
        if (!favorite) {
            console.warn('收藏失败：餐厅数据无效');
            return false;
        }

        const index = this.favorites.findIndex(f => f.id === favorite.id);
        if (index !== -1) {
            this.favorites[index] = {
                ...this.favorites[index],
                ...favorite,
                favoritedAt: this.favorites[index].favoritedAt || favorite.favoritedAt
            };
            this.saveFavorites('favorite-updated');
            return true;
        }

        this.favorites.unshift(favorite);
        this.saveFavorites('favorite-added');
        console.log(`❤️ 已收藏: ${favorite.name}`);
        return true;
    }

    removeFavorite(restaurantId) {
        const id = Number(restaurantId);
        const index = this.favorites.findIndex(f => f.id === id);
        if (index === -1) {
            console.log('该餐厅不在收藏中');
            return false;
        }

        const removed = this.favorites.splice(index, 1)[0];
        this.saveFavorites('favorite-removed');
        console.log(`💔 已取消收藏: ${removed.name}`);
        return true;
    }

    toggleFavorite(restaurant) {
        const id = Number(restaurant?.id);
        if (!Number.isFinite(id)) return false;

        if (this.isFavorited(id)) {
            this.removeFavorite(id);
            return false;
        }

        this.addFavorite(restaurant);
        return true;
    }

    isFavorited(restaurantId) {
        const id = Number(restaurantId);
        return this.favorites.some(f => f.id === id);
    }

    getFavoriteById(restaurantId) {
        const id = Number(restaurantId);
        return this.favorites.find(f => f.id === id) || null;
    }

    getFavorites() {
        return this.normalizeFavorites(this.favorites);
    }

    getCount() {
        return this.favorites.length;
    }

    clearAll() {
        this.favorites = [];
        this.saveFavorites('favorites-cleared');
        console.log('🗑️ 已清空所有收藏');
    }

    notifyChange(source = 'unknown') {
        window.dispatchEvent(new CustomEvent('favorites:changed', {
            detail: {
                source,
                count: this.getCount(),
                favorites: this.getFavorites()
            }
        }));
    }
}

const favoritesManager = new FavoritesManager();
