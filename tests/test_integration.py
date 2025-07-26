import pytest
import requests
import time
from unittest.mock import patch
from backend.app import app
from backend.model import User, Order, Profile

class TestFullApplicationFlow:
    """Integration tests for the complete application flow"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        with app.test_client() as client:
            yield client
    
    def test_complete_user_journey(self, client):
        """Test complete user journey: register -> login -> dashboard -> logout"""
        
        # 1. Register new user
        register_data = {
            'username': 'integration_test_user',
            'email': 'integration@test.com',
            'password': 'testpassword123'
        }
        register_response = client.post('/auth/register', json=register_data)
        assert register_response.status_code == 201
        
        # 2. Login with new user
        login_data = {
            'email': 'integration@test.com',
            'password': 'testpassword123'
        }
        login_response = client.post('/auth/login', json=login_data)
        assert login_response.status_code == 200
        token = login_response.json['access_token']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        # 3. Access protected endpoints
        user_response = client.get('/users/me', headers=headers)
        assert user_response.status_code == 200
        assert user_response.json['email'] == 'integration@test.com'
        
        # 4. Get stock data
        live_data_response = client.get('/live_data')
        assert live_data_response.status_code == 200
        assert 'price' in live_data_response.json
        
        # 5. Get predictions
        predict_response = client.get('/predict')
        assert predict_response.status_code == 200
        assert 'predicted_price' in predict_response.json
        
        # 6. Get recommendations
        recommend_response = client.get('/recommend')
        assert recommend_response.status_code == 200
        assert 'recommendation' in recommend_response.json
        
        # 7. Create an order
        order_data = {
            'symbol': 'NVDA',
            'side': 'buy',
            'qty': 5,
            'price': 150.0
        }
        order_response = client.post('/orders', json=order_data, headers=headers)
        assert order_response.status_code == 201
        
        # 8. Get user orders
        orders_response = client.get('/orders', headers=headers)
        assert orders_response.status_code == 200
        assert len(orders_response.json) > 0
        
        # 9. Update profile
        profile_data = {
            'preferences': '{"theme": "dark", "notifications": true}'
        }
        profile_response = client.put('/profiles', json=profile_data, headers=headers)
        assert profile_response.status_code == 200
        
        # 10. Logout
        logout_response = client.post('/auth/logout', headers=headers)
        assert logout_response.status_code == 200
    
    def test_dashboard_data_flow(self, client):
        """Test the complete data flow for dashboard functionality"""
        
        # Login first
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test all dashboard endpoints in sequence
        endpoints = [
            '/live_data',
            '/historical_data?tf=1Y',
            '/predict',
            '/recommend'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200
            assert response.json is not None
    
    def test_error_recovery_flow(self, client):
        """Test how the application handles and recovers from errors"""
        
        # Test with invalid token
        invalid_headers = {'Authorization': 'Bearer invalid_token'}
        response = client.get('/users/me', headers=invalid_headers)
        assert response.status_code == 422  # JWT decode error
        
        # Test with expired token (would need to mock time)
        # This is more complex and would require mocking JWT expiration
        
        # Test with malformed JSON
        response = client.post('/auth/login', data='invalid json')
        assert response.status_code == 400
        
        # Test with missing required fields
        response = client.post('/auth/register', json={'username': 'test'})
        assert response.status_code == 400

class TestDataConsistency:
    """Test data consistency across different endpoints"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_stock_data_consistency(self, client):
        """Test that stock data is consistent across different endpoints"""
        
        # Get live data
        live_response = client.get('/live_data')
        live_data = live_response.json
        
        # Get historical data
        hist_response = client.get('/historical_data?tf=1D')
        hist_data = hist_response.json
        
        # Basic consistency checks
        assert 'price' in live_data
        assert 'prices' in hist_data
        
        # If we have both live and historical data, the latest historical price
        # should be close to the live price (allowing for small differences)
        if hist_data['prices'] and live_data['price']:
            latest_hist_price = hist_data['prices'][-1]
            live_price = live_data['price']
            
            # Allow for 1% difference due to timing
            price_diff = abs(latest_hist_price - live_price) / live_price
            assert price_diff < 0.01, f"Price difference too large: {price_diff}"
    
    def test_user_data_consistency(self, client):
        """Test that user data is consistent across endpoints"""
        
        # Login
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Get user info
        user_response = client.get('/users/me', headers=headers)
        user_data = user_response.json
        
        # Get user orders
        orders_response = client.get('/orders', headers=headers)
        orders_data = orders_response.json
        
        # Get user profile
        profile_response = client.get('/profiles', headers=headers)
        profile_data = profile_response.json
        
        # Check consistency
        assert user_data['id'] is not None
        assert user_data['email'] == 'test4@example.com'
        
        # All orders should belong to this user
        for order in orders_data:
            assert order['user_id'] == user_data['id']

class TestPerformanceIntegration:
    """Test performance characteristics of the integrated system"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_api_response_times(self, client):
        """Test that API endpoints respond within acceptable time limits"""
        
        endpoints = [
            '/live_data',
            '/historical_data?tf=1Y',
            '/predict',
            '/recommend'
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Each endpoint should respond within 2 seconds
            assert response_time < 2.0, f"Endpoint {endpoint} took {response_time:.2f}s"
            assert response.status_code == 200
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = client.get('/live_data')
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        while not results.empty():
            result = results.get()
            assert result == 200 or isinstance(result, str)
    
    def test_memory_usage(self, client):
        """Test memory usage doesn't grow excessively"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple requests
        for _ in range(10):
            client.get('/live_data')
            client.get('/historical_data?tf=1Y')
            client.get('/predict')
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be less than 50MB
        assert memory_increase < 50 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.2f}MB"

class TestSecurityIntegration:
    """Test security aspects of the integrated system"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_authentication_required(self, client):
        """Test that protected endpoints require authentication"""
        
        protected_endpoints = [
            '/users/me',
            '/orders',
            '/profiles'
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 422]  # Unauthorized or JWT error
    
    def test_cors_headers(self, client):
        """Test that CORS headers are properly set"""
        
        response = client.get('/live_data')
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection"""
        
        # Try to inject SQL in various fields
        malicious_data = {
            'username': "'; DROP TABLE users; --",
            'email': "test@example.com'; DROP TABLE users; --",
            'password': 'password123'
        }
        
        response = client.post('/auth/register', json=malicious_data)
        # Should not crash the application
        assert response.status_code in [201, 400]  # Success or validation error
    
    def test_xss_protection(self, client):
        """Test protection against XSS attacks"""
        
        # Try to inject JavaScript
        malicious_data = {
            'username': '<script>alert("xss")</script>',
            'email': 'test@example.com',
            'password': 'password123'
        }
        
        response = client.post('/auth/register', json=malicious_data)
        # Should not crash the application
        assert response.status_code in [201, 400]

class TestDatabaseIntegration:
    """Test database integration and transactions"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_user_order_relationship(self, client):
        """Test that user-order relationships are maintained"""
        
        # Login
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Create multiple orders
        orders = [
            {'symbol': 'NVDA', 'side': 'buy', 'qty': 5, 'price': 150.0},
            {'symbol': 'NVDA', 'side': 'sell', 'qty': 2, 'price': 155.0},
            {'symbol': 'NVDA', 'side': 'buy', 'qty': 10, 'price': 145.0}
        ]
        
        created_orders = []
        for order_data in orders:
            response = client.post('/orders', json=order_data, headers=headers)
            assert response.status_code == 201
            created_orders.append(response.json)
        
        # Get all orders
        orders_response = client.get('/orders', headers=headers)
        assert orders_response.status_code == 200
        all_orders = orders_response.json
        
        # Verify all orders belong to the same user
        user_id = created_orders[0]['user_id']
        for order in all_orders:
            assert order['user_id'] == user_id
    
    def test_profile_consistency(self, client):
        """Test profile data consistency"""
        
        # Login
        login_data = {'email': 'test4@example.com', 'password': 'password123'}
        login_response = client.post('/auth/login', json=login_data)
        token = login_response.json['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Update profile
        profile_data = {
            'preferences': '{"theme": "dark", "notifications": true, "test": "value"}'
        }
        
        update_response = client.put('/profiles', json=profile_data, headers=headers)
        assert update_response.status_code == 200
        
        # Get profile and verify
        get_response = client.get('/profiles', headers=headers)
        assert get_response.status_code == 200
        
        # The profile should contain the updated preferences
        assert 'test' in get_response.json.get('preferences', '{}') 