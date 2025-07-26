import pytest
import json
from unittest.mock import patch, MagicMock
from backend.app import app
from backend.model import User, Order, Profile

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_headers():
    """Helper to create authenticated request headers"""
    def _auth_headers(token):
        return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    return _auth_headers

class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        }
        response = client.post('/auth/register', json=data)
        assert response.status_code == 201
        assert 'message' in response.json
        assert response.json['message'] == 'User created successfully'

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        data = {
            'username': 'testuser2',
            'email': 'test4@example.com',  # Existing email
            'password': 'password123'
        }
        response = client.post('/auth/register', json=data)
        assert response.status_code == 400
        assert 'error' in response.json

    def test_login_success(self, client):
        """Test successful login"""
        data = {
            'email': 'test4@example.com',
            'password': 'password123'
        }
        response = client.post('/auth/login', json=data)
        assert response.status_code == 200
        assert 'access_token' in response.json
        assert 'email' in response.json
        assert 'id' in response.json

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = client.post('/auth/login', json=data)
        assert response.status_code == 401
        assert 'error' in response.json

    def test_logout_authenticated(self, client, auth_headers):
        """Test logout with valid token"""
        # First login to get token
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        
        response = client.post('/auth/logout', headers=auth_headers(token))
        assert response.status_code == 200
        assert 'message' in response.json

class TestStockDataEndpoints:
    """Test stock data endpoints"""
    
    @patch('backend.app.yf.Ticker')
    def test_historical_data_1y(self, mock_ticker, client):
        """Test historical data endpoint with 1Y timeframe"""
        # Mock the yfinance response
        mock_data = MagicMock()
        mock_data.history.return_value = MagicMock(
            index=['2023-01-01', '2023-01-02'],
            __getitem__=lambda self, key: [100.0, 101.0] if key == 'Close' else [1000, 1100]
        )
        mock_ticker.return_value = mock_data
        
        response = client.get('/historical_data?tf=1Y')
        assert response.status_code == 200
        data = response.json
        assert 'dates' in data
        assert 'prices' in data
        assert 'rsi' in data
        assert 'macd' in data

    @patch('backend.app.yf.Ticker')
    def test_live_data(self, mock_ticker, client):
        """Test live data endpoint"""
        # Mock the yfinance response
        mock_info = {
            'currentPrice': 150.0,
            'previousClose': 148.0,
            'volume': 1000000,
            'dayHigh': 152.0,
            'dayLow': 147.0,
            'open': 149.0
        }
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = mock_info
        mock_ticker_instance.history.return_value = MagicMock(
            empty=False,
            __getitem__=lambda self, key: [1000000] if key == 'Volume' else [150.0]
        )
        mock_ticker.return_value = mock_ticker_instance
        
        response = client.get('/live_data')
        assert response.status_code == 200
        data = response.json
        assert 'price' in data
        assert 'price_change' in data
        assert 'volume' in data

    @patch('backend.app.scrape_market_sentiment')
    @patch('backend.app.get_prediction')
    def test_predict_endpoint(self, mock_prediction, mock_news, client):
        """Test prediction endpoint"""
        mock_prediction.return_value = 155.0
        mock_news.return_value = ['NVIDIA announces new GPU', 'Stock price rises']
        
        response = client.get('/predict')
        assert response.status_code == 200
        data = response.json
        assert 'predicted_price' in data
        assert 'news' in data
        assert isinstance(data['news'], list)

    @patch('backend.app.get_recommendation')
    def test_recommend_endpoint(self, mock_recommendation, client):
        """Test recommendation endpoint"""
        mock_recommendation.return_value = ('buy', 'high', {
            'rsi': 25.0,
            'macd': 0.5,
            'stochastic_k': 15.0,
            'stochastic_d': 12.0
        })
        
        response = client.get('/recommend')
        assert response.status_code == 200
        data = response.json
        assert 'recommendation' in data
        assert 'confidence' in data
        assert 'indicators' in data

class TestUserEndpoints:
    """Test user-related endpoints"""
    
    def test_get_current_user_authenticated(self, client, auth_headers):
        """Test getting current user with valid token"""
        # First login to get token
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        
        response = client.get('/users/me', headers=auth_headers(token))
        assert response.status_code == 200
        data = response.json
        assert 'id' in data
        assert 'email' in data
        assert 'username' in data

    def test_get_current_user_unauthenticated(self, client):
        """Test getting current user without token"""
        response = client.get('/users/me')
        assert response.status_code == 401

class TestOrderEndpoints:
    """Test order endpoints"""
    
    def test_create_order_authenticated(self, client, auth_headers):
        """Test creating an order with valid token"""
        # First login to get token
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        
        order_data = {
            'symbol': 'NVDA',
            'side': 'buy',
            'qty': 10,
            'price': 150.0
        }
        
        response = client.post('/orders', json=order_data, headers=auth_headers(token))
        assert response.status_code == 201
        data = response.json
        assert 'id' in data
        assert data['symbol'] == 'NVDA'
        assert data['side'] == 'buy'

    def test_get_user_orders_authenticated(self, client, auth_headers):
        """Test getting user orders with valid token"""
        # First login to get token
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        
        response = client.get('/orders', headers=auth_headers(token))
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)

class TestProfileEndpoints:
    """Test profile endpoints"""
    
    def test_get_profile_authenticated(self, client, auth_headers):
        """Test getting user profile with valid token"""
        # First login to get token
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        
        response = client.get('/profiles', headers=auth_headers(token))
        assert response.status_code == 200

    def test_update_profile_authenticated(self, client, auth_headers):
        """Test updating user profile with valid token"""
        # First login to get token
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        
        profile_data = {
            'preferences': json.dumps({
                'theme': 'dark',
                'notifications': True
            })
        }
        
        response = client.put('/profiles', json=profile_data, headers=auth_headers(token))
        assert response.status_code == 200
        data = response.json
        assert 'message' in data

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_endpoint(self, client):
        """Test accessing non-existent endpoint"""
        response = client.get('/invalid-endpoint')
        assert response.status_code == 404

    def test_invalid_json(self, client):
        """Test sending invalid JSON"""
        response = client.post('/auth/login', data='invalid json')
        assert response.status_code == 400

    def test_missing_required_fields(self, client):
        """Test missing required fields in registration"""
        data = {'username': 'testuser'}  # Missing email and password
        response = client.post('/auth/register', json=data)
        assert response.status_code == 400 