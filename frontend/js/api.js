// ==================== api.js ====================
// API服务模块 - 负责所有后端接口调用

const API_BASE_URL = 'http://127.0.0.1:5000/api';

class APIService {
    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    /**
     * 获取推荐餐厅列表
     * @param {Object} params - 请求参数
     * @param {number} params.lat - 纬度
     * @param {number} params.lng - 经度
     * @param {number} params.max_price - 最高价格
     * @param {number} params.max_distance - 最大距离（米）
     * @param {Array} params.cuisines - 菜系偏好
     * @param {boolean} params.accept_wait - 是否接受排队
     * @returns {Promise<Array>} 推荐餐厅列表
     */
    async getRecommendations(params) {
        try {
            const response = await this.client.post('/recommend', params);
            if (response.data.status === 'success') {
                return response.data.data;
            } else {
                throw new Error(response.data.message || '推荐失败');
            }
        } catch (error) {
            console.error('推荐API错误:', error);
            throw error;
        }
    }

    /**
     * 获取路径规划
     * @param {Object} params - 请求参数
     * @param {Object} params.origin - 起点 {lat, lng}
     * @param {Object} params.destination - 终点 {lat, lng}
     * @param {string} params.mode - 出行方式 (walking, biking, transit)
     * @returns {Promise<Object>} 路径信息
     */
    async getRoute(params) {
        try {
            const response = await this.client.post('/route', params);
            if (response.data.status === 'success') {
                return response.data.data;
            } else {
                throw new Error(response.data.message || '路径规划失败');
            }
        } catch (error) {
            console.error('路径规划API错误:', error);
            throw error;
        }
    }

    /**
     * 获取附近所有餐厅(支持分页)
     * @param {Object} params - 请求参数
     * @param {number} params.lat - 纬度
     * @param {number} params.lng - 经度
     * @param {number} params.max_distance - 最大距离(米,默认3000)
     * @param {number} params.page - 页码(默认1)
     * @param {number} params.page_size - 每页数量(默认20)
     * @returns {Promise<Object>} 包含数据和分页信息
     */
    async getNearbyRestaurants(params) {
        try {
            const response = await this.client.get('/nearby', {
                params: {
                    lat: params.lat,
                    lng: params.lng,
                    max_distance: params.max_distance || 3000,
                    page: params.page || 1,
                    page_size: params.page_size || 20
                }
            });
            
            if (response.data.success) {
                return response.data;
            } else {
                throw new Error(response.data.message || '获取失败');
            }
        } catch (error) {
            console.error('获取附近餐厅错误:', error);
            throw error;
        }
    }

    /**
     * 高级筛选餐厅
     * @param {Object} params - 筛选参数
     * @returns {Promise<Object>} 包含数据和分页信息
     */
    async filterRestaurants(params) {
        try {
            const response = await this.client.post('/filter', params);
            
            if (response.data.success) {
                return response.data;
            } else {
                throw new Error(response.data.message || '筛选失败');
            }
        } catch (error) {
            console.error('筛选餐厅错误:', error);
            throw error;
        }
    }

    /**
     * 搜索餐厅
     * @param {string} keyword - 搜索关键词
     * @param {number} limit - 返回数量限制(默认20)
     * @returns {Promise<Array>} 搜索结果列表
     */
    async searchRestaurants(keyword, limit = 20) {
        try {
            const response = await this.client.get('/search', {
                params: {
                    keyword: keyword,
                    limit: limit
                }
            });
            
            if (response.data.success) {
                return response.data.data;
            } else {
                throw new Error(response.data.message || '搜索失败');
            }
        } catch (error) {
            console.error('搜索API错误:', error);
            throw error;
        }
    }

    /**
     * 获取所有餐厅列表
     * @returns {Promise<Array>} 餐厅列表
     */
    async getAllRestaurants() {
        try {
            const response = await this.client.get('/restaurants');
            return response.data.data;
        } catch (error) {
            console.error('获取餐厅列表错误:', error);
            return [];
        }
    }

    /**
     * 获取餐厅详情
     * @param {number} id - 餐厅ID
     * @returns {Promise<Object>} 餐厅详情
     */
    async getRestaurantById(id) {
        try {
            const response = await this.client.get(`/restaurants/${id}`);
            return response.data.data;
        } catch (error) {
            console.error('获取餐厅详情错误:', error);
            return null;
        }
    }

    /**
     * 提交用户反馈
     * @param {Object} feedback - 反馈信息
     * @returns {Promise<Object>} 反馈结果
     */
    async submitFeedback(feedback) {
        try {
            const response = await this.client.post('/feedback', feedback);
            return response.data;
        } catch (error) {
            console.error('提交反馈错误:', error);
            throw error;
        }
    }

    /**
     * 健康检查
     * @returns {Promise<boolean>} 服务是否正常
     */
    async healthCheck() {
        try {
            const response = await this.client.get('/health');
            return response.data.status === 'success';
        } catch (error) {
            console.error('健康检查失败:', error);
            return false;
        }
    }
}

// 创建全局单例
const apiService = new APIService();