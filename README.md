# Django Finance: AI-Powered Portfolio Analysis

Django Finance is a web application that provides intelligent financial portfolio analysis and recommendations using OpenAI's large language models. This application helps users gain insights into their investment portfolios and receive actionable recommendations to optimize their investments.

## 🌟 Features

### 📊 Stock Data Retrieval
- Real-time stock data fetching from Yahoo Finance
- Concurrent processing for multiple tickers
- Comprehensive stock information including market cap, sector, and asset class

### 🤖 AI-Powered Portfolio Analysis
- Deep analysis of portfolio composition and balance
- Risk assessment and diversification evaluation
- Performance insights and strengths/weaknesses identification
- Personalized analysis based on investment goals
- Cash allocation recommendations
- All powered by OpenAI's GPT models

### 💡 Intelligent Investment Recommendations
- Actionable recommendations for each asset (Buy, Hold, Sell)
- Specific guidance on quantity (All, Some, More)
- Suggestions for new investments aligned with your goals
- Recommendations that consider available cash
- Clear reasoning for each recommendation

### 🧠 Modular Prompt Management
- Structured system for managing AI prompts
- Centralized templates for consistent AI interactions
- Easy extensibility for adding new AI features

## 🔧 Technology Stack

- **Backend**: Django and Django REST Framework
- **AI**: OpenAI GPT models (configurable)
- **Financial Data**: Yahoo Finance API
- **Environment Management**: python-dotenv

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Basic understanding of investing concepts

## 🚀 Getting Started

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yevgetman/django-finance.git
   cd django-finance
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. Create a `.env` file in the project root with the following variables:
   ```
   # OpenAI API Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o
   OPENAI_RECOMMENDATIONS_MODEL=gpt-4o

   # Django Configuration
   DEBUG=True
   SECRET_KEY=your_secret_key_here
   ```

2. Replace `your_openai_api_key_here` with your actual OpenAI API key.

### Running the Application

1. Apply migrations:
   ```bash
   python manage.py migrate
   ```

2. Start the development server:
   ```bash
   python manage.py runserver
   ```

3. Access the application at `http://127.0.0.1:8000/`

## 📡 API Endpoints

### Stock Information

```
GET /api/stocks/?tickers=AAPL,MSFT,GOOGL
```
Returns detailed information about the specified stocks.

### Portfolio Analysis

```
POST /api/analyze/
```
Analyzes a portfolio and provides AI-powered insights and recommendations.

**Parameters:**
- `portfolio`: Array of assets with their details (required)
- `cash`: Available cash for investment (optional, default: 0)
- `investment_goals`: Text description of investment objectives, risk tolerance, time horizon, etc. (optional, default: empty string)

Example request body:
```json
{
  "portfolio": [
    {
      "symbol": "AAPL",
      "type": "Stock",
      "shares": 10,
      "current_price": 150,
      "value": 1500
    },
    {
      "symbol": "MSFT",
      "type": "Stock",
      "shares": 5,
      "current_price": 300,
      "value": 1500
    }
  ],
  "cash": 5000,
  "investment_goals": "Looking to diversify into renewable energy with moderate risk tolerance and a 10-year investment horizon."
}
```

Example response:
```json
{
  "total_value": 3000,
  "total_portfolio_value": 8000,
  "cash": 5000,
  "asset_count": 2,
  "asset_types": ["Stock"],
  "investment_goals": "Looking to diversify into renewable energy with moderate risk tolerance and a 10-year investment horizon.",
  "analysis": "Detailed AI analysis of the portfolio...",
  "recommendations": [
    {
      "ticker": "AAPL",
      "action": "HOLD",
      "quantity": "ALL",
      "reason": "Strong performance and growth potential."
    },
    {
      "ticker": "MSFT",
      "action": "BUY",
      "quantity": "MORE",
      "reason": "Excellent growth trajectory and cloud dominance."
    },
    {
      "ticker": "ICLN",
      "action": "BUY",
      "quantity": "NEW",
      "reason": "Provides exposure to renewable energy sector aligning with investment goals."
    }
  ]
}
```

## 🧠 AI Integration

The application uses OpenAI's GPT models for two primary functions:

1. **Portfolio Analysis**: Evaluates your portfolio composition, balance, risk, and diversification.
2. **Investment Recommendations**: Provides specific actions for each asset and suggests new investments.

The AI integration uses a sophisticated prompt management system found in `portfolio/prompts.py`, which allows for:
- Structured prompt templates
- Dynamic data injection
- Configurable model parameters
- Easy extension for new AI features

## 🔒 Security

- API keys are stored in environment variables
- The `.env` file is excluded from version control
- Django's security features protect against common web vulnerabilities

## 📝 Project Structure

```
django-finance/
├── financial_advisor/     # Django project settings
├── portfolio/             # Main app
│   ├── views.py           # API endpoints
│   ├── prompts.py         # AI prompt management
│   ├── ai_utils.py        # AI helper utilities
├── .env                   # Environment variables (create this)
├── requirements.txt       # Project dependencies
└── manage.py              # Django management script
```

## 📚 AI Prompt System

The application features a modular prompt management system that:
1. Maintains consistent AI interactions
2. Formats data for optimal AI understanding
3. Parses AI responses into structured data
4. Handles errors gracefully

This system makes it easy to add new AI-powered features by simply defining new prompt templates.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [OpenAI](https://openai.com/) for providing the AI models
- [Yahoo Finance API](https://pypi.org/project/yfinance/) for financial data
- [Django](https://www.djangoproject.com/) for the web framework
