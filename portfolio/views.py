from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import yfinance as yf
import concurrent.futures
import os
from openai import OpenAI
from .prompts import get_portfolio_analysis_prompt, get_portfolio_recommendations_prompt

def get_ticker_data(ticker):
    """Helper function to get data for a single ticker"""
    try:
        ticker_data = yf.Ticker(ticker)
        info = ticker_data.info
        
        # Determine if it's an ETF, mutual fund, or stock
        quote_type = info.get('quoteType', '').lower()
        
        # Get market cap category
        market_cap = info.get('marketCap', 0)
        if market_cap > 200000000000:  # $200B
            cap_category = 'Mega Cap'
        elif market_cap > 10000000000:  # $10B
            cap_category = 'Large Cap'
        elif market_cap > 2000000000:  # $2B
            cap_category = 'Mid Cap'
        elif market_cap > 300000000:  # $300M
            cap_category = 'Small Cap'
        elif market_cap > 50000000:  # $50M
            cap_category = 'Micro Cap'
        else:
            cap_category = 'Nano Cap'
        
        # Different properties based on security type
        result = {
            'ticker': ticker,
            'name': info.get('shortName', 'Unknown'),
            'market_cap': market_cap,
            'market_cap_category': cap_category,
            'currency': info.get('currency', 'USD'),
            'country': info.get('country', 'Unknown'),
            'quote_type': quote_type
        }
        
        # For ETFs and Mutual Funds
        if quote_type in ('etf', 'mutualfund'):
            result.update({
                'asset_class': 'ETF/Fund',
                'sector': info.get('category', 'Unknown ETF'),
                'fund_family': info.get('fundFamily', 'Unknown'),
                'fund_objective': info.get('fundObjective', ''),
                'yield': info.get('yield', 0),
                'total_assets': info.get('totalAssets', 0),
                'fund_style': info.get('morningStarRiskRating', 'Unknown')
            })
            
            # Try to determine if it's a sector ETF from the name or category
            if 'sector' in info.get('category', '').lower() or any(sector in info.get('longName', '').lower() for sector in 
                   ['technology', 'healthcare', 'financial', 'energy', 'utilities', 
                    'industrial', 'materials', 'consumer', 'real estate', 'telecom']):
                result['is_sector_etf'] = True
            else:
                result['is_sector_etf'] = False
                
        # For regular stocks
        else:
            result.update({
                'asset_class': 'Stock',
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'website': info.get('website', '')
            })
            
        return result
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e),
            'name': 'Unknown',
            'asset_class': 'Unknown',
            'sector': 'Unknown',
            'market_cap': 0,
            'market_cap_category': 'Unknown',
            'currency': 'USD',
            'country': 'Unknown',
            'quote_type': 'unknown'
        }

@api_view(['POST'])
@permission_classes([AllowAny])
def get_ticker_info(request):
    """Get sector and market cap data for a list of tickers"""
    tickers = request.data.get('tickers', [])
    
    if not tickers:
        return Response({'error': 'Please provide a list of tickers'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Using ThreadPoolExecutor to fetch data for multiple tickers in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_ticker_data, ticker): ticker for ticker in tickers}
        for future in concurrent.futures.as_completed(futures):
            ticker = futures[future]
            try:
                data = future.result()
                results.append(data)
            except Exception as e:
                results.append({
                    'ticker': ticker,
                    'error': str(e),
                    'name': 'Unknown',
                    'asset_class': 'Unknown',
                    'sector': 'Unknown',
                    'market_cap': 0,
                    'market_cap_category': 'Unknown',
                    'quote_type': 'unknown'
                })
    
    return Response({
        'count': len(results),
        'results': results
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_portfolio(request):
    """Analyze a portfolio and provide recommendations"""
    # Get portfolio data from the request
    portfolio_data = request.data.get('portfolio', [])
    
    if not portfolio_data:
        return Response({'error': 'Portfolio data is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate some basic metrics
    total_value = sum(asset.get('value', 0) for asset in portfolio_data)
    asset_count = len(portfolio_data)
    asset_types = set(asset.get('type') for asset in portfolio_data if asset.get('type'))
    
    # Create OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    ai_analysis = "Analysis unavailable"
    ai_recommendations = []
    
    # Step 1: Generate AI-powered analysis using first model
    try:
        # Get formatted prompt for portfolio analysis
        analysis_prompt_config = get_portfolio_analysis_prompt(
            portfolio_data, 
            total_value, 
            asset_count, 
            asset_types
        )
        
        analysis_response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o'),
            messages=analysis_prompt_config['messages'],
            max_tokens=analysis_prompt_config['max_tokens'],
            temperature=analysis_prompt_config['temperature']
        )
        
        ai_analysis = analysis_response.choices[0].message.content
        
    except Exception as e:
        ai_analysis = f"AI analysis temporarily unavailable: {str(e)}"
    
    # Step 2: Generate recommendations using second model
    try:
        # Only proceed if analysis was successful
        if not ai_analysis.startswith("AI analysis temporarily unavailable"):
            # Get formatted prompt for portfolio recommendations
            recommendations_prompt_config = get_portfolio_recommendations_prompt(
                portfolio_data, 
                total_value, 
                asset_count, 
                asset_types,
                analysis=ai_analysis
            )
            
            recommendations_response = client.chat.completions.create(
                model=os.getenv('OPENAI_RECOMMENDATIONS_MODEL', 'gpt-4o'),
                messages=recommendations_prompt_config['messages'],
                max_tokens=recommendations_prompt_config['max_tokens'],
                temperature=recommendations_prompt_config['temperature']
            )
            
            # Process recommendations response
            recommendations_text = recommendations_response.choices[0].message.content
            
            # Extract recommendations into a list (split by line breaks and filter out empty lines)
            ai_recommendations = [
                line.strip() for line in recommendations_text.split('\n') 
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('ALSO')
            ]
            
            # If splitting didn't work well, use the whole text
            if not ai_recommendations:
                ai_recommendations = [recommendations_text]
    except Exception as e:
        ai_recommendations = [f"Recommendations temporarily unavailable: {str(e)}"] 
    
    # Portfolio analysis response
    analysis = {
        'total_value': total_value,
        'asset_count': asset_count,
        'asset_types': list(asset_types),
        'analysis': ai_analysis,
        'recommendations': ai_recommendations
    }
    
    return Response(analysis)
