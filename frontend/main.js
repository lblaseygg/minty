let priceChart, rsiChart, macdChart;
let currentTimeframe = '1Y';
let lastLabels = { price: [], rsi: [], macd: [] };

async function fetchLiveData() {
    try {
        const res = await fetch('/live_data');
        if (!res.ok) throw new Error('Network response was not ok');
        return await res.json();
    } catch (e) {
        return {};
    }
}

async function fetchHistoricalData(tf = '1Y') {
    const res = await fetch(`/historical_data?tf=${tf}`);
    return await res.json();
}

async function fetchPrediction() {
    const res = await fetch('/predict');
    return await res.json();
}

async function fetchRecommendation() {
    const res = await fetch('/recommend');
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
                    borderColor: '#76b900',
                    backgroundColor: 'rgba(118,185,0,0.08)',
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
                legend: { display: false },
                title: { display: false },
                tooltip: {
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
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Price', color: '#e0e0e0' },
                    ticks: { color: '#e0e0e0', callback: v => `$${v}` },
                    grid: { color: 'rgba(255,255,255,0.08)' }
                }
            }
        }
    };
    priceChart = updateOrCreateChart(priceChart, priceCtx, priceConfig, 'price', historical.dates, forceRecreate);

    // RSI Chart (unchanged)
    const rsiCtx = document.getElementById('rsi-chart').getContext('2d');
    const rsiConfig = {
        type: 'line',
        data: {
            labels: historical.dates,
            datasets: [
                {
                    label: 'RSI',
                    data: historical.rsi,
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76,175,80,0.08)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e0e0e0' } },
                title: { display: false }
            },
            scales: {
                x: {
                    display: false, // Hide x-axis labels
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y: {
                    min: 0, max: 100,
                    ticks: { color: '#e0e0e0' },
                    grid: { color: 'rgba(255,255,255,0.08)' }
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
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0
                },
                {
                    label: 'Signal',
                    data: historical.macd_signal,
                    borderColor: '#76b900',
                    backgroundColor: 'rgba(118,185,0,0.08)',
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { labels: { color: '#e0e0e0' } },
                title: { display: false }
            },
            scales: {
                x: {
                    display: false, // Hide x-axis labels
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y: { ticks: { color: '#e0e0e0' }, grid: { color: 'rgba(255,255,255,0.08)' } }
            }
        }
    };
    macdChart = updateOrCreateChart(macdChart, macdCtx, macdConfig, 'macd', historical.dates, forceRecreate);
}

async function updateDashboard(tf = currentTimeframe, forceRecreate = false) {
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
    await updateDashboard(currentTimeframe, true);
    setInterval(() => updateDashboard(currentTimeframe, false), 15000); // Refresh every 15 seconds
}); 