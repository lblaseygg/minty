import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Test configuration
pytest_plugins = []

@pytest.fixture(scope="session")
def test_config():
    """Test configuration for the entire test session"""
    return {
        'TESTING': True,
        'JWT_SECRET_KEY': 'test-secret-key-for-testing',
        'DATABASE_URL': 'sqlite:///:memory:',  # Use in-memory database for tests
        'FINNHUB_API_KEY': 'test-api-key'
    }

@pytest.fixture(scope="session")
def temp_data_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def mock_yfinance():
    """Mock yfinance for testing"""
    with patch('backend.app.yf') as mock_yf:
        # Mock ticker info
        mock_info = {
            'currentPrice': 150.0,
            'previousClose': 148.0,
            'volume': 1000000,
            'dayHigh': 152.0,
            'dayLow': 147.0,
            'open': 149.0
        }
        
        # Mock history data
        mock_history = MagicMock()
        mock_history.empty = False
        mock_history.__getitem__ = lambda self, key: {
            'Close': [150.0, 151.0],
            'Volume': [1000000, 1100000],
            'Open': [149.0, 150.0],
            'High': [152.0, 153.0],
            'Low': [147.0, 148.0]
        }.get(key, [])
        
        mock_ticker = MagicMock()
        mock_ticker.info = mock_info
        mock_ticker.history.return_value = mock_history
        mock_yf.Ticker.return_value = mock_ticker
        
        yield mock_yf

@pytest.fixture(scope="function")
def mock_requests():
    """Mock requests for testing external APIs"""
    with patch('backend.app.requests') as mock_req:
        # Mock Finnhub API response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'headline': 'NVIDIA announces new GPU'},
            {'headline': 'Stock price rises'},
            {'headline': 'Market analysis positive'}
        ]
        mock_response.status_code = 200
        mock_req.get.return_value = mock_response
        
        yield mock_req

@pytest.fixture(scope="function")
def mock_model():
    """Mock ML model components"""
    with patch('backend.model.load_and_train') as mock_load:
        # Mock model components
        mock_data = MagicMock()
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = [[0.5] * 30]
        mock_model = MagicMock()
        mock_model.predict.return_value = [155.0]
        mock_features = [f'feature_{i}' for i in range(30)]
        
        mock_load.return_value = (mock_data, mock_scaler, mock_model, mock_features)
        
        yield mock_load

@pytest.fixture(scope="function")
def sample_stock_data():
    """Sample stock data for testing"""
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    data = pd.DataFrame({
        'Date': dates,
        'Open': np.random.uniform(100, 200, 100),
        'High': np.random.uniform(150, 250, 100),
        'Low': np.random.uniform(50, 150, 100),
        'Close': np.random.uniform(100, 200, 100),
        'Volume': np.random.uniform(1000000, 5000000, 100)
    })
    
    return data

@pytest.fixture(scope="function")
def sample_user_data():
    """Sample user data for testing"""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword123'
    }

@pytest.fixture(scope="function")
def sample_order_data():
    """Sample order data for testing"""
    return {
        'symbol': 'NVDA',
        'side': 'buy',
        'qty': 10,
        'price': 150.0
    }

@pytest.fixture(scope="function")
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        'preferences': '{"theme": "dark", "notifications": true}'
    }

@pytest.fixture(scope="function")
def auth_headers():
    """Helper to create authenticated request headers"""
    def _auth_headers(token):
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    return _auth_headers

@pytest.fixture(scope="function")
def valid_token():
    """Generate a valid JWT token for testing"""
    from backend.app import app
    from flask_jwt_extended import create_access_token
    
    with app.app_context():
        token = create_access_token(identity=1)
        return token

@pytest.fixture(scope="function")
def mock_database():
    """Mock database session"""
    with patch('backend.app.SessionLocal') as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        yield mock_db

@pytest.fixture(scope="function")
def mock_csv_file(temp_data_dir):
    """Create a mock CSV file for testing"""
    import pandas as pd
    
    csv_path = os.path.join(temp_data_dir, 'nvidiastock.csv')
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    data = pd.DataFrame({
        'Date': dates,
        'Open': [100] * 50,
        'High': [150] * 50,
        'Low': [50] * 50,
        'Close': [120] * 50,
        'Volume': ['1,000,000'] * 50
    })
    
    data.to_csv(csv_path, index=False)
    
    with patch('backend.model.pd.read_csv') as mock_read:
        mock_read.return_value = data
        yield csv_path

@pytest.fixture(scope="function")
def mock_environment_variables():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'JWT_SECRET_KEY': 'test-secret-key',
        'FINNHUB_API_KEY': 'test-finnhub-key',
        'DATABASE_URL': 'sqlite:///:memory:'
    }):
        yield

@pytest.fixture(scope="function")
def mock_chart_js():
    """Mock Chart.js for frontend tests"""
    with patch('frontend.main.Chart') as mock_chart:
        mock_chart_instance = MagicMock()
        mock_chart_instance.destroy = MagicMock()
        mock_chart_instance.update = MagicMock()
        mock_chart.return_value = mock_chart_instance
        yield mock_chart

@pytest.fixture(scope="function")
def mock_fetch():
    """Mock fetch API for frontend tests"""
    with patch('frontend.main.fetch') as mock_fetch:
        yield mock_fetch

@pytest.fixture(scope="function")
def mock_local_storage():
    """Mock localStorage for frontend tests"""
    storage = {}
    
    def get_item(key):
        return storage.get(key)
    
    def set_item(key, value):
        storage[key] = value
    
    def remove_item(key):
        if key in storage:
            del storage[key]
    
    with patch('frontend.main.localStorage') as mock_storage:
        mock_storage.getItem = get_item
        mock_storage.setItem = set_item
        mock_storage.removeItem = remove_item
        yield mock_storage

# Performance testing fixtures
@pytest.fixture(scope="function")
def performance_timer():
    """Timer for performance testing"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()

@pytest.fixture(scope="function")
def memory_monitor():
    """Monitor memory usage for testing"""
    import psutil
    import os
    
    class MemoryMonitor:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.initial_memory = None
            self.final_memory = None
        
        def start(self):
            self.initial_memory = self.process.memory_info().rss
        
        def stop(self):
            self.final_memory = self.process.memory_info().rss
        
        def increase(self):
            if self.initial_memory and self.final_memory:
                return self.final_memory - self.initial_memory
            return None
        
        def increase_mb(self):
            increase = self.increase()
            if increase:
                return increase / 1024 / 1024
            return None
    
    return MemoryMonitor()

# Test data generators
@pytest.fixture(scope="function")
def generate_stock_data():
    """Generate stock data for testing"""
    import pandas as pd
    import numpy as np
    
    def _generate_stock_data(periods=100, start_date='2023-01-01'):
        dates = pd.date_range(start_date, periods=periods, freq='D')
        
        # Generate realistic stock data
        base_price = 150.0
        prices = []
        for i in range(periods):
            # Add some random walk behavior
            change = np.random.normal(0, 2)  # Daily change with std dev of 2
            base_price += change
            base_price = max(base_price, 10)  # Ensure positive price
            prices.append(base_price)
        
        data = pd.DataFrame({
            'Date': dates,
            'Open': [p + np.random.normal(0, 1) for p in prices],
            'High': [p + abs(np.random.normal(0, 3)) for p in prices],
            'Low': [p - abs(np.random.normal(0, 3)) for p in prices],
            'Close': prices,
            'Volume': np.random.uniform(1000000, 5000000, periods)
        })
        
        return data
    
    return _generate_stock_data

@pytest.fixture(scope="function")
def generate_user_data():
    """Generate user data for testing"""
    import random
    import string
    
    def _generate_user_data():
        username = ''.join(random.choices(string.ascii_lowercase, k=8))
        email = f"{username}@example.com"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        return {
            'username': username,
            'email': email,
            'password': password
        }
    
    return _generate_user_data

# Cleanup fixtures
@pytest.fixture(scope="function", autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    # Cleanup code here if needed
    pass

# Test markers
def pytest_configure(config):
    """Configure custom test markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )

# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test file names
        if 'test_api' in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif 'test_model' in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif 'test_integration' in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif 'performance' in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
        elif 'security' in item.nodeid.lower():
            item.add_marker(pytest.mark.security) 