let priceChart, rsiChart, macdChart;
let currentTimeframe = '1Y';
let lastLabels = { price: [], rsi: [], macd: [] };

// Stock information data
const STOCK_INFO = {
    'NVDA': {
        name: 'NVIDIA',
        description: 'NVIDIA Corporation is a multinational technology company that designs graphics processing units (GPUs) for the gaming and professional markets, as well as system on a chip units (SoCs) for the mobile computing and automotive market.',
        sector: 'Technology',
        industry: 'Semiconductors',
        founded: '1993',
        headquarters: 'Santa Clara, California'
    },
    'AAPL': {
        name: 'Apple',
        description: 'Apple Inc. is an American multinational technology company that specializes in consumer electronics, computer software, and online services. Apple is the world\'s largest technology company by revenue.',
        sector: 'Technology',
        industry: 'Consumer Electronics',
        founded: '1976',
        headquarters: 'Cupertino, California'
    },
    'GOOGL': {
        name: 'Google',
        description: 'Alphabet Inc. is an American multinational technology conglomerate holding company. It is the parent company of Google and several former Google subsidiaries.',
        sector: 'Technology',
        industry: 'Internet Services',
        founded: '1998',
        headquarters: 'Mountain View, California'
    },
    'MSFT': {
        name: 'Microsoft',
        description: 'Microsoft Corporation is an American multinational technology company which produces computer software, consumer electronics, personal computers, and related services.',
        sector: 'Technology',
        industry: 'Software',
        founded: '1975',
        headquarters: 'Redmond, Washington'
    },
    'TSLA': {
        name: 'Tesla',
        description: 'Tesla, Inc. is an American electric vehicle and clean energy company based in Austin, Texas. Tesla designs and manufactures electric cars, battery energy storage, solar panels, and related products and services.',
        sector: 'Consumer Discretionary',
        industry: 'Automobiles',
        founded: '2003',
        headquarters: 'Austin, Texas'
    },
    'META': {
        name: 'Meta',
        description: 'Meta Platforms, Inc. is an American multinational technology conglomerate. The company owns Facebook, Instagram, and WhatsApp, among other products and services.',
        sector: 'Technology',
        industry: 'Internet Services',
        founded: '2004',
        headquarters: 'Menlo Park, California'
    },
    'AMZN': {
        name: 'Amazon',
        description: 'Amazon.com, Inc. is an American multinational technology company focusing on e-commerce, cloud computing, digital streaming, and artificial intelligence.',
        sector: 'Consumer Discretionary',
        industry: 'Internet Retail',
        founded: '1994',
        headquarters: 'Seattle, Washington'
    },
    'AMD': {
        name: 'AMD',
        description: 'Advanced Micro Devices, Inc. is an American multinational semiconductor company that develops computer processors and related technologies for business and consumer markets.',
        sector: 'Technology',
        industry: 'Semiconductors',
        founded: '1969',
        headquarters: 'Santa Clara, California'
    }
};

// Function to update about section
function updateAboutSection(symbol) {
    const stockInfo = STOCK_INFO[symbol] || STOCK_INFO['NVDA']; // Default to NVIDIA if not found
    
    // Update the about section elements
    document.getElementById('about-stock-name').textContent = stockInfo.name;
    document.getElementById('about-description').textContent = stockInfo.description;
    document.getElementById('about-sector').textContent = stockInfo.sector;
    document.getElementById('about-industry').textContent = stockInfo.industry;
    document.getElementById('about-founded').textContent = stockInfo.founded;
    document.getElementById('about-headquarters').textContent = stockInfo.headquarters;
    
    // Also update the stock name in the header
    document.getElementById('stock-name').textContent = stockInfo.name;
}

// Utility to get symbol from URL
function getSelectedSymbol() {
    const params = new URLSearchParams(window.location.search);
    const symbol = params.get('symbol');
    return symbol ? symbol.toUpperCase() : 'NVDA';
}

const selectedSymbol = getSelectedSymbol();

async function fetchLiveData() {
    try {
        const res = await fetch(`/live_data/${selectedSymbol}`);
        if (!res.ok) throw new Error('Network response was not ok');
        return await res.json();
    } catch (e) {
        return {};
    }
}

async function fetchHistoricalData(tf = '1Y') {
    const res = await fetch(`/historical_data/${selectedSymbol}?tf=${tf}`);
    return await res.json();
}

async function fetchPrediction() {
    const res = await fetch(`/predict/${selectedSymbol}`);
    return await res.json();
}

async function fetchRecommendation() {
    const res = await fetch(`/recommend/${selectedSymbol}`);
    return await res.json();
}

function updateLiveStats(live) {
    // Live price and change
    const priceElem = document.getElementById('current-price');
    const changeElem = document.getElementById('price-change');
    priceElem.textContent = live && live.price ? `$${live.price.toFixed(2)}` : '--';
    let changeText = '--';
    let changeClass = 'neutral';
    if (live && live.price_change !== undefined && live.price_change_pct !== undefined) {
        const isUp = live.price_change > 0;
        changeText = `${isUp ? '+' : ''}${live.price_change.toFixed(2)} (${isUp ? '+' : ''}${live.price_change_pct.toFixed(2)}%)`;
        changeClass = isUp ? 'up' : (live.price_change < 0 ? 'down' : 'neutral');
    }
    changeElem.textContent = changeText;
    changeElem.className = changeClass;

    // Key stats (simplified)
    document.getElementById('stat-open').textContent = live && live.open !== undefined ? `$${live.open}` : '--';
    document.getElementById('stat-high').textContent = live && live.dayHigh !== undefined ? `$${live.dayHigh}` : '--';
    document.getElementById('stat-low').textContent = live && live.dayLow !== undefined ? `$${live.dayLow}` : '--';
    document.getElementById('stat-volume').textContent = (live && typeof live.volume === 'number' && !isNaN(live.volume)) ? live.volume.toLocaleString() : '--';
}

function setActiveTimeframe(tf) {
    document.querySelectorAll('.timeframe-selector button').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tf') === tf);
    });
}

function updateOrCreateChart(chartRef, ctx, config, lastLabelsKey, newLabels, forceRecreate = false) {
    if (forceRecreate && chartRef) {
        chartRef.destroy();
        chartRef = null;
    }
    if (!chartRef || !lastLabels[lastLabelsKey] || lastLabels[lastLabelsKey].length !== newLabels.length) {
        lastLabels[lastLabelsKey] = [...newLabels];
        return new Chart(ctx, config);
    } else {
        chartRef.data.labels = newLabels;
        chartRef.data.datasets.forEach((ds, i) => {
            ds.data = config.data.datasets[i].data;
        });
        chartRef.update();
        return chartRef;
    }
}

function renderCharts(historical, forceRecreate = false) {
    // Price Chart (simplified, no volume)
    const priceCtx = document.getElementById('price-chart').getContext('2d');
    const priceConfig = {
        type: 'line',
        data: {
            labels: historical.dates,
            datasets: [
                {
                    label: '',
                    data: historical.prices,
                    borderColor: '#cce3de',
                    backgroundColor: 'rgba(204, 227, 222, 0.08)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { 
                    display: false,
                    labels: { color: '#ffffff' }
                },
                title: { 
                    display: false,
                    color: '#ffffff'
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 10, 10, 0.95)',
                    titleColor: '#ffffff',
                    bodyColor: '#cce3de',
                    borderColor: '#cce3de',
                    borderWidth: 1,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return `Price: $${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: false, // Hide x-axis labels
                    grid: { color: 'rgba(204, 227, 222, 0.1)' }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { 
                        display: true, 
                        text: 'Price', 
                        color: '#ffffff',
                        font: { size: 12 }
                    },
                    ticks: { 
                        color: '#ffffff', 
                        font: { size: 12 },
                        callback: v => `$${v}` 
                    },
                    grid: { color: 'rgba(204, 227, 222, 0.1)' }
                }
            }
        }
    };
    priceChart = updateOrCreateChart(priceChart, priceCtx, priceConfig, 'price', historical.dates, forceRecreate);

    // RSI Chart
    const rsiCtx = document.getElementById('rsi-chart').getContext('2d');
    const rsiConfig = {
        type: 'line',
        data: {
            labels: historical.dates,
            datasets: [
                {
                    label: 'RSI',
                    data: historical.rsi,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { 
                    labels: { 
                        color: '#ffffff',
                        font: { size: 12 }
                    } 
                },
                title: { 
                    display: false,
                    color: '#ffffff'
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 10, 10, 0.95)',
                    titleColor: '#ffffff',
                    bodyColor: '#cce3de',
                    borderColor: '#cce3de',
                    borderWidth: 1,
                    cornerRadius: 8
                }
            },
            scales: {
                x: {
                    display: false,
                    grid: { color: 'rgba(204, 227, 222, 0.1)' }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { 
                        display: true, 
                        text: 'RSI', 
                        color: '#ffffff',
                        font: { size: 12 }
                    },
                    ticks: { 
                        color: '#ffffff',
                        font: { size: 12 }
                    },
                    grid: { color: 'rgba(204, 227, 222, 0.1)' }
                }
            }
        }
    };
    rsiChart = updateOrCreateChart(rsiChart, rsiCtx, rsiConfig, 'rsi', historical.dates, forceRecreate);

    // MACD Chart (simplified, no histogram)
    const macdCtx = document.getElementById('macd-chart').getContext('2d');
    const macdConfig = {
        type: 'line',
        data: {
            labels: historical.dates,
            datasets: [
                {
                    label: 'MACD',
                    data: historical.macd,
                    borderColor: '#ffd700',
                    backgroundColor: 'rgba(255,215,0,0.08)',
                    borderWidth: 1,
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0
                },
                {
                    label: 'Signal',
                    data: historical.macd_signal,
                    borderColor: '#76b900',
                    backgroundColor: 'rgba(118,185,0,0.08)',
                    borderWidth: 1,
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#000000' } },
                title: { display: false }
            },
            scales: {
                x: {
                    display: false, // Hide x-axis labels
                    grid: { color: 'rgba(0,0,0,0.1)' }
                },
                y: { ticks: { color: '#000000' }, grid: { color: 'rgba(0,0,0,0.1)' } }
            }
        }
    };
    macdChart = updateOrCreateChart(macdChart, macdCtx, macdConfig, 'macd', historical.dates, forceRecreate);
}

async function updateDashboard(tf = currentTimeframe, forceRecreate = false) {
    // Update about section with current stock
    updateAboutSection(selectedSymbol);
    
    // Fetch and update live stats
    const live = await fetchLiveData();
    updateLiveStats(live);

    // Fetch and render historical charts
    const historical = await fetchHistoricalData(tf);

    // Append the latest price to the chart if it's newer
    if (live && live.price && historical.dates && historical.prices) {
        // Try to get the current date and time in the same format as historical.dates
        const now = new Date();
        let latestLabel = '';
        if (historical.dates.length > 0) {
            latestLabel = historical.dates[historical.dates.length - 1];
        }
        // For intraday, use time; for daily, use date
        let liveLabel = now.toISOString().slice(0, 16).replace('T', ' '); // 'YYYY-MM-DD HH:MM'
        // Only append if the price is new (not already the last point)
        if (latestLabel !== liveLabel) {
            historical.dates.push(liveLabel);
            historical.prices.push(live.price);
        }
    }

    renderCharts(historical, forceRecreate);

    // Fetch and update AI recommendation and news
    const rec = await fetchRecommendation();
    const recommendationElement = document.getElementById('recommendation');
    const confidenceElement = document.getElementById('confidence');
    if (!rec.recommendation || rec.recommendation === 'Not enough data') {
        recommendationElement.textContent = 'Not enough data for recommendation';
        recommendationElement.className = '';
    } else {
        recommendationElement.textContent = rec.recommendation;
        recommendationElement.className = rec.recommendation;
    }
    if (!rec.confidence || rec.confidence === 'Not enough data') {
        confidenceElement.textContent = 'Not enough data';
    } else {
        confidenceElement.textContent = rec.confidence;
    }

    // Fetch prediction and news (for news only)
    const pred = await fetchPrediction();
    const newsList = document.getElementById('news-list');
    newsList.innerHTML = '';
    if (pred.news && pred.news.length > 0) {
        pred.news.forEach(news => {
            const li = document.createElement('li');
            li.textContent = news;
            newsList.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = 'No news available.';
        newsList.appendChild(li);
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    // Timeframe button logic
    document.querySelectorAll('.timeframe-selector button').forEach(btn => {
        btn.addEventListener('click', async function() {
            const tf = btn.getAttribute('data-tf');
            if (tf !== currentTimeframe) {
                currentTimeframe = tf;
                setActiveTimeframe(tf);
                await updateDashboard(tf, true); // Force chart recreation
            }
        });
    });

    // Buy/Sell button logic
    document.getElementById('buy-btn').addEventListener('click', function() {
        window.location.href = `trade.html?symbol=${selectedSymbol}&side=buy`;
    });

    document.getElementById('sell-btn').addEventListener('click', function() {
        window.location.href = `trade.html?symbol=${selectedSymbol}&side=sell`;
    });

    await updateDashboard(currentTimeframe, true);
    setInterval(() => updateDashboard(currentTimeframe, false), 15000); // Refresh every 15 seconds
}); 