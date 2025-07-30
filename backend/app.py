from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import yfinance as yf
from datetime import datetime, timedelta
from model import load_and_train, get_prediction, get_recommendation, Base, User, Order, Profile, Portfolio
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_jwt_extended.exceptions import JWTExtendedException
from werkzeug.exceptions import Unauthorized
from flask_cors import CORS
import alpaca_trade_api as tradeapi
from config import DATABASE_URL, JWT_SECRET_KEY, ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable CORS for all routes

# JWT Configuration
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)

# Alpaca API Configuration
if ALPACA_API_KEY and ALPACA_SECRET_KEY:
    alpaca = tradeapi.REST(
        ALPACA_API_KEY,
        ALPACA_SECRET_KEY,
        ALPACA_BASE_URL,
        api_version='v2'
    )
else:
    alpaca = None
    print("Warning: Alpaca API credentials not found. Paper trading will be simulated.")

global data, scaler, model, features

# Stock configuration
STOCKS = {
    'NVDA': {'name': 'NVIDIA', 'symbol': 'NVDA'},
    'AMD': {'name': 'Advanced Micro Devices', 'symbol': 'AMD'},
    'AAPL': {'name': 'Apple Inc.', 'symbol': 'AAPL'},
    'GOOGL': {'name': 'Alphabet Inc.', 'symbol': 'GOOGL'},
    'MSFT': {'name': 'Microsoft Corporation', 'symbol': 'MSFT'},
    'TSLA': {'name': 'Tesla Inc.', 'symbol': 'TSLA'},
    'META': {'name': 'Meta Platforms', 'symbol': 'META'},
    'AMZN': {'name': 'Amazon.com Inc.', 'symbol': 'AMZN'}
}

# Global variables for each stock
stock_data = {}
stock_models = {}
stock_scalers = {}
stock_features = {}

def get_stock_data(symbol):
    """Get or initialize stock data"""
    if symbol not in stock_data:
        stock_data[symbol] = {}
    return stock_data[symbol]

def get_stock_model(symbol):
    """Get or initialize stock model"""
    if symbol not in stock_models:
        stock_models[symbol] = {}
    return stock_models[symbol]

def get_stock_scaler(symbol):
    """Get or initialize stock scaler"""
    if symbol not in stock_scalers:
        stock_scalers[symbol] = {}
    return stock_scalers[symbol]

def get_stock_features(symbol):
    """Get or initialize stock features"""
    if symbol not in stock_features:
        stock_features[symbol] = {}
    return stock_features[symbol]

# Database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Helper function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def execute_paper_trade(symbol, side, qty, price):
    """Execute a paper trade using Alpaca API"""
    try:
        if alpaca:
            # Get current market price if not provided
            if not price:
                ticker = alpaca.get_latest_trade(symbol)
                price = ticker.price
            
            # Create the order
            order = alpaca.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='day'
            )
            
            return {
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'filled_price': price,
                'filled_at': datetime.utcnow().isoformat()
            }
        else:
            # Simulate paper trading if Alpaca is not configured
            return {
                'success': True,
                'order_id': f'sim_{datetime.utcnow().timestamp()}',
                'status': 'filled',
                'filled_price': price,
                'filled_at': datetime.utcnow().isoformat(),
                'simulated': True
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_account_info():
    """Get account information from Alpaca"""
    try:
        if alpaca:
            account = alpaca.get_account()
            return {
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity)
            }
        else:
            # Return simulated account info
            return {
                'cash': 100000.0,
                'buying_power': 100000.0,
                'portfolio_value': 100000.0,
                'equity': 100000.0,
                'simulated': True
            }
    except Exception as e:
        return {
            'error': str(e)
        }

def get_portfolio_positions(user_id):
    """Get current portfolio positions for a specific user"""
    try:
        print(f"=== GET_PORTFOLIO_POSITIONS CALLED with user_id: {user_id} ===")
        
        # Always use the portfolio table for now
        return get_portfolio_from_table(user_id)
        
    except Exception as e:
        print(f"Error getting portfolio positions: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_portfolio_from_table(user_id):
    """Get portfolio positions directly from the portfolio table"""
    try:
        print(f"=== GET_PORTFOLIO_FROM_TABLE CALLED with user_id: {user_id} ===")
        db = next(get_db())
        print("Database session created")
        
        # Query all portfolios for this user
        portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        print(f"Found {len(portfolios)} portfolio entries")
        
        result = []
        for portfolio in portfolios:
            print(f"Processing portfolio: {portfolio.symbol}, qty: {portfolio.quantity}, avg_price: {portfolio.avg_price}")
            if portfolio.quantity > 0:  # Only include positions with positive quantity
                # Get current price
                try:
                    ticker = yf.Ticker(portfolio.symbol)
                    current_price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')
                    if not current_price:
                        hist = ticker.history(period='1d', interval='1m')
                        if not hist.empty:
                            current_price = float(hist['Close'][-1])
                        else:
                            current_price = portfolio.avg_price
                except Exception as e:
                    print(f"Error getting current price for {portfolio.symbol}: {e}")
                    current_price = portfolio.avg_price
                
                market_value = portfolio.quantity * current_price
                unrealized_pl = market_value - (portfolio.quantity * portfolio.avg_price)
                
                position_data = {
                    'symbol': portfolio.symbol,
                    'qty': portfolio.quantity,
                    'avg_entry_price': portfolio.avg_price,
                    'current_price': current_price,
                    'market_value': market_value,
                    'unrealized_pl': unrealized_pl
                }
                print(f"Adding position: {position_data}")
                result.append(position_data)
            else:
                print(f"Skipping portfolio {portfolio.symbol} - quantity <= 0")
        
        print(f"Final result: {result}")
        return result
    except Exception as e:
        print(f"Error getting portfolio from table: {e}")
        import traceback
        traceback.print_exc()
        return []

def scrape_market_sentiment(symbol='NVDA'):
    try:
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol={symbol}&from={week_ago}&to={today}&token={api_key}"
        )
        response = requests.get(url, timeout=5)
        news_items = []
        data = response.json()
        for article in data:
            headline = article.get('headline')
            if headline:
                news_items.append(str(headline))
            if len(news_items) >= 5:
                break
        if not news_items:
            news_items = ["No news available."]
        return news_items
    except Exception as e:
        print(f"Error fetching news from Finnhub: {e}")
        return ["No news available."]

# Initialize model and data
data, scaler, model, features = load_and_train()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'landing.html')

@app.route('/predict', methods=['GET'])
def predict():
    global data, scaler, model, features
    data, scaler, model, features = load_and_train()
    predicted_price = get_prediction(data, scaler, model, features)
    news_items = scrape_market_sentiment()
    return jsonify({
        'predicted_price': predicted_price,
        'news': [str(n) for n in news_items]
    })

@app.route('/recommend', methods=['GET'])
def recommend():
    global data, features
    data, _, _, features = load_and_train()
    recommendation, confidence, indicators = get_recommendation(data, features)
    if recommendation is None:
        return jsonify({
            'recommendation': "Not enough data",
            'confidence': "Not enough data",
            'indicators': {},
            'error': 'No valid data for recommendation'
        })
    return jsonify({
        'recommendation': str(recommendation),
        'confidence': str(confidence),
        'indicators': indicators
    })

@app.route('/historical_data', methods=['GET'])
def historical_data():
    tf = request.args.get('tf', '1Y').upper()
    ticker = yf.Ticker('NVDA')
    if tf == '1D':
        hist = ticker.history(period='1d', interval='1m')
        dates = [d.strftime('%Y-%m-%d %H:%M') for d in hist.index]
    elif tf == '1W':
        hist = ticker.history(period='5d', interval='5m')
        dates = [d.strftime('%Y-%m-%d %H:%M') for d in hist.index]
    elif tf == '1M':
        hist = ticker.history(period='1mo', interval='30m')
        dates = [d.strftime('%Y-%m-%d %H:%M') for d in hist.index]
    elif tf == '3M':
        hist = ticker.history(period='3mo', interval='1d')
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
    elif tf == 'YTD':
        hist = ticker.history(period='ytd', interval='1d')
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
    elif tf == 'ALL':
        hist = ticker.history(period='max', interval='1d')
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
    else:  # Default to 1Y
        hist = ticker.history(period='1y', interval='1d')
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]

    # Compute indicators if data is available
    if not hist.empty:
        prices = hist['Close'].fillna(method='ffill').tolist()
        # RSI
        import ta
        rsi = ta.momentum.RSIIndicator(hist['Close']).rsi().fillna(0).tolist()
        # MACD
        macd_obj = ta.trend.MACD(hist['Close'])
        macd = macd_obj.macd().fillna(0).tolist()
        macd_signal = macd_obj.macd_signal().fillna(0).tolist()
    else:
        prices = []
        rsi = []
        macd = []
        macd_signal = []

    chart_data = {
        'dates': dates,
        'prices': prices,
        'rsi': rsi,
        'macd': macd,
        'macd_signal': macd_signal,
    }
    return jsonify(chart_data)

@app.route('/live_data', methods=['GET'])
def live_data():
    ticker = yf.Ticker('NVDA')
    info = ticker.info

    # Fallback to history for price if info is empty
    price = info.get('currentPrice') or info.get('regularMarketPrice')
    prev_close = info.get('previousClose')
    dayHigh = info.get('dayHigh')
    dayLow = info.get('dayLow')
    open_ = info.get('open')

    # Always try to get the latest volume from history if possible
    hist = ticker.history(period='1d', interval='1m')
    volume = None
    if not hist.empty:
        volume = int(hist['Volume'][-1])
        if price is None:
            price = float(hist['Close'][-1])
        if prev_close is None and len(hist) > 1:
            prev_close = float(hist['Close'][-2])
        if open_ is None:
            open_ = float(hist['Open'][0])
        if dayHigh is None:
            dayHigh = float(hist['High'].max())
        if dayLow is None:
            dayLow = float(hist['Low'].min())

    # Fallback to info volume if history is empty
    if volume is None:
        volume = info.get('volume')

    # Round open and low
    open_ = round(open_, 2) if open_ is not None else None
    dayLow = round(dayLow, 2) if dayLow is not None else None

    price_change = price - prev_close if price is not None and prev_close is not None else None
    price_change_pct = (price_change / prev_close * 100) if price_change is not None and prev_close else None

    return jsonify({
        'price': price,
        'price_change': price_change,
        'price_change_pct': price_change_pct,
        'volume': volume,
        'dayHigh': dayHigh,
        'dayLow': dayLow,
        'open': open_,
    })

@app.route('/retrain', methods=['POST'])
def retrain():
    global data, scaler, model, features
    data, scaler, model, features = load_and_train()
    predicted_price = get_prediction(data, scaler, model, features)
    return jsonify({
        'success': True,
        'predicted_price': predicted_price
    })

@app.route('/stocks')
def get_stocks():
    """Get list of available stocks"""
    return jsonify(STOCKS)

@app.route('/predict/<symbol>', methods=['GET'])
def predict_stock(symbol):
    symbol = symbol.upper()
    if symbol not in STOCKS:
        return jsonify({'error': 'Stock not found'}), 404
    
    try:
        data = get_stock_data(symbol)
        scaler = get_stock_scaler(symbol)
        model = get_stock_model(symbol)
        features = get_stock_features(symbol)
        
        # Retrain if needed
        data, scaler, model, features = load_and_train(symbol)
        stock_data[symbol] = data
        stock_models[symbol] = model
        stock_scalers[symbol] = scaler
        stock_features[symbol] = features
        
        predicted_price = get_prediction(data, scaler, model, features)
        news_items = scrape_market_sentiment(symbol)
        return jsonify({
            'predicted_price': predicted_price,
            'news': [str(n) for n in news_items]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommend/<symbol>', methods=['GET'])
def recommend_stock(symbol):
    symbol = symbol.upper()
    if symbol not in STOCKS:
        return jsonify({'error': 'Stock not found'}), 404
    
    try:
        data = get_stock_data(symbol)
        features = get_stock_features(symbol)
        
        # Retrain if needed
        data, _, _, features = load_and_train(symbol)
        stock_data[symbol] = data
        stock_features[symbol] = features
        
        recommendation, confidence, indicators = get_recommendation(data, features)
        if recommendation is None:
            return jsonify({
                'recommendation': "Not enough data",
                'confidence': "Not enough data",
                'indicators': {},
                'error': 'No valid data for recommendation'
            })
        return jsonify({
            'recommendation': str(recommendation),
            'confidence': str(confidence),
            'indicators': indicators
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/historical_data/<symbol>', methods=['GET'])
def historical_data_stock(symbol):
    symbol = symbol.upper()
    if symbol not in STOCKS:
        return jsonify({'error': 'Stock not found'}), 404
    
    tf = request.args.get('tf', '1Y').upper()
    ticker = yf.Ticker(symbol)
    if tf == '1D':
        hist = ticker.history(period='1d', interval='1m')
        dates = [d.strftime('%Y-%m-%d %H:%M') for d in hist.index]
    elif tf == '1W':
        hist = ticker.history(period='5d', interval='5m')
        dates = [d.strftime('%Y-%m-%d %H:%M') for d in hist.index]
    elif tf == '1M':
        hist = ticker.history(period='1mo', interval='30m')
        dates = [d.strftime('%Y-%m-%d %H:%M') for d in hist.index]
    elif tf == '3M':
        hist = ticker.history(period='3mo', interval='1d')
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
    elif tf == 'YTD':
        hist = ticker.history(period='ytd', interval='1d')
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
    elif tf == 'ALL':
        hist = ticker.history(period='max', interval='1d')
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
    else:  # Default to 1Y
        hist = ticker.history(period='1y', interval='1d')
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]

    # Compute indicators if data is available
    if not hist.empty:
        prices = hist['Close'].fillna(method='ffill').tolist()
        # RSI
        import ta
        rsi = ta.momentum.RSIIndicator(hist['Close']).rsi().fillna(0).tolist()
        # MACD
        macd_obj = ta.trend.MACD(hist['Close'])
        macd = macd_obj.macd().fillna(0).tolist()
        macd_signal = macd_obj.macd_signal().fillna(0).tolist()
    else:
        prices = []
        rsi = []
        macd = []
        macd_signal = []

    chart_data = {
        'dates': dates,
        'prices': prices,
        'rsi': rsi,
        'macd': macd,
        'macd_signal': macd_signal,
    }
    return jsonify(chart_data)

@app.route('/live_data/<symbol>', methods=['GET'])
def live_data_stock(symbol):
    symbol = symbol.upper()
    if symbol not in STOCKS:
        return jsonify({'error': 'Stock not found'}), 404
    
    ticker = yf.Ticker(symbol)
    info = ticker.info

    # Fallback to history for price if info is empty
    price = info.get('currentPrice') or info.get('regularMarketPrice')
    prev_close = info.get('previousClose')
    dayHigh = info.get('dayHigh')
    dayLow = info.get('dayLow')
    open_ = info.get('open')

    # Always try to get the latest volume from history if possible
    hist = ticker.history(period='1d', interval='1m')
    volume = None
    if not hist.empty:
        volume = int(hist['Volume'][-1])
        if price is None:
            price = float(hist['Close'][-1])
        if prev_close is None and len(hist) > 1:
            prev_close = float(hist['Close'][-2])
        if open_ is None:
            open_ = float(hist['Open'][0])
        if dayHigh is None:
            dayHigh = float(hist['High'].max())
        if dayLow is None:
            dayLow = float(hist['Low'].min())

    # Fallback to info volume if history is empty
    if volume is None:
        volume = info.get('volume')

    # Round open and low
    open_ = round(open_, 2) if open_ is not None else None
    dayLow = round(dayLow, 2) if dayLow is not None else None

    price_change = price - prev_close if price is not None and prev_close is not None else None
    price_change_pct = (price_change / prev_close * 100) if price_change is not None and prev_close else None

    return jsonify({
        'price': price,
        'price_change': price_change,
        'price_change_pct': price_change_pct,
        'volume': volume,
        'dayHigh': dayHigh,
        'dayLow': dayLow,
        'open': open_,
    })

# Authentication endpoints
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    db = next(get_db())
    
    # Check if username already exists
    if db.query(User).filter(User.username == data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    # Check if email already exists
    if db.query(User).filter(User.email == data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token with string user ID
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'access_token': access_token
    }), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    db = next(get_db())
    
    user = db.query(User).filter(User.email == data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Create access token with string user ID
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'access_token': access_token
    }), 200

@app.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    # JWT tokens are stateless, so we just return a success message
    return jsonify({'message': 'Successfully logged out'})

# Protected user endpoints
@app.route('/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat()
    })

# Protected order endpoints
@app.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        db = next(get_db())
        
        # Validate required fields
        required_fields = ['symbol', 'side', 'qty']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract order data
        symbol = data.get('symbol').upper()
        side = data.get('side')  # 'buy' or 'sell'
        qty = int(data.get('qty'))
        price_raw = data.get('price')
        price = float(price_raw) if price_raw is not None else 0  # Handle None values properly
        order_type = data.get('order_type', 'market')
        
        # Validate side
        if side not in ['buy', 'sell']:
            return jsonify({'error': 'Side must be either "buy" or "sell"'}), 400
        
        # Validate quantity
        if qty <= 0:
            return jsonify({'error': 'Quantity must be greater than 0'}), 400
        
        # Get current user
        user = db.query(User).filter(User.id == current_user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get current market price if not provided
        if price == 0:
            try:
                ticker = yf.Ticker(symbol)
                current_price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')
                if not current_price:
                    hist = ticker.history(period='1d', interval='1m')
                    if not hist.empty:
                        current_price = float(hist['Close'][-1])
                    else:
                        return jsonify({'error': 'Unable to get current price for symbol'}), 400
                price = current_price
            except Exception as e:
                return jsonify({'error': f'Error getting current price: {str(e)}'}), 400
        
        # Calculate order value
        order_value = qty * price
        
        # Check if user has enough balance for buy orders
        if side == 'buy':
            if user.balance < order_value:
                return jsonify({'error': f'Insufficient balance. Required: ${order_value:.2f}, Available: ${user.balance:.2f}'}), 400
        
        # Check if user has enough shares for sell orders
        if side == 'sell':
            # Get current portfolio position
            portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user_id, Portfolio.symbol == symbol).first()
            if not portfolio or portfolio.quantity < qty:
                return jsonify({'error': f'Insufficient shares. Required: {qty}, Available: {portfolio.quantity if portfolio else 0}'}), 400
        
        # Execute the paper trade
        trade_result = execute_paper_trade(
            symbol=symbol,
            side=side,
            qty=qty,
            price=price
        )
        
        if not trade_result['success']:
            return jsonify({'error': f'Trade execution failed: {trade_result["error"]}'}), 400
        
        # Create new order
        new_order = Order(
            user_id=current_user_id,
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            status='filled',  # For paper trading, assume immediate fill
            alpaca_order_id=trade_result.get('order_id')
        )
        
        # Save order to database
        db.add(new_order)
        
        # Update user balance
        if side == 'buy':
            user.balance -= order_value
        else:  # sell
            user.balance += order_value
        
        # Update portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user_id, Portfolio.symbol == symbol).first()
        
        if side == 'buy':
            if portfolio:
                # Update existing position
                total_cost = portfolio.quantity * portfolio.avg_price + order_value
                portfolio.quantity += qty
                portfolio.avg_price = total_cost / portfolio.quantity
                portfolio.updated_at = datetime.utcnow()
            else:
                # Create new position
                portfolio = Portfolio(
                    user_id=current_user_id,
                    symbol=symbol,
                    quantity=qty,
                    avg_price=price
                )
                db.add(portfolio)
        else:  # sell
            if portfolio:
                portfolio.quantity -= qty
                if portfolio.quantity <= 0:
                    db.delete(portfolio)
                else:
                    portfolio.updated_at = datetime.utcnow()
        
        # Commit all changes
        db.commit()
        
        return jsonify({
            'message': 'Order placed successfully',
            'order_id': new_order.id,
            'symbol': symbol,
            'side': side,
            'quantity': qty,
            'price': price,
            'total_value': order_value,
            'status': 'filled',
            'executed_at': datetime.utcnow().isoformat(),
            'new_balance': user.balance
        }), 201
        
    except Exception as e:
        print(f"=== ORDER ERROR ===")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"==================")
        db.rollback()
        return jsonify({'error': f'Order placement failed: {str(e)}'}), 500

@app.route('/orders', methods=['GET'])
def get_user_orders():
    print("=== ORDERS ENDPOINT CALLED ===")
    try:
        # Temporarily get user_id from query param for testing
        user_id = int(request.args.get('user_id', '1'))  # Convert to integer
        print(f"User ID: {user_id}")
        
        db = next(get_db())
        orders = db.query(Order).filter(Order.user_id == user_id).all()
        print(f"Found {len(orders)} orders")
        
        orders_data = [{
            'id': order.id,
            'symbol': order.symbol,
            'side': order.side,
            'qty': order.qty,
            'price': order.price,
            'status': order.status,
            'timestamp': order.timestamp.isoformat()
        } for order in orders]
        
        print("Orders data:", orders_data)
        return jsonify(orders_data)
    except Exception as e:
        print(f"Orders endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/account', methods=['GET'])
def get_account():
    """Get account information including cash, buying power, and portfolio value"""
    print("=== ACCOUNT ENDPOINT CALLED ===")
    try:
        account_info = get_account_info()
        print("Account info:", account_info)
        
        if 'error' in account_info:
            print("Account error:", account_info['error'])
            return jsonify({'error': account_info['error']}), 500
        
        return jsonify(account_info)
    except Exception as e:
        print(f"Account endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/portfolio', methods=['GET'])
def get_portfolio():
    """Get current portfolio positions"""
    print("=== PORTFOLIO ENDPOINT CALLED ===")
    try:
        # Temporarily get user_id from query param for testing
        user_id = int(request.args.get('user_id', '1'))  # Convert to integer
        print(f"User ID: {user_id}")
        
        positions = get_portfolio_positions(user_id)
        print("Positions:", positions)
        
        if isinstance(positions, dict) and 'error' in positions:
            print("Portfolio error:", positions['error'])
            return jsonify({'error': positions['error']}), 500
        
        return jsonify({'positions': positions})
    except Exception as e:
        print(f"Portfolio endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

# Protected profile endpoints
@app.route('/profiles', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    db = next(get_db())
    
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    return jsonify({
        'id': profile.id,
        'user_id': profile.user_id,
        'risk_tolerance': profile.risk_tolerance,
        'investment_goals': profile.investment_goals,
        'preferred_sectors': profile.preferred_sectors,
        'created_at': profile.created_at.isoformat(),
        'updated_at': profile.updated_at.isoformat()
    })

@app.route('/profiles', methods=['POST'])
@jwt_required()
def create_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = next(get_db())
    
    # Check if profile already exists
    if db.query(Profile).filter(Profile.user_id == user_id).first():
        return jsonify({'error': 'Profile already exists'}), 400
    
    profile = Profile(
        user_id=user_id,
        risk_tolerance=data.get('risk_tolerance', 'moderate'),
        investment_goals=data.get('investment_goals', []),
        preferred_sectors=data.get('preferred_sectors', [])
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return jsonify({
        'id': profile.id,
        'user_id': profile.user_id,
        'risk_tolerance': profile.risk_tolerance,
        'investment_goals': profile.investment_goals,
        'preferred_sectors': profile.preferred_sectors,
        'created_at': profile.created_at.isoformat(),
        'updated_at': profile.updated_at.isoformat()
    }), 201

@app.route('/profiles', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    db = next(get_db())
    
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    # Update profile fields
    if 'risk_tolerance' in data:
        profile.risk_tolerance = data['risk_tolerance']
    if 'investment_goals' in data:
        profile.investment_goals = data['investment_goals']
    if 'preferred_sectors' in data:
        profile.preferred_sectors = data['preferred_sectors']
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    
    return jsonify({
        'id': profile.id,
        'user_id': profile.user_id,
        'risk_tolerance': profile.risk_tolerance,
        'investment_goals': profile.investment_goals,
        'preferred_sectors': profile.preferred_sectors,
        'created_at': profile.created_at.isoformat(),
        'updated_at': profile.updated_at.isoformat()
    })

# Add JWT error handler
@app.errorhandler(422)
def handle_422_error(error):
    print("=== 422 ERROR HANDLER ===")
    print(f"Error: {error}")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Authorization header: {request.headers.get('Authorization')}")
    return jsonify({'error': 'JWT token validation failed'}), 422

@app.errorhandler(Unauthorized)
def handle_unauthorized(error):
    print("=== UNAUTHORIZED ERROR HANDLER ===")
    print(f"Error: {error}")
    print(f"Request headers: {dict(request.headers)}")
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/debug/users', methods=['GET'])
def debug_users():
    """Debug endpoint to check users in database"""
    try:
        db = next(get_db())
        users = db.query(User).all()
        users_data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'balance': user.balance
        } for user in users]
        
        print("Users in database:", users_data)
        return jsonify({'users': users_data})
    except Exception as e:
        print(f"Debug users error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug/portfolio', methods=['GET'])
def debug_portfolio():
    """Debug endpoint to check portfolio entries"""
    try:
        db = next(get_db())
        portfolios = db.query(Portfolio).all()
        portfolios_data = [{
            'id': portfolio.id,
            'user_id': portfolio.user_id,
            'symbol': portfolio.symbol,
            'quantity': portfolio.quantity,
            'avg_price': portfolio.avg_price
        } for portfolio in portfolios]
        
        print("Portfolio entries:", portfolios_data)
        return jsonify({'portfolios': portfolios_data})
    except Exception as e:
        print(f"Debug portfolio error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test/portfolio', methods=['GET'])
def test_portfolio():
    """Test endpoint to check portfolio query directly"""
    try:
        print("=== TEST PORTFOLIO ENDPOINT ===")
        user_id = int(request.args.get('user_id', '1'))
        print(f"Testing with user_id: {user_id}")
        
        db = next(get_db())
        print("Database session created")
        
        # Direct query
        portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        print(f"Direct query found {len(portfolios)} portfolios")
        
        for p in portfolios:
            print(f"Portfolio: {p.symbol}, qty: {p.quantity}, price: {p.avg_price}")
        
        # Test the function
        positions = get_portfolio_positions(user_id)
        print(f"Function returned {len(positions)} positions")
        
        return jsonify({
            'direct_query_count': len(portfolios),
            'function_positions': positions,
            'test': 'success'
        })
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)