from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import yfinance as yf
from datetime import datetime, timedelta
from model import load_and_train, get_prediction, get_recommendation, Base, User, Order, Profile
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
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
        if alpaca:
            positions = alpaca.list_positions()
            return [{
                'symbol': pos.symbol,
                'qty': float(pos.qty),
                'avg_entry_price': float(pos.avg_entry_price),
                'current_price': float(pos.current_price),
                'market_value': float(pos.market_value),
                'unrealized_pl': float(pos.unrealized_pl)
            } for pos in positions]
        else:
            # Calculate positions from order history
            return calculate_positions_from_orders(user_id)
    except Exception as e:
        print(f"Error getting portfolio positions: {e}")
        return []

def calculate_positions_from_orders(user_id):
    """Calculate portfolio positions from order history for a specific user"""
    try:
        db = next(get_db())
        # Get all filled orders grouped by symbol
        orders = db.query(Order).filter(Order.user_id == user_id, Order.status == 'filled').all()
        
        positions = {}
        for order in orders:
            symbol = order.symbol
            if symbol not in positions:
                positions[symbol] = {
                    'symbol': symbol,
                    'qty': 0,
                    'total_cost': 0,
                    'avg_entry_price': 0
                }
            
            if order.side == 'buy':
                positions[symbol]['qty'] += order.qty
                positions[symbol]['total_cost'] += order.qty * order.price
            elif order.side == 'sell':
                positions[symbol]['qty'] -= order.qty
                # For sells, we reduce the total cost proportionally
                if positions[symbol]['qty'] > 0:
                    cost_per_share = positions[symbol]['total_cost'] / (positions[symbol]['qty'] + order.qty)
                    positions[symbol]['total_cost'] = positions[symbol]['qty'] * cost_per_share
                else:
                    positions[symbol]['total_cost'] = 0
        
        # Convert to list and add current prices
        result = []
        for symbol, pos in positions.items():
            if pos['qty'] > 0:  # Only include positions with positive quantity
                # Get current price
                try:
                    ticker = yf.Ticker(symbol)
                    current_price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')
                    if not current_price:
                        hist = ticker.history(period='1d', interval='1m')
                        if not hist.empty:
                            current_price = float(hist['Close'][-1])
                        else:
                            current_price = pos['avg_entry_price'] if pos['avg_entry_price'] > 0 else 0
                except:
                    current_price = pos['avg_entry_price'] if pos['avg_entry_price'] > 0 else 0
                
                avg_entry_price = pos['total_cost'] / pos['qty'] if pos['qty'] > 0 else 0
                market_value = pos['qty'] * current_price
                unrealized_pl = market_value - pos['total_cost']
                
                result.append({
                    'symbol': symbol,
                    'qty': pos['qty'],
                    'avg_entry_price': avg_entry_price,
                    'current_price': current_price,
                    'market_value': market_value,
                    'unrealized_pl': unrealized_pl
                })
        
        return result
    except Exception as e:
        print(f"Error calculating positions: {e}")
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
    user_id = get_jwt_identity()
    data = request.get_json()
    db = next(get_db())
    
    # Validate required fields
    required_fields = ['symbol', 'side', 'qty']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate side
    if data['side'] not in ['buy', 'sell']:
        return jsonify({'error': 'Side must be either "buy" or "sell"'}), 400
    
    # Validate quantity
    if data['qty'] <= 0:
        return jsonify({'error': 'Quantity must be greater than 0'}), 400
    
    # Execute the paper trade
    trade_result = execute_paper_trade(
        symbol=data['symbol'],
        side=data['side'],
        qty=data['qty'],
        price=data.get('price')  # Optional, will use market price if not provided
    )
    
    if not trade_result['success']:
        return jsonify({'error': f'Trade execution failed: {trade_result["error"]}'}), 400
    
    # Store order in database
    order = Order(
        user_id=user_id,
        symbol=data['symbol'],
        side=data['side'],
        qty=data['qty'],
        price=trade_result['filled_price'],
        status=trade_result['status'],
        alpaca_order_id=trade_result.get('order_id')
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return jsonify({
        'id': order.id,
        'user_id': order.user_id,
        'symbol': order.symbol,
        'side': order.side,
        'qty': order.qty,
        'price': order.price,
        'status': order.status,
        'timestamp': order.timestamp.isoformat(),
        'alpaca_order_id': order.alpaca_order_id,
        'trade_result': trade_result
    }), 201

@app.route('/orders', methods=['GET'])
@jwt_required()
def get_user_orders():
    user_id = get_jwt_identity()
    db = next(get_db())
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    
    return jsonify([{
        'id': order.id,
        'symbol': order.symbol,
        'side': order.side,
        'qty': order.qty,
        'price': order.price,
        'status': order.status,
        'timestamp': order.timestamp.isoformat()
    } for order in orders])

@app.route('/account', methods=['GET'])
@jwt_required()
def get_account():
    """Get account information including cash, buying power, and portfolio value"""
    account_info = get_account_info()
    
    if 'error' in account_info:
        return jsonify({'error': account_info['error']}), 500
    
    return jsonify(account_info)

@app.route('/portfolio', methods=['GET'])
@jwt_required()
def get_portfolio():
    """Get current portfolio positions"""
    user_id = get_jwt_identity()
    positions = get_portfolio_positions(user_id)
    
    if isinstance(positions, dict) and 'error' in positions:
        return jsonify({'error': positions['error']}), 500
    
    return jsonify({'positions': positions})

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)