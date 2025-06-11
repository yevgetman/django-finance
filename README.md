# Django Finance: AI-Powered Portfolio Analysis

Django Finance is a web application that provides intelligent financial portfolio analysis and recommendations using OpenAI's large language models. This application helps users gain insights into their investment portfolios and receive actionable recommendations to optimize their investments.

## 🌟 Features

### 🔐 Dual-Header Authentication System
- **Two-tier authentication approach**:
  - **Authorization header (required)**: Contains global API key for API access
  - **Authentication header (optional)**: Contains user-specific API key for personalized features
- Support for both authenticated and anonymous API access
- User accounts with unique API keys for personalized experiences
- No traditional login required - API key based access only
- Management commands for creating users and managing API keys
- Automatic tracking of last API access times

### 📊 Stock Data Retrieval
- Real-time stock data fetching from Yahoo Finance
- Concurrent processing for multiple tickers
- Comprehensive stock information including market cap, sector, and asset class
- **Automatic asset type derivation** from yfinance data (ETF, Stock, Mutual Fund, etc.)
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
- **Monthly recurring investment recommendations** based on regular cash contributions
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

**Authentication System:**

All API endpoints require the **Authorization header** with a global API key:
```
Authorization: ApiKey GLOBAL_API_KEY_HERE
```

For personalized features and user-specific data, include the optional **Authentication header**:
```
Authentication: ApiKey USER_API_KEY_HERE
```

**Access Levels:**
- **Anonymous access**: Only Authorization header required (global API key)
- **Authenticated access**: Both Authorization and Authentication headers required

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
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "api_key": "YQ52FZMskRJBRiHlt5Rh3W7arwFkcgrqf5rGlL3pQ4rqXviF4sxoBx_ER4GKFo-h",
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

**Asset requirements:** Each asset entry must include a `symbol` field and **either** `shares` **or** `value` (dollar amount). If you supply only one, the other will be calculated automatically based on the latest market price. You can optionally include an `account` field to specify which account the asset belongs to (e.g., "Trading", "IRA", "401k"). The `type` field is **automatically derived** from yfinance data and no longer needs to be specified.

Example request body:
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
    },
    {
      "symbol": "VTI",
      "shares": 5
      // No account specified will use "Default" account
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
Provides specific investment recommendations for a portfolio, including monthly recurring investment plans.

**Parameters:**
- `portfolio`: Array of assets with their details (required)
- `cash`: Available cash for investment (optional, default: 0)
- `monthly_cash`: Monthly cash contribution amount for recurring investments (optional, default: 0)
- `investment_goals`: Text description of investment objectives, risk tolerance, time horizon, etc. (optional, default: empty string)
- `chat`: Conversational context or questions to include in the recommendations (optional, default: empty string)
- `conversation_id`: UUID for continuing a previous conversation (optional)

**Asset requirements:** Each asset entry must include a `symbol` field and **either** `shares` **or** `value`. The `type` field is **automatically derived** from yfinance data.

Example request body:
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
  "investment_goals": "Looking to diversify into renewable energy with moderate risk tolerance and a 10-year investment horizon.",
  "chat": "I can invest $500 monthly. How should I allocate this?"
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
  "recommendations": [
    {
      "ticker": "AAPL",
      "action": "HOLD",
      "amount": 0,
      "account": "Trading",
      "comments": "Strong performance and growth potential."
    },
    {
      "ticker": "MSFT",
      "action": "BUY",
      "amount": 2500,
      "account": "IRA",
      "comments": "Excellent growth trajectory and cloud dominance."
    },
    {
      "ticker": "ICLN",
      "action": "BUY",
      "amount": 5300,
      "account": "Default",
      "comments": "[NEW ASSET] Provides exposure to renewable energy sector aligning with investment goals."
    }
  ],
  "recommendations_by_account": {
    "Trading": [
      {
        "ticker": "AAPL",
        "action": "HOLD",
        "amount": 0,
        "account": "Trading",
        "comments": "Strong performance and growth potential."
      }
    ],
    "IRA": [
      {
        "ticker": "MSFT",
        "action": "BUY",
        "amount": 2500,
        "account": "IRA",
        "comments": "Excellent growth trajectory and cloud dominance."
      }
    ],
    "Default": [
      {
        "ticker": "ICLN",
        "action": "BUY",
        "amount": 5300,
        "account": "Default",
        "comments": "[NEW ASSET] Provides exposure to renewable energy sector aligning with investment goals."
      }
    ]
  },
  "recurrent_investements": [
    {
      "ticker": "VTI",
      "action": "BUY",
      "amount": 200,
      "account": "Default",
      "comments": "Monthly allocation to broad market index for diversification."
    },
    {
      "ticker": "ICLN",
      "action": "BUY",
      "amount": 300,
      "account": "Default",
      "comments": "Monthly investment in clean energy to build position over time."
    }
  ],
  "feedback": "Your portfolio shows good exposure to tech but could benefit from diversification into renewable energy given your stated goals. The recommendations aim to maintain your core holdings while adding green energy exposure to align with your 10-year horizon. The monthly $500 allocation focuses on building diversified positions gradually.",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Chat Continuation

```
POST /api/chat/
```
Dedicated endpoint for follow-up conversations and questions related to previous analysis or recommendations. Supports both authenticated and anonymous users.

**Parameters:**
- `message`: The chat message or question (required)
- `conversation_id`: UUID of the conversation to continue (optional)

**Authentication Options:**
- **Anonymous users**: Only Authorization header required (conversations not linked to user accounts)
- **Authenticated users**: Both Authorization and Authentication headers required (conversations linked to user accounts)

Example request:
```json
{
  "message": "What if I want to be more aggressive with my investments?",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

Example response:
```json
{
  "response": "For a more aggressive approach, you could increase your allocation to growth stocks and emerging sectors like AI and clean tech. Consider reducing your bond allocation and increasing exposure to small-cap growth funds...",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

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

## 🔒 Security and Authentication

### Authentication Flow
- **Authorization header** (required): Contains global API key that grants access to the API itself
- **Authentication header** (optional): Contains user-specific API key that links requests to user accounts
- **Anonymous users**: Can access API with only the Authorization header
- **Authenticated users**: Can access personalized features with both headers
- **Error responses**:
  - Missing Authorization header: 403 Forbidden
  - Invalid Authentication header: 401 Unauthorized

## 🔍 Debugging

- API keys are stored in environment variables
- The `.env` file is excluded from version control
- Django's security features protect against common web vulnerabilities
- Comprehensive AI debug mode captures full prompt messages (system + user) for all LLM calls
- Debug information includes timing, token usage, complete conversation context, and AI provider details
- AI provider tracking shows which provider (OpenAI or Anthropic) was used for each request
- Conditional debug logging based on `DEBUG` environment variable to keep production logs clean

### AI Debug Mode

When `AI_DEBUG=True` is set in your `.env` file, all API responses will include detailed debug information:

```json
{
  "ai_debug": {
    "enabled": true,
    "total_request_duration_ms": 7581,
    "llm_calls": [
      {
        "model": "claude-3-5-sonnet-20240620",
        "provider": "Anthropic",
        "prompt_type": "portfolio_recommendations",
        "timestamp": "2025-06-08T13:45:30.123456",
        "config": {
          "max_tokens": 1000,
          "temperature": 0.7
        },
        "response": {
          "content_length": 2500,
          "duration_ms": 3200
        }
      }
    ],
    "summary": {
      "total_llm_calls": 1,
      "models_used": ["claude-3-5-sonnet-20240620"],
      "providers_used": ["Anthropic"],
      "prompt_types": ["portfolio_recommendations"],
      "total_llm_duration_ms": 3200,
      "errors": []
    }
  }
}
```

This debug information is invaluable for:
- Tracking which AI provider was used for each request
- Monitoring performance differences between providers
- Debugging issues with specific models or providers
- Analyzing prompt effectiveness and response quality
- Optimizing token usage and request duration

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

## 🆕 Recent Updates

#### Authentication Enhancements
- Added dual-header authentication system separating API access from user identification
- Enabled anonymous API access with global API key (Authorization header only)
- Updated database schema to support anonymous conversations
- Maintained backward compatibility for authenticated users

#### Automatic Asset Type Detection
- **Deprecated manual `type` parameter** - asset types are now automatically derived from yfinance data
- Supports detection of: ETF, Stock, Mutual Fund, Crypto, Index, Currency, and more
- Fallback logic ensures all assets have a valid type classification
- More accurate asset classification using real-time market data
- Eliminates manual entry errors and keeps asset types up-to-date

#### Monthly Recurring Investment Recommendations
- Added `monthly_cash` parameter to the recommendations endpoint for regular monthly contributions
- New `recurrent_investements` response field containing AI-generated monthly allocation recommendations
- Separate recurring investment logic that considers monthly cash flow for building positions over time
- Monthly recommendations are BUY-only actions that align with investment goals and portfolio strategy
- AI can recommend leaving some monthly cash uninvested or allocated to cash/treasuries when appropriate

### Account-Based Portfolio Recommendations
- Added support for account-specific investment recommendations (Trading, IRA, 401k, etc.)
- Portfolio assets can now include an optional `account` field to specify which account they belong to
- Recommendations are grouped by account in the response under a new `recommendations_by_account` key
- Assets without an explicit account are assigned to a "Default" account
- The AI considers account types when generating tailored investment advice

### Enhanced Conversation Support
- Added dedicated `/api/chat/` endpoint for follow-up conversations
- Persistent conversation threads across analysis, recommendations, and chat endpoints
- Improved context retention for more coherent multi-turn interactions
- Support for conversational questions via the `chat` parameter in all endpoints

### Terminology Improvements
- Changed response field from `quantity` to `amount` to clearly indicate dollar values rather than share quantities
- Changed response field from `reason` to `comments` for more intuitive terminology
- Added `[NEW ASSET]` prefix to comments for new investment recommendations for clearer differentiation

### Response Format Enhancements
- Converted the `amount` field from string to numeric (float) type
- Improved parsing logic to properly separate amount values from comments
- Maintained backward compatibility with legacy field names during transition
- Enhanced feedback section with more detailed strategic explanations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [OpenAI](https://openai.com/) for providing the AI models
- [Yahoo Finance API](https://pypi.org/project/yfinance/) for financial data
- [Django](https://www.djangoproject.com/) for the web framework
