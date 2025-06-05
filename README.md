# Django Finance: AI-Powered Portfolio Analysis

Django Finance is a web application that provides intelligent financial portfolio analysis and recommendations using OpenAI's large language models. This application helps users gain insights into their investment portfolios and receive actionable recommendations to optimize their investments.

## 🌟 Features

### 🔐 API Key Authentication
- Secure API access using custom API key authentication
- User accounts with unique API keys for each user
- No traditional login required - API key based access only
- Management commands for creating users and managing API keys
- Automatic tracking of last API access times

### 📊 Stock Data Retrieval
- Real-time stock data fetching from Yahoo Finance
- Concurrent processing for multiple tickers
- Comprehensive stock information including market cap, sector, and asset class
- Auto-derives missing `shares` *or* `value` for each asset using live market prices

### 🤖 AI-Powered Portfolio Analysis
- Deep analysis of portfolio composition and balance
- Risk assessment and diversification evaluation
- Performance insights and strengths/weaknesses identification
- Personalized analysis based on investment goals
- Cash allocation recommendations
- All powered by OpenAI's GPT models
- Persistent conversation threads for continued context
- Conversational input via dedicated chat parameter

### 💡 Intelligent Investment Recommendations
- Actionable recommendations for each asset (Buy, Hold, Sell)
- Specific dollar amounts for each BUY or SELL action (use 0 for HOLD)
- Suggestions for new investments aligned with your goals
- Recommendations that consider available cash
- Clear reasoning for each recommendation
- Dedicated feedback section explaining the rationale behind recommendations
- Separate API endpoint for targeted recommendations

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
   
   # OpenAI Assistants (optional)
   # OPENAI_ASSISTANT_ID=your_analysis_assistant_id
   # OPENAI_RECOMMENDATIONS_ASSISTANT_ID=your_recommendations_assistant_id

   # Django Configuration
   DEBUG=True
   SECRET_KEY=your_secret_key_here
   AI_DEBUG=True  # Enable to include AI debug information in responses
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

**Authentication Required:** All API endpoints require authentication using an API key in the Authorization header:
```
Authorization: ApiKey YOUR_API_KEY_HERE
```

### User Registration

```
POST /api/register/
```
**No authentication required** - Creates a new user account and returns an API key for subsequent requests.

**Required Parameters:**
- `email`: User's email address (used as username)

**Optional Parameters:**
- `first_name`: User's first name
- `last_name`: User's last name

Example request:
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

Example response:
```json
{
  "user_id": "84b27392-2345-4b5b-87ba-d370d005b2b4",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "api_key": "YQ52FZMskRJBRiHlt5Rh3W7arwFkcgrqf5rGlL3pQ4rqXviF4sxoBx_ER4GKFo-h",
  "created_at": "2025-06-05T18:27:39.123456Z",
  "message": "User created successfully"
}
```

**Important:** Store the API key securely as it cannot be retrieved again. Use it in the Authorization header for all subsequent API requests.

### Stock Information

```
POST /api/ticker-info/
```
Returns sector, market-cap, and classification details for the specified tickers. Send a JSON body such as:

```json
{"tickers": ["AAPL", "MSFT", "GOOGL"]}
```

### Portfolio Analysis

```
POST /api/analyze/
```
Analyzes a portfolio and provides AI-powered insights (without recommendations).

**Parameters:**
- `portfolio`: Array of assets with their details (required)
- `cash`: Available cash for investment (optional, default: 0)
- `investment_goals`: Text description of investment objectives, risk tolerance, time horizon, etc. (optional, default: empty string)
- `chat`: Conversational context or questions to include in the analysis (optional, default: empty string)
- `conversation_id`: UUID for continuing a previous conversation (optional)

**Asset requirements:** Each asset entry must include a `symbol` field and **either** `shares` **or** `value` (dollar amount). If you supply only one, the other will be calculated automatically based on the latest market price.

Example request body:
```json
{
  "portfolio": [
    {
      "symbol": "AAPL",
      "type": "Stock",
      "shares": 10
    },
    {
      "symbol": "MSFT",
      "type": "Stock",
      "value": 1500
    }
  ],
  "cash": 5000,
  "investment_goals": "Looking to diversify into renewable energy with moderate risk tolerance and a 10-year investment horizon.",
  "chat": "I'm particularly interested in clean tech and AI. How should I balance these interests?"
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
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Portfolio Recommendations

```
POST /api/recommendations/
```
Provides specific investment recommendations for a portfolio.

**Parameters:**
- `portfolio`: Array of assets with their details (required)
- `cash`: Available cash for investment (optional, default: 0)
- `investment_goals`: Text description of investment objectives, risk tolerance, time horizon, etc. (optional, default: empty string)
- `chat`: Conversational context or questions to include in the recommendations (optional, default: empty string)
- `conversation_id`: UUID for continuing a previous conversation (optional)

**Asset requirements:** Each asset entry must include a `symbol` field and **either** `shares` **or** `value`.

Example response:
```json
{
  "total_value": 3000,
  "total_portfolio_value": 8000,
  "cash": 5000,
  "asset_count": 2,
  "asset_types": ["Stock"],
  "investment_goals": "Looking to diversify into renewable energy with moderate risk tolerance and a 10-year investment horizon.",
  "recommendations": [
    {
      "ticker": "AAPL",
      "action": "HOLD",
      "quantity": 0,
      "reason": "Strong performance and growth potential."
    },
    {
      "ticker": "MSFT",
      "action": "BUY",
      "quantity": 2500,
      "reason": "Excellent growth trajectory and cloud dominance."
    },
    {
      "ticker": "ICLN",
      "action": "BUY",
      "quantity": 5300,
      "reason": "Provides exposure to renewable energy sector aligning with investment goals."
    }
  ],
  "feedback": "Your portfolio shows good exposure to tech but could benefit from diversification into renewable energy given your stated goals. The recommendations aim to maintain your core holdings while adding green energy exposure to align with your 10-year horizon.",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}

## 👥 User Management

The application includes management commands for creating and managing API users:

### Create a New User
```bash
python manage.py create_api_user username email@example.com --first-name John --last-name Doe
```

### List All Users
```bash
python manage.py list_api_users
```

### List Only Active Users
```bash
python manage.py list_api_users --active-only
```

### Show Partial API Keys (for debugging)
```bash
python manage.py list_api_users --show-keys
```

### Regenerate API Key for a User
```bash
python manage.py regenerate_api_key username
```

**Important:** API keys are displayed only once when created or regenerated. Store them securely as they cannot be retrieved again.

## 🧠 AI Integration

The application uses OpenAI's GPT models for two primary functions:

1. **Portfolio Analysis**: Evaluates your portfolio composition, balance, risk, and diversification.
2. **Investment Recommendations**: Provides specific actions for each asset and suggests new investments.

The AI integration uses a sophisticated prompt management system found in `portfolio/prompts.py`, which allows for:
- Structured prompt templates
- Dynamic data injection
- Configurable model parameters
- Easy extension for new AI features

### 🔄 Conversation Persistence and Context

The application supports persistent conversations with the AI for both analysis and recommendations:

- Each conversation is assigned a unique `conversation_id`
- Clients can pass the `conversation_id` in subsequent requests to continue the conversation
- The AI maintains context from previous interactions within the same conversation
- Separate conversation threads for analysis and recommendations
- Leverages OpenAI's thread-based conversation APIs (with fallback to direct completions)
- Dedicated `chat` parameter allows users to provide conversational context or specific questions
- Both analysis and recommendations endpoints support the `chat` parameter for consistent user experience

## 🔒 Security and Debugging

- API keys are stored in environment variables
- The `.env` file is excluded from version control
- Django's security features protect against common web vulnerabilities
- Comprehensive AI debug mode captures full prompt messages (system + user) for all LLM calls
- Debug information includes timing, token usage, and complete conversation context

## 📝 Project Structure

```
django-finance/
├── financial_advisor/     # Django project settings
├── portfolio/             # Main app
│   ├── views.py           # API endpoints
│   ├── prompts.py         # AI prompt management
│   ├── ai_utils.py        # AI helper utilities
│   ├── ai_debug.py        # Debug tools for AI interactions
│   ├── conversation_utils.py # Conversation persistence utilities
│   ├── models.py          # Database models (including Conversation model)
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
5. Incorporates conversational context from user chat input

This system makes it easy to add new AI-powered features by simply defining new prompt templates.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [OpenAI](https://openai.com/) for providing the AI models
- [Yahoo Finance API](https://pypi.org/project/yfinance/) for financial data
- [Django](https://www.djangoproject.com/) for the web framework
