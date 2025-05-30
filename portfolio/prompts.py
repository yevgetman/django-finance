"""
Prompt management module for AI-powered financial analysis.

This module provides a centralized way to manage and inject prompts
for various AI analysis functions with dynamic data interpolation.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Template for AI prompts with dynamic data injection capabilities."""
    system_message: str
    user_template: str
    max_tokens: int = 1000
    temperature: float = 0.7
    
    def format_user_message(self, **kwargs) -> str:
        """Format the user template with provided data."""
        return self.user_template.format(**kwargs)
    
    def get_messages(self, **kwargs) -> list:
        """Get formatted messages for OpenAI API."""
        return [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": self.format_user_message(**kwargs)}
        ]


class PromptManager:
    """Central manager for all AI prompts used in the application."""
    
    # Portfolio Analysis Prompt
    PORTFOLIO_ANALYSIS = PromptTemplate(
        system_message=(
            "You are a professional financial advisor with expertise in portfolio analysis "
            "and investment strategy. Provide detailed, actionable insights based on the "
            "portfolio data provided."
        ),
        user_template="""
As a professional financial advisor, analyze the following portfolio and provide detailed insights:

{portfolio_summary}

Please provide:
1. Overall portfolio assessment
2. Risk analysis
3. Diversification evaluation
4. Performance insights
5. Key strengths and weaknesses

Keep the analysis professional, concise, and actionable. Focus on portfolio balance, risk management, and growth potential.
        """.strip(),
        max_tokens=1000,
        temperature=0.7
    )
    
    # Risk Assessment Prompt (Example for future use)
    RISK_ASSESSMENT = PromptTemplate(
        system_message=(
            "You are a risk management specialist with expertise in financial risk analysis. "
            "Focus on identifying and quantifying various types of investment risks."
        ),
        user_template="""
Analyze the risk profile of the following portfolio:

{portfolio_summary}

Please provide:
1. Market risk assessment
2. Concentration risk analysis
3. Sector/geographic exposure risks
4. Liquidity risk evaluation
5. Risk mitigation recommendations

Provide specific risk scores and actionable risk management strategies.
        """.strip(),
        max_tokens=800,
        temperature=0.6
    )
    
    # Investment Recommendation Prompt (Example for future use)
    INVESTMENT_RECOMMENDATION = PromptTemplate(
        system_message=(
            "You are an investment strategist specializing in portfolio optimization "
            "and asset allocation recommendations."
        ),
        user_template="""
Based on the current portfolio composition and market conditions:

{portfolio_summary}

Market Context: {market_context}
Investment Goals: {investment_goals}
Risk Tolerance: {risk_tolerance}

Provide specific investment recommendations including:
1. Asset allocation adjustments
2. Specific securities to consider
3. Rebalancing strategies
4. Timeline for implementation
5. Expected outcomes

Focus on actionable, specific recommendations with clear rationale.
        """.strip(),
        max_tokens=1200,
        temperature=0.8
    )
    
    @classmethod
    def get_prompt(cls, prompt_name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        return getattr(cls, prompt_name, None)
    
    @classmethod
    def list_available_prompts(cls) -> list:
        """List all available prompt templates."""
        return [
            attr for attr in dir(cls) 
            if isinstance(getattr(cls, attr), PromptTemplate)
        ]


def format_portfolio_summary(portfolio_data: list, total_value: float, 
                           asset_count: int, asset_types: set) -> str:
    """
    Format portfolio data into a structured summary for AI analysis.
    
    Args:
        portfolio_data: List of portfolio assets
        total_value: Total portfolio value
        asset_count: Number of assets
        asset_types: Set of asset types
    
    Returns:
        Formatted portfolio summary string
    """
    portfolio_summary = f"""
Portfolio Summary:
- Total Value: ${total_value:,.2f}
- Number of Assets: {asset_count}
- Asset Types: {', '.join(asset_types) if asset_types else 'Not specified'}

Detailed Holdings:"""
    
    for asset in portfolio_data:
        portfolio_summary += f"""
- {asset.get('symbol', 'Unknown')}: {asset.get('type', 'Unknown')} - ${asset.get('value', 0):,.2f}
  Shares: {asset.get('shares', 'N/A')}, Current Price: ${asset.get('current_price', 'N/A')}"""
    
    return portfolio_summary


def get_portfolio_analysis_prompt(portfolio_data: list, total_value: float,
                                asset_count: int, asset_types: set) -> Dict[str, Any]:
    """
    Get formatted portfolio analysis prompt with data injection.
    
    Args:
        portfolio_data: List of portfolio assets
        total_value: Total portfolio value
        asset_count: Number of assets
        asset_types: Set of asset types
    
    Returns:
        Dictionary containing messages, max_tokens, and temperature for OpenAI API
    """
    prompt_template = PromptManager.get_prompt('PORTFOLIO_ANALYSIS')
    
    if not prompt_template:
        raise ValueError("Portfolio analysis prompt not found")
    
    portfolio_summary = format_portfolio_summary(
        portfolio_data, total_value, asset_count, asset_types
    )
    
    return {
        'messages': prompt_template.get_messages(portfolio_summary=portfolio_summary),
        'max_tokens': prompt_template.max_tokens,
        'temperature': prompt_template.temperature
    }
