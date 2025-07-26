import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor
import ta
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice
import yfinance as yf
from datetime import datetime, timedelta

def create_features(df):
    df = df.copy()
    
    # Price-based indicators
    df['MA5'] = ta.trend.sma_indicator(df['Close'], window=5)
    df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['MA50'] = ta.trend.sma_indicator(df['Close'], window=50)
    
    # EMA indicators
    df['EMA12'] = ta.trend.ema_indicator(df['Close'], window=12)
    df['EMA26'] = ta.trend.ema_indicator(df['Close'], window=26)
    
    # MACD
    macd = MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()
    
    # RSI
    df['RSI'] = RSIIndicator(df['Close']).rsi()
    
    # Bollinger Bands
    bollinger = BollingerBands(df['Close'])
    df['BB_Upper'] = bollinger.bollinger_hband()
    df['BB_Lower'] = bollinger.bollinger_lband()
    df['BB_Middle'] = bollinger.bollinger_mavg()
    
    # Stochastic Oscillator
    stoch = StochasticOscillator(df['High'], df['Low'], df['Close'])
    df['Stoch_K'] = stoch.stoch()
    df['Stoch_D'] = stoch.stoch_signal()
    
    # Volume indicators
    df['Volume_MA5'] = ta.trend.sma_indicator(df['Volume'], window=5)
    df['Volume_Change'] = df['Volume'].pct_change()
    
    # VWAP
    df['VWAP'] = VolumeWeightedAveragePrice(
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        volume=df['Volume']
    ).volume_weighted_average_price()
    
    # Price changes
    df['Price_Change'] = df['Close'].pct_change()
    df['Price_Change_5d'] = df['Close'].pct_change(periods=5)
    
    # Lagged closes, returns, volatility
    for lag in range(1, 6):
        df[f'Close_lag{lag}'] = df['Close'].shift(lag)
        df[f'Return_lag{lag}'] = df['Close'].pct_change(lag)
    df['Volatility_5d'] = df['Close'].pct_change().rolling(5).std()
    df['Volatility_10d'] = df['Close'].pct_change().rolling(10).std()
    
    return df

def load_and_train(symbol='NVDA'):
    # Fetch data from yfinance instead of CSV
    ticker = yf.Ticker(symbol)
    data = ticker.history(period='2y', interval='1d')
    
    if data.empty:
        raise ValueError(f"No data available for {symbol}")
    
    # Reset index to get Date as a column
    data = data.reset_index()
    data = data.rename(columns={'Date': 'Date'})
    
    # Ensure we have the required columns
    required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Convert data types
    data['Date'] = pd.to_datetime(data['Date'])
    data['Volume'] = data['Volume'].astype(float)
    data['Close'] = data['Close'].astype(float)
    data['High'] = data['High'].astype(float)
    data['Low'] = data['Low'].astype(float)
    data['Open'] = data['Open'].astype(float)
    
    # Sort by date
    data = data.sort_values('Date')

    data = create_features(data)
    data = data.dropna()
    features = [
        'MA5', 'MA20', 'MA50', 'EMA12', 'EMA26',
        'MACD', 'MACD_Signal', 'MACD_Hist',
        'RSI', 'BB_Upper', 'BB_Lower', 'BB_Middle',
        'Stoch_K', 'Stoch_D',
        'Volume_MA5', 'Volume_Change', 'VWAP',
        'Price_Change', 'Price_Change_5d',
        'Close_lag1', 'Close_lag2', 'Close_lag3', 'Close_lag4', 'Close_lag5',
        'Return_lag1', 'Return_lag2', 'Return_lag3', 'Return_lag4', 'Return_lag5',
        'Volatility_5d', 'Volatility_10d'
    ]
    
    # Ensure all features exist
    available_features = [f for f in features if f in data.columns]
    if len(available_features) < len(features):
        print(f"Warning: Some features missing for {symbol}. Available: {available_features}")
        features = available_features
    
    X = data[features]
    y = data['Close'].shift(-1)
    X = X[:-1]
    y = y[:-1]
    
    if X.empty or y.empty:
        raise ValueError(f"Insufficient data for {symbol}")
    
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    model = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42)
    model.fit(X_scaled, y)
    return data, scaler, model, features

def get_prediction(data, scaler, model, features):
    latest_data = create_features(data.tail(50))
    latest_data = latest_data.dropna()
    if latest_data.empty:
        fallback_data = create_features(data).dropna()
        if fallback_data.empty:
            return None
        latest_features = fallback_data[features].iloc[[-1]]
    else:
        latest_features = latest_data[features].iloc[[-1]]
    latest_features_scaled = scaler.transform(latest_features)
    predicted_price = model.predict(latest_features_scaled)[0]
    return float(round(predicted_price, 2))

def get_recommendation(data, features):
    fallback_data = create_features(data).dropna()
    if fallback_data.empty:
        return None, None, {}
    
    latest_row = fallback_data.iloc[[-1]]
    rsi = latest_row['RSI'].iloc[-1]
    macd = latest_row['MACD'].iloc[-1]
    macd_signal = latest_row['MACD_Signal'].iloc[-1]
    stoch_k = latest_row['Stoch_K'].iloc[-1]
    stoch_d = latest_row['Stoch_D'].iloc[-1]
    
    recommendation = 'hold'
    confidence = 'medium'
    
    if rsi > 70:
        recommendation = 'sell'
        confidence = 'high'
    elif rsi < 30:
        recommendation = 'buy'
        confidence = 'high'
    if macd > macd_signal:
        recommendation = 'buy'
        confidence = 'high'
    elif macd < macd_signal:
        recommendation = 'sell'
        confidence = 'high'
    if stoch_k > 80 and stoch_d > 80:
        recommendation = 'sell'
        confidence = 'medium'
    elif stoch_k < 20 and stoch_d < 20:
        recommendation = 'buy'
        confidence = 'medium'
    
    indicators = {
        'rsi': float(round(rsi, 2)),
        'macd': float(round(macd, 2)),
        'stochastic_k': float(round(stoch_k, 2)),
        'stochastic_d': float(round(stoch_d, 2))
    }
    
    return recommendation, confidence, indicators 

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(512), nullable=False)
    balance = Column(Float, default=100000.0)  # Starting balance for paper trading
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", uselist=False, back_populates="user")
    orders = relationship("Order", back_populates="user")
    portfolio = relationship("Portfolio", back_populates="user")

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    symbol = Column(String(10), nullable=False)
    side = Column(String(4), nullable=False)  # 'buy' or 'sell'
    qty = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    alpaca_order_id = Column(String(50), nullable=True)  # Store Alpaca order ID
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="orders")

class Portfolio(Base):
    __tablename__ = 'portfolio'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    symbol = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="portfolio")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'avg_price': self.avg_price,
            'current_price': self.get_current_price(),
            'total_value': self.quantity * self.get_current_price(),
            'unrealized_pnl': self.get_unrealized_pnl(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def get_current_price(self):
        try:
            stock = yf.Ticker(self.symbol)
            return stock.info.get('regularMarketPrice', self.avg_price)
        except:
            return self.avg_price
    
    def get_unrealized_pnl(self):
        current_price = self.get_current_price()
        return (current_price - self.avg_price) * self.quantity

class Profile(Base):
    __tablename__ = 'profiles'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    preferences = Column(Text)

    user = relationship("User", back_populates="profile")