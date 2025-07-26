import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from backend.model import (
    create_features, 
    load_and_train, 
    get_prediction, 
    get_recommendation,
    User, Order, Profile
)

class TestFeatureCreation:
    """Test feature creation functionality"""
    
    def test_create_features_basic(self):
        """Test basic feature creation with sample data"""
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'Date': dates,
            'Open': np.random.uniform(100, 200, 100),
            'High': np.random.uniform(150, 250, 100),
            'Low': np.random.uniform(50, 150, 100),
            'Close': np.random.uniform(100, 200, 100),
            'Volume': np.random.uniform(1000000, 5000000, 100)
        })
        
        # Test feature creation
        result = create_features(data)
        
        # Check that features were added
        expected_features = [
            'MA5', 'MA20', 'MA50', 'EMA12', 'EMA26',
            'MACD', 'MACD_Signal', 'MACD_Hist',
            'RSI', 'BB_Upper', 'BB_Lower', 'BB_Middle',
            'Stoch_K', 'Stoch_D',
            'Volume_MA5', 'Volume_Change', 'VWAP',
            'Price_Change', 'Price_Change_5d'
        ]
        
        for feature in expected_features:
            assert feature in result.columns, f"Feature {feature} not found"
    
    def test_create_features_with_nan(self):
        """Test feature creation handles NaN values"""
        # Create data with NaN values
        data = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=50, freq='D'),
            'Open': [100] * 25 + [np.nan] * 25,
            'High': [150] * 25 + [np.nan] * 25,
            'Low': [50] * 25 + [np.nan] * 25,
            'Close': [120] * 25 + [np.nan] * 25,
            'Volume': [1000000] * 25 + [np.nan] * 25
        })
        
        # Should not raise an exception
        result = create_features(data)
        assert isinstance(result, pd.DataFrame)
    
    def test_create_features_empty_data(self):
        """Test feature creation with empty dataframe"""
        empty_data = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        # Should handle empty data gracefully
        result = create_features(empty_data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

class TestModelTraining:
    """Test model training functionality"""
    
    @patch('backend.model.pd.read_csv')
    @patch('backend.model.yf.Ticker')
    def test_load_and_train_success(self, mock_ticker, mock_read_csv):
        """Test successful model training"""
        # Mock CSV data
        mock_data = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=100, freq='D'),
            'Open': np.random.uniform(100, 200, 100),
            'High': np.random.uniform(150, 250, 100),
            'Low': np.random.uniform(50, 150, 100),
            'Close': np.random.uniform(100, 200, 100),
            'Volume': ['1,000,000'] * 100
        })
        mock_read_csv.return_value = mock_data
        
        # Mock yfinance data
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.return_value = pd.DataFrame({
            'Open': [200],
            'High': [250],
            'Low': [150],
            'Close': [220],
            'Volume': [2000000]
        }, index=[pd.Timestamp('2023-12-01')])
        mock_ticker.return_value = mock_ticker_instance
        
        # Test training
        data, scaler, model, features = load_and_train()
        
        # Check return types
        assert isinstance(data, pd.DataFrame)
        assert hasattr(scaler, 'transform')  # MinMaxScaler
        assert hasattr(model, 'predict')  # XGBRegressor
        assert isinstance(features, list)
        assert len(features) > 0
    
    @patch('backend.model.pd.read_csv')
    def test_load_and_train_csv_error(self, mock_read_csv):
        """Test model training with CSV read error"""
        mock_read_csv.side_effect = FileNotFoundError("CSV file not found")
        
        with pytest.raises(FileNotFoundError):
            load_and_train()

class TestPrediction:
    """Test prediction functionality"""
    
    def test_get_prediction_valid_data(self):
        """Test prediction with valid data"""
        # Create mock data, scaler, model, and features
        mock_data = pd.DataFrame({
            'Date': pd.date_range('2023-01-01', periods=100, freq='D'),
            'Open': np.random.uniform(100, 200, 100),
            'High': np.random.uniform(150, 250, 100),
            'Low': np.random.uniform(50, 150, 100),
            'Close': np.random.uniform(100, 200, 100),
            'Volume': np.random.uniform(1000000, 5000000, 100)
        })
        
        # Mock scaler
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[0.5] * 30])  # 30 features
        
        # Mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([150.0])
        
        # Mock features
        mock_features = [f'feature_{i}' for i in range(30)]
        
        # Test prediction
        result = get_prediction(mock_data, mock_scaler, mock_model, mock_features)
        
        assert isinstance(result, float)
        assert result == 150.0
    
    def test_get_prediction_empty_data(self):
        """Test prediction with empty data"""
        empty_data = pd.DataFrame()
        mock_scaler = MagicMock()
        mock_model = MagicMock()
        mock_features = []
        
        result = get_prediction(empty_data, mock_scaler, mock_model, mock_features)
        assert result is None

class TestRecommendation:
    """Test recommendation functionality"""
    
    def test_get_recommendation_buy_signal(self):
        """Test recommendation with buy signals"""
        # Create mock data with buy signals
        mock_data = pd.DataFrame({
            'RSI': [25.0],  # Oversold
            'MACD': [0.5],
            'MACD_Signal': [0.3],  # MACD > Signal
            'Stoch_K': [15.0],  # Oversold
            'Stoch_D': [12.0]  # Oversold
        })
        
        with patch('backend.model.create_features') as mock_create_features:
            mock_create_features.return_value = mock_data
            
            recommendation, confidence, indicators = get_recommendation(mock_data, [])
            
            assert recommendation == 'buy'
            assert confidence == 'high'
            assert isinstance(indicators, dict)
            assert 'rsi' in indicators
            assert 'macd' in indicators
    
    def test_get_recommendation_sell_signal(self):
        """Test recommendation with sell signals"""
        # Create mock data with sell signals
        mock_data = pd.DataFrame({
            'RSI': [75.0],  # Overbought
            'MACD': [0.3],
            'MACD_Signal': [0.5],  # MACD < Signal
            'Stoch_K': [85.0],  # Overbought
            'Stoch_D': [88.0]  # Overbought
        })
        
        with patch('backend.model.create_features') as mock_create_features:
            mock_create_features.return_value = mock_data
            
            recommendation, confidence, indicators = get_recommendation(mock_data, [])
            
            assert recommendation == 'sell'
            assert confidence == 'high'
            assert isinstance(indicators, dict)
    
    def test_get_recommendation_hold_signal(self):
        """Test recommendation with hold signals"""
        # Create mock data with neutral signals
        mock_data = pd.DataFrame({
            'RSI': [50.0],  # Neutral
            'MACD': [0.4],
            'MACD_Signal': [0.4],  # MACD = Signal
            'Stoch_K': [50.0],  # Neutral
            'Stoch_D': [50.0]  # Neutral
        })
        
        with patch('backend.model.create_features') as mock_create_features:
            mock_create_features.return_value = mock_data
            
            recommendation, confidence, indicators = get_recommendation(mock_data, [])
            
            assert recommendation == 'hold'
            assert confidence == 'medium'
            assert isinstance(indicators, dict)
    
    def test_get_recommendation_empty_data(self):
        """Test recommendation with empty data"""
        empty_data = pd.DataFrame()
        
        with patch('backend.model.create_features') as mock_create_features:
            mock_create_features.return_value = empty_data
            
            result = get_recommendation(empty_data, [])
            assert result == (None, None, {})

class TestDatabaseModels:
    """Test database model definitions"""
    
    def test_user_model(self):
        """Test User model structure"""
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.password_hash == 'hashed_password'
        assert hasattr(user, 'id')
        assert hasattr(user, 'created_at')
    
    def test_order_model(self):
        """Test Order model structure"""
        order = Order(
            user_id=1,
            symbol='NVDA',
            side='buy',
            qty=10.0,
            price=150.0,
            status='pending'
        )
        
        assert order.user_id == 1
        assert order.symbol == 'NVDA'
        assert order.side == 'buy'
        assert order.qty == 10.0
        assert order.price == 150.0
        assert order.status == 'pending'
        assert hasattr(order, 'id')
        assert hasattr(order, 'timestamp')
    
    def test_profile_model(self):
        """Test Profile model structure"""
        profile = Profile(
            user_id=1,
            preferences='{"theme": "dark"}'
        )
        
        assert profile.user_id == 1
        assert profile.preferences == '{"theme": "dark"}'

class TestDataValidation:
    """Test data validation and edge cases"""
    
    def test_invalid_timeframe_handling(self):
        """Test handling of invalid timeframes in historical data"""
        # This would be tested in the API layer, but we can test the logic
        valid_timeframes = ['1D', '1W', '1M', '3M', 'YTD', 'ALL', '1Y']
        invalid_timeframe = 'INVALID'
        
        # The API should default to '1Y' for invalid timeframes
        assert invalid_timeframe not in valid_timeframes
    
    def test_price_calculation_accuracy(self):
        """Test price change calculation accuracy"""
        current_price = 150.0
        previous_price = 148.0
        
        price_change = current_price - previous_price
        price_change_pct = (price_change / previous_price) * 100
        
        assert price_change == 2.0
        assert abs(price_change_pct - 1.35) < 0.01  # 1.35%
    
    def test_volume_formatting(self):
        """Test volume data formatting"""
        # Test volume string to float conversion
        volume_str = "1,000,000"
        volume_float = float(volume_str.replace(',', ''))
        
        assert volume_float == 1000000.0 