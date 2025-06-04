import pytest

from portfolio.prompts import (
    get_portfolio_analysis_prompt,
    get_portfolio_recommendations_prompt,
)


def test_analysis_prompt_includes_goals(sample_portfolio_data, investment_goals):
    prompt_conf = get_portfolio_analysis_prompt(
        sample_portfolio_data,
        total_value=2900,
        asset_count=2,
        asset_types={"stock"},
        cash=0,
        investment_goals=investment_goals,
    )
    messages = prompt_conf["messages"]
    assert any(investment_goals in msg["content"] for msg in messages)


def test_recommendations_prompt_format(sample_portfolio_data, investment_goals):
    prompt_conf = get_portfolio_recommendations_prompt(
        sample_portfolio_data,
        total_value=2900,
        asset_count=2,
        asset_types={"stock"},
        analysis="Sample analysis",
        cash=1000,
        investment_goals=investment_goals,
        chat="",
    )
    messages = prompt_conf["messages"]
    # Should contain the RESPONSE FORMAT template marker
    assert any("RESPONSE FORMAT" in msg["content"] for msg in messages)
