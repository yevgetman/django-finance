# AI Finance API Documentation

## Overview

The AI Finance API provides intelligent portfolio analysis and investment recommendations powered by advanced AI models. This RESTful API helps you analyze your investment portfolio, get personalized recommendations, and receive ongoing financial guidance through a conversational interface.

## 🔑 Authentication

All API endpoints require authentication using API keys provided in HTTP headers.

### Required Headers

**For All Users:**
- `Authorization: YOUR_GLOBAL_API_KEY` - Required for all requests

**For Registered Users (Optional):**
- `Authentication: YOUR_USER_API_KEY` - Provides personalized features and conversation history

### Getting Started

1. **Anonymous Access**: Use only the Authorization header with the global API key
2. **Personalized Access**: Register for a user account to get your personal API key for enhanced features

## 📋 API Endpoints

### 1. User Registration

Create a new user account to access personalized features.

**Endpoint:** `POST /api/register/`

**Headers Required:**
- `Authorization: YOUR_GLOBAL_API_KEY`

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "api_key": "your_personal_api_key_here",
  "created_at": "2025-01-15T10:30:00Z",
  "message": "User created successfully"
}
```

**Important:** Save your API key securely - it won't be shown again!

---

### 2. Portfolio Analysis

Get comprehensive AI-powered analysis of your investment portfolio.

**Endpoint:** `POST /api/analyze/`

**Headers Required:**
- `Authorization: YOUR_GLOBAL_API_KEY`
- `Authentication: YOUR_USER_API_KEY` (optional, for personalized analysis)

**Request Body:**
```json
{
  "portfolio": [
    {
      "symbol": "AAPL",
      "shares": 10,
      "account": "Trading"
    },
    {
      "symbol": "MSFT", 
      "value": 1500,
      "account": "IRA"
    }
  ],
  "cash": 5000,
  "investment_goals": "Growth with moderate risk for retirement in 15 years",
  "conversation_id": "optional-uuid-for-continuing-conversation"
}
```

**Portfolio Asset Requirements:**
- `symbol`: Stock ticker symbol (required)
- `shares` OR `value`: Either number of shares owned OR dollar value of holding (one required)
- `account`: Account type like "Trading", "IRA", "401k" (optional)

**Response:**
```json
{
  "total_value": 3000,
  "total_portfolio_value": 8000,
  "cash": 5000,
  "asset_count": 2,
  "asset_types": ["Stock"],
  "analysis": "Your portfolio shows strong concentration in technology stocks with AAPL and MSFT representing the majority of holdings. While both are quality companies, this creates sector concentration risk...",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

### 3. Investment Recommendations

Get specific buy/sell/hold recommendations for your portfolio.

**Endpoint:** `POST /api/recommendations/`

**Headers Required:**
- `Authorization: YOUR_GLOBAL_API_KEY`
- `Authentication: YOUR_USER_API_KEY` (optional, for personalized recommendations)

**Request Body:**
```json
{
  "portfolio": [
    {
      "symbol": "AAPL",
      "shares": 10,
      "account": "Trading"
    },
    {
      "symbol": "MSFT",
      "value": 1500,
      "account": "IRA"
    }
  ],
  "cash": 5000,
  "monthly_cash": 500,
  "investment_goals": "Diversify into renewable energy with moderate risk",
  "chat": "I can invest $500 monthly. How should I allocate this?"
}
```

**Additional Parameters:**
- `monthly_cash`: Amount available for monthly investing (optional)
- `chat`: Specific questions or context for recommendations (optional)

**Response:**
```json
{
  "total_value": 3000,
  "total_portfolio_value": 8000,
  "cash": 5000,
  "recommendations": [
    {
      "ticker": "AAPL",
      "action": "HOLD",
      "amount": 0,
      "account": "Trading",
      "comments": "Strong performance and growth potential"
    },
    {
      "ticker": "MSFT",
      "action": "BUY", 
      "amount": 2500,
      "account": "IRA",
      "comments": "Excellent growth trajectory and cloud dominance"
    },
    {
      "ticker": "ICLN",
      "action": "BUY",
      "amount": 3000,
      "account": "Default",
      "comments": "[NEW ASSET] Clean energy ETF for renewable diversification"
    }
  ],
  "recommendations_by_account": {
    "Trading": [...],
    "IRA": [...],
    "Default": [...]
  },
  "recurrent_investments": [
    {
      "ticker": "VTI",
      "action": "BUY",
      "amount": 250,
      "account": "Default", 
      "comments": "Monthly broad market allocation"
    },
    {
      "ticker": "ICLN",
      "action": "BUY",
      "amount": 250,
      "account": "Default",
      "comments": "Monthly clean energy investment"
    }
  ],
  "feedback": "Your portfolio would benefit from diversification beyond tech stocks. The recommendations focus on adding renewable energy exposure while maintaining your core holdings...",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Recommendation Actions:**
- `BUY`: Purchase recommendation with dollar amount
- `SELL`: Sell recommendation with dollar amount  
- `HOLD`: Keep current position (amount will be 0)

**New Assets:** Recommendations for new investments are marked with `[NEW ASSET]` in the comments.

---

### 4. Chat & Follow-up Questions

Continue conversations and ask follow-up questions about your portfolio.

**Endpoint:** `POST /api/chat/`

**Headers Required:**
- `Authorization: YOUR_GLOBAL_API_KEY`
- `Authentication: YOUR_USER_API_KEY` (optional, for conversation history)

**Request Body:**
```json
{
  "message": "What if I want to be more aggressive with my investments?",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response:**
```json
{
  "response": "For a more aggressive approach, you could increase allocation to growth stocks and emerging sectors like AI and biotech. Consider reducing bond exposure and adding small-cap growth funds...",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

### 5. Stock Information Lookup

Get detailed information about any stock or ETF.

**Endpoint:** `POST /api/ticker-info/`

**Headers Required:**
- `Authorization: YOUR_GLOBAL_API_KEY`

**Request Body:**
```json
{
  "tickers": ["AAPL", "MSFT", "ICLN"]
}
```

**Response:**
```json
{
  "ticker_data": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "asset_class": "Stock",
      "sector": "Technology",
      "market_cap": 3000000000000,
      "market_cap_category": "Mega Cap",
      "currency": "USD",
      "country": "United States"
    },
    {
      "ticker": "ICLN", 
      "name": "iShares Global Clean Energy ETF",
      "asset_class": "ETF/Fund",
      "sector": "Clean Energy",
      "yield": 0.02,
      "total_assets": 5000000000,
      "is_sector_etf": true
    }
  ]
}
```

---

### 6. Delete Account

Delete your user account and all associated data.

**Endpoint:** `DELETE /api/delete-account/`

**Headers Required:**
- `Authorization: YOUR_GLOBAL_API_KEY`
- `Authentication: YOUR_USER_API_KEY`

**Request Body:** None required

**Response:**
```json
{
  "message": "Account deleted successfully"
}
```

## 🎯 Key Features

### Automatic Asset Classification
The API automatically determines whether your holdings are stocks, ETFs, mutual funds, or other asset types - no need to specify manually.

### Live Market Data
All analysis uses real-time stock prices and market data for accurate valuations and recommendations.

### Flexible Input
You can specify holdings by either:
- Number of shares owned
- Total dollar value of the position

### Account-Based Organization
Organize your portfolio across different account types (Trading, IRA, 401k, etc.) for tax-optimized recommendations.

### Conversation Continuity
Use conversation IDs to maintain context across multiple API calls for ongoing financial guidance.

### Monthly Investment Planning
Get recommendations for regular monthly investments to build your portfolio over time.

## 📊 Response Data

### Portfolio Metrics
- `total_value`: Combined value of all holdings
- `total_portfolio_value`: Total including cash
- `asset_count`: Number of different assets
- `asset_types`: Types of assets in portfolio

### Recommendation Types
- **Individual Recommendations**: Specific actions for each holding
- **Account-Based Grouping**: Recommendations organized by account type
- **Recurring Investments**: Monthly investment suggestions
- **Strategic Feedback**: Overall strategy explanation

## ⚠️ Important Notes

### API Key Security
- Never share your API keys publicly
- Store them securely in your application
- Regenerate keys if compromised

### Rate Limits
- API requests are subject to reasonable rate limits
- Contact support if you need higher limits for production use

### Data Accuracy
- All stock data is sourced from reliable financial APIs
- Prices are updated in real-time during market hours
- Analysis reflects current market conditions

### Investment Disclaimer
- This API provides educational information only
- Not professional financial advice
- Always consult qualified financial advisors for investment decisions
- Past performance doesn't guarantee future results

## 🚀 Getting Started

1. **Get API Access**: Contact us for your global API key
2. **Test Anonymous Access**: Try the ticker-info endpoint
3. **Register for Personal Features**: Create a user account for portfolio analysis
4. **Start Analyzing**: Upload your portfolio and get AI-powered insights!

## 💡 Tips for Best Results

### Portfolio Input
- Include diverse asset types for comprehensive analysis
- Specify account types for tax-optimized recommendations
- Provide clear investment goals and time horizons

### Questions & Chat
- Ask specific questions about your portfolio
- Mention your risk tolerance and investment timeline
- Follow up with clarifying questions for detailed guidance

### Goal Setting
Be specific about:
- Investment timeline (retirement in X years)
- Risk tolerance (conservative, moderate, aggressive)
- Specific objectives (growth, income, diversification)
- Any constraints (tax considerations, ESG preferences)

---

*This API is powered by advanced AI models and real-time financial data to provide personalized investment guidance. Always remember that this is educational information and not professional financial advice.*
