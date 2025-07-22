# 🌿 Minty - AI-Powered Stock Trading Platform

A modern, AI-driven stock trading platform that combines real-time market data, machine learning predictions, and intuitive portfolio management. Built as a Portfolio Project for Holberton School.

## ✨ Features

### 🚀 **Core Trading Features**
- **Real-time Market Data**: Live stock prices with Yahoo Finance integration
- **AI-Powered Predictions**: Machine learning models for price forecasting
- **Paper Trading**: Risk-free trading simulation with virtual money
- **Portfolio Management**: Track positions, P&L, and performance analytics
- **Technical Analysis**: RSI, MACD, Bollinger Bands, and more indicators

### 🎯 **Advanced Capabilities**
- **Smart Recommendations**: AI-driven buy/sell/hold signals
- **Multi-Stock Support**: Trade NVIDIA, Apple, AMD, and more
- **Order Management**: Market and limit orders with real-time execution
- **Performance Tracking**: Comprehensive portfolio analytics and charts
- **User Authentication**: Secure JWT-based authentication system

### 🎨 **User Experience**
- **Apple-Inspired Design**: Clean, modern interface with smooth animations
- **Responsive Layout**: Optimized for desktop, tablet, and mobile
- **Interactive Charts**: Real-time data visualization with Chart.js
- **Intuitive Navigation**: Seamless user flow from landing to trading

## 🛠️ Tech Stack

### **Frontend**
- **HTML5**: Semantic markup and accessibility
- **CSS3**: Modern styling with Apple-inspired design
- **JavaScript (ES6+)**: Interactive features and real-time updates
- **Chart.js**: Data visualization and technical charts
- **Font Awesome**: Icon library for UI elements

### **Backend**
- **Python 3.13**: Server-side logic and API development
- **Flask**: Web framework for RESTful API endpoints
- **SQLAlchemy**: Object-relational mapping (ORM)
- **Flask-JWT-Extended**: Authentication and authorization
- **Flask-CORS**: Cross-origin resource sharing

### **Database**
- **MySQL**: Relational database management system
- **XAMPP**: Local development environment
- **SQLAlchemy ORM**: Database abstraction layer

### **Machine Learning**
- **scikit-learn**: Machine learning algorithms
- **XGBoost**: Gradient boosting for price predictions
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **yfinance**: Yahoo Finance API for market data
- **ta**: Technical analysis indicators

## 🚀 Quick Start

### **Prerequisites**
- Python 3.13+
- MySQL (via XAMPP)
- Git
- Modern web browser

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/lblaseygg/minty.git
   cd minty
   ```

2. **Set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   # Start XAMPP and enable MySQL
   # Create database: minty_db
   python3 setup_xampp_database.py
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

6. **Start the application**
   ```bash
   python3 backend/app.py
   ```

7. **Access the platform**
   - Open browser and navigate to: `http://localhost:5001`
   - Or directly open: `frontend/landing.html`

## 📖 Usage Guide

### **Getting Started**
1. **Landing Page**: Explore features and project overview
2. **Create Account**: Register with email and password
3. **Login**: Access your trading dashboard
4. **First Trade**: Select a stock and place your first paper trade

### **Trading Interface**
- **Stock Selection**: Choose from available stocks (NVDA, AAPL, AMD, etc.)
- **Order Placement**: Set quantity, price, and order type
- **Portfolio View**: Monitor positions and performance
- **AI Insights**: View predictions and recommendations

## 🏗️ Project Structure

```
minty/
├── frontend/                 # Frontend application
│   ├── assets/              # Images, logos, and static files
│   │   ├── minty-logo-icon.svg
│   │   └── *.svg            # Stock company logos
│   ├── landing.html         # Landing page
│   ├── documentation.html   # Documentation page
│   ├── index.html           # Main dashboard
│   ├── login.html           # Login page
│   ├── register.html        # Registration page
│   ├── trade.html           # Trading interface
│   ├── portfolio.html       # Portfolio management
│   ├── profile.html         # User profile
│   ├── *.css                # Stylesheets
│   └── *.js                 # JavaScript files
├── backend/                 # Backend application
│   ├── app.py              # Main Flask application
│   ├── model.py            # Machine learning models
│   ├── config.py           # Configuration settings
│   └── database.py         # Database models
├── database/               # Database setup and scripts
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── setup_xampp_database.py # Database setup script
└── README.md              # Project documentation
```

## 🔧 Configuration

### **Environment Variables**
```env
# Database Configuration
DATABASE_TYPE=mysql
MYSQL_USER=minty_user
MYSQL_PASSWORD=your_secure_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=minty_db

# Security
JWT_SECRET_KEY=your_very_secure_secret_key_here

# Application
FLASK_ENV=development
DEBUG=True

# Optional: Alpaca Trading API
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

## 📊 API Reference

### **Authentication Endpoints**
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `POST /auth/logout` - User logout

### **Market Data Endpoints**
- `GET /stocks` - Get available stocks
- `GET /live_data/{symbol}` - Real-time stock data
- `GET /historical_data/{symbol}` - Historical price data
- `GET /predict/{symbol}` - AI price predictions
- `GET /recommend/{symbol}` - Trading recommendations

### **Trading Endpoints**
- `POST /orders` - Create trading order
- `GET /orders` - Get user orders
- `GET /portfolio` - Get portfolio positions
- `GET /account` - Get account information

## 🤖 Machine Learning Features

### **AI Prediction Model**
- **Algorithm**: XGBoost Regressor
- **Features**: Price data, technical indicators, market sentiment
- **Training**: 2 years of historical data
- **Output**: Price predictions with confidence scores

### **Technical Indicators**
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence
- **Bollinger Bands**: Volatility indicators
- **Moving Averages**: Trend analysis

## 🚀 Deployment

### **Local Development**
```bash
python3 backend/app.py
# Access at http://localhost:5001
```

### **Production Deployment**
- **Heroku**: Easy deployment with Git integration
- **Railway**: Modern platform with automatic deployments
- **AWS**: Enterprise-grade cloud deployment
- **Docker**: Containerized deployment option

## 📚 Documentation

- **User Guide**: [Documentation](frontend/documentation.html)
- **API Reference**: Complete endpoint documentation
- **Setup Guide**: Step-by-step installation instructions

## 👨‍💻 Team

- **Luis Fernando Feliciano**: Full-stack developer and project lead
- **GitHub**: [@lblaseygg](https://github.com/lblaseygg)
- **LinkedIn**: [Luis Fernando Feliciano](https://www.linkedin.com/in/luisfernandofeliciano/)
- **Twitter**: [@luisdevgg](https://x.com/luisdevgg)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Holberton School**: Portfolio project framework
- **Yahoo Finance**: Market data API
- **Chart.js**: Data visualization library
- **Font Awesome**: Icon library
- **Flask**: Web framework
- **XGBoost**: Machine learning library

---

**Minty Trading Platform** - Empowering traders with AI-driven insights and intuitive portfolio management.

*Built with ❤️ for Holberton School Portfolio Project:)*