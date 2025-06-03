from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import yfinance as yf
import concurrent.futures
import os
import time
from openai import OpenAI
from .prompts import get_portfolio_analysis_prompt, get_portfolio_recommendations_prompt
from .ai_debug import create_debug_collector, inject_debug_data
import pandas as pd
import re

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

def update_portfolio_with_live_prices(portfolio_data):
    """
    Update portfolio data with live stock prices from yfinance.
    
    Args:
        portfolio_data: List of portfolio assets
        
    Returns:
        Updated portfolio data with current prices and recalculated values
    """
    # Create a copy of the portfolio data to avoid modifying the original
    updated_portfolio = []
    
    for asset in portfolio_data:
        # Create a copy of the asset to avoid modifying the original
        updated_asset = asset.copy()
        
        # Get the ticker symbol
        ticker_symbol = asset.get('symbol')
        if not ticker_symbol:
            # Skip assets without a symbol
            updated_portfolio.append(updated_asset)
            continue
            
        try:
            # Fetch live price data from yfinance
            ticker_obj = yf.Ticker(ticker_symbol)
            
            # Get the latest price information
            live_price = None
            
            # First try to get the regular market price
            try:
                live_price = ticker_obj.info.get('regularMarketPrice')
            except Exception as e:
                pass
                
            # If that fails, try to get the current price from history
            if not live_price:
                try:
                    history = ticker_obj.history(period="1d")
                    if not history.empty:
                        live_price = history.iloc[-1]['Close']
                except Exception as e:
                    pass
            
            # Update the asset with the live price
            if live_price:
                updated_asset['current_price'] = float(live_price)
                
                # If shares are provided, update the value based on current price
                if 'shares' in updated_asset and updated_asset.get('shares'):
                    try:
                        shares = float(updated_asset.get('shares', 0))
                        updated_asset['value'] = shares * float(live_price)
                    except (ValueError, TypeError):
                        # Keep original value if shares can't be converted to float
                        pass
                        
                print(f"Updated {ticker_symbol} with live price: ${live_price}")
        except Exception as e:
            # If there's an error fetching the price, log it and keep the existing data
            print(f"Error fetching data for {ticker_symbol}: {str(e)}")
            
        updated_portfolio.append(updated_asset)
    
    return updated_portfolio


@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_portfolio(request):
    """Analyze a portfolio and provide recommendations"""
    # Initialize AI debug collector
    debug_collector = create_debug_collector()
    
    # Get portfolio data from the request
    portfolio_data = request.data.get('portfolio', [])
    
    if not portfolio_data:
        return Response({'error': 'Portfolio data is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Update portfolio with live stock prices from yfinance
    portfolio_data = update_portfolio_with_live_prices(portfolio_data)
    
    # Get available cash and investment goals
    cash = request.data.get('cash', 0)
    investment_goals = request.data.get('investment_goals', '')
    
    # Recalculate metrics with updated prices
    total_value = sum(asset.get('value', 0) for asset in portfolio_data)
    asset_count = len(portfolio_data)
    asset_types = set(asset.get('type') for asset in portfolio_data if asset.get('type'))
    
    # Total portfolio value including cash
    total_portfolio_value = total_value + cash
    
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
            asset_types,
            cash=cash,
            investment_goals=investment_goals
        )
        
        # Record the LLM call for debugging
        analysis_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        call_id = debug_collector.record_llm_call(
            model=analysis_model,
            prompt_type="portfolio_analysis",
            messages=analysis_prompt_config['messages'],
            max_tokens=analysis_prompt_config['max_tokens'],
            temperature=analysis_prompt_config['temperature']
        )
        
        # Make the API call with timing
        start_time = time.time()
        analysis_response = client.chat.completions.create(
            model=analysis_model,
            messages=analysis_prompt_config['messages'],
            max_tokens=analysis_prompt_config['max_tokens'],
            temperature=analysis_prompt_config['temperature']
        )
        duration_ms = int((time.time() - start_time) * 1000)
        
        ai_analysis = analysis_response.choices[0].message.content
        
        # Update debug collector with response data
        debug_collector.update_llm_call_response(
            call_id=call_id,
            response_content=ai_analysis,
            response_tokens=analysis_response.usage.total_tokens if hasattr(analysis_response, 'usage') else None,
            duration_ms=duration_ms
        )
        
    except Exception as e:
        ai_analysis = f"AI analysis temporarily unavailable: {str(e)}"
        # Update debug collector with error
        if 'call_id' in locals():
            debug_collector.update_llm_call_response(
                call_id=call_id,
                response_content="",
                error=str(e)
            )
    
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
                analysis=ai_analysis,
                cash=cash,
                investment_goals=investment_goals
            )
            
            # Record the LLM call for debugging
            recommendations_model = os.getenv('OPENAI_RECOMMENDATIONS_MODEL', 'gpt-4o')
            rec_call_id = debug_collector.record_llm_call(
                model=recommendations_model,
                prompt_type="portfolio_recommendations",
                messages=recommendations_prompt_config['messages'],
                max_tokens=recommendations_prompt_config['max_tokens'],
                temperature=recommendations_prompt_config['temperature']
            )
            
            # Make the API call with timing
            start_time = time.time()
            recommendations_response = client.chat.completions.create(
                model=recommendations_model,
                messages=recommendations_prompt_config['messages'],
                max_tokens=recommendations_prompt_config['max_tokens'],
                temperature=recommendations_prompt_config['temperature']
            )
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Process recommendations response
            recommendations_text = recommendations_response.choices[0].message.content
            
            # Update debug collector with response data
            debug_collector.update_llm_call_response(
                call_id=rec_call_id,
                response_content=recommendations_text,
                response_tokens=recommendations_response.usage.total_tokens if hasattr(recommendations_response, 'usage') else None,
                duration_ms=duration_ms
            )
            
            # Function to extract feedback section from recommendations text
            def extract_feedback(text):
                # Simple extraction method: look for 'FEEDBACK:' header and capture everything after it
                feedback_match = re.search(r'(?i)(?:###\s*)?\bFEEDBACK:\b\s*(.*)', text, re.DOTALL)
                if feedback_match:
                    # Get everything after the FEEDBACK: marker
                    raw_feedback = feedback_match.group(1).strip()
                    print(f"Found feedback section with {len(raw_feedback)} characters")
                    return raw_feedback
                    
                # Fallback: look for content after the last recommendation
                lines = text.split('\n')
                last_recommendation_index = -1
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('-') and ('ACTION:' in line or 'TICKER:' in line):
                        last_recommendation_index = i
                
                if last_recommendation_index >= 0 and last_recommendation_index < len(lines) - 2:  # At least two lines after
                    # Skip one line after the last recommendation in case it's empty
                    potential_content = "\n".join(lines[last_recommendation_index + 2:]).strip()
                    if potential_content:
                        print(f"Found content after recommendations: {len(potential_content)} characters")
                        return potential_content
                        
                print("No feedback section found")
                return ""
            
            # Initialize variables for recommendations and feedback
            structured_recommendations = []
            feedback_text = "" # Default empty feedback in case extraction fails
            
            if recommendations_text:
                # Extract feedback section
                feedback_text = extract_feedback(recommendations_text)
                
                # Process recommendations (lines starting with dash)
                for line in recommendations_text.split('\n'):
                    # Skip empty lines and only process recommendation lines (starting with dash)
                    if line.strip() and line.strip().startswith('-'):
                        # Remove the dash and trim
                        line = line[1:].strip()
                        
                        try:
                            # Improved parsing for structured format
                            # Look for explicit labels and handle different formatting possibilities
                        
                            # Parse ticker - try multiple formats and ensure it's not empty
                            ticker = ''
                            if 'TICKER:' in line:
                                ticker_part = line.split('TICKER:')[1].split(',')[0].strip()
                                ticker = ticker_part.replace('[', '').replace(']', '')
                            elif 'Symbol:' in line:
                                ticker_part = line.split('Symbol:')[1].split(',')[0].strip()
                                ticker = ticker_part.replace('[', '').replace(']', '')
                            
                            # If we still don't have a ticker but have a symbol in the portfolio data, try to match
                            if not ticker and 'ACTION:' in line and 'QUANTITY:' in line:
                                for asset in portfolio_data:
                                    asset_symbol = asset.get('symbol', '')
                                    # If this recommendation seems to match an existing asset
                                    if asset_symbol and asset_symbol in line:
                                        ticker = asset_symbol
                                        break
                            
                            # Parse action
                            action_part = ''
                            if 'ACTION:' in line:
                                action_part = line.split('ACTION:')[1].split(',')[0].strip()
                            
                            # Parse quantity - now expecting numeric dollar amounts
                            quantity_part = ''
                            if 'QUANTITY:' in line:
                                quantity_raw = line.split('QUANTITY:')[1].split(',')[0].strip()
                                # Clean up the quantity value and validate it's numeric
                                quantity_cleaned = quantity_raw.replace('$', '').replace(',', '')
                                try:
                                    # Validate that it's a number
                                    float(quantity_cleaned)
                                    quantity_part = quantity_cleaned
                                except ValueError:
                                    # If not numeric, keep the original value for debugging
                                    quantity_part = quantity_raw
                            
                            # Parse reason
                            reason_part = ''
                            if 'REASON:' in line:
                                reason_part = line.split('REASON:')[1].strip()
                            
                            # Create structured recommendation with improved data
                            recommendation = {
                                'ticker': ticker,
                                'action': action_part,
                                'quantity': quantity_part,
                                'reason': reason_part
                            }
                            
                            structured_recommendations.append(recommendation)
                        except Exception as e:
                            # If parsing fails, include the raw line
                            structured_recommendations.append({
                                'ticker': 'PARSE_ERROR',
                                'action': 'UNKNOWN',
                                'quantity': 'UNKNOWN',
                                'reason': f'Error parsing: {line}'
                            })
            
            # If parsing didn't work well, include the raw text
            if not structured_recommendations:
                structured_recommendations = [{
                    'ticker': 'RAW_RESPONSE',
                    'action': 'UNKNOWN',
                    'quantity': 'UNKNOWN',
                    'reason': recommendations_text
                }]
                
            ai_recommendations = structured_recommendations
    except Exception as e:
        ai_recommendations = [{
            'ticker': 'ERROR',
            'action': 'UNAVAILABLE',
            'quantity': 'UNKNOWN',
            'reason': f"Recommendations temporarily unavailable: {str(e)}"
        }]
        feedback_text = "Unable to generate feedback due to an error."
        # Update debug collector with error
        if 'rec_call_id' in locals():
            debug_collector.update_llm_call_response(
                call_id=rec_call_id,
                response_content="",
                error=str(e)
            )
    
    # Portfolio analysis response
    analysis = {
        'total_value': total_value,
        'total_portfolio_value': total_portfolio_value,
        'cash': cash,
        'asset_count': asset_count,
        'asset_types': list(asset_types),
        'investment_goals': investment_goals,
        'analysis': ai_analysis,
        'recommendations': ai_recommendations,
        'feedback': feedback_text
    }
    
    # Inject debug data if enabled
    enhanced_response = inject_debug_data(analysis, debug_collector)
    
    return Response(enhanced_response)
