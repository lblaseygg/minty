// Trading page functionality
let orders = [];
let accountInfo = {};

// Sidebar functions
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    const burgerMenu = document.querySelector('.burger-menu');
    
    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
    burgerMenu.classList.toggle('active');
}

function searchStock() {
    const searchInput = document.getElementById('stock-search');
    const query = searchInput.value.trim().toUpperCase();
    
    if (query) {
        // Navigate to the stock page with the searched symbol
        window.location.href = `index.html?symbol=${query}`;
    }
}

// Check authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadAccountInfo();
    loadPortfolioPositions();
    loadOrderHistory();
    loadAvailableStocks();
    
    // Handle URL parameters for pre-selecting side
    const urlParams = new URLSearchParams(window.location.search);
    const side = urlParams.get('side');
    if (side && (side === 'buy' || side === 'sell')) {
        document.getElementById('side').value = side;
    }
});

// Authentication functions
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
}

// API functions
async function makeAuthenticatedRequest(url, options = {}) {
    const token = localStorage.getItem('token');
    if (!token) {
        throw new Error('No authentication token');
    }

    const defaultOptions = {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    };

    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
        return;
    }

    return response;
}

// Account functions
async function loadAccountInfo() {
    try {
        const response = await makeAuthenticatedRequest('/account');
        if (response.ok) {
            accountInfo = await response.json();
            updateAccountDisplay();
        } else {
            console.error('Failed to load account info');
        }
    } catch (error) {
        console.error('Error loading account info:', error);
        showMessage('Error loading account information', 'error');
    }
}

// Stock functions
async function loadAvailableStocks() {
    try {
        const response = await fetch('/stocks');
        if (response.ok) {
            const stocks = await response.json();
            populateStockDropdown(stocks);
        } else {
            console.error('Failed to load available stocks');
        }
    } catch (error) {
        console.error('Error loading available stocks:', error);
        showMessage('Error loading available stocks', 'error');
    }
}

function populateStockDropdown(stocks) {
    const symbolSelect = document.getElementById('symbol');
    const symbolFilter = document.getElementById('symbol-filter');
    
    // Clear existing options except the first placeholder
    symbolSelect.innerHTML = '<option value="">Select a stock...</option>';
    symbolFilter.innerHTML = '<option value="">All Symbols</option>';
    
    // Add stock options to both dropdowns
    Object.entries(stocks).forEach(([symbol, stockInfo]) => {
        // Add to main symbol select
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = `${symbol} - ${stockInfo.name}`;
        symbolSelect.appendChild(option);
        
        // Add to symbol filter
        const filterOption = document.createElement('option');
        filterOption.value = symbol;
        filterOption.textContent = symbol;
        symbolFilter.appendChild(filterOption);
    });
    
    // Set default value to NVDA if available
    if (stocks.NVDA) {
        symbolSelect.value = 'NVDA';
    }
    
    // Add search functionality to the dropdown
    symbolSelect.addEventListener('keydown', function(e) {
        if (e.key.length === 1) {
            // User typed a character, search for matching options
            const searchChar = e.key.toLowerCase();
            const options = Array.from(this.options);
            
            // Find the first option that starts with the typed character
            const matchingOption = options.find(option => 
                option.value.toLowerCase().startsWith(searchChar)
            );
            
            if (matchingOption) {
                this.value = matchingOption.value;
            }
        }
    });
    
    // Add change event to show current price when stock is selected
    symbolSelect.addEventListener('change', function() {
        const selectedSymbol = this.value;
        if (selectedSymbol) {
            showCurrentPrice(selectedSymbol);
        }
    });
}

// Function to show current price for selected stock
async function showCurrentPrice(symbol) {
    try {
        const response = await fetch(`/live_data/${symbol}`);
        if (response.ok) {
            const data = await response.json();
            const price = data.price;
            if (price) {
                // Update the price field with current market price
                const priceInput = document.getElementById('price');
                if (priceInput) {
                    priceInput.placeholder = `Current price: $${price.toFixed(2)}`;
                    priceInput.title = `Current market price: $${price.toFixed(2)}`;
                }
            }
        }
    } catch (error) {
        console.error('Error fetching current price:', error);
    }
}

function updateAccountDisplay() {
    document.getElementById('cash-amount').textContent = formatCurrency(accountInfo.cash || 0);
    document.getElementById('buying-power').textContent = formatCurrency(accountInfo.buying_power || 0);
    document.getElementById('portfolio-value').textContent = formatCurrency(accountInfo.portfolio_value || 0);
    document.getElementById('equity').textContent = formatCurrency(accountInfo.equity || 0);
}

// Portfolio functions
async function loadPortfolioPositions() {
    try {
        const response = await makeAuthenticatedRequest('/portfolio');
        if (response.ok) {
            const data = await response.json();
            updatePositionsDisplay(data.positions || []);
        } else {
            console.error('Failed to load portfolio positions');
        }
    } catch (error) {
        console.error('Error loading portfolio positions:', error);
    }
}

function updatePositionsDisplay(positions) {
    const container = document.getElementById('positions-container');
    
    if (positions.length === 0) {
        container.innerHTML = '<p class="no-positions">No positions yet. Start trading to see your portfolio!</p>';
        return;
    }

    const positionsHTML = positions.map(position => `
        <div class="position-item">
            <div class="position-header">
                <h3>${position.symbol}</h3>
                <span class="position-qty">${position.qty} shares</span>
            </div>
            <div class="position-details">
                <div class="position-stat">
                    <span class="stat-label">Avg Entry</span>
                    <span class="stat-value">${formatCurrency(position.avg_entry_price)}</span>
                </div>
                <div class="position-stat">
                    <span class="stat-label">Current Price</span>
                    <span class="stat-value">${formatCurrency(position.current_price)}</span>
                </div>
                <div class="position-stat">
                    <span class="stat-label">Market Value</span>
                    <span class="stat-value">${formatCurrency(position.market_value)}</span>
                </div>
                <div class="position-stat">
                    <span class="stat-label">Unrealized P&L</span>
                    <span class="stat-value ${position.unrealized_pl >= 0 ? 'positive' : 'negative'}">
                        ${formatCurrency(position.unrealized_pl)}
                    </span>
                </div>
            </div>
        </div>
    `).join('');

    container.innerHTML = positionsHTML;
}

// Order functions
async function loadOrderHistory() {
    try {
        const symbolFilter = document.getElementById('symbol-filter').value;
        const sideFilter = document.getElementById('side-filter').value;
        const statusFilter = document.getElementById('status-filter').value;

        let url = '/orders';
        const params = new URLSearchParams();
        if (symbolFilter) params.append('symbol', symbolFilter);
        if (sideFilter) params.append('side', sideFilter);
        if (statusFilter) params.append('status', statusFilter);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }

        const response = await makeAuthenticatedRequest(url);
        if (response.ok) {
            orders = await response.json();
            updateOrdersDisplay();
        } else {
            console.error('Failed to load order history');
        }
    } catch (error) {
        console.error('Error loading order history:', error);
        showMessage('Error loading order history', 'error');
    }
}

function updateOrdersDisplay() {
    const tbody = document.getElementById('orders-tbody');
    
    if (orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-orders">No orders found</td></tr>';
        return;
    }

    const ordersHTML = orders.map(order => `
        <tr>
            <td>${formatDate(order.timestamp)}</td>
            <td><strong>${order.symbol}</strong></td>
            <td>
                <span class="order-side ${order.side}">
                    ${order.side.toUpperCase()}
                </span>
            </td>
            <td>${order.qty}</td>
            <td>${formatCurrency(order.price)}</td>
            <td>${formatCurrency(order.total_value || order.qty * order.price)}</td>
            <td>
                <span class="order-status ${order.status}">
                    ${order.status.toUpperCase()}
                </span>
            </td>
            <td>
                ${order.status === 'pending' ? 
                    `<button onclick="cancelOrder(${order.id})" class="btn btn-small btn-danger">
                        <i class="fas fa-times"></i> Cancel
                    </button>` : 
                    '-'
                }
            </td>
        </tr>
    `).join('');

    tbody.innerHTML = ordersHTML;
}

async function placeOrder(orderData) {
    try {
        showLoading(true);
        
        const response = await makeAuthenticatedRequest('/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });

        if (response.ok) {
            const result = await response.json();
            
            // Show receipt instead of just a message
            showReceipt(result, orderData);
            
            // Reset form
            document.getElementById('order-form').reset();
            
            // Reload data
            await Promise.all([
                loadAccountInfo(),
                loadPortfolioPositions(),
                loadOrderHistory()
            ]);
        } else {
            const error = await response.json();
            showMessage(`Order failed: ${error.error}`, 'error');
        }
    } catch (error) {
        console.error('Error placing order:', error);
        showMessage('Error placing order. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// Receipt functions
function showReceipt(orderResult, orderData) {
    const modal = document.getElementById('receipt-modal');
    const now = new Date();
    
    // Update receipt content
    document.getElementById('receipt-order-id').textContent = orderResult.order_id || orderResult.id || 'N/A';
    document.getElementById('receipt-date').textContent = now.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('receipt-symbol').textContent = orderData.symbol;
    document.getElementById('receipt-side').textContent = orderData.side.toUpperCase();
    document.getElementById('receipt-qty').textContent = orderData.qty.toLocaleString();
    
    // Show actual price if available, otherwise show market price
    const actualPrice = orderResult.price || orderData.price;
    document.getElementById('receipt-price').textContent = actualPrice ? formatCurrency(actualPrice) : 'Market Price';
    
    // Remove total amount row
    const totalRow = document.querySelector('.receipt-details .detail-row.total');
    if (totalRow) {
        totalRow.style.display = 'none';
    }
    
    // Update status based on order result
    const statusText = document.getElementById('receipt-status-text');
    const statusDesc = document.getElementById('receipt-status-desc');
    const statusIcon = document.querySelector('.status-icon');
    
    if (orderResult.status === 'filled' || orderResult.status === 'accepted') {
        statusText.textContent = 'Order Confirmed';
        statusDesc.textContent = 'Your order has been successfully placed';
        statusIcon.className = 'status-icon success';
        statusIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
    } else {
        statusText.textContent = 'Order Pending';
        statusDesc.textContent = 'Your order is being processed';
        statusIcon.className = 'status-icon success';
        statusIcon.innerHTML = '<i class="fas fa-clock"></i>';
    }
    
    // Show modal
    modal.classList.add('show');
}

function closeReceipt() {
    const modal = document.getElementById('receipt-modal');
    modal.classList.remove('show');
}

function viewPortfolio() {
    closeReceipt();
    window.location.href = 'portfolio.html';
}

async function cancelOrder(orderId) {
    if (!confirm('Are you sure you want to cancel this order?')) {
        return;
    }

    try {
        const response = await makeAuthenticatedRequest(`/orders/${orderId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showMessage('Order cancelled successfully', 'success');
            await loadOrderHistory();
        } else {
            const error = await response.json();
            showMessage(`Failed to cancel order: ${error.error}`, 'error');
        }
    } catch (error) {
        console.error('Error cancelling order:', error);
        showMessage('Error cancelling order', 'error');
    }
}

// Form handling
document.getElementById('order-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const orderData = {
        symbol: formData.get('symbol').toUpperCase(),
        side: formData.get('side'),
        qty: parseInt(formData.get('qty')),
        price: formData.get('price') ? parseFloat(formData.get('price')) : null
    };

    // Validation
    if (orderData.qty <= 0) {
        showMessage('Quantity must be greater than 0', 'error');
        return;
    }

    if (orderData.price !== null && orderData.price <= 0) {
        showMessage('Price must be greater than 0', 'error');
        return;
    }

    placeOrder(orderData);
});

// Filter event listeners
document.getElementById('symbol-filter').addEventListener('change', loadOrderHistory);
document.getElementById('side-filter').addEventListener('change', loadOrderHistory);
document.getElementById('status-filter').addEventListener('change', loadOrderHistory);

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = show ? 'flex' : 'none';
}

function showMessage(message, type = 'info') {
    const container = document.getElementById('message-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    
    container.appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 5000);
}

// Auto-refresh account info every 30 seconds
setInterval(loadAccountInfo, 30000); 