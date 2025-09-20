class TravelAssistant {
    constructor() {
        this.routePoints = [];
        this.satellitePoints = [];
        this.currentPointId = 0;
        this.currentSatelliteId = 0;
        this.isLightTheme = false;
        this.cards = [];
        this.allCardsData = []; // 存储所有卡片数据
        this.selectedPointId = null; // 当前选中的节点ID
        this.itineraryData = []; // 按日程组织的行程数据
        this.currentSlide = 0; // 当前显示的日程
        this.config = {}; // 应用配置
        this.websocket = null; // WebSocket连接
        this.isConnected = false; // 连接状态
        this.messageIdMap = new Map(); // 消息ID映射，用于更新现有消息
        this.init();
    }

    async init() {
        this.loadThemePreference();
        this.updateTime();
        this.setupEventListeners();

        // 初始化WebSocket连接
        this.initWebSocket();

        // 从mock数据加载初始数据
        await this.loadInitialData();

        // 设置数据更新监听
        this.setupDataListeners();

        // 启动实时数据同步
        this.startDataSync();

        setInterval(() => this.updateTime(), 1000);
    }

    // 初始化WebSocket连接
    initWebSocket() {
        try {
            this.websocket = new WebSocket('ws://localhost:9001');

            this.websocket.onopen = (event) => {
                console.log('WebSocket连接已建立');
                this.isConnected = true;
                this.updateConnectionStatus();
                this.addChatMessage('已连接到智能助手服务', 'assistant');
                // 清理之前的消息ID映射，开始新的会话
                this.messageIdMap.clear();
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('处理WebSocket消息失败:', error);
                    this.addChatMessage('收到无效消息格式', 'assistant');
                }
            };

            this.websocket.onclose = (event) => {
                console.log('WebSocket连接已关闭', event.code, event.reason);
                this.isConnected = false;
                this.updateConnectionStatus();

                if (!event.wasClean) {
                    this.addChatMessage('与助手连接中断，尝试重连中...', 'assistant');
                    // 5秒后重连
                    setTimeout(() => this.initWebSocket(), 5000);
                }
            };

            this.websocket.onerror = (event) => {
                console.error('WebSocket连接错误:', event);
                this.isConnected = false;
                this.updateConnectionStatus();
                this.addChatMessage('连接助手服务失败，请检查服务是否启动', 'assistant');
            };

        } catch (error) {
            console.error('初始化WebSocket失败:', error);
            this.addChatMessage('无法连接到助手服务', 'assistant');
        }
    }

    // 处理WebSocket消息
    handleWebSocketMessage(data) {
        console.log('收到WebSocket消息:', data);

        // 处理带ID的消息（来自Agent的流式输出）
        if (data.id) {
            this.handleAgentMessage(data);
            return;
        }

        // 处理传统的系统消息类型
        switch (data.type) {
            case 'assistant_message':
            case 'assistant_response':
                this.addChatMessage(data.content, 'assistant');
                break;
            case 'user_message':
                // 用户消息已经在发送时显示，这里不重复显示
                break;
            case 'system':
            case 'system_message':
                this.addChatMessage(data.content, 'assistant');
                break;
            case 'error':
                this.addChatMessage(`错误: ${data.content}`, 'assistant');
                break;
            case 'progress_update':
                this.addChatMessage(data.content, 'assistant');
                break;
            default:
                console.log('未知消息类型:', data.type);
                this.addChatMessage(data.content || '收到消息', 'assistant');
        }
    }

    // 更新连接状态显示
    updateConnectionStatus() {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.chat-status span:last-child');

        if (this.isConnected) {
            statusDot.className = 'status-dot online';
            statusText.textContent = '在线';
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = '离线';
        }
    }

    // 发送WebSocket消息
    sendWebSocketMessage(content) {
        if (!this.isConnected || !this.websocket) {
            this.addChatMessage('未连接到助手服务，无法发送消息', 'assistant');
            return false;
        }

        try {
            const message = {
                type: "user_input",
                content: content
            };

            this.websocket.send(JSON.stringify(message));
            console.log('发送WebSocket消息:', message);
            return true;
        } catch (error) {
            console.error('发送WebSocket消息失败:', error);
            this.addChatMessage('发送消息失败', 'assistant');
            return false;
        }
    }

    // 加载初始数据
    async loadInitialData() {
        try {
            // 并行加载所有数据
            const [config, routePoints, cards, itinerary] = await Promise.all([
                window.TravelAPI.getConfig(),
                window.TravelAPI.getRoutePoints(),
                window.TravelAPI.getCards(),
                window.TravelAPI.getItinerary()
            ]);

            this.config = config;
            this.routePoints = routePoints.map(point => ({
                ...point,
                id: this.currentPointId++
            }));
            this.allCardsData = cards;
            this.itineraryData = itinerary;

            // 更新页面内容
            this.updateAppTitle();
            this.updateLocationDisplay();
            this.updateCardsDisplay();
            this.updateRouteDisplay();
            this.updateRouteInfo();
            this.generateSatellitePoints();
            this.renderSatellitePoints();

            console.log('初始数据加载完成:', {
                config: this.config,
                routePoints: this.routePoints.length,
                cards: this.allCardsData.length,
                itinerary: this.itineraryData.length
            });
        } catch (error) {
            console.error('加载初始数据失败:', error);
            this.addChatMessage('数据加载失败，请刷新页面重试', 'assistant');
        }
    }

    // 设置数据更新监听
    setupDataListeners() {
        // 监听配置更新
        window.DataEvents.on('configUpdated', (newConfig) => {
            this.config = newConfig;
            this.updateAppTitle();
            this.updateLocationDisplay();
            this.addChatMessage('配置已更新', 'assistant');
        });

        // 监听路线点更新
        window.DataEvents.on('routePointsUpdated', (newPoints) => {
            this.routePoints = newPoints;
            this.updateRouteDisplay();
            this.updateRouteInfo();
            this.generateSatellitePoints();
            this.renderSatellitePoints();
            this.addChatMessage('路线已更新', 'assistant');
        });

        // 监听卡片更新
        window.DataEvents.on('cardsUpdated', (newCards) => {
            this.allCardsData = newCards;
            this.updateCardsDisplay(this.selectedPointId);
            this.addChatMessage('信息卡片已更新', 'assistant');
        });

        // 监听行程更新
        window.DataEvents.on('itineraryUpdated', (newItinerary) => {
            this.itineraryData = newItinerary;
            this.addChatMessage('行程安排已更新', 'assistant');
        });

        // 监听路线点添加
        window.DataEvents.on('routePointAdded', (newPoint) => {
            this.addChatMessage(`已添加新${this.getPointTypeText(newPoint.type)}：${newPoint.name}`, 'assistant');
        });

        // 监听路线点删除
        window.DataEvents.on('routePointRemoved', (removedPoint) => {
            this.addChatMessage(`已删除${this.getPointTypeText(removedPoint.type)}：${removedPoint.name}`, 'assistant');
        });

        // 监听全局数据变化事件
        window.DataEvents.on('dataChanged', (changeInfo) => {
            console.log('数据变化检测:', changeInfo);
            // 可以在这里添加全局数据变化的处理逻辑
            // 比如显示变化通知、记录操作日志等
        });
    }

    // 更新应用标题
    updateAppTitle() {
        const titleElement = document.querySelector('.header-left h1');
        if (titleElement && this.config.title) {
            titleElement.textContent = this.config.title;
        }
    }

    // 更新位置显示
    updateLocationDisplay() {
        const locationElement = document.querySelector('.location');
        if (locationElement && this.config.location) {
            locationElement.textContent = `当前位置：${this.config.location}`;
        }
    }

    updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        document.getElementById('current-time').textContent = timeString;
    }

    setupEventListeners() {
        // 主题切换按钮
        const themeToggle = document.getElementById('theme-toggle');
        themeToggle.addEventListener('click', () => {
            this.toggleTheme();
        });

        // 总览按钮
        const overviewBtn = document.getElementById('overview-btn');
        overviewBtn.addEventListener('click', () => {
            this.showOverviewPopup();
        });

        // 弹窗关闭事件
        const popupClose = document.getElementById('popup-close');
        const popupOverlay = document.getElementById('popup-overlay');

        popupClose.addEventListener('click', () => {
            this.hideOverviewPopup();
        });

        popupOverlay.addEventListener('click', () => {
            this.hideOverviewPopup();
        });

        // 卡片刷新按钮
        const cardsRefresh = document.getElementById('cards-refresh');
        cardsRefresh.addEventListener('click', () => {
            this.refreshCards();
        });

        // 聊天输入事件
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');

        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        // 快捷操作按钮
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                this.handleQuickAction(action);
            });
        });

        // 规划控制按钮
        document.getElementById('add-point').addEventListener('click', () => {
            this.addRoutePoint();
        });

        document.getElementById('add-hotel').addEventListener('click', () => {
            this.addHotelPoint();
        });

        document.getElementById('optimize-route').addEventListener('click', () => {
            this.optimizeRoute();
        });

        // SVG点击事件（添加景点或酒店）
        document.getElementById('route-canvas').addEventListener('click', (e) => {
            const rect = e.target.getBoundingClientRect();
            const svg = document.getElementById('route-canvas');
            const viewBox = svg.viewBox.baseVal;

            const x = (e.clientX - rect.left) / rect.width * viewBox.width;
            const y = (e.clientY - rect.top) / rect.height * viewBox.height;

            // 按住Shift键添加酒店，否则添加景点
            const type = e.shiftKey ? 'hotel' : 'attraction';
            this.addRoutePointAt(x, y, type);
        });
    }

    sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (message) {
            this.addChatMessage(message, 'user');
            input.value = '';

            // 发送到WebSocket服务
            const sent = this.sendWebSocketMessage(message);

            // 如果WebSocket发送失败，回退到模拟AI回复
            if (!sent) {
                setTimeout(() => {
                    this.handleAIResponse(message);
                }, 1000);
            }
        }
    }

    addChatMessage(text, sender = 'assistant', messageId = null) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        // 如果有messageId，添加到DOM元素用于后续更新
        if (messageId) {
            messageDiv.setAttribute('data-message-id', messageId);
        }

        const currentTime = new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <div class="avatar-icon">${sender === 'user' ? '👤' : '🤖'}</div>
            </div>
            <div class="message-content">
                <div class="message-text">${text}</div>
                <div class="message-time">${currentTime}</div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // 如果有messageId，将DOM元素映射存储
        if (messageId) {
            this.messageIdMap.set(messageId, messageDiv);
        }
    }

    // 处理Agent消息（带ID的流式消息）
    handleAgentMessage(data) {
        const messageId = data.id;
        const agentName = data.name || 'Agent';

        console.log(`处理Agent消息 ID: ${messageId}, 来自: ${agentName}`);

        // 提取和格式化消息内容
        const formattedContent = this.formatAgentContent(data.content, agentName);

        // 检查是否已存在相同ID的消息
        if (this.messageIdMap.has(messageId)) {
            // 更新现有消息
            console.log(`更新现有消息 ID: ${messageId}`);
            this.updateChatMessageContent(messageId, formattedContent, data.timestamp);
        } else {
            // 创建新消息
            console.log(`创建新消息 ID: ${messageId}`);
            this.addChatMessageWithContent(formattedContent, 'assistant', messageId);
        }
    }

    // 格式化Agent消息内容，处理不同类型的content
    formatAgentContent(content, agentName) {
        if (!content || !Array.isArray(content)) {
            return typeof content === 'string' ? content : '';
        }

        let formattedParts = [];

        content.forEach(item => {
            switch (item.type) {
                case 'text':
                    if (item.text && item.text.trim()) {
                        formattedParts.push({
                            type: 'text',
                            content: item.text
                        });
                    }
                    break;

                case 'tool_use':
                    formattedParts.push({
                        type: 'tool_use',
                        content: `🔧 正在调用工具: ${item.name}`,
                        details: {
                            name: item.name,
                            id: item.id,
                            input: item.input
                        }
                    });
                    break;

                case 'tool_result':
                    // 提取工具结果的文本内容
                    let resultText = '';
                    if (item.output && Array.isArray(item.output)) {
                        resultText = item.output
                            .filter(output => output.type === 'text')
                            .map(output => output.text)
                            .join('');
                    }

                    formattedParts.push({
                        type: 'tool_result',
                        content: `✅ 工具调用完成: ${item.name}`,
                        details: {
                            name: item.name,
                            id: item.id,
                            resultText: resultText.length > 200 ? resultText.substring(0, 200) + '...' : resultText,
                            fullResult: resultText
                        }
                    });
                    break;

                default:
                    console.log('未知内容类型:', item.type);
            }
        });

        return formattedParts;
    }

    // 添加带格式化内容的聊天消息
    addChatMessageWithContent(formattedContent, sender = 'assistant', messageId = null) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        // 如果有messageId，添加到DOM元素用于后续更新
        if (messageId) {
            messageDiv.setAttribute('data-message-id', messageId);
        }

        const currentTime = new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });

        // 构建消息内容HTML
        const messageContentHtml = this.buildMessageContentHtml(formattedContent);

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <div class="avatar-icon">${sender === 'user' ? '👤' : '🤖'}</div>
            </div>
            <div class="message-content">
                <div class="message-text">${messageContentHtml}</div>
                <div class="message-time">${currentTime}</div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // 如果有messageId，将DOM元素映射存储
        if (messageId) {
            this.messageIdMap.set(messageId, messageDiv);
        }

        // 设置工具调用的展开/折叠事件
        this.setupToolToggleEvents(messageDiv);
    }

    // 构建消息内容HTML
    buildMessageContentHtml(formattedContent) {
        if (typeof formattedContent === 'string') {
            return formattedContent;
        }

        if (!Array.isArray(formattedContent)) {
            return '';
        }

        let html = '';
        formattedContent.forEach((part, index) => {
            switch (part.type) {
                case 'text':
                    html += `<div class="text-content">${part.content}</div>`;
                    break;

                case 'tool_use':
                    html += `
                        <div class="tool-call tool-use" data-tool-id="${part.details.id}">
                            <div class="tool-header" onclick="toggleToolDetails(this)">
                                <span class="tool-icon">🔧</span>
                                <span class="tool-summary">${part.content}</span>
                                <span class="tool-toggle">▼</span>
                            </div>
                            <div class="tool-details" style="display: none;">
                                <div class="tool-detail-item">
                                    <strong>工具名称:</strong> ${part.details.name}
                                </div>
                                <div class="tool-detail-item">
                                    <strong>调用ID:</strong> ${part.details.id}
                                </div>
                                <div class="tool-detail-item">
                                    <strong>输入参数:</strong>
                                    <pre class="tool-input">${JSON.stringify(part.details.input, null, 2)}</pre>
                                </div>
                            </div>
                        </div>
                    `;
                    break;

                case 'tool_result':
                    html += `
                        <div class="tool-call tool-result" data-tool-id="${part.details.id}">
                            <div class="tool-header" onclick="toggleToolDetails(this)">
                                <span class="tool-icon">✅</span>
                                <span class="tool-summary">${part.content}</span>
                                <span class="tool-toggle">▼</span>
                            </div>
                            <div class="tool-details" style="display: none;">
                                <div class="tool-detail-item">
                                    <strong>工具名称:</strong> ${part.details.name}
                                </div>
                                <div class="tool-detail-item">
                                    <strong>结果ID:</strong> ${part.details.id}
                                </div>
                                <div class="tool-detail-item">
                                    <strong>结果预览:</strong>
                                    <div class="tool-result-preview">${part.details.resultText}</div>
                                </div>
                                ${part.details.fullResult.length > 200 ? `
                                    <div class="tool-detail-item">
                                        <button class="tool-expand-btn" onclick="showFullResult(this)"
                                                data-full-result="${encodeURIComponent(part.details.fullResult)}">
                                            查看完整结果
                                        </button>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                    break;
            }
        });

        return html;
    }

    // 更新现有消息的格式化内容
    updateChatMessageContent(messageId, formattedContent, timestamp = null) {
        const messageElement = this.messageIdMap.get(messageId);
        if (!messageElement) {
            console.warn(`未找到ID为 ${messageId} 的消息元素`);
            return;
        }

        // 更新消息文本内容
        const messageTextElement = messageElement.querySelector('.message-text');
        if (messageTextElement) {
            const newContentHtml = this.buildMessageContentHtml(formattedContent);
            messageTextElement.innerHTML = newContentHtml;
        }

        // 更新时间戳（如果提供）
        if (timestamp) {
            const messageTimeElement = messageElement.querySelector('.message-time');
            if (messageTimeElement) {
                const time = new Date(timestamp).toLocaleTimeString('zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
                messageTimeElement.textContent = time;
            }
        }

        // 重新设置工具调用的展开/折叠事件
        this.setupToolToggleEvents(messageElement);

        // 滚动到最新位置
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // 设置工具调用的展开/折叠事件
    setupToolToggleEvents(messageElement) {
        // 这个方法为工具调用设置事件监听器
        // 实际的切换逻辑通过全局函数实现，因为HTML onclick需要全局函数
    }


    handleAIResponse(userMessage) {
        const responses = {
            '推荐景点': '根据您的位置，我推荐以下景点：外滩、东方明珠、豫园、田子坊。这些都是上海的经典景点，适合一日游。',
            '查看天气': '今天上海天气晴朗，温度22-28°C，适合出行。建议准备防晒用品。',
            '路况信息': '当前主要道路畅通，预计到达各景点无明显拥堵。建议避开晚高峰时段17:00-19:00。',
            '规划路线': '我已为您规划了最优路线，总行程约50公里，预计需要6小时。请查看左侧地图。'
        };

        let response = '我理解了您的需求。';

        // 简单的关键词匹配
        if (userMessage.includes('景点') || userMessage.includes('推荐')) {
            response = responses['推荐景点'];
        } else if (userMessage.includes('天气')) {
            response = responses['查看天气'];
        } else if (userMessage.includes('路况') || userMessage.includes('交通')) {
            response = responses['路况信息'];
        } else if (userMessage.includes('规划') || userMessage.includes('路线')) {
            response = responses['规划路线'];
        } else {
            response = `关于"${userMessage}"，我建议您可以通过快捷按钮获取推荐景点、天气和路况信息。如需具体帮助，请详细描述您的需求。`;
        }

        this.addChatMessage(response, 'assistant');
    }

    handleQuickAction(action) {
        const actionTexts = {
            'recommend': '推荐景点',
            'weather': '查看天气',
            'traffic': '路况信息',
            'deviation': '路线偏离',
            'alternative': '换个其他景点',
            'delay': '休息了4小时来不及去了'
        };

        const actionText = actionTexts[action] || action;
        this.addChatMessage(actionText, 'user');

        // 优先通过WebSocket发送
        const sent = this.sendWebSocketMessage(actionText);

        // 如果WebSocket发送失败，回退到模拟AI回复
        if (!sent) {
            setTimeout(() => {
                this.handleAIResponse(actionText);
            }, 500);
        }
    }

    // 刷新卡片数据
    async refreshCards() {
        try {
            // 重新获取卡片数据
            const newCards = await window.TravelAPI.getCards();

            // 模拟刷新数据 - 更新时间戳
            newCards.forEach(card => {
                card.time = this.getCurrentTime();

                // 随机更新一些数据
                if (card.type === 'weather') {
                    const temps = ['22°C', '24°C', '26°C', '28°C'];
                    card.value = temps[Math.floor(Math.random() * temps.length)];
                } else if (card.type === 'hotel') {
                    const statuses = ['available', 'busy'];
                    const statusTexts = ['有房', '紧张'];
                    const randomIndex = Math.floor(Math.random() * statuses.length);
                    card.status = statuses[randomIndex];
                    card.statusText = statusTexts[randomIndex];
                }
            });

            // 更新数据
            await window.TravelAPI.updateCards(newCards);
            this.addChatMessage('信息已刷新', 'assistant');
        } catch (error) {
            console.error('刷新卡片失败:', error);
            this.addChatMessage('刷新失败，请重试', 'assistant');
        }
    }

    // 实时数据同步 - 基于变化追踪的高效同步
    startDataSync() {
        let lastSyncTime = Date.now();

        // 每10秒检查数据变化（轻量级检查）
        setInterval(async () => {
            try {
                // 首先检查是否有新的数据变化
                const lastUpdateTime = await window.TravelAPI.getLastUpdateTime();

                if (lastUpdateTime > lastSyncTime) {
                    // 有新变化，获取变化历史
                    const changes = await window.TravelAPI.getChangeHistory(lastSyncTime);

                    if (changes.length > 0) {
                        console.log(`检测到 ${changes.length} 个数据变化:`, changes);

                        // 根据变化类型重新获取对应数据
                        const changeTypes = [...new Set(changes.map(c => c.type))];

                        for (const type of changeTypes) {
                            switch (type) {
                                case 'config':
                                    const config = await window.TravelAPI.getConfig();
                                    if (JSON.stringify(this.config) !== JSON.stringify(config)) {
                                        this.config = config;
                                        this.updateAppTitle();
                                        this.updateLocationDisplay();
                                    }
                                    break;

                                case 'routePoints':
                                    const routePoints = await window.TravelAPI.getRoutePoints();
                                    if (JSON.stringify(this.routePoints) !== JSON.stringify(routePoints)) {
                                        this.routePoints = routePoints;
                                        this.updateRouteDisplay();
                                        this.updateRouteInfo();
                                        this.generateSatellitePoints();
                                        this.renderSatellitePoints();
                                    }
                                    break;

                                case 'cards':
                                    const cards = await window.TravelAPI.getCards();
                                    if (JSON.stringify(this.allCardsData) !== JSON.stringify(cards)) {
                                        this.allCardsData = cards;
                                        this.updateCardsDisplay(this.selectedPointId);
                                    }
                                    break;

                                case 'itinerary':
                                    const itinerary = await window.TravelAPI.getItinerary();
                                    if (JSON.stringify(this.itineraryData) !== JSON.stringify(itinerary)) {
                                        this.itineraryData = itinerary;
                                    }
                                    break;
                            }
                        }

                        lastSyncTime = Date.now();
                    }
                }
            } catch (error) {
                console.error('数据同步失败:', error);
            }
        }, 10000); // 10秒检查一次
    }

    addRoutePoint() {
        const canvas = document.getElementById('route-canvas');
        const viewBox = canvas.viewBox.baseVal;

        // 随机位置添加景点
        const x = Math.random() * (viewBox.width - 100) + 50;
        const y = Math.random() * (viewBox.height - 100) + 50;

        this.addRoutePointAt(x, y, 'attraction');
    }

    addHotelPoint() {
        const canvas = document.getElementById('route-canvas');
        const viewBox = canvas.viewBox.baseVal;

        // 随机位置添加酒店
        const x = Math.random() * (viewBox.width - 100) + 50;
        const y = Math.random() * (viewBox.height - 100) + 50;

        this.addHotelPointAt(x, y);
    }

    async addRoutePointAt(x, y, type = 'attraction') {
        const pointName = type === 'hotel' ? `酒店${this.getHotelCount() + 1}` : `景点${this.getAttractionCount() + 1}`;

        const newPoint = {
            x: x,
            y: y,
            name: pointName,
            type: type
        };

        try {
            // 通过API添加路线点
            await window.TravelAPI.addRoutePoint(newPoint);
            // 事件监听器会自动更新页面
        } catch (error) {
            console.error('添加路线点失败:', error);
            this.addChatMessage('添加路线点失败，请重试', 'assistant');
        }
    }

    async addHotelPointAt(x, y) {
        await this.addRoutePointAt(x, y, 'hotel');
    }

    getAttractionCount() {
        return this.routePoints.filter(point => point.type === 'attraction').length;
    }

    getHotelCount() {
        return this.routePoints.filter(point => point.type === 'hotel').length;
    }

    updateRouteDisplay() {
        const pointsGroup = document.getElementById('route-points');
        const linesGroup = document.getElementById('route-lines');
        const satelliteGroup = document.getElementById('satellite-points');

        // 清空现有元素
        pointsGroup.innerHTML = '';
        linesGroup.innerHTML = '';
        satelliteGroup.innerHTML = '';

        // 绘制连接线（只连接主要路线节点，不包含卫星节点）
        const mainRoutePoints = this.routePoints.filter(point =>
            point.type !== 'satellite' && point.type !== 'restaurant'
        );

        for (let i = 0; i < mainRoutePoints.length - 1; i++) {
            const current = mainRoutePoints[i];
            const next = mainRoutePoints[i + 1];

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            line.setAttribute('class', 'route-line');
            line.setAttribute('d', `M ${current.x} ${current.y} L ${next.x} ${next.y}`);
            linesGroup.appendChild(line);
        }

        // 绘制主要节点
        this.routePoints.forEach((point, index) => {
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', `route-point ${point.type}`);
            group.setAttribute('data-id', point.id);

            // 节点圆圈
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', point.x);
            circle.setAttribute('cy', point.y);
            circle.setAttribute('r', point.type === 'start' || point.type === 'end' ? 20 : 15);

            // 节点编号或图标
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', point.x);
            text.setAttribute('y', point.y);

            // 根据节点类型显示不同内容
            if (point.type === 'hotel') {
                text.textContent = 'H';
                text.setAttribute('font-size', '14');
                text.setAttribute('font-weight', 'bold');
            } else {
                text.textContent = index + 1;
            }

            // 节点名称标签
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', point.x);
            label.setAttribute('y', point.y - 25);
            label.setAttribute('text-anchor', 'middle');
            label.setAttribute('fill', this.getLabelColor(point.type));
            label.setAttribute('font-size', '12');
            label.textContent = point.name;

            group.appendChild(circle);
            group.appendChild(text);
            group.appendChild(label);

            // 添加点击事件
            group.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showPointDetails(point);
            });

            pointsGroup.appendChild(group);
        });

        // 绘制卫星节点
        this.renderSatellitePoints();
    }

    renderSatellitePoints() {
        const satelliteGroup = document.getElementById('satellite-points');

        this.satellitePoints.forEach(satellite => {
            // 绘制连接线到主节点
            if (satellite.parentPoint) {
                const connection = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                connection.setAttribute('class', 'satellite-connection');
                connection.setAttribute('d', `M ${satellite.parentPoint.x} ${satellite.parentPoint.y} L ${satellite.x} ${satellite.y}`);
                satelliteGroup.appendChild(connection);
            }

            // 绘制卫星节点
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', `satellite-point ${satellite.type}`);
            group.setAttribute('data-id', satellite.id);

            // 卫星节点圆圈
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', satellite.x);
            circle.setAttribute('cy', satellite.y);
            circle.setAttribute('r', 8);

            // 卫星节点图标
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', satellite.x);
            text.setAttribute('y', satellite.y);
            text.textContent = satellite.icon || 'R';

            // 卫星节点标签
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('class', 'satellite-label');
            label.setAttribute('x', satellite.x);
            label.setAttribute('y', satellite.y + 15);
            label.textContent = satellite.name;

            group.appendChild(circle);
            group.appendChild(text);
            group.appendChild(label);

            // 添加点击事件
            group.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showSatelliteDetails(satellite);
            });

            satelliteGroup.appendChild(group);
        });
    }

    generateSatellitePoints() {
        // 清空现有卫星节点
        this.satellitePoints = [];

        // 为主要节点生成餐饮卫星节点
        this.routePoints.forEach(point => {
            if (point.type === 'attraction' || point.type === 'hotel') {
                // 在主节点周围随机生成1-2个餐饮点
                const satelliteCount = Math.floor(Math.random() * 2) + 1;

                for (let i = 0; i < satelliteCount; i++) {
                    const angle = (Math.PI * 2 / satelliteCount) * i + Math.random() * Math.PI / 4;
                    const distance = 30 + Math.random() * 20; // 距离主节点30-50像素

                    const satelliteX = point.x + Math.cos(angle) * distance;
                    const satelliteY = point.y + Math.sin(angle) * distance;

                    // 确保卫星节点在画布范围内
                    const clampedX = Math.max(20, Math.min(780, satelliteX));
                    const clampedY = Math.max(20, Math.min(580, satelliteY));

                    const restaurants = ['川菜馆', '粤菜厅', '西餐厅', '火锅店', '咖啡厅', '茶餐厅', '面包房', '快餐店'];
                    const restaurantName = restaurants[Math.floor(Math.random() * restaurants.length)];

                    this.satellitePoints.push({
                        id: this.currentSatelliteId++,
                        x: clampedX,
                        y: clampedY,
                        name: restaurantName,
                        type: 'restaurant',
                        icon: 'R',
                        parentPoint: point
                    });
                }
            }
        });
    }

    showSatelliteDetails(satellite) {
        const message = `餐饮详情：${satellite.name}\n位置：附近${satellite.parentPoint.name}\n类型：餐饮服务`;
        this.addChatMessage(message, 'assistant');
    }

    showPointDetails(point) {
        // 更新选中的节点ID
        this.selectedPointId = point.id;

        // 更新卡片显示
        this.updateCardsDisplay(point.id);

        // 添加聊天消息
        const message = `已选择${this.getPointTypeText(point.type)}：${point.name}，相关信息已显示在卡片中`;
        this.addChatMessage(message, 'assistant');

        // 视觉反馈：高亮选中的节点
        this.highlightSelectedPoint(point.id);
    }

    highlightSelectedPoint(pointId) {
        // 移除所有节点的选中状态
        document.querySelectorAll('.route-point').forEach(node => {
            node.classList.remove('selected');
        });

        // 添加选中状态到当前节点
        const selectedNode = document.querySelector(`[data-id="${pointId}"]`);
        if (selectedNode) {
            selectedNode.classList.add('selected');
        }
    }

    getLabelColor(type) {
        const colors = {
            'start': '#00ff88',
            'end': '#ff4444',
            'hotel': '#ffaa00',
            'attraction': '#00d4ff'
        };
        return colors[type] || '#00d4ff';
    }

    getPointTypeText(type) {
        const types = {
            'start': '起点',
            'end': '终点',
            'attraction': '景点',
            'hotel': '酒店'
        };
        return types[type] || '景点';
    }

    updateRouteInfo() {
        const pointCount = this.routePoints.length;
        const totalDistance = this.calculateTotalDistance();
        const estimatedTime = Math.ceil(totalDistance / 10); // 假设平均速度10km/h

        document.getElementById('point-count').textContent = `${pointCount} 个`;
        document.getElementById('total-distance').textContent = `${totalDistance.toFixed(1)} km`;
        document.getElementById('estimated-time').textContent = `${estimatedTime} 小时`;
    }

    calculateTotalDistance() {
        let total = 0;
        for (let i = 0; i < this.routePoints.length - 1; i++) {
            const current = this.routePoints[i];
            const next = this.routePoints[i + 1];
            const distance = Math.sqrt(
                Math.pow(next.x - current.x, 2) + Math.pow(next.y - current.y, 2)
            );
            total += distance * 0.1; // 转换为公里（假设比例）
        }
        return total;
    }

    loadThemePreference() {
        const savedTheme = localStorage.getItem('travel-assistant-theme');
        if (savedTheme === 'light') {
            this.isLightTheme = true;
            document.body.classList.add('light-theme');
            this.updateThemeIcons();
        }
    }

    toggleTheme() {
        this.isLightTheme = !this.isLightTheme;

        if (this.isLightTheme) {
            document.body.classList.add('light-theme');
            localStorage.setItem('travel-assistant-theme', 'light');
            this.addChatMessage('已切换到白天模式', 'assistant');
        } else {
            document.body.classList.remove('light-theme');
            localStorage.setItem('travel-assistant-theme', 'dark');
            this.addChatMessage('已切换到夜间模式', 'assistant');
        }

        this.updateThemeIcons();
    }

    updateThemeIcons() {
        const sunIcon = document.querySelector('.sun-icon');
        const moonIcon = document.querySelector('.moon-icon');

        if (this.isLightTheme) {
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'block';
        } else {
            sunIcon.style.display = 'block';
            moonIcon.style.display = 'none';
        }
    }

    getCurrentTime() {
        return new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    updateCardsDisplay(pointId = null) {
        // 根据选中的节点过滤卡片
        if (pointId !== null) {
            this.cards = this.allCardsData.filter(card => {
                return card.pointTypes.includes('all') || card.pointId === pointId;
            });
        } else {
            // 显示通用卡片
            this.cards = this.allCardsData.filter(card => {
                return card.pointTypes.includes('all');
            });
        }

        this.renderCards();
    }

    renderCards() {
        const container = document.getElementById('cards-container');
        container.innerHTML = '';

        this.cards.forEach(card => {
            const cardElement = document.createElement('div');
            cardElement.className = 'info-card';
            cardElement.dataset.cardId = card.id;

            // 创建展开的详细内容HTML
            let expandedContentHTML = '';
            if (card.expandedContent) {
                expandedContentHTML = `
                    <div class="card-expanded-content">
                        <div class="expanded-section">
                            <div class="expanded-title">详细描述</div>
                            <div class="expanded-text">${card.expandedContent.description}</div>
                        </div>
                `;

                // 添加特色/功能列表
                if (card.expandedContent.features) {
                    expandedContentHTML += `
                        <div class="expanded-section">
                            <div class="expanded-title">特色功能</div>
                            <ul class="expanded-list">
                                ${card.expandedContent.features.map(feature => `<li>${feature}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }

                // 添加详细信息
                if (card.expandedContent.details) {
                    expandedContentHTML += `
                        <div class="expanded-section">
                            <div class="expanded-title">详细信息</div>
                            <ul class="expanded-list">
                                ${card.expandedContent.details.map(detail => `<li>${detail}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }

                // 添加开放时间
                if (card.expandedContent.openHours) {
                    expandedContentHTML += `
                        <div class="expanded-section">
                            <div class="expanded-title">开放时间</div>
                            <div class="expanded-text">${card.expandedContent.openHours}</div>
                        </div>
                    `;
                }

                // 添加交通信息
                if (card.expandedContent.transportation) {
                    expandedContentHTML += `
                        <div class="expanded-section">
                            <div class="expanded-title">交通方式</div>
                            <div class="expanded-text">${card.expandedContent.transportation}</div>
                        </div>
                    `;
                }

                // 添加预订信息
                if (card.expandedContent.reservation) {
                    expandedContentHTML += `
                        <div class="expanded-section">
                            <div class="expanded-title">预订须知</div>
                            <div class="expanded-text">${card.expandedContent.reservation}</div>
                        </div>
                    `;
                }

                // 添加特色菜品
                if (card.expandedContent.specialties) {
                    expandedContentHTML += `
                        <div class="expanded-section">
                            <div class="expanded-title">招牌菜品</div>
                            <ul class="expanded-list">
                                ${card.expandedContent.specialties.map(item => `<li>${item}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }

                // 添加预报信息
                if (card.expandedContent.forecast) {
                    expandedContentHTML += `
                        <div class="expanded-section">
                            <div class="expanded-title">天气预报</div>
                            <div class="expanded-text">${card.expandedContent.forecast}</div>
                        </div>
                    `;
                }

                // 添加建议提示
                if (card.expandedContent.suggestion || card.expandedContent.tips) {
                    const tipContent = card.expandedContent.suggestion || card.expandedContent.tips;
                    expandedContentHTML += `
                        <div class="expanded-section">
                            <div class="expanded-title">温馨提示</div>
                            <div class="expanded-text">${tipContent}</div>
                        </div>
                    `;
                }

                expandedContentHTML += '</div>';
            }

            cardElement.innerHTML = `
                <div class="card-header">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div class="card-icon ${card.type}">
                            ${card.icon}
                        </div>
                        <h4 class="card-title">${card.title}</h4>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="card-time">${card.time}</span>
                        ${card.expandedContent ? `
                            <svg class="card-expand-icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M7 10l5 5 5-5z"/>
                            </svg>
                        ` : ''}
                    </div>
                </div>
                <div class="card-content">${card.content}</div>
                <div class="card-details">
                    <span class="card-value">${card.value}</span>
                    <span class="card-status ${card.status}">${card.statusText}</span>
                </div>
                ${expandedContentHTML}
            `;

            cardElement.addEventListener('click', () => {
                this.handleCardClick(card, cardElement);
            });

            container.appendChild(cardElement);
        });
    }

    handleCardClick(card, cardElement) {
        // 如果卡片有展开内容，切换展开状态
        if (card.expandedContent) {
            const isExpanded = cardElement.classList.contains('expanded');

            // 先收起所有其他卡片
            document.querySelectorAll('.info-card.expanded').forEach(otherCard => {
                if (otherCard !== cardElement) {
                    otherCard.classList.remove('expanded');
                }
            });

            // 切换当前卡片的展开状态
            if (isExpanded) {
                cardElement.classList.remove('expanded');
                this.addChatMessage(`收起了${card.title}的详细信息`, 'assistant');
            } else {
                cardElement.classList.add('expanded');
                this.addChatMessage(`展开了${card.title}的详细信息，请查看卡片中的完整内容`, 'assistant');
            }
        } else {
            // 没有展开内容的卡片，显示原有消息
            let message = '';
            switch(card.type) {
                case 'weather':
                    message = `天气详情：${card.content}，当前温度${card.value}。`;
                    break;
                case 'hotel':
                    message = `酒店信息：${card.content}，价格${card.value}，房间状态：${card.statusText}。`;
                    break;
                case 'attraction':
                    message = `景点介绍：${card.content}，门票${card.value}，开放状态：${card.statusText}。`;
                    break;
                case 'restaurant':
                    message = `餐厅信息：${card.content}，人均价格${card.value}，营业状态：${card.statusText}。`;
                    break;
                default:
                    message = `${card.title}：${card.content}`;
            }
            this.addChatMessage(message, 'assistant');
        }
    }

    optimizeRoute() {
        if (this.routePoints.length < 3) {
            this.addChatMessage('至少需要3个景点才能优化路线', 'assistant');
            return;
        }

        // 简单的路线优化：按距离排序（这里使用简化算法）
        const start = this.routePoints[0];
        const end = this.routePoints[this.routePoints.length - 1];
        const middle = this.routePoints.slice(1, -1);

        // 对中间点按到起点的距离排序
        middle.sort((a, b) => {
            const distA = Math.sqrt(Math.pow(a.x - start.x, 2) + Math.pow(a.y - start.y, 2));
            const distB = Math.sqrt(Math.pow(b.x - start.x, 2) + Math.pow(b.y - start.y, 2));
            return distA - distB;
        });

        this.routePoints = [start, ...middle, end];
        this.updateRouteDisplay();
        this.updateRouteInfo();
        this.generateSatellitePoints();
        this.renderSatellitePoints(); // 更新卫星节点显示

        this.addChatMessage('路线已优化完成！已按最短路径重新排列景点顺序。', 'assistant');
    }

    showOverviewPopup() {
        const popup = document.getElementById('overview-popup');
        popup.classList.add('show');
        this.currentSlide = 0;
        this.renderItinerary();

        // 延迟设置导航，确保DOM已渲染
        setTimeout(() => {
            this.setupSlideNavigation();
        }, 100);

        this.addChatMessage('已打开行程总览，查看完整7天旅游计划。可以左右滑动查看每日详情', 'assistant');
    }

    hideOverviewPopup() {
        const popup = document.getElementById('overview-popup');
        popup.classList.remove('show');
    }

    setupSlideNavigation() {
        // 设置导航事件
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const navPrev = document.getElementById('nav-prev');
        const navNext = document.getElementById('nav-next');

        prevBtn.onclick = () => this.previousSlide();
        nextBtn.onclick = () => this.nextSlide();
        navPrev.onclick = () => this.previousSlide();
        navNext.onclick = () => this.nextSlide();

        // 设置指示器点击事件
        this.updateNavigationButtons();
        this.createDayIndicators();

        // 键盘事件
        document.addEventListener('keydown', (e) => {
            if (document.getElementById('overview-popup').classList.contains('show')) {
                if (e.key === 'ArrowLeft') this.previousSlide();
                if (e.key === 'ArrowRight') this.nextSlide();
                if (e.key === 'Escape') this.hideOverviewPopup();
            }
        });

        // 触摸滑动事件
        this.setupTouchEvents();
    }

    setupTouchEvents() {
        const daysContainer = document.getElementById('days-container');
        let startX = 0;
        let currentX = 0;
        let isDragging = false;
        let startTime = 0;

        // 触摸开始
        daysContainer.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            currentX = startX;
            isDragging = true;
            startTime = Date.now();
            daysContainer.style.transition = 'none';
        }, { passive: true });

        // 触摸移动
        daysContainer.addEventListener('touchmove', (e) => {
            if (!isDragging) return;

            currentX = e.touches[0].clientX;
            const deltaX = currentX - startX;
            const currentTranslate = -this.currentSlide * 100;
            const movePercent = (deltaX / window.innerWidth) * 100;

            daysContainer.style.transform = `translateX(${currentTranslate + movePercent}%)`;
        }, { passive: true });

        // 触摸结束
        daysContainer.addEventListener('touchend', (e) => {
            if (!isDragging) return;

            isDragging = false;
            daysContainer.style.transition = 'transform 0.3s ease';

            const deltaX = currentX - startX;
            const deltaTime = Date.now() - startTime;
            const velocity = Math.abs(deltaX) / deltaTime;

            // 判断是否触发滑动
            const threshold = window.innerWidth * 0.2; // 20% 的屏幕宽度
            const shouldSlide = Math.abs(deltaX) > threshold || velocity > 0.5;

            if (shouldSlide) {
                if (deltaX > 0 && this.currentSlide > 0) {
                    this.previousSlide();
                } else if (deltaX < 0 && this.currentSlide < this.itineraryData.length - 1) {
                    this.nextSlide();
                } else {
                    this.updateSlidePosition();
                }
            } else {
                this.updateSlidePosition();
            }
        }, { passive: true });

        // 鼠标事件（桌面端）
        let isMouseDown = false;
        let mouseStartX = 0;
        let mouseCurrentX = 0;

        daysContainer.addEventListener('mousedown', (e) => {
            isMouseDown = true;
            mouseStartX = e.clientX;
            mouseCurrentX = mouseStartX;
            daysContainer.style.transition = 'none';
            daysContainer.style.cursor = 'grabbing';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isMouseDown) return;

            mouseCurrentX = e.clientX;
            const deltaX = mouseCurrentX - mouseStartX;
            const currentTranslate = -this.currentSlide * 100;
            const movePercent = (deltaX / window.innerWidth) * 100;

            daysContainer.style.transform = `translateX(${currentTranslate + movePercent}%)`;
        });

        document.addEventListener('mouseup', (e) => {
            if (!isMouseDown) return;

            isMouseDown = false;
            daysContainer.style.transition = 'transform 0.3s ease';
            daysContainer.style.cursor = 'grab';

            const deltaX = mouseCurrentX - mouseStartX;
            const threshold = window.innerWidth * 0.15;

            if (Math.abs(deltaX) > threshold) {
                if (deltaX > 0 && this.currentSlide > 0) {
                    this.previousSlide();
                } else if (deltaX < 0 && this.currentSlide < this.itineraryData.length - 1) {
                    this.nextSlide();
                } else {
                    this.updateSlidePosition();
                }
            } else {
                this.updateSlidePosition();
            }
        });

        // 设置初始样式
        daysContainer.style.cursor = 'grab';
    }

    // 清理WebSocket连接
    cleanup() {
        if (this.websocket) {
            console.log('关闭WebSocket连接');
            this.websocket.close(1000, '页面关闭');
            this.websocket = null;
        }
        // 清理消息ID映射
        this.messageIdMap.clear();
    }

    createDayIndicators() {
        const indicatorsContainer = document.getElementById('day-indicators');
        indicatorsContainer.innerHTML = '';

        this.itineraryData.forEach((day, index) => {
            const indicator = document.createElement('div');
            indicator.className = `day-indicator ${index === this.currentSlide ? 'active' : ''}`;
            indicator.title = `第${day.day}天`;
            indicator.onclick = () => this.goToSlide(index);
            indicatorsContainer.appendChild(indicator);
        });
    }

    previousSlide() {
        console.log(`Previous slide: current=${this.currentSlide}`);
        if (this.currentSlide > 0) {
            this.currentSlide--;
            this.updateSlidePosition();
            this.updateNavigationButtons();
            this.updateDayIndicators();
            console.log(`Moved to slide ${this.currentSlide}`);
        } else {
            console.log('Already at first slide');
        }
    }

    nextSlide() {
        console.log(`Next slide: current=${this.currentSlide}, max=${this.itineraryData.length - 1}`);
        if (this.currentSlide < this.itineraryData.length - 1) {
            this.currentSlide++;
            this.updateSlidePosition();
            this.updateNavigationButtons();
            this.updateDayIndicators();
            console.log(`Moved to slide ${this.currentSlide}`);
        } else {
            console.log('Already at last slide');
        }
    }

    goToSlide(index) {
        this.currentSlide = index;
        this.updateSlidePosition();
        this.updateNavigationButtons();
        this.updateDayIndicators();
    }

    updateSlidePosition() {
        const container = document.getElementById('days-container');
        // 计算滑动百分比：每一页是总宽度的 1/7
        const slidePercent = 100 / this.itineraryData.length;
        const translateX = -this.currentSlide * slidePercent;
        container.style.transform = `translateX(${translateX}%)`;

        // 调试信息
        console.log(`Sliding to day ${this.currentSlide + 1}`);
        console.log(`Slide percent: ${slidePercent}%`);
        console.log(`TranslateX: ${translateX}%`);
        console.log(`Container transform: ${container.style.transform}`);
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const navPrev = document.getElementById('nav-prev');
        const navNext = document.getElementById('nav-next');

        // 更新禁用状态
        const isFirst = this.currentSlide === 0;
        const isLast = this.currentSlide === this.itineraryData.length - 1;

        prevBtn.classList.toggle('disabled', isFirst);
        navPrev.classList.toggle('disabled', isFirst);
        nextBtn.classList.toggle('disabled', isLast);
        navNext.classList.toggle('disabled', isLast);
    }

    updateDayIndicators() {
        const indicators = document.querySelectorAll('.day-indicator');
        indicators.forEach((indicator, index) => {
            indicator.classList.toggle('active', index === this.currentSlide);
        });
    }

    renderItinerary() {
        const daysContainer = document.getElementById('days-container');

        // 计算容器总宽度 = 天数 × 100%
        const totalWidth = this.itineraryData.length * 100;
        daysContainer.style.width = `${totalWidth}%`;

        let html = '';
        this.itineraryData.forEach((day, dayIndex) => {
            html += `
                <div class="day-slide" data-day="${dayIndex}">
                    <div class="day-header-large">
                        <div class="day-title-large">${day.title}</div>
                        <div class="day-date-large">${day.date} · 第${day.day}天</div>
                        <div class="day-summary-large">${day.summary}</div>
                    </div>
                    <div class="day-content-large">
            `;

            day.items.forEach((item, itemIndex) => {
                html += `
                    <div class="itinerary-item-large ${item.type}" data-item="${itemIndex}">
                        <div class="item-time-large">${item.time}</div>
                        <div class="item-content-large">
                            <div class="item-title-large">
                                <div class="item-icon-large ${item.type}">
                                    ${this.getItemIconText(item.type)}
                                </div>
                                ${item.title}
                            </div>
                            <div class="item-description-large">${item.description}</div>
                            <div class="item-details-large">
                                <div class="item-detail-large price">
                                    <span>💰</span>
                                    <span>${item.price}</span>
                                </div>
                                <div class="item-detail-large duration">
                                    <span>⏱️</span>
                                    <span>${item.duration}</span>
                                </div>
                                ${item.type === 'attraction' ? `
                                    <div class="item-detail-large">
                                        <span>📍</span>
                                        <span>景点游览</span>
                                    </div>
                                ` : ''}
                                ${item.type === 'hotel' ? `
                                    <div class="item-detail-large">
                                        <span>🛏️</span>
                                        <span>住宿休息</span>
                                    </div>
                                ` : ''}
                                ${item.type === 'restaurant' ? `
                                    <div class="item-detail-large">
                                        <span>🍴</span>
                                        <span>用餐时间</span>
                                    </div>
                                ` : ''}
                                ${item.type === 'start' ? `
                                    <div class="item-detail-large">
                                        <span>🚀</span>
                                        <span>行程开始</span>
                                    </div>
                                ` : ''}
                                ${item.type === 'end' ? `
                                    <div class="item-detail-large">
                                        <span>🏁</span>
                                        <span>行程结束</span>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        daysContainer.innerHTML = html;

        // 确保初始位置正确
        this.updateSlidePosition();

        // 调试信息
        console.log(`Rendered ${this.itineraryData.length} days`);
        console.log(`Container width set to: ${totalWidth}%`);
        const slides = daysContainer.querySelectorAll('.day-slide');
        console.log(`Found ${slides.length} slide elements`);
        slides.forEach((slide, index) => {
            console.log(`Slide ${index} width: ${slide.offsetWidth}px`);
        });
    }

    getItemIconText(type) {
        const icons = {
            'start': '🚀',
            'end': '🏁',
            'attraction': '🎯',
            'hotel': 'H',
            'restaurant': 'R'
        };
        return icons[type] || '📍';
    }
}

// 全局函数：切换工具调用详情的显示/隐藏
function toggleToolDetails(headerElement) {
    const toolCall = headerElement.parentElement;
    const details = toolCall.querySelector('.tool-details');
    const toggle = headerElement.querySelector('.tool-toggle');

    if (details.style.display === 'none') {
        details.style.display = 'block';
        toggle.textContent = '▲';
    } else {
        details.style.display = 'none';
        toggle.textContent = '▼';
    }
}

// 全局函数：显示完整的工具结果
function showFullResult(buttonElement) {
    const fullResult = decodeURIComponent(buttonElement.getAttribute('data-full-result'));

    // 创建模态框显示完整结果
    const modal = document.createElement('div');
    modal.className = 'tool-result-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;

    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: var(--bg-primary);
        color: var(--text-primary);
        padding: 20px;
        border-radius: 8px;
        max-width: 80%;
        max-height: 80%;
        overflow: auto;
        position: relative;
    `;

    const closeButton = document.createElement('button');
    closeButton.textContent = '✕';
    closeButton.style.cssText = `
        position: absolute;
        top: 10px;
        right: 15px;
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
        color: var(--text-primary);
    `;
    closeButton.onclick = () => modal.remove();

    const resultText = document.createElement('pre');
    resultText.style.cssText = `
        white-space: pre-wrap;
        word-wrap: break-word;
        font-family: monospace;
        font-size: 12px;
        line-height: 1.4;
        margin: 0;
        padding-top: 30px;
    `;
    resultText.textContent = fullResult;

    modalContent.appendChild(closeButton);
    modalContent.appendChild(resultText);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);

    // 点击模态框外部关闭
    modal.onclick = (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    };
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    const travelAssistant = new TravelAssistant();

    // 页面关闭时清理WebSocket连接
    window.addEventListener('beforeunload', () => {
        travelAssistant.cleanup();
    });
});