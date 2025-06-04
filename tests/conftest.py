import pytest
import json

@pytest.fixture
def sample_portfolio_data():
    return [
        {
            "symbol": "AAPL",
            "shares": 10,
            "value": 1500,
            "type": "stock"
        },
        {
            "symbol": "GOOGL",
            "shares": 5,
            "value": 1400,
            "type": "stock"
        }
    ]

@pytest.fixture
def investment_goals():
    return "Long-term growth and diversification"

@pytest.fixture
def cash_available():
    return 5000
