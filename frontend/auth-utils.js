// Authentication utilities for Minty
// This file contains shared authentication functions used across all pages

// Clear all user-specific data from localStorage and browser memory
function clearUserData() {
    // Clear all localStorage items except for any non-user-specific settings
    const keysToKeep = ['theme', 'language']; // Add any global settings you want to keep
    const keysToRemove = [];
    
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && !keysToKeep.includes(key)) {
            keysToRemove.push(key);
        }
    }
    
    keysToRemove.forEach(key => {
        localStorage.removeItem(key);
    });
    
    // Clear any cached data in memory
    if (typeof window !== 'undefined') {
        // Clear any global variables that might hold user data
        if (window.portfolioData) delete window.portfolioData;
        if (window.userData) delete window.userData;
        if (window.chartData) delete window.chartData;
        
        // Clear any chart instances that might be holding data
        if (window.priceChart) {
            window.priceChart.destroy();
            window.priceChart = null;
        }
        if (window.rsiChart) {
            window.rsiChart.destroy();
            window.rsiChart = null;
        }
        if (window.macdChart) {
            window.macdChart.destroy();
            window.macdChart = null;
        }
        if (window.totalInvestmentsChart) {
            window.totalInvestmentsChart.destroy();
            window.totalInvestmentsChart = null;
        }
        if (window.allocationChart) {
            window.allocationChart.destroy();
            window.allocationChart = null;
        }
    }
    
    console.log('Cleared all user-specific data');
}

// Check if user is authenticated
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Logout function that clears all user data
function logout() {
    // Clear all user data before logout
    clearUserData();
    window.location.href = 'login.html';
}

// Make functions globally available
window.clearUserData = clearUserData;
window.checkAuth = checkAuth;
window.logout = logout; 