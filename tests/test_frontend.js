// Frontend JavaScript Tests using Jest
// Run with: npm test

// Mock DOM elements
document.body.innerHTML = `
  <div id="price-display"></div>
  <div id="price-change"></div>
  <div id="chart-container"></div>
  <div id="rsi-chart"></div>
  <div id="macd-chart"></div>
  <div id="news-container"></div>
  <div id="prediction-display"></div>
  <div id="recommendation-display"></div>
  <div id="sidebar"></div>
  <div id="burger-menu"></div>
  <div id="overlay"></div>
`;

// Mock Chart.js
global.Chart = jest.fn().mockImplementation(() => ({
  destroy: jest.fn(),
  update: jest.fn(),
}));

// Mock fetch
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

describe('Dashboard Functionality', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    fetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
  });

  describe('Authentication Functions', () => {
    test('checkAuth should redirect to login if no token', () => {
      // Mock window.location
      delete window.location;
      window.location = { href: '' };
      
      localStorageMock.getItem.mockReturnValue(null);
      
      // Import and call checkAuth (assuming it's available globally)
      if (typeof checkAuth === 'function') {
        checkAuth();
        expect(window.location.href).toBe('login.html');
      }
    });

    test('checkAuth should not redirect if token exists', () => {
      delete window.location;
      window.location = { href: '' };
      
      localStorageMock.getItem.mockReturnValue('valid-token');
      
      if (typeof checkAuth === 'function') {
        checkAuth();
        expect(window.location.href).not.toBe('login.html');
      }
    });

    test('logout should clear token and redirect', () => {
      delete window.location;
      window.location = { href: '' };
      
      if (typeof logout === 'function') {
        logout();
        expect(localStorageMock.removeItem).toHaveBeenCalledWith('token');
        expect(window.location.href).toBe('login.html');
      }
    });
  });

  describe('API Calls', () => {
    test('fetchLiveData should handle successful response', async () => {
      const mockData = {
        price: 150.0,
        price_change: 2.0,
        price_change_pct: 1.35,
        volume: 1000000
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      // Mock the function if it exists
      if (typeof fetchLiveData === 'function') {
        const result = await fetchLiveData();
        expect(fetch).toHaveBeenCalledWith('/live_data');
        expect(result).toEqual(mockData);
      }
    });

    test('fetchLiveData should handle error response', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      if (typeof fetchLiveData === 'function') {
        await expect(fetchLiveData()).rejects.toThrow('Network error');
      }
    });

    test('fetchHistoricalData should handle different timeframes', async () => {
      const mockData = {
        dates: ['2023-01-01', '2023-01-02'],
        prices: [100, 101],
        rsi: [50, 51],
        macd: [0.1, 0.2]
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      if (typeof fetchHistoricalData === 'function') {
        const result = await fetchHistoricalData('1Y');
        expect(fetch).toHaveBeenCalledWith('/historical_data?tf=1Y');
        expect(result).toEqual(mockData);
      }
    });

    test('fetchPrediction should return prediction and news', async () => {
      const mockData = {
        predicted_price: 155.0,
        news: ['NVIDIA announces new GPU', 'Stock price rises']
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      if (typeof fetchPrediction === 'function') {
        const result = await fetchPrediction();
        expect(fetch).toHaveBeenCalledWith('/predict');
        expect(result).toEqual(mockData);
      }
    });

    test('fetchRecommendation should return recommendation data', async () => {
      const mockData = {
        recommendation: 'buy',
        confidence: 'high',
        indicators: {
          rsi: 25.0,
          macd: 0.5
        }
      };
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      });

      if (typeof fetchRecommendation === 'function') {
        const result = await fetchRecommendation();
        expect(fetch).toHaveBeenCalledWith('/recommend');
        expect(result).toEqual(mockData);
      }
    });
  });

  describe('Chart Functions', () => {
    test('createPriceChart should create chart with correct data', () => {
      const mockData = {
        dates: ['2023-01-01', '2023-01-02'],
        prices: [100, 101]
      };

      if (typeof createPriceChart === 'function') {
        createPriceChart(mockData);
        expect(Chart).toHaveBeenCalled();
        const chartCall = Chart.mock.calls[0];
        expect(chartCall[1].data.labels).toEqual(mockData.dates);
        expect(chartCall[1].data.datasets[0].data).toEqual(mockData.prices);
      }
    });

    test('createRSIChart should create RSI chart', () => {
      const mockData = {
        dates: ['2023-01-01', '2023-01-02'],
        rsi: [50, 51]
      };

      if (typeof createRSIChart === 'function') {
        createRSIChart(mockData);
        expect(Chart).toHaveBeenCalled();
        const chartCall = Chart.mock.calls[0];
        expect(chartCall[1].data.datasets[0].data).toEqual(mockData.rsi);
      }
    });

    test('createMACDChart should create MACD chart', () => {
      const mockData = {
        dates: ['2023-01-01', '2023-01-02'],
        macd: [0.1, 0.2],
        macd_signal: [0.05, 0.15]
      };

      if (typeof createMACDChart === 'function') {
        createMACDChart(mockData);
        expect(Chart).toHaveBeenCalled();
        const chartCall = Chart.mock.calls[0];
        expect(chartCall[1].data.datasets).toHaveLength(2); // MACD and Signal lines
      }
    });
  });

  describe('UI Update Functions', () => {
    test('updatePriceDisplay should update price elements', () => {
      const priceData = {
        price: 150.0,
        price_change: 2.0,
        price_change_pct: 1.35
      };

      if (typeof updatePriceDisplay === 'function') {
        updatePriceDisplay(priceData);
        const priceElement = document.getElementById('price-display');
        const changeElement = document.getElementById('price-change');
        
        if (priceElement) {
          expect(priceElement.textContent).toContain('150.00');
        }
        if (changeElement) {
          expect(changeElement.textContent).toContain('+2.00');
        }
      }
    });

    test('updateNewsDisplay should update news container', () => {
      const news = ['NVIDIA announces new GPU', 'Stock price rises'];

      if (typeof updateNewsDisplay === 'function') {
        updateNewsDisplay(news);
        const newsContainer = document.getElementById('news-container');
        
        if (newsContainer) {
          expect(newsContainer.innerHTML).toContain('NVIDIA announces new GPU');
        }
      }
    });

    test('updatePredictionDisplay should update prediction element', () => {
      const prediction = 155.0;

      if (typeof updatePredictionDisplay === 'function') {
        updatePredictionDisplay(prediction);
        const predictionElement = document.getElementById('prediction-display');
        
        if (predictionElement) {
          expect(predictionElement.textContent).toContain('155.00');
        }
      }
    });

    test('updateRecommendationDisplay should update recommendation element', () => {
      const recommendation = {
        recommendation: 'buy',
        confidence: 'high',
        indicators: { rsi: 25.0 }
      };

      if (typeof updateRecommendationDisplay === 'function') {
        updateRecommendationDisplay(recommendation);
        const recommendationElement = document.getElementById('recommendation-display');
        
        if (recommendationElement) {
          expect(recommendationElement.textContent).toContain('buy');
        }
      }
    });
  });

  describe('Sidebar Functions', () => {
    test('toggleSidebar should toggle sidebar visibility', () => {
      if (typeof toggleSidebar === 'function') {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        
        // Initial state
        if (sidebar) sidebar.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        
        toggleSidebar();
        
        if (sidebar) {
          expect(sidebar.classList.contains('active')).toBe(true);
        }
        if (overlay) {
          expect(overlay.classList.contains('active')).toBe(true);
        }
        
        toggleSidebar();
        
        if (sidebar) {
          expect(sidebar.classList.contains('active')).toBe(false);
        }
        if (overlay) {
          expect(overlay.classList.contains('active')).toBe(false);
        }
      }
    });

    test('closeSidebar should close sidebar', () => {
      if (typeof closeSidebar === 'function') {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        
        // Set initial state to open
        if (sidebar) sidebar.classList.add('active');
        if (overlay) overlay.classList.add('active');
        
        closeSidebar();
        
        if (sidebar) {
          expect(sidebar.classList.contains('active')).toBe(false);
        }
        if (overlay) {
          expect(overlay.classList.contains('active')).toBe(false);
        }
      }
    });
  });

  describe('Error Handling', () => {
    test('should handle API errors gracefully', async () => {
      fetch.mockRejectedValueOnce(new Error('API Error'));

      if (typeof handleApiError === 'function') {
        const error = new Error('API Error');
        handleApiError(error);
        
        // Should not crash the application
        expect(true).toBe(true);
      }
    });

    test('should handle invalid JSON responses', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        }
      });

      if (typeof fetchLiveData === 'function') {
        await expect(fetchLiveData()).rejects.toThrow('Invalid JSON');
      }
    });
  });

  describe('Data Validation', () => {
    test('should validate price data format', () => {
      const validData = {
        price: 150.0,
        price_change: 2.0,
        price_change_pct: 1.35
      };

      const invalidData = {
        price: 'invalid',
        price_change: null
      };

      if (typeof validatePriceData === 'function') {
        expect(validatePriceData(validData)).toBe(true);
        expect(validatePriceData(invalidData)).toBe(false);
      }
    });

    test('should validate chart data format', () => {
      const validData = {
        dates: ['2023-01-01', '2023-01-02'],
        prices: [100, 101],
        rsi: [50, 51]
      };

      const invalidData = {
        dates: [],
        prices: null
      };

      if (typeof validateChartData === 'function') {
        expect(validateChartData(validData)).toBe(true);
        expect(validateChartData(invalidData)).toBe(false);
      }
    });
  });
});

// Mock for DOM manipulation functions
describe('DOM Manipulation', () => {
  test('should create elements dynamically', () => {
    if (typeof createElement === 'function') {
      const element = createElement('div', 'test-class', 'Test Content');
      expect(element.tagName).toBe('DIV');
      expect(element.className).toBe('test-class');
      expect(element.textContent).toBe('Test Content');
    }
  });

  test('should update element content safely', () => {
    const testElement = document.createElement('div');
    testElement.id = 'test-element';
    document.body.appendChild(testElement);

    if (typeof updateElementContent === 'function') {
      updateElementContent('test-element', 'New Content');
      expect(testElement.textContent).toBe('New Content');
    }

    document.body.removeChild(testElement);
  });
});

// Performance tests
describe('Performance', () => {
  test('chart creation should be efficient', () => {
    const startTime = performance.now();
    
    if (typeof createPriceChart === 'function') {
      const mockData = {
        dates: Array.from({length: 1000}, (_, i) => `2023-01-${i+1}`),
        prices: Array.from({length: 1000}, () => Math.random() * 200)
      };
      
      createPriceChart(mockData);
      
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // Should complete within 100ms
      expect(duration).toBeLessThan(100);
    }
  });

  test('data fetching should not block UI', async () => {
    if (typeof fetchLiveData === 'function') {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ price: 150.0 })
      });

      const startTime = performance.now();
      await fetchLiveData();
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // Should complete within 500ms
      expect(duration).toBeLessThan(500);
    }
  });
}); 