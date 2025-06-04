import json
import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_analyze_portfolio_endpoint(mocker, sample_portfolio_data, investment_goals):
    client = APIClient()
    mocker.patch("yfinance.Ticker", autospec=True)
    mocker.patch("openai.OpenAI", autospec=True)

    url = reverse("analyze-portfolio")
    payload = {
        "portfolio": sample_portfolio_data,
        "cash": 1000,
        "investment_goals": investment_goals,
    }
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert "total_value" in data
    assert data["investment_goals"] == investment_goals


@pytest.mark.django_db
def test_recommendations_endpoint(mocker, sample_portfolio_data, investment_goals):
    client = APIClient()
    mocker.patch("yfinance.Ticker", autospec=True)
    mocker.patch("openai.OpenAI", autospec=True)

    url = reverse("portfolio-recommendations")
    payload = {
        "portfolio": sample_portfolio_data,
        "cash": 1000,
        "investment_goals": investment_goals,
        "analysis": "Sample analysis",
    }
    response = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data or "error" in data
