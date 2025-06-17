from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import yfinance as yf
from datetime import datetime, timedelta
from model import load_and_train, get_prediction, get_recommendation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')

global data, scaler, model, features

def scrape_market_sentiment():
    try:
        api_key = os.getenv('FINNHUB_API_KEY')
        if not api_key:
            raise ValueError("FINNHUB_API_KEY not found in environment variables")
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol=NVDA&from={week_ago}&to={today}&token={api_key}"
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
    return send_from_directory(app.static_folder, 'index.html')

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

if __name__ == '__main__':
    app.run(debug=True)
