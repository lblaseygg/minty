let totalInvestmentsChart, allocationChart;

// Add timeframe selector functionality
let currentTimeframe = '1M';
let portfolioHistoryData = {};
let lastChartData = null; // Track last chart data to prevent unnecessary updates

// Stock name mapping
const STOCKS = {
    'NVDA': 'NVIDIA',
    'AMD': 'AMD',
    'AAPL': 'Apple',
    'GOOGL': 'Google',
    'MSFT': 'Microsoft',
    'TSLA': 'Tesla',
    'META': 'Meta',
    'AMZN': 'Amazon'
};

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatPercentage(value) {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

function getChangeClass(value) {
    if (value > 0) return 'up';
    if (value < 0) return 'down';
    return 'neutral';
}

// API functions
async function fetchUserInfo() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5001/users/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch user info');
        return await response.json();
    } catch (error) {
        console.error('Error fetching user info:', error);
        return null;
    }
}

async function fetchAccountInfo() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5001/account', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch account info');
        return await response.json();
    } catch (error) {
        console.error('Error fetching account info:', error);
        return null;
    }
}

async function fetchPortfolio() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5001/portfolio', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch portfolio');
        return await response.json();
    } catch (error) {
        console.error('Error fetching portfolio:', error);
        return { positions: [] };
    }
}

async function fetchOrders() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5001/orders', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch orders');
        return await response.json();
    } catch (error) {
        console.error('Error fetching orders:', error);
        return [];
    }
}

async function fetchLivePrices(symbols) {
    try {
        const prices = {};
        for (const symbol of symbols) {
            const response = await fetch(`http://localhost:5001/live_data/${symbol}`);
            if (response.ok) {
                const data = await response.json();
                prices[symbol] = data.price || 0;
            }
        }
        return prices;
    } catch (error) {
        console.error('Error fetching live prices:', error);
        return {};
    }
}

// Fetch portfolio historical data
async function fetchPortfolioHistory(timeframe = '1M') {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`http://localhost:5001/portfolio/history?timeframe=${timeframe}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            // If endpoint doesn't exist, return null to use real data
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching portfolio history:', error);
        return null;
    }
}

// Generate real portfolio data based on actual trades and orders
function generateRealPortfolioData(portfolioData, livePrices, accountInfo, orders, timeframe = '1M') {
    const now = new Date();
    const data = [];
    
    // Calculate current total portfolio value
    const totalCurrentValue = portfolioData.positions.reduce((sum, pos) => {
        const currentPrice = livePrices[pos.symbol] || pos.current_price || pos.avg_entry_price;
        return sum + (pos.qty * currentPrice);
    }, 0);
    
    const cashValue = accountInfo?.cash || 0;
    const currentTotalValue = totalCurrentValue + cashValue;
    
    // Get the starting date based on timeframe
    let startDate;
    switch(timeframe) {
        case '1D':
            startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000); // 24 hours ago
            break;
        case '1W':
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); // 7 days ago
            break;
        case '1M':
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000); // 30 days ago
            break;
        case '3M':
            startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000); // 90 days ago
            break;
        case '1Y':
            startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000); // 365 days ago
            break;
        default:
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    }
    
    // Filter orders within the timeframe
    const relevantOrders = orders.filter(order => {
        const orderDate = new Date(order.timestamp);
        return orderDate >= startDate && orderDate <= now;
    });
    
    // Sort orders by timestamp
    relevantOrders.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    // Calculate portfolio value at different points
    let runningCash = accountInfo?.cash || 0;
    let runningPositions = {};
    
    // Add initial cash (assuming you started with 100k)
    const initialCash = 100000;
    runningCash = initialCash;
    
    // Create data points based on actual trades
    const timePoints = [];
    
    // Add start point
    timePoints.push({
        date: startDate,
        cash: initialCash,
        positions: {},
        totalValue: initialCash
    });
    
    // Process each order to track portfolio changes
    relevantOrders.forEach(order => {
        const orderDate = new Date(order.timestamp);
        
        if (order.status === 'filled' || order.status === 'accepted') {
            const orderValue = order.qty * order.price;
            
            if (order.side === 'buy') {
                // Buying stock
                if (runningCash >= orderValue) {
                    runningCash -= orderValue;
                    
                    if (!runningPositions[order.symbol]) {
                        runningPositions[order.symbol] = {
                            qty: 0,
                            avgPrice: 0,
                            totalCost: 0
                        };
                    }
                    
                    const position = runningPositions[order.symbol];
                    const newTotalCost = position.totalCost + orderValue;
                    const newQty = position.qty + order.qty;
                    position.avgPrice = newTotalCost / newQty;
                    position.qty = newQty;
                    position.totalCost = newTotalCost;
                }
            } else if (order.side === 'sell') {
                // Selling stock
                if (runningPositions[order.symbol] && runningPositions[order.symbol].qty >= order.qty) {
                    const position = runningPositions[order.symbol];
                    const soldValue = order.qty * order.price;
                    runningCash += soldValue;
                    
                    position.qty -= order.qty;
                    position.totalCost = position.avgPrice * position.qty;
                    
                    if (position.qty <= 0) {
                        delete runningPositions[order.symbol];
                    }
                }
            }
            
            // Calculate current portfolio value at this point
            let currentPortfolioValue = runningCash;
            Object.keys(runningPositions).forEach(symbol => {
                const position = runningPositions[symbol];
                // Use current live price or order price as fallback
                const currentPrice = livePrices[symbol] || order.price;
                currentPortfolioValue += position.qty * currentPrice;
            });
            
            timePoints.push({
                date: orderDate,
                cash: runningCash,
                positions: { ...runningPositions },
                totalValue: currentPortfolioValue
            });
        }
    });
    
    // Add current point
    timePoints.push({
        date: now,
        cash: cashValue,
        positions: portfolioData.positions.reduce((acc, pos) => {
            acc[pos.symbol] = {
                qty: pos.qty,
                avgPrice: pos.avg_entry_price,
                totalCost: pos.qty * pos.avg_entry_price
            };
            return acc;
        }, {}),
        totalValue: currentTotalValue
    });
    
    // Convert to chart data format
    return {
        data: timePoints.map(point => ({
            date: point.date.toISOString(),
            value: point.totalValue
        }))
    };
}

// Create the total investments chart with timeframe support
function createTotalInvestmentsChart(portfolioData, livePrices, accountInfo, orders, timeframe = '1M') {
    const ctx = document.getElementById('total-investments-chart').getContext('2d');
    
    // Calculate current portfolio value
    const totalCurrentValue = portfolioData.positions.reduce((sum, pos) => {
        const currentPrice = livePrices[pos.symbol] || pos.current_price || pos.avg_entry_price;
        return sum + (pos.qty * currentPrice);
    }, 0);
    
    const cashValue = accountInfo?.cash || 0;
    const totalPortfolioValue = totalCurrentValue + cashValue;
    
    // Try to fetch real historical data first
    fetchPortfolioHistory(timeframe).then(historyData => {
        let chartData;
        
        if (historyData && historyData.data && historyData.data.length > 0) {
            // Use real historical data if available
            chartData = historyData;
        } else {
            // Generate realistic data based on actual trades and orders
            chartData = generateRealPortfolioData(portfolioData, livePrices, accountInfo, orders, timeframe);
            console.log('Generated real portfolio data:', chartData);
        }
        
        // Check if chart data has actually changed
        const newChartDataString = JSON.stringify(chartData);
        if (lastChartData === newChartDataString && totalInvestmentsChart) {
            console.log('Chart data unchanged, skipping chart update');
            return; // Don't update chart if data hasn't changed
        }
        
        // Update last chart data
        lastChartData = newChartDataString;
        
        const labels = chartData.data.map(point => {
            const date = new Date(point.date);
            switch(timeframe) {
                case '1D':
                    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                case '1W':
                    return date.toLocaleDateString('en-US', { weekday: 'short' });
                case '1M':
                case '3M':
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                case '1Y':
                    return date.toLocaleDateString('en-US', { month: 'short' });
                default:
                    return date.toLocaleDateString();
            }
        });
        
        const values = chartData.data.map(point => point.value);
        
        if (totalInvestmentsChart) {
            totalInvestmentsChart.destroy();
        }
        
        totalInvestmentsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Portfolio Value',
                    data: values,
                    borderColor: '#76b900',
                    backgroundColor: 'rgba(118,185,0,0.05)',
                    fill: true,
                    tension: 0.2,
                    borderWidth: 2,
                    pointBackgroundColor: 'transparent',
                    pointBorderColor: 'transparent',
                    pointRadius: 0,
                    pointHoverRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#76b900',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `Portfolio Value: ${formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { 
                            color: 'rgba(255,255,255,0.03)',
                            drawBorder: false
                        },
                        ticks: { 
                            color: '#a0a0a0',
                            font: {
                                size: 11
                            }
                        },
                        border: {
                            display: false
                        }
                    },
                    y: {
                        grid: { 
                            color: 'rgba(255,255,255,0.03)',
                            drawBorder: false
                        },
                        ticks: { 
                            color: '#a0a0a0',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        },
                        border: {
                            display: false
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                elements: {
                    point: {
                        radius: 0
                    }
                }
            }
        });
    });
}

// Add timeframe selector event listeners
function initializeTimeframeSelector() {
    const timeframeButtons = document.querySelectorAll('.timeframe-selector button');
    
    timeframeButtons.forEach(button => {
        button.addEventListener('click', async function() {
            // Remove active class from all buttons
            timeframeButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update current timeframe
            const newTimeframe = this.dataset.tf;
            
            // Only update chart if timeframe actually changed
            if (newTimeframe !== currentTimeframe) {
                currentTimeframe = newTimeframe;
                
                // Reset chart data to force refresh
                lastChartData = null;
                
                // Fetch fresh data and update chart
                try {
                    const [accountInfo, portfolioData, orders] = await Promise.all([
                        fetchAccountInfo(),
                        fetchPortfolio(),
                        fetchOrders()
                    ]);
                    
                    if (accountInfo && portfolioData) {
                        const symbols = [...new Set(portfolioData.positions.map(pos => pos.symbol))];
                        const livePrices = await fetchLivePrices(symbols);
                        createTotalInvestmentsChart(portfolioData, livePrices, accountInfo, orders, currentTimeframe);
                    }
                } catch (error) {
                    console.error('Error updating chart timeframe:', error);
                }
            }
        });
    });
}

// Display functions
function updatePortfolioHeader(userInfo) {
    const portfolioTitle = document.querySelector('.logo h1');
    if (userInfo && userInfo.username) {
        // Capitalize the first letter of the username
        const username = userInfo.username.charAt(0).toUpperCase() + userInfo.username.slice(1);
        portfolioTitle.textContent = `${username}'s Portfolio`;
        // Update page title as well
        document.title = `Minty - ${username}'s Portfolio`;
    } else {
        portfolioTitle.textContent = 'Portfolio';
        document.title = 'Minty - Portfolio Dashboard';
    }
}

function updatePortfolioSummary(accountInfo, portfolioData, livePrices) {
    const totalInvested = portfolioData.positions.reduce((sum, pos) => {
        return sum + (pos.qty * pos.avg_entry_price);
    }, 0);

    const totalCurrentValue = portfolioData.positions.reduce((sum, pos) => {
        const currentPrice = livePrices[pos.symbol] || pos.current_price || pos.avg_entry_price;
        return sum + (pos.qty * currentPrice);
    }, 0);

    const totalPnL = totalCurrentValue - totalInvested;
    const totalPnLPercent = totalInvested > 0 ? (totalPnL / totalInvested) * 100 : 0;
    const totalPortfolioValue = totalCurrentValue + (accountInfo?.cash || 0);

    // Update summary elements
    document.getElementById('total-portfolio-value').textContent = formatCurrency(totalPortfolioValue);
    document.getElementById('cash-available').textContent = formatCurrency(accountInfo?.cash || 0);
    document.getElementById('total-invested').textContent = formatCurrency(totalInvested);
    
    const pnlElement = document.getElementById('total-pnl');
    pnlElement.textContent = formatCurrency(totalPnL);
    pnlElement.className = getChangeClass(totalPnL);

    const changeElement = document.getElementById('total-change');
    changeElement.textContent = formatPercentage(totalPnLPercent);
    changeElement.className = getChangeClass(totalPnLPercent);

    // Update chart summary
    document.getElementById('chart-total-value').textContent = formatCurrency(totalPortfolioValue);
    document.getElementById('chart-total-pnl').textContent = formatCurrency(totalPnL);
    document.getElementById('chart-total-pnl-percent').textContent = formatPercentage(totalPnLPercent);
    
    const chartPnlElement = document.getElementById('chart-total-pnl');
    const chartPnlPercentElement = document.getElementById('chart-total-pnl-percent');
    chartPnlElement.className = getChangeClass(totalPnL);
    chartPnlPercentElement.className = getChangeClass(totalPnLPercent);
}

function updateHoldingsList(portfolioData, livePrices) {
    const container = document.getElementById('holdings-container');
    container.innerHTML = '';

    if (portfolioData.positions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-chart-line"></i>
                <p>No holdings yet</p>
                <p>Start trading to see your portfolio here</p>
            </div>
        `;
        return;
    }

    portfolioData.positions.forEach(position => {
        const currentPrice = livePrices[position.symbol] || position.current_price || position.avg_entry_price;
        const marketValue = position.qty * currentPrice;
        const costBasis = position.qty * position.avg_entry_price;
        const totalReturn = marketValue - costBasis;
        const totalReturnPercent = costBasis > 0 ? (totalReturn / costBasis) * 100 : 0;

        const holdingElement = document.createElement('div');
        holdingElement.className = 'holding-item';
        holdingElement.innerHTML = `
            <div class="holding-symbol">
                <strong>${position.symbol}</strong>
                <span>${STOCKS[position.symbol] || position.symbol}</span>
            </div>
            <div class="holding-shares">
                <span>${position.qty.toFixed(2)} shares</span>
            </div>
            <div class="holding-return">
                <strong class="${getChangeClass(totalReturn)}">${formatCurrency(totalReturn)}</strong>
                <span class="${getChangeClass(totalReturnPercent)}">${formatPercentage(totalReturnPercent)}</span>
            </div>
        `;
        container.appendChild(holdingElement);
    });
}

function updateRecentActivity(orders) {
    const container = document.getElementById('activity-list');
    container.innerHTML = '';

    if (orders.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history"></i>
                <p>No recent activity</p>
            </div>
        `;
        return;
    }

    // Show last 10 orders
    const recentOrders = orders.slice(-10).reverse();
    
    recentOrders.forEach(order => {
        const activityElement = document.createElement('div');
        activityElement.className = 'activity-item';
        activityElement.innerHTML = `
            <div class="activity-icon ${order.side}">
                <i class="fas fa-${order.side === 'buy' ? 'arrow-up' : 'arrow-down'}"></i>
            </div>
            <div class="activity-details">
                <div class="activity-main">
                    <strong>${order.side.toUpperCase()} ${order.qty} ${order.symbol}</strong>
                    <span>@ ${formatCurrency(order.price)}</span>
                </div>
                <div class="activity-meta">
                    <span>${new Date(order.timestamp).toLocaleDateString()}</span>
                    <span class="status ${order.status}">${order.status}</span>
                </div>
            </div>
        `;
        container.appendChild(activityElement);
    });
}

function createAllocationChart(portfolioData, livePrices) {
    const ctx = document.getElementById('allocation-chart').getContext('2d');
    
    const allocations = portfolioData.positions.map(position => {
        const currentPrice = livePrices[position.symbol] || position.current_price || position.avg_entry_price;
        return {
            symbol: position.symbol,
            name: STOCKS[position.symbol] || position.symbol,
            value: position.qty * currentPrice
        };
    });
    
    const totalValue = allocations.reduce((sum, item) => sum + item.value, 0);
    
    if (allocationChart) {
        allocationChart.destroy();
    }
    
    if (allocations.length === 0) {
        // Show empty state
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        ctx.fillStyle = '#666';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('No holdings to display', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }
    
    const colors = ['#76b900', '#4caf50', '#2196f3', '#ff9800', '#f44336', '#9c27b0', '#00bcd4', '#795548'];
    
    allocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: allocations.map(item => item.name),
            datasets: [{
                data: allocations.map(item => item.value),
                backgroundColor: colors.slice(0, allocations.length),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e0e0e0',
                        padding: 10,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const percentage = ((value / totalValue) * 100).toFixed(1);
                            return `${context.label}: ${formatCurrency(value)} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Refresh functions
function refreshHoldings() {
    updatePortfolio();
}

function refreshActivity() {
    updatePortfolio();
}

// Main update function
async function updatePortfolio() {
    try {
        console.log('Starting portfolio update...');
        
        const [userInfo, accountInfo, portfolioData, orders] = await Promise.all([
            fetchUserInfo(),
            fetchAccountInfo(),
            fetchPortfolio(),
            fetchOrders()
        ]);

        console.log('Fetched data:', {
            userInfo: !!userInfo,
            accountInfo: !!accountInfo,
            portfolioData: portfolioData?.positions?.length || 0,
            orders: orders?.length || 0
        });

        if (!userInfo || !accountInfo || !portfolioData) {
            console.error('Failed to fetch portfolio data');
            return;
        }

        // Update header
        updatePortfolioHeader(userInfo);

        // Get unique symbols for live price fetching
        const symbols = [...new Set(portfolioData.positions.map(pos => pos.symbol))];
        console.log('Fetching live prices for symbols:', symbols);
        const livePrices = await fetchLivePrices(symbols);
        console.log('Live prices:', livePrices);

        // Update summary and holdings (these should always update)
        updatePortfolioSummary(accountInfo, portfolioData, livePrices);
        updateHoldingsList(portfolioData, livePrices);
        updateRecentActivity(orders);
        
        // Check if chart elements exist before creating charts
        const totalChartElement = document.getElementById('total-investments-chart');
        const allocationChartElement = document.getElementById('allocation-chart');
        
        console.log('Chart elements found:', {
            totalChart: !!totalChartElement,
            allocationChart: !!allocationChartElement
        });
        
        // Only update charts if they don't exist and elements are found
        if (!totalInvestmentsChart && totalChartElement) {
            console.log('Creating total investments chart...');
            createTotalInvestmentsChart(portfolioData, livePrices, accountInfo, orders, currentTimeframe);
        }
        
        if (!allocationChart && allocationChartElement) {
            console.log('Creating allocation chart...');
            createAllocationChart(portfolioData, livePrices);
        }

        console.log('Portfolio update completed successfully');
    } catch (error) {
        console.error('Error updating portfolio:', error);
    }
}

// Quick price update function (doesn't refresh charts)
async function updatePricesOnly() {
    try {
        const portfolioData = await fetchPortfolio();
        if (!portfolioData || portfolioData.positions.length === 0) return;
        
        const symbols = [...new Set(portfolioData.positions.map(pos => pos.symbol))];
        const livePrices = await fetchLivePrices(symbols);
        
        // Update only the summary and holdings with new prices
        const accountInfo = await fetchAccountInfo();
        updatePortfolioSummary(accountInfo, portfolioData, livePrices);
        updateHoldingsList(portfolioData, livePrices);
    } catch (error) {
        console.error('Error updating prices:', error);
    }
}

// Initialize portfolio with timeframe selector
document.addEventListener('DOMContentLoaded', async function() {
    try {
        console.log('Initializing portfolio...');
        
        // Check if required elements exist
        const totalChartElement = document.getElementById('total-investments-chart');
        const allocationChartElement = document.getElementById('allocation-chart');
        const timeframeButtons = document.querySelectorAll('.timeframe-selector button');
        
        console.log('Required elements found:', {
            totalChart: !!totalChartElement,
            allocationChart: !!allocationChartElement,
            timeframeButtons: timeframeButtons.length
        });
        
        await updatePortfolio();
        initializeTimeframeSelector();
        
        // Refresh portfolio data every 2 minutes to prevent excessive chart updates
        setInterval(updatePortfolio, 120000);
        
        // Update prices every 30 seconds for responsive price updates
        setInterval(updatePricesOnly, 30000);
        
        console.log('Portfolio initialized successfully');
    } catch (error) {
        console.error('Error initializing portfolio:', error);
    }
});