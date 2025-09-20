// Mock数据 - 模拟后端接口返回的数据结构
// 在实际项目中，这些数据会通过API接口获取

// 基础配置信息
window.TravelConfig = {
    location: '上海市',
    totalDays: 7,
    startDate: '2024-01-15',
    title: '上海七日游'
};

// 路线点数据 (对应地图上的节点)
window.RoutePointsData = [
    { id: 0, x: 150, y: 100, name: '外滩', type: 'start' },
    { id: 1, x: 300, y: 200, name: '东方明珠', type: 'attraction' },
    { id: 2, x: 420, y: 180, name: '和平饭店', type: 'hotel' },
    { id: 3, x: 500, y: 150, name: '豫园', type: 'attraction' },
    { id: 4, x: 580, y: 250, name: '外滩茂悦酒店', type: 'hotel' },
    { id: 5, x: 650, y: 300, name: '田子坊', type: 'attraction' },
    { id: 6, x: 400, y: 450, name: '上海博物馆', type: 'end' }
];

// 信息卡片数据
window.CardsData = [
    // 通用卡片
    {
        id: 'weather-general',
        type: 'weather',
        title: '当前天气',
        content: '上海市晴朗，温度适宜，适合出行',
        value: '24°C',
        status: 'available',
        statusText: '晴朗',
        icon: '☀️',
        pointTypes: ['all'],
        pointId: null,
        expandedContent: {
            description: '今日天气状况良好，适宜户外活动和旅游观光。',
            details: ['湿度: 65%', '风速: 微风 2级', '紫外线: 中等', '空气质量: 良'],
            forecast: '未来24小时天气稳定，无降水',
            suggestion: '建议携带防晒用品，适量补充水分'
        }
    },
    {
        id: 'weather-forecast',
        type: 'weather',
        title: '明日天气',
        content: '多云转晴，气温22-26°C，微风',
        value: '26°C',
        status: 'available',
        statusText: '多云',
        icon: '⛅',
        pointTypes: ['all'],
        pointId: null,
        expandedContent: {
            description: '明日天气转好，适合继续旅游行程。',
            details: ['最高温度: 26°C', '最低温度: 22°C', '降水概率: 10%', '能见度: 良好'],
            forecast: '上午多云，下午转晴',
            suggestion: '早晚稍凉，建议准备薄外套'
        }
    },

    // 外滩相关卡片
    {
        id: 'bund-info',
        type: 'attraction',
        title: '外滩详情',
        content: '上海外滩，黄浦江西岸的风景线，万国建筑博览群',
        value: '免费',
        status: 'available',
        statusText: '全天开放',
        icon: '🏛️',
        pointTypes: ['attraction'],
        pointId: 0,
        expandedContent: {
            description: '外滩是上海最著名的风景线，拥有52幢风格各异的古典复兴大楼。',
            features: ['万国建筑博览群', '黄浦江江景', '历史文化街区', '夜景灯光秀'],
            openHours: '全天开放',
            transportation: '地铁2号线、10号线南京东路站',
            tips: '最佳游览时间为黄昏时分，可同时欣赏日落和夜景'
        }
    },
    {
        id: 'bund-restaurant',
        type: 'restaurant',
        title: '外滩餐厅',
        content: '外滩三号米其林餐厅，正宗法式料理',
        value: '¥680',
        status: 'available',
        statusText: '可预订',
        icon: '🍽️',
        pointTypes: ['attraction'],
        pointId: 0,
        expandedContent: {
            description: '外滩三号是一家米其林推荐餐厅，提供正宗的法式料理。',
            features: ['米其林推荐', '江景位置', '法式料理', '精致环境'],
            openHours: '11:30-14:30, 17:30-22:00',
            reservation: '建议提前预订',
            specialties: ['法式鹅肝', '波士顿龙虾', '黑松露料理']
        }
    },

    // 东方明珠相关卡片
    {
        id: 'pearl-info',
        type: 'attraction',
        title: '东方明珠',
        content: '上海地标建筑，468米高塔，观景餐厅',
        value: '¥160',
        status: 'available',
        statusText: '开放中',
        icon: '🗼',
        pointTypes: ['attraction'],
        pointId: 1
    },
    {
        id: 'pearl-restaurant',
        type: 'restaurant',
        title: '旋转餐厅',
        content: '东方明珠旋转餐厅，360度俯瞰浦江',
        value: '¥520',
        status: 'busy',
        statusText: '需预约',
        icon: '🍽️',
        pointTypes: ['attraction'],
        pointId: 1
    },

    // 和平饭店相关卡片
    {
        id: 'peace-hotel',
        type: 'hotel',
        title: '和平饭店',
        content: '历史悠久的奢华酒店，外滩核心位置',
        value: '¥1680',
        status: 'available',
        statusText: '有房',
        icon: '🏨',
        pointTypes: ['hotel'],
        pointId: 2
    },
    {
        id: 'peace-dining',
        type: 'restaurant',
        title: '和平咖啡厅',
        content: '经典英式下午茶，复古装修风格',
        value: '¥280',
        status: 'available',
        statusText: '营业中',
        icon: '☕',
        pointTypes: ['hotel'],
        pointId: 2
    },

    // 豫园相关卡片
    {
        id: 'yuyuan-info',
        type: 'attraction',
        title: '豫园景区',
        content: '明代古典园林，传统江南建筑精华',
        value: '¥40',
        status: 'available',
        statusText: '开放中',
        icon: '🏮',
        pointTypes: ['attraction'],
        pointId: 3
    },

    // 茂悦酒店相关卡片
    {
        id: 'maoyue-hotel',
        type: 'hotel',
        title: '外滩茂悦酒店',
        content: '现代化商务酒店，江景房推荐',
        value: '¥1280',
        status: 'busy',
        statusText: '紧张',
        icon: '🏨',
        pointTypes: ['hotel'],
        pointId: 4
    },

    // 田子坊相关卡片
    {
        id: 'tianzifang-info',
        type: 'attraction',
        title: '田子坊',
        content: '石库门弄堂改造的创意园区，艺术文化街区',
        value: '免费',
        status: 'available',
        statusText: '开放中',
        icon: '🎨',
        pointTypes: ['attraction'],
        pointId: 5
    },

    // 上海博物馆相关卡片
    {
        id: 'museum-info',
        type: 'attraction',
        title: '上海博物馆',
        content: '中国古代艺术珍品，青铜器、陶瓷、书画',
        value: '免费',
        status: 'available',
        statusText: '开放中',
        icon: '🏛️',
        pointTypes: ['attraction'],
        pointId: 6
    }
];

// 七天行程数据
window.ItineraryData = [
    {
        day: 1,
        date: '2024-01-15',
        title: '第一天 - 外滩历史文化之旅',
        summary: '3个景点 · 3个用餐 · 1晚住宿',
        items: [
            {
                time: '09:00',
                type: 'start',
                title: '外滩',
                description: '上海最著名的风景线，万国建筑博览群，欣赏黄浦江美景。漫步外滩，感受百年历史沉淀',
                price: '免费',
                duration: '2小时',
                icon: '🏛️'
            },
            {
                time: '11:30',
                type: 'restaurant',
                title: '外滩三号米其林餐厅',
                description: '正宗法式料理，江景用餐体验。位于历史建筑内，享受精致午餐',
                price: '¥680',
                duration: '1.5小时',
                icon: '🍽️'
            },
            {
                time: '14:00',
                type: 'attraction',
                title: '东方明珠',
                description: '上海地标建筑，468米高塔观景。登塔俯瞰浦江两岸，体验高空观光',
                price: '¥160',
                duration: '2小时',
                icon: '🗼'
            },
            {
                time: '17:00',
                type: 'restaurant',
                title: '东方明珠旋转餐厅',
                description: '360度俯瞰浦江，晚餐体验。在旋转餐厅享受日落晚餐',
                price: '¥520',
                duration: '2小时',
                icon: '🍽️'
            },
            {
                time: '20:00',
                type: 'hotel',
                title: '和平饭店',
                description: '历史悠久的奢华酒店，外滩核心位置。感受老上海的优雅与奢华',
                price: '¥1680',
                duration: '过夜',
                icon: '🏨'
            }
        ]
    },
    {
        day: 2,
        date: '2024-01-16',
        title: '第二天 - 传统文化体验',
        summary: '2个景点 · 3个用餐 · 1晚住宿',
        items: [
            {
                time: '08:30',
                type: 'restaurant',
                title: '和平咖啡厅',
                description: '经典英式下午茶，复古装修风格。在历史建筑中享受精致早餐',
                price: '¥280',
                duration: '1小时',
                icon: '☕'
            },
            {
                time: '10:30',
                type: 'attraction',
                title: '豫园景区',
                description: '明代古典园林，传统江南建筑精华。游览古典园林，体验传统文化',
                price: '¥40',
                duration: '3小时',
                icon: '🏮'
            },
            {
                time: '14:00',
                type: 'restaurant',
                title: '南翔小笼包',
                description: '豫园特色小笼包，传统上海味道。品尝正宗上海小笼包',
                price: '¥120',
                duration: '1小时',
                icon: '🥟'
            },
            {
                time: '16:00',
                type: 'attraction',
                title: '田子坊',
                description: '石库门弄堂改造的创意园区，艺术文化街区。探索艺术工作室和特色商店',
                price: '免费',
                duration: '2.5小时',
                icon: '🎨'
            },
            {
                time: '19:00',
                type: 'restaurant',
                title: '田子坊创意餐厅',
                description: '融合菜系，艺术氛围浓厚。在创意餐厅享受晚餐',
                price: '¥320',
                duration: '1.5小时',
                icon: '🍴'
            },
            {
                time: '21:00',
                type: 'hotel',
                title: '外滩茂悦酒店',
                description: '现代化商务酒店，江景房推荐。享受现代舒适的住宿体验',
                price: '¥1280',
                duration: '过夜',
                icon: '🏨'
            }
        ]
    },
    {
        day: 3,
        date: '2024-01-17',
        title: '第三天 - 文化艺术之旅',
        summary: '2个景点 · 2个用餐',
        items: [
            {
                time: '09:00',
                type: 'restaurant',
                title: '酒店自助早餐',
                description: '丰富的中西式早餐，江景用餐。在江景餐厅享受丰盛早餐',
                price: '¥180',
                duration: '1小时',
                icon: '🍳'
            },
            {
                time: '10:30',
                type: 'attraction',
                title: '上海博物馆',
                description: '中国古代艺术珍品，青铜器、陶瓷、书画收藏。深度了解中华文明',
                price: '免费',
                duration: '3小时',
                icon: '🏛️'
            },
            {
                time: '14:30',
                type: 'restaurant',
                title: '博物馆咖啡厅',
                description: '文化主题餐厅，简餐轻食。在文化氛围中享受午后时光',
                price: '¥150',
                duration: '1小时',
                icon: '☕'
            },
            {
                time: '16:00',
                type: 'attraction',
                title: '新天地',
                description: '石库门建筑群改造的时尚街区。体验传统与现代完美融合',
                price: '免费',
                duration: '2小时',
                icon: '🏪'
            }
        ]
    },
    {
        day: 4,
        date: '2024-01-18',
        title: '第四天 - 现代都市探索',
        summary: '3个景点 · 3个用餐 · 1晚住宿',
        items: [
            {
                time: '09:30',
                type: 'attraction',
                title: '陆家嘴金融区',
                description: '现代摩天大楼群，金融中心地标。感受上海现代化发展成就',
                price: '免费',
                duration: '1.5小时',
                icon: '🏢'
            },
            {
                time: '11:30',
                type: 'restaurant',
                title: '环球金融中心观景餐厅',
                description: '高空景观餐厅，俯瞰整个上海。在云端享受精致午餐',
                price: '¥850',
                duration: '2小时',
                icon: '🌆'
            },
            {
                time: '14:00',
                type: 'attraction',
                title: '上海科技馆',
                description: '现代科技展览馆，互动体验丰富。探索科技的魅力和未来',
                price: '¥60',
                duration: '3小时',
                icon: '🔬'
            },
            {
                time: '17:30',
                type: 'attraction',
                title: '世纪公园',
                description: '大型城市公园，自然风光优美。在城市绿洲中放松身心',
                price: '¥10',
                duration: '1.5小时',
                icon: '🌳'
            },
            {
                time: '19:30',
                type: 'restaurant',
                title: '日式料理店',
                description: '正宗日式料理，新鲜刺身寿司。品味精致的日式美食',
                price: '¥480',
                duration: '1.5小时',
                icon: '🍣'
            },
            {
                time: '21:30',
                type: 'hotel',
                title: '浦东香格里拉',
                description: '豪华五星酒店，江景套房。享受奢华舒适的住宿体验',
                price: '¥2200',
                duration: '过夜',
                icon: '🏨'
            }
        ]
    },
    {
        day: 5,
        date: '2024-01-19',
        title: '第五天 - 购物娱乐之旅',
        summary: '2个景点 · 3个用餐 · 1个娱乐',
        items: [
            {
                time: '10:00',
                type: 'attraction',
                title: '南京路步行街',
                description: '中华商业第一街，购物天堂。体验上海最繁华的商业街区',
                price: '免费',
                duration: '2.5小时',
                icon: '🛍️'
            },
            {
                time: '12:30',
                type: 'restaurant',
                title: '老上海茶餐厅',
                description: '传统上海菜，怀旧装修风格。品尝地道的上海本帮菜',
                price: '¥220',
                duration: '1小时',
                icon: '🥘'
            },
            {
                time: '14:30',
                type: 'attraction',
                title: '淮海路商业街',
                description: '时尚购物街区，国际品牌汇集。享受高端购物体验',
                price: '免费',
                duration: '2小时',
                icon: '👗'
            },
            {
                time: '17:00',
                type: 'restaurant',
                title: '法式甜品店',
                description: '精致法式甜品，下午茶时光。享受浪漫的法式下午茶',
                price: '¥180',
                duration: '1小时',
                icon: '🧁'
            },
            {
                time: '19:00',
                type: 'restaurant',
                title: '意大利餐厅',
                description: '正宗意式料理，浪漫用餐环境。品味地道的意大利风味',
                price: '¥420',
                duration: '2小时',
                icon: '🍝'
            },
            {
                time: '21:30',
                type: 'attraction',
                title: '黄浦江夜游',
                description: '游船夜游，欣赏两岸灯火辉煌。在江上观赏上海夜景',
                price: '¥150',
                duration: '1.5小时',
                icon: '🚢'
            }
        ]
    },
    {
        day: 6,
        date: '2024-01-20',
        title: '第六天 - 自然文化体验',
        summary: '3个景点 · 2个用餐 · 1晚住宿',
        items: [
            {
                time: '08:30',
                type: 'attraction',
                title: '朱家角古镇',
                description: '江南水乡古镇，千年历史文化。体验江南水乡的古朴魅力',
                price: '¥80',
                duration: '4小时',
                icon: '🏘️'
            },
            {
                time: '13:00',
                type: 'restaurant',
                title: '古镇特色餐厅',
                description: '江南水乡菜系，古色古香环境。在古镇品尝传统江南美食',
                price: '¥180',
                duration: '1小时',
                icon: '🦆'
            },
            {
                time: '15:00',
                type: 'attraction',
                title: '大观园',
                description: '红楼梦主题园林，古典建筑群。走进红楼梦的诗意世界',
                price: '¥60',
                duration: '2小时',
                icon: '🏯'
            },
            {
                time: '17:30',
                type: 'attraction',
                title: '辰山植物园',
                description: '大型植物园，四季花卉展示。在植物王国中享受自然之美',
                price: '¥60',
                duration: '2小时',
                icon: '🌺'
            },
            {
                time: '20:00',
                type: 'restaurant',
                title: '农家乐餐厅',
                description: '生态农家菜，绿色健康美食。品尝新鲜有机的农家美味',
                price: '¥160',
                duration: '1.5小时',
                icon: '🌽'
            },
            {
                time: '22:00',
                type: 'hotel',
                title: '度假村酒店',
                description: '生态度假村，自然环境优美。在自然怀抱中享受宁静夜晚',
                price: '¥980',
                duration: '过夜',
                icon: '🏡'
            }
        ]
    },
    {
        day: 7,
        date: '2024-01-21',
        title: '第七天 - 告别上海',
        summary: '1个景点 · 2个用餐 · 购物纪念',
        items: [
            {
                time: '09:00',
                type: 'restaurant',
                title: '度假村早餐',
                description: '健康有机早餐，田园风味。在自然环境中享受最后一顿早餐',
                price: '¥120',
                duration: '1小时',
                icon: '🥞'
            },
            {
                time: '10:30',
                type: 'attraction',
                title: '城隍庙',
                description: '传统庙宇建筑，祈福文化体验。感受上海传统宗教文化',
                price: '¥10',
                duration: '1.5小时',
                icon: '⛩️'
            },
            {
                time: '12:30',
                type: 'restaurant',
                title: '城隍庙小吃街',
                description: '上海传统小吃汇聚，美食天堂。品尝各种上海特色小吃',
                price: '¥80',
                duration: '1小时',
                icon: '🍡'
            },
            {
                time: '14:00',
                type: 'attraction',
                title: '特产购物',
                description: '购买上海特产纪念品，留住美好回忆。为亲友选购伴手礼',
                price: '¥300',
                duration: '2小时',
                icon: '🎁'
            },
            {
                time: '16:30',
                type: 'end',
                title: '返程准备',
                description: '整理行李，前往机场或车站。结束美好的上海七日之旅',
                price: '交通费',
                duration: '告别',
                icon: '✈️'
            }
        ]
    }
];

// 数据更新事件系统
window.DataEvents = {
    listeners: {},

    // 添加事件监听
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    },

    // 触发事件
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
        // 也触发全局数据变化事件
        if (event !== 'dataChanged') {
            this.emit('dataChanged', { type: event, data });
        }
    },

    // 移除事件监听
    off(event, callback) {
        if (this.listeners[event]) {
            const index = this.listeners[event].indexOf(callback);
            if (index > -1) {
                this.listeners[event].splice(index, 1);
            }
        }
    }
};

// 数据变化追踪
window.DataTracker = {
    lastUpdate: Date.now(),
    changeLog: [],

    // 记录数据变化
    logChange(type, action, data) {
        this.changeLog.push({
            timestamp: Date.now(),
            type,
            action,
            data: JSON.parse(JSON.stringify(data))
        });
        this.lastUpdate = Date.now();

        // 只保留最近50条记录
        if (this.changeLog.length > 50) {
            this.changeLog = this.changeLog.slice(-50);
        }
    },

    // 获取最近的变化
    getRecentChanges(since = 0) {
        return this.changeLog.filter(change => change.timestamp > since);
    }
};

// API模拟函数 - 模拟后端接口
window.TravelAPI = {
    // 获取基础配置
    getConfig() {
        return Promise.resolve(window.TravelConfig);
    },

    // 获取路线点数据
    getRoutePoints() {
        return Promise.resolve(window.RoutePointsData);
    },

    // 获取卡片数据
    getCards() {
        return Promise.resolve(window.CardsData);
    },

    // 获取行程数据
    getItinerary() {
        return Promise.resolve(window.ItineraryData);
    },

    // 更新配置
    updateConfig(newConfig) {
        const oldConfig = JSON.parse(JSON.stringify(window.TravelConfig));
        Object.assign(window.TravelConfig, newConfig);
        window.DataTracker.logChange('config', 'update', { old: oldConfig, new: window.TravelConfig });
        window.DataEvents.emit('configUpdated', window.TravelConfig);
        return Promise.resolve(window.TravelConfig);
    },

    // 更新路线点
    updateRoutePoints(newPoints) {
        const oldPoints = JSON.parse(JSON.stringify(window.RoutePointsData));
        window.RoutePointsData = newPoints;
        window.DataTracker.logChange('routePoints', 'update', { old: oldPoints, new: window.RoutePointsData });
        window.DataEvents.emit('routePointsUpdated', window.RoutePointsData);
        return Promise.resolve(window.RoutePointsData);
    },

    // 更新卡片数据
    updateCards(newCards) {
        const oldCards = JSON.parse(JSON.stringify(window.CardsData));
        window.CardsData = newCards;
        window.DataTracker.logChange('cards', 'update', { old: oldCards, new: window.CardsData });
        window.DataEvents.emit('cardsUpdated', window.CardsData);
        return Promise.resolve(window.CardsData);
    },

    // 更新行程数据
    updateItinerary(newItinerary) {
        const oldItinerary = JSON.parse(JSON.stringify(window.ItineraryData));
        window.ItineraryData = newItinerary;
        window.DataTracker.logChange('itinerary', 'update', { old: oldItinerary, new: window.ItineraryData });
        window.DataEvents.emit('itineraryUpdated', window.ItineraryData);
        return Promise.resolve(window.ItineraryData);
    },

    // 添加新的路线点
    addRoutePoint(point) {
        const newId = Math.max(...window.RoutePointsData.map(p => p.id)) + 1;
        const newPoint = { ...point, id: newId };
        window.RoutePointsData.push(newPoint);
        window.DataTracker.logChange('routePoints', 'add', newPoint);
        window.DataEvents.emit('routePointAdded', newPoint);
        window.DataEvents.emit('routePointsUpdated', window.RoutePointsData);
        return Promise.resolve(newPoint);
    },

    // 删除路线点
    removeRoutePoint(pointId) {
        const index = window.RoutePointsData.findIndex(p => p.id === pointId);
        if (index > -1) {
            const removedPoint = window.RoutePointsData.splice(index, 1)[0];
            window.DataTracker.logChange('routePoints', 'remove', removedPoint);
            window.DataEvents.emit('routePointRemoved', removedPoint);
            window.DataEvents.emit('routePointsUpdated', window.RoutePointsData);
            return Promise.resolve(removedPoint);
        }
        return Promise.reject(new Error('Point not found'));
    },

    // 获取数据变化历史
    getChangeHistory(since = 0) {
        return Promise.resolve(window.DataTracker.getRecentChanges(since));
    },

    // 获取最后更新时间
    getLastUpdateTime() {
        return Promise.resolve(window.DataTracker.lastUpdate);
    }
};

// 控制台输出，方便调试
console.log('Mock数据已加载');
console.log('可用的全局变量：');
console.log('- TravelConfig:', window.TravelConfig);
console.log('- RoutePointsData:', window.RoutePointsData);
console.log('- CardsData:', window.CardsData.length, '条卡片数据');
console.log('- ItineraryData:', window.ItineraryData.length, '天行程数据');
console.log('- TravelAPI: 模拟API接口');
console.log('- DataEvents: 数据更新事件系统');