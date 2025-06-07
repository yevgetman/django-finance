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
            "portfolio data provided. Pay special attention to how assets are distributed across "
            "different account types (e.g., Trading, IRA, 401k) and consider the appropriate "
            "investment strategies for each account type."
        ),
        user_template="""
As a professional financial advisor, analyze the following portfolio and provide detailed insights:

{portfolio_summary}

Please provide:
1. Overall portfolio assessment
2. Risk analysis
3. Diversification evaluation
4. Performance insights
5. Account-specific analysis (if multiple accounts are present)
6. Key strengths and weaknesses

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
            "Your task is to provide specific buy, sell, hold, or move recommendations for each asset in "
            "the portfolio, plus suggestions for new investments to improve portfolio balance. "
            "Consider the user's available cash, MONTHLY CASH FLOW, investment goals, and account types when making recommendations. "
            "Pay attention to how assets are distributed across different accounts (e.g., Trading, IRA, 401k) "
            "and ensure your recommendations are appropriate for each account type. "
            "Always provide specific dollar amounts for transactions, not vague quantities. "
            "Group your recommendations by account type, treating assets without an account designation "
            "as belonging to a 'Default' account. "
            "In addition, devise a recurring monthly investment plan that makes strategic use of the user's available monthly_cash."
        ),
        user_template="""
Based on the portfolio analysis below, provide specific actionable recommendations for each asset in this portfolio.

INVESTMENT GOALS:
{investment_goals}

MONTHLY CASH AVAILABLE FOR INVESTMENT:
{monthly_cash}

CONVERSATION CONTEXT:
{chat}

PORTFOLIO ANALYSIS:
{analysis}

PORTFOLIO DETAILS:
{portfolio_summary}

RESPONSE FORMAT:
You MUST format your response as a structured list of recommendations grouped by account, with each recommendation strictly following this format:

## ACCOUNT: [ACCOUNT NAME]

FOR EXISTING ASSETS:
- TICKER: AAPL, ACTION: BUY, AMOUNT: 2500, ACCOUNT: Trading, COMMENTS: Strong growth potential and undervalued at current price.

FOR NEW INVESTMENTS:
- TICKER: VTI, ACTION: BUY, AMOUNT: 5000, ACCOUNT: IRA, COMMENTS: [NEW ASSET] Adds broad market exposure and diversification.

FOR SELLING ASSETS:
- TICKER: TSLA, ACTION: SELL, AMOUNT: 1500, ACCOUNT: Default, COMMENTS: Overvalued and high volatility risk.

FOR MOVING ASSETS:
- TICKER: IVV, ACTION: MOVE, AMOUNT: 300, ACCOUNT: IRA, COMMENTS: Move $300 of IVV to IRA.

IMPORTANT INSTRUCTIONS:
1. Each recommendation MUST start with a dash and appear on its own line
2. You MUST include the EXACT ticker symbol for each asset (do not leave TICKER blank or use placeholders)
3. For existing assets, use the ticker symbols provided in the portfolio details
4. For new investments, suggest SPECIFIC ticker symbols (not generic asset classes)
5. Use ONLY these ACTION values: BUY, HOLD, SELL, or MOVE
6. AMOUNT must be a specific dollar amount (e.g., 1000, 2500, 5000) representing the dollar value to buy/sell/move
7. For SELL actions, the amount should not exceed the current value of the holding
8. For MOVE actions, ensure the amount does not exceed the current value of the holding and specify the target ACCOUNT field
9. For BUY actions, ensure the total recommended purchases do not exceed available cash
10. For HOLD actions, use AMOUNT: 0 (no transaction needed)
11. Include brief COMMENTS limited to one sentence that aligns with the user's investment goals when applicable
12. When recommending NEW investments, ensure they align with the user's stated investment goals and always prefix the COMMENTS with "[NEW ASSET]" to clearly indicate it's a new addition
13. Take into account the user's available cash when suggesting purchases, and stay within those limits
14. Be strategic about dollar amounts - consider portfolio balance, risk management, and diversification
15. Group recommendations by account type with a header "## ACCOUNT: [ACCOUNT NAME]"
16. For assets without an account designation, group them under "## ACCOUNT: Default"
17. Include the ACCOUNT field in each recommendation line to clearly indicate which account it belongs to
18. When assets are in different account types (e.g., Trading, IRA, 401k), consider the appropriate investment strategies for each account type
19. For retirement accounts like IRAs and 401ks, focus on long-term growth and tax advantages
20. For taxable accounts, consider tax efficiency and shorter-term liquidity needs
21. New investment recommendations should be placed under the most appropriate account type

NEW REQUIREMENT – MONTHLY ALLOCATION PLAN:
After the account-based recommendations above, provide a separate section titled "## RECURRING INVESTMENTS (Monthly Allocation)". In that section:
* ONLY list BUY recommendations for how to allocate the {monthly_cash} amount EACH MONTH.
* The combined AMOUNT values in this section MUST NOT EXCEED {monthly_cash}.
* It is acceptable to leave a portion unallocated; in that case, include a line with TICKER: CASH to reflect the amount held in cash, or a treasury ETF (e.g., BIL, SHV) if recommending treasury bills.
* Follow the exact same dash-delimited structured format as other recommendations but omit the ACCOUNT field (assume "Default") unless you specifically want it in another account.

Example recurring investments section (illustrative):

## RECURRING INVESTMENTS (Monthly Allocation)
- TICKER: VOO, ACTION: BUY, AMOUNT: 400, COMMENTS: Low-cost S&P 500 exposure.
- TICKER: ICLN, ACTION: BUY, AMOUNT: 150, COMMENTS: Diversify into clean energy.
- TICKER: CASH, ACTION: BUY, AMOUNT: 250, COMMENTS: Keep cash reserve for future opportunities.

You MUST include this recurring investments section.

AFTER all recommendations and recurring investments, provide a section titled "FEEDBACK:" that contains your overall assessment, rationale, and strategic thinking behind your recommendations. This should include:
1. A summary of the current portfolio's strengths and weaknesses
2. The high-level strategy behind your recommendations
3. How your recommendations align with the user's investment goals
4. Any additional context or considerations the user should be aware of

Limit this feedback to a few paragraphs or less and make it conversational and actionable.
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
        account = asset.get('account', '')
        account_info = f" | Account: {account}" if account else ""
        portfolio_summary += f"""
- TICKER: {ticker} | Type: {asset.get('type', 'Unknown')} | Value: ${asset.get('value', 0):,.2f}{account_info}
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
                                      investment_goals: str = '', chat: str = '',
                                      monthly_cash: float = 0) -> Dict[str, Any]:
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
        chat: User's conversational text input for additional context
        monthly_cash: Monthly cash available for investment
    
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
            investment_goals=investment_goals,
            chat=chat,
            monthly_cash=monthly_cash
        ),
        'max_tokens': prompt_template.max_tokens,
        'temperature': prompt_template.temperature
    }
