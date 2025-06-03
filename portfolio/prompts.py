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
    
    # Portfolio Recommendations Prompt
    PORTFOLIO_RECOMMENDATIONS = PromptTemplate(
        system_message=(
            "You are a professional financial advisor specializing in actionable portfolio recommendations. "
            "Your task is to provide specific buy, sell, or hold recommendations for each asset in "
            "the portfolio, plus suggestions for new investments to improve portfolio balance. "
            "Consider the user's available cash and investment goals when making recommendations. "
            "Always provide specific dollar amounts for transactions, not vague quantities."
        ),
        user_template="""
Based on the portfolio analysis below, provide specific actionable recommendations for each asset in this portfolio.

INVESTMENT GOALS:
{investment_goals}

PORTFOLIO ANALYSIS:
{analysis}

PORTFOLIO DETAILS:
{portfolio_summary}

RESPONSE FORMAT:
You MUST format your response as a structured list of recommendations, with each recommendation strictly following this format:

FOR EXISTING ASSETS:
- TICKER: AAPL, ACTION: BUY, QUANTITY: 2500, REASON: Strong growth potential and undervalued at current price.

FOR NEW INVESTMENTS:
- TICKER: VTI, ACTION: BUY, QUANTITY: 5000, REASON: Adds broad market exposure and diversification.

FOR SELLING ASSETS:
- TICKER: TSLA, ACTION: SELL, QUANTITY: 1500, REASON: Overvalued and high volatility risk.

IMPORTANT INSTRUCTIONS:
1. Each recommendation MUST start with a dash and appear on its own line
2. You MUST include the EXACT ticker symbol for each asset (do not leave TICKER blank or use placeholders)
3. For existing assets, use the ticker symbols provided in the portfolio details
4. For new investments, suggest SPECIFIC ticker symbols (not generic asset classes)
5. Use ONLY these ACTION values: BUY, HOLD, or SELL
6. QUANTITY must be a specific dollar amount (e.g., 1000, 2500, 5000) representing the dollar value to buy/sell
7. For SELL actions, the quantity should not exceed the current value of the holding
8. For BUY actions, ensure the total recommended purchases do not exceed available cash
9. For HOLD actions, use QUANTITY: 0 (no transaction needed)
10. Include a brief REASON limited to one sentence that aligns with the user's investment goals when applicable
11. When recommending NEW investments, ensure they align with the user's stated investment goals
12. Take into account the user's available cash when suggesting purchases, and stay within those limits
13. Be strategic about dollar amounts - consider portfolio balance, risk management, and diversification

You MUST provide a recommendation for EACH existing asset in the portfolio, followed by 2-3 recommendations for NEW investments that would improve portfolio balance and achieve the stated investment goals.
        """.strip(),
        max_tokens=1200,
        temperature=0.7
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
                           asset_count: int, asset_types: set,
                           cash: float = 0, investment_goals: str = '') -> str:
    """
    Format portfolio data into a structured summary for AI analysis.
    
    Args:
        portfolio_data: List of portfolio assets
        total_value: Total portfolio value
        asset_count: Number of assets
        asset_types: Set of asset types
        cash: Available cash for investment
        investment_goals: User's investment goals and preferences
    
    Returns:
        Formatted portfolio summary string
    """
    # Calculate total portfolio value including cash
    total_portfolio_value = total_value + cash
    
    portfolio_summary = f"""
Portfolio Summary:
- Total Portfolio Value: ${total_portfolio_value:,.2f}
- Investment Assets Value: ${total_value:,.2f}
- Available Cash: ${cash:,.2f}
- Number of Assets: {asset_count}
- Asset Types: {', '.join(asset_types) if asset_types else 'Not specified'}"""

    # Add investment goals if provided
    if investment_goals:
        portfolio_summary += f"""

Investment Goals:
{investment_goals}"""
        
    portfolio_summary += """

Detailed Holdings:"""
    
    # Make ticker symbols prominent in the summary
    for asset in portfolio_data:
        # Ensure symbol is prominently displayed at the start
        ticker = asset.get('symbol', 'Unknown')
        portfolio_summary += f"""
- TICKER: {ticker} | Type: {asset.get('type', 'Unknown')} | Value: ${asset.get('value', 0):,.2f}
  Shares: {asset.get('shares', 'N/A')} | Current Price: ${asset.get('current_price', 'N/A')}"""
    
    return portfolio_summary


def get_portfolio_analysis_prompt(portfolio_data: list, total_value: float,
                                asset_count: int, asset_types: set,
                                cash: float = 0, investment_goals: str = '') -> Dict[str, Any]:
    """
    Get formatted portfolio analysis prompt with data injection.
    
    Args:
        portfolio_data: List of portfolio assets
        total_value: Total portfolio value
        asset_count: Number of assets
        asset_types: Set of asset types
        cash: Available cash for investment
        investment_goals: User's investment goals and preferences
    
    Returns:
        Dictionary containing messages, max_tokens, and temperature for OpenAI API
    """
    prompt_template = PromptManager.get_prompt('PORTFOLIO_ANALYSIS')
    
    if not prompt_template:
        raise ValueError("Portfolio analysis prompt not found")
    
    portfolio_summary = format_portfolio_summary(
        portfolio_data, total_value, asset_count, asset_types,
        cash=cash, investment_goals=investment_goals
    )
    
    return {
        'messages': prompt_template.get_messages(portfolio_summary=portfolio_summary),
        'max_tokens': prompt_template.max_tokens,
        'temperature': prompt_template.temperature
    }


def get_portfolio_recommendations_prompt(portfolio_data: list, total_value: float,
                                      asset_count: int, asset_types: set, 
                                      analysis: str, cash: float = 0,
                                      investment_goals: str = '') -> Dict[str, Any]:
    """
    Get formatted portfolio recommendations prompt with data injection.
    
    Args:
        portfolio_data: List of portfolio assets
        total_value: Total portfolio value
        asset_count: Number of assets
        asset_types: Set of asset types
        analysis: Previous AI analysis of the portfolio
        cash: Available cash for investment
        investment_goals: User's investment goals and preferences
    
    Returns:
        Dictionary containing messages, max_tokens, and temperature for OpenAI API
    """
    prompt_template = PromptManager.get_prompt('PORTFOLIO_RECOMMENDATIONS')
    
    if not prompt_template:
        raise ValueError("Portfolio recommendations prompt not found")
    
    portfolio_summary = format_portfolio_summary(
        portfolio_data, total_value, asset_count, asset_types,
        cash=cash, investment_goals=investment_goals
    )
    
    return {
        'messages': prompt_template.get_messages(
            portfolio_summary=portfolio_summary,
            analysis=analysis,
            investment_goals=investment_goals
        ),
        'max_tokens': prompt_template.max_tokens,
        'temperature': prompt_template.temperature
    }
