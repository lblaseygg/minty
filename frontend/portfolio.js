let totalInvestmentsChart, allocationChart;

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

// Display functions
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
        const unrealizedPnL = marketValue - costBasis;
        const unrealizedPnLPercent = costBasis > 0 ? (unrealizedPnL / costBasis) * 100 : 0;

        const holdingElement = document.createElement('div');
        holdingElement.className = 'holding-item';
        holdingElement.innerHTML = `
            <div class="holding-header">
                <div class="holding-symbol">
                    <strong>${position.symbol}</strong>
                    <span>${STOCKS[position.symbol] || position.symbol}</span>
                </div>
                <div class="holding-price">
                    <strong>$${currentPrice.toFixed(2)}</strong>
                    <span class="${getChangeClass(unrealizedPnLPercent)}">${formatPercentage(unrealizedPnLPercent)}</span>
                </div>
            </div>
            <div class="holding-details">
                <div class="detail">
                    <span>Shares Owned:</span>
                    <strong>${position.qty.toFixed(2)}</strong>
                </div>
                <div class="detail">
                    <span>Market Value:</span>
                    <strong>${formatCurrency(marketValue)}</strong>
                </div>
                <div class="detail">
                    <span>P&L:</span>
                    <strong class="${getChangeClass(unrealizedPnL)}">${formatCurrency(unrealizedPnL)}</strong>
                </div>
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

function createTotalInvestmentsChart(portfolioData, livePrices, accountInfo) {
    const ctx = document.getElementById('total-investments-chart').getContext('2d');
    
    // Calculate current portfolio value
    const totalCurrentValue = portfolioData.positions.reduce((sum, pos) => {
        const currentPrice = livePrices[pos.symbol] || pos.current_price || pos.avg_entry_price;
        return sum + (pos.qty * currentPrice);
    }, 0);
    
    const cashValue = accountInfo?.cash || 0;
    const totalPortfolioValue = totalCurrentValue + cashValue;
    
    // Create demo data for portfolio growth over time
    // In a real app, this would come from historical portfolio data
    const baseValue = Math.max(10000, totalPortfolioValue * 0.8); // Start with a reasonable base
    const labels = ['1M ago', '2W ago', '1W ago', 'Today'];
    const values = [
        baseValue,
        baseValue * 1.02,
        baseValue * 0.98,
        totalPortfolioValue
    ];
    
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
                backgroundColor: 'rgba(118,185,0,0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointBackgroundColor: '#76b900',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#76b900',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return `Portfolio Value: ${formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#e0e0e0' }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { 
                        color: '#e0e0e0',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
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
        const [accountInfo, portfolioData, orders] = await Promise.all([
            fetchAccountInfo(),
            fetchPortfolio(),
            fetchOrders()
        ]);

        if (!accountInfo || !portfolioData) {
            console.error('Failed to fetch portfolio data');
            return;
        }

        // Get unique symbols for live price fetching
        const symbols = [...new Set(portfolioData.positions.map(pos => pos.symbol))];
        const livePrices = await fetchLivePrices(symbols);

        // Update all sections
        updatePortfolioSummary(accountInfo, portfolioData, livePrices);
        updateHoldingsList(portfolioData, livePrices);
        updateRecentActivity(orders);
        createTotalInvestmentsChart(portfolioData, livePrices, accountInfo);
        createAllocationChart(portfolioData, livePrices);

    } catch (error) {
        console.error('Error updating portfolio:', error);
    }
}

// Initialize portfolio
document.addEventListener('DOMContentLoaded', async function() {
    await updatePortfolio();
    
    // Refresh portfolio data every 30 seconds
    setInterval(updatePortfolio, 30000);
}); 

// ... existing code ...

// Add timeframe selector functionality
let currentTimeframe = '1M';
let portfolioHistoryData = {};

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
            // If endpoint doesn't exist, generate simulated data
            return generateSimulatedPortfolioHistory(timeframe);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching portfolio history:', error);
        return generateSimulatedPortfolioHistory(timeframe);
    }
}

// Generate simulated portfolio history data
function generateSimulatedPortfolioHistory(timeframe) {
    const now = new Date();
    const data = [];
    let baseValue = 100000; // Starting portfolio value
    
    // Generate data points based on timeframe
    let days, interval;
    switch(timeframe) {
        case '1D':
            days = 1;
            interval = 15; // 15-minute intervals
            break;
        case '1W':
            days = 7;
            interval = 60; // 1-hour intervals
            break;
        case '1M':
            days = 30;
            interval = 1440; // Daily intervals
            break;
        case '3M':
            days = 90;
            interval = 1440; // Daily intervals
            break;
        case '1Y':
            days = 365;
            interval = 1440; // Daily intervals
            break;
        default:
            days = 30;
            interval = 1440;
    }
    
    const totalPoints = Math.floor((days * 24 * 60) / interval);
    
    for (let i = 0; i < totalPoints; i++) {
        const date = new Date(now.getTime() - (totalPoints - i) * interval * 60 * 1000);
        
        // Simulate realistic portfolio growth with some volatility
        const volatility = 0.02; // 2% daily volatility
        const growth = 0.0005; // 0.05% daily growth on average
        const randomFactor = (Math.random() - 0.5) * volatility;
        baseValue *= (1 + growth + randomFactor);
        
        data.push({
            date: date.toISOString(),
            value: Math.max(0, baseValue)
        });
    }
    
    return { data };
}

// Update the total investments chart with timeframe support
function createTotalInvestmentsChart(portfolioData, livePrices, accountInfo, timeframe = '1M') {
    const ctx = document.getElementById('total-investments-chart').getContext('2d');
    
    // Calculate current portfolio value
    const totalCurrentValue = portfolioData.positions.reduce((sum, pos) => {
        const currentPrice = livePrices[pos.symbol] || pos.current_price || pos.avg_entry_price;
        return sum + (pos.qty * currentPrice);
    }, 0);
    
    const cashValue = accountInfo?.cash || 0;
    const totalPortfolioValue = totalCurrentValue + cashValue;
    
    // Fetch historical data
    fetchPortfolioHistory(timeframe).then(historyData => {
        const labels = historyData.data.map(point => {
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
        
        const values = historyData.data.map(point => point.value);
        
        // Add current value as the last point
        labels.push('Now');
        values.push(totalPortfolioValue);
        
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
                    backgroundColor: 'rgba(118,185,0,0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointBackgroundColor: '#76b900',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#76b900',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `Portfolio Value: ${formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#e0e0e0' }
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { 
                            color: '#e0e0e0',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    });
}

// Add timeframe selector event listeners
function initializeTimeframeSelector() {
    const timeframeButtons = document.querySelectorAll('.timeframe-selector button');
    
    timeframeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            timeframeButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update current timeframe
            currentTimeframe = this.dataset.tf;
            
            // Refresh the chart with new timeframe
            updatePortfolio();
        });
    });
}

// Update the main updatePortfolio function
async function updatePortfolio() {
    try {
        const [accountInfo, portfolioData, orders] = await Promise.all([
            fetchAccountInfo(),
            fetchPortfolio(),
            fetchOrders()
        ]);

        if (!accountInfo || !portfolioData) {
            console.error('Failed to fetch portfolio data');
            return;
        }

        // Get unique symbols for live price fetching
        const symbols = [...new Set(portfolioData.positions.map(pos => pos.symbol))];
        const livePrices = await fetchLivePrices(symbols);

        // Update all sections
        updatePortfolioSummary(accountInfo, portfolioData, livePrices);
        updateHoldingsList(portfolioData, livePrices);
        updateRecentActivity(orders);
        createTotalInvestmentsChart(portfolioData, livePrices, accountInfo, currentTimeframe);
        createAllocationChart(portfolioData, livePrices);

    } catch (error) {
        console.error('Error updating portfolio:', error);
    }
}

// Initialize portfolio with timeframe selector
document.addEventListener('DOMContentLoaded', async function() {
    await updatePortfolio();
    initializeTimeframeSelector();
    
    // Refresh portfolio data every 30 seconds
    setInterval(updatePortfolio, 30000);
});