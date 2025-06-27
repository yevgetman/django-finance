from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import GlobalHardcodedAPIKeyPermission, IsAuthenticatedOrAnonymous
import yfinance as yf
import concurrent.futures
import os
import time
import uuid
from .ai_providers import AIRequestManager
from .prompts import get_portfolio_analysis_prompt, get_portfolio_recommendations_prompt
from .ai_debug import create_debug_collector, inject_debug_data
from .conversation_utils import get_or_create_conversation, format_message_for_thread, add_message_to_thread, get_latest_assistant_message, run_thread_with_assistant, get_thread_messages
import pandas as pd
import re
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from .models import Conversation

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
    Update portfolio data with live stock prices from yfinance and derive asset types.
    
    Args:
        portfolio_data: List of portfolio assets
        
    Returns:
        Updated portfolio data with current prices, recalculated values, and derived asset types
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
            
            # Get ticker info for asset type derivation
            info = ticker_obj.info
            
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
                
                # Derive missing value or shares using current price
                try:
                    price = float(live_price)
                    shares_present = updated_asset.get('shares') not in (None, "")
                    value_present = updated_asset.get('value') not in (None, "")

                    # If shares are provided but value is missing or zero, calculate value
                    if shares_present and not value_present:
                        shares = float(updated_asset.get('shares'))
                        updated_asset['value'] = shares * price
                    # If value is provided but shares are missing or zero, calculate shares
                    elif value_present and not shares_present:
                        value = float(updated_asset.get('value'))
                        if price != 0:
                            updated_asset['shares'] = value / price
                except (ValueError, TypeError):
                    # Skip calculation if conversion fails
                    pass
            
            # Derive asset type from yfinance data
            try:
                quote_type = info.get('quoteType', '').lower()
                
                # Map yfinance quote types to our asset types
                if quote_type == 'etf':
                    updated_asset['type'] = 'ETF'
                elif quote_type == 'mutualfund':
                    updated_asset['type'] = 'Mutual Fund'
                elif quote_type in ('equity', 'stock'):
                    updated_asset['type'] = 'Stock'
                elif quote_type == 'cryptocurrency':
                    updated_asset['type'] = 'Crypto'
                elif quote_type == 'index':
                    updated_asset['type'] = 'Index'
                elif quote_type == 'currency':
                    updated_asset['type'] = 'Currency'
                else:
                    # Fallback: try to determine from other info fields
                    if 'fund' in info.get('longName', '').lower() or 'etf' in info.get('longName', '').lower():
                        updated_asset['type'] = 'ETF'
                    else:
                        updated_asset['type'] = 'Stock'  # Default fallback
                        
                if os.getenv('DEBUG', 'False').lower() == 'true':
                    print(f"Updated {ticker_symbol} with live price: ${live_price}, type: {updated_asset['type']}")
            except Exception as e:
                # If type derivation fails, use existing type or default to 'Stock'
                if 'type' not in updated_asset:
                    updated_asset['type'] = 'Stock'
                if os.getenv('DEBUG', 'False').lower() == 'true':
                    print(f"Could not derive type for {ticker_symbol}, using: {updated_asset['type']}")
                        
        except Exception as e:
            # If there's an error fetching the price, log it and keep the existing data
            if os.getenv('DEBUG', 'False').lower() == 'true':
                print(f"Error fetching data for {ticker_symbol}: {str(e)}")
            # Ensure type exists even if fetching fails
            if 'type' not in updated_asset:
                updated_asset['type'] = 'Stock'  # Default fallback
            
        updated_portfolio.append(updated_asset)
    
    return updated_portfolio


@api_view(['POST'])
def analyze_portfolio(request):
    """
    Analyze a portfolio and provide AI-powered insights
    
    Expected request format:
    {
        "portfolio": [
            {
                "symbol": "AAPL",
                "shares": 10,
                "value": 1500,
                "account": "Trading"  # Optional: account type (e.g., Trading, IRA, 401k)
            },
            ...
        ],
        "cash": 5000,
        "investment_goals": "Growth with moderate risk",
        "conversation_id": "optional-uuid"
    }
    
    Note: The 'type' field is automatically derived from yfinance data and no longer needs to be specified.
    """
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
    # Ensure cash is numeric
    try:
        cash = float(cash) if cash else 0
    except (ValueError, TypeError):
        cash = 0
        
    investment_goals = request.data.get('investment_goals', '')
    chat = request.data.get('chat', '')
    conversation_id = request.data.get('conversation_id')
    
    # Recalculate metrics with updated prices
    total_value = sum(asset.get('value', 0) for asset in portfolio_data)
    asset_count = len(portfolio_data)
    asset_types = set(asset.get('type') for asset in portfolio_data if asset.get('type'))
    
    # Total portfolio value including cash
    total_portfolio_value = total_value + cash
    
    # Create AI request manager
    ai_manager = AIRequestManager()
    
    # Get or create a conversation thread
    try:
        # Handle anonymous users by passing None for user
        user = request.user if request.user.is_authenticated else None
        conversation, created = get_or_create_conversation(
            conversation_id=conversation_id,
            conversation_type='analysis',
            user=user
        )
        
        # Update the conversation with the latest portfolio data
        conversation.last_portfolio_data = {
            'portfolio': portfolio_data,
            'cash': cash,
            'investment_goals': investment_goals,
            'chat': chat
        }
        conversation.save(update_fields=['last_portfolio_data'])
    except Exception as e:
        # If conversation creation fails, create a fallback response object
        # This won't have conversation persistence but will allow the API to work
        if os.getenv('DEBUG', 'False').lower() == 'true':
            print(f"Error creating conversation: {str(e)}")
        conversation = type('obj', (object,), {'id': 'temp-' + str(uuid.uuid4())})
    
    # Step 1: Generate AI-powered analysis using conversation thread
    call_id = None  # Initialize call_id to ensure it's always defined
    try:
        # Format the message for the conversation thread
        message_content = format_message_for_thread(
            portfolio_data, 
            total_value, 
            cash, 
            investment_goals, 
            chat, 
            'analysis'
        )
        
        # Record the LLM call for debugging using full prompt messages
        analysis_prompt_config = get_portfolio_analysis_prompt(portfolio_data, total_value, asset_count, asset_types, cash, investment_goals)
        
        # Get the provider for this endpoint
        analysis_provider = AIRequestManager.get_analysis_provider()
        provider_name = analysis_provider.get_provider_name()
        model_name = analysis_provider.model if hasattr(analysis_provider, 'model') else 'unknown'
        
        call_id = debug_collector.record_llm_call(
            model=model_name,
            provider=provider_name,
            prompt_type="portfolio_analysis",
            messages=analysis_prompt_config['messages']
        )
        
        start_time = time.time()  # Initialize start_time for duration tracking
        
        # Check if we should use OpenAI assistants or direct API
        assistant_id = os.getenv('OPENAI_ASSISTANT_ID', '')
        
        if assistant_id and hasattr(conversation, 'thread_id'):
            # Use OpenAI assistants API (only works with OpenAI)
            add_message_to_thread(conversation.thread_id, message_content)
            run_thread_with_assistant(conversation.thread_id, assistant_id)
            assistant_message = get_latest_assistant_message(conversation.thread_id)
            ai_analysis = assistant_message.content[0].text.value if assistant_message else "Analysis unavailable"
        else:
            # Use direct AI provider API (works with both OpenAI and Anthropic)
            ai_response = AIRequestManager.make_request(
                endpoint_type='analysis',
                messages=analysis_prompt_config['messages'],
                max_tokens=analysis_prompt_config['max_tokens'],
                temperature=analysis_prompt_config['temperature']
            )
            
            if ai_response['success']:
                ai_analysis = ai_response['content']
            else:
                ai_analysis = f"Analysis unavailable: {ai_response['error']}"
        
        # Record the completion for debugging
        debug_collector.update_llm_call_response(
            call_id,
            response_content=str(ai_analysis),
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
    except Exception as error:
        # Record the error for debugging
        if call_id is not None:
            debug_collector.update_llm_call_response(
                call_id,
                response_content=None,
                error=str(error),
                duration_ms=int((time.time() - start_time) * 1000)
            )
        ai_analysis = f"Analysis error: {str(error)}"
    
    # Portfolio analysis response
    analysis = {
        'total_value': total_value,
        'total_portfolio_value': total_portfolio_value,
        'cash': cash,
        'asset_count': asset_count,
        'asset_types': list(asset_types),
        'investment_goals': investment_goals,
        'analysis': ai_analysis,
        'conversation_id': str(conversation.id)
    }
    
    # Inject debug data if enabled
    enhanced_response = inject_debug_data(analysis, debug_collector)
    
    return Response(enhanced_response)


@api_view(['POST'])
def get_portfolio_recommendations(request):
    """
    Get portfolio recommendations from AI model
    
    Expected request format:
    {
        "portfolio": [
            {
                "symbol": "AAPL",
                "shares": 10,
                "value": 1500,
                "account": "Trading"  # Optional: account type (e.g., Trading, IRA, 401k)
            },
            ...
        ],
        "cash": 5000,
        "investment_goals": "Growth with moderate risk",
        "monthly_cash": 500,  # New optional monthly contribution
        "conversation_id": "optional-uuid"
    }
    
    Note: The 'type' field is automatically derived from yfinance data and no longer needs to be specified.
    """
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
    # Ensure cash is numeric
    try:
        cash = float(cash) if cash else 0
    except (ValueError, TypeError):
        cash = 0
        
    monthly_cash = request.data.get('monthly_cash', 0)
    # Ensure monthly_cash is numeric
    try:
        monthly_cash = float(monthly_cash) if monthly_cash else 0
    except (ValueError, TypeError):
        monthly_cash = 0
        
    investment_goals = request.data.get('investment_goals', '')
    chat = request.data.get('chat', '')
    conversation_id = request.data.get('conversation_id')
    
    # Recalculate metrics with updated prices
    total_value = sum(asset.get('value', 0) for asset in portfolio_data)
    asset_count = len(portfolio_data)
    asset_types = set(asset.get('type') for asset in portfolio_data if asset.get('type'))
    
    # Total portfolio value including cash
    total_portfolio_value = total_value + cash
    
    # Create AI request manager
    ai_manager = AIRequestManager()
    ai_recommendations = []
    feedback_text = ""
    
    # Get or create a conversation thread
    try:
        # Handle anonymous users by passing None for user
        user = request.user if request.user.is_authenticated else None
        conversation, created = get_or_create_conversation(
            conversation_id=conversation_id,
            conversation_type='recommendations',
            user=user
        )
        
        # Update the conversation with the latest portfolio data
        conversation.last_portfolio_data = {
            'portfolio': portfolio_data,
            'cash': cash,
            'investment_goals': investment_goals,
            'chat': chat
        }
        conversation.save(update_fields=['last_portfolio_data'])
    except Exception as e:
        # If conversation creation fails, create a fallback response object
        # This won't have conversation persistence but will allow the API to work
        if os.getenv('DEBUG', 'False').lower() == 'true':
            print(f"Error creating conversation: {str(e)}")
        conversation = type('obj', (object,), {'id': 'temp-' + str(uuid.uuid4())})
    
    # Step 1: Generate AI-powered recommendations using conversation thread
    call_id = None  # Initialize call_id to ensure it's always defined
    try:
        # Format the message for the conversation thread
        message_content = format_message_for_thread(
            portfolio_data,
            total_value,
            cash,
            investment_goals,
            chat,
            'recommendations'
        )
        
        # Record the LLM call for debugging using full prompt messages
        recommendations_prompt_config = get_portfolio_recommendations_prompt(
            portfolio_data, 
            total_value, 
            asset_count, 
            asset_types, 
            cash, 
            investment_goals,
            monthly_cash
        )
        
        # Get the provider for this endpoint
        recommendations_provider = AIRequestManager.get_recommendations_provider()
        provider_name = recommendations_provider.get_provider_name()
        model_name = recommendations_provider.model if hasattr(recommendations_provider, 'model') else 'unknown'
        
        call_id = debug_collector.record_llm_call(
            model=model_name,
            provider=provider_name,
            prompt_type="portfolio_recommendations",
            messages=recommendations_prompt_config['messages']
        )
        
        start_time = time.time()  # Initialize start_time for duration tracking
        
        # Check if we should use OpenAI assistants or direct API
        assistant_id = os.getenv('OPENAI_RECOMMENDATIONS_ASSISTANT_ID', '')
        
        if assistant_id and hasattr(conversation, 'thread_id'):
            # Use OpenAI assistants API (only works with OpenAI)
            add_message_to_thread(conversation.thread_id, message_content)
            run_thread_with_assistant(conversation.thread_id, assistant_id)
            assistant_message = get_latest_assistant_message(conversation.thread_id)
            ai_recommendations_text = assistant_message.content[0].text.value if assistant_message else "Recommendations unavailable"
        else:
            # Use direct AI provider API (works with both OpenAI and Anthropic)
            ai_response = AIRequestManager.make_request(
                endpoint_type='recommendations',
                messages=recommendations_prompt_config['messages'],
                max_tokens=recommendations_prompt_config['max_tokens'],
                temperature=recommendations_prompt_config['temperature']
            )
            
            if ai_response['success']:
                ai_recommendations_text = ai_response['content']
            else:
                ai_recommendations_text = f"Recommendations unavailable: {ai_response['error']}"
        
        # Record the completion for debugging
        debug_collector.update_llm_call_response(
            call_id,
            response_content=str(ai_recommendations_text),
            duration_ms=int((time.time() - start_time) * 1000)
        )
        
    except Exception as error:
        # Record the error for debugging
        if call_id is not None:
            debug_collector.update_llm_call_response(
                call_id,
                response_content=None,
                error=str(error),
                duration_ms=int((time.time() - start_time) * 1000)
            )
        ai_recommendations_text = f"Recommendations error: {str(error)}"
    
    # Function to extract feedback section from recommendations text
    def extract_feedback(text):
        # Simple extraction method: look for 'FEEDBACK:' header and capture everything after it
        feedback_match = re.search(r'(?i)(?:###\s*)?\bFEEDBACK:\b\s*(.*)', text, re.DOTALL)
        if feedback_match:
            # Get everything after the FEEDBACK: marker
            raw_feedback = feedback_match.group(1).strip()
            feedback_text = raw_feedback
                
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
                feedback_text = potential_content
                    
        return feedback_text
    
    # Initialize variables for recommendations, recurring investments, and feedback
    structured_recommendations = []
    recurrent_investments = []
    feedback_text = ""  # Default empty feedback in case extraction fails
    
    try:
        if ai_recommendations_text:
            feedback_text = extract_feedback(ai_recommendations_text)
            
            # Process recommendations (lines starting with dash)
            in_recurring_section = False
            
            for raw_line in ai_recommendations_text.split('\n'):
                line = raw_line.rstrip()
                
                # Detect section headers
                if line.strip().lower().startswith('##'):
                    header_text = line.lower()
                    if 'recurring investment' in header_text:
                        in_recurring_section = True
                    else:
                        in_recurring_section = False
                    continue  # Skip header line itself
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Only process recommendation lines (starting with dash)
                if not line.strip().startswith('-'):
                    continue
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
                            asset_symbol = asset.get('symbol')
                            # If this recommendation seems to match an existing asset
                            if asset_symbol and asset_symbol in line:
                                ticker = asset_symbol
                                break
                    
                    # Parse action
                    action_part = ''
                    if 'ACTION:' in line:
                        action_part = line.split('ACTION:')[1].split(',')[0].strip()
                    
                    # Parse amount - expecting numeric dollar amounts
                    amount_part = ''
                    if 'AMOUNT:' in line:
                        # Extract the substring after 'AMOUNT:' up to either 'ACCOUNT:', 'COMMENTS:' or 'REASON:' or the end of the line.
                        amt_segment = line.split('AMOUNT:')[1]
                        # Check for ACCOUNT: first (new format with account)
                        if 'ACCOUNT:' in amt_segment:
                            amt_segment = amt_segment.split('ACCOUNT:')[0]
                        # Check for COMMENTS: next (new format)
                        elif 'COMMENTS:' in amt_segment:
                            amt_segment = amt_segment.split('COMMENTS:')[0]
                        # Backward compatibility with REASON: format
                        elif 'REASON:' in amt_segment:
                            amt_segment = amt_segment.split('REASON:')[0]
                        # Remove any leading/trailing whitespace and a trailing comma, but preserve internal commas
                        amount_raw = amt_segment.strip().rstrip(',')
                        # Clean up the amount value and validate it's numeric
                        amount_cleaned = amount_raw.replace('$', '').replace(',', '')
                        try:
                            # Validate that it's a number
                            parsed_amount = float(amount_cleaned) if amount_cleaned else 0.0
                            # For HOLD actions with 0 amount, return integer 0 instead of 0.0
                            if action_part == 'HOLD' and parsed_amount == 0.0:
                                amount_part = 0
                            else:
                                amount_part = parsed_amount
                        except ValueError:
                            # If not numeric, keep the original value for debugging
                            amount_part = amount_raw
                    # For backward compatibility (during transition period)
                    elif 'QUANTITY:' in line:
                        # Extract the substring after 'QUANTITY:' up to either 'ACCOUNT:', 'COMMENTS:' or 'REASON:' or the end of the line.
                        qty_segment = line.split('QUANTITY:')[1]
                        # Check for ACCOUNT: first (new format with account)
                        if 'ACCOUNT:' in qty_segment:
                            qty_segment = qty_segment.split('ACCOUNT:')[0]
                        # Check for COMMENTS: next (new format)
                        elif 'COMMENTS:' in qty_segment:
                            qty_segment = qty_segment.split('COMMENTS:')[0]
                        # Backward compatibility with REASON: format
                        elif 'REASON:' in qty_segment:
                            qty_segment = qty_segment.split('REASON:')[0]
                        # Remove any leading/trailing whitespace and a trailing comma, but preserve internal commas
                        amount_raw = qty_segment.strip().rstrip(',')
                        # Clean up the amount value and validate it's numeric
                        amount_cleaned = amount_raw.replace('$', '').replace(',', '')
                        try:
                            # Validate that it's a number
                            parsed_amount = float(amount_cleaned) if amount_cleaned else 0.0
                            # For HOLD actions with 0 amount, return integer 0 instead of 0.0
                            if action_part == 'HOLD' and parsed_amount == 0.0:
                                amount_part = 0
                            else:
                                amount_part = parsed_amount
                        except ValueError:
                            # If not numeric, keep the original value for debugging
                            amount_part = amount_raw
                    
                    # Parse account information
                    account_part = 'Default'  # Default account if not specified
                    if 'ACCOUNT:' in line:
                        account_segment = line.split('ACCOUNT:')[1]
                        if ',' in account_segment:
                            account_part = account_segment.split(',')[0].strip()
                        else:
                            account_part = account_segment.strip()
                    
                    # Parse comments (formerly reason)
                    comments_part = ''
                    if 'COMMENTS:' in line:
                        comments_part = line.split('COMMENTS:')[1].strip()
                    # For backward compatibility (during transition period)
                    elif 'REASON:' in line:
                        comments_part = line.split('REASON:')[1].strip()
                    
                    # Create structured recommendation with improved data
                    recommendation = {
                        'ticker': ticker,
                        'action': action_part,
                        'amount': amount_part,
                        'account': account_part,
                        'comments': comments_part
                    }
                    
                    if in_recurring_section:
                        recurrent_investments.append(recommendation)
                    else:
                        structured_recommendations.append(recommendation)
                except Exception as e:
                    # If parsing fails, include the raw line
                    if in_recurring_section:
                        recurrent_investments.append({
                            'ticker': 'PARSE_ERROR',
                            'action': 'UNKNOWN',
                            'amount': 'UNKNOWN',
                            'account': 'Default',
                            'comments': f'Error parsing: {line}'
                        })
                    else:
                        structured_recommendations.append({
                            'ticker': 'PARSE_ERROR',
                            'action': 'UNKNOWN',
                            'amount': 'UNKNOWN',
                            'account': 'Default',
                            'comments': f'Error parsing: {line}'
                        })
        
        # If parsing didn't work well, include the raw text
        if not structured_recommendations:
            structured_recommendations = [{
                'ticker': 'RAW_RESPONSE',
                'action': 'UNKNOWN',
                'amount': 'UNKNOWN',
                'account': 'Default',
                'comments': ai_recommendations_text
            }]
        # Ensure recurrent_investments list exists even if parsing fails
        if not recurrent_investments:
            recurrent_investments = []
            
        ai_recommendations = structured_recommendations
        
        # Validation: Ensure MOVE actions do not exceed existing holdings
        if structured_recommendations:
            # Build a mapping of current holdings value by ticker
            holdings_value = {}
            for asset in portfolio_data:
                sym = asset.get('symbol')
                val = asset.get('value', 0)
                holdings_value[sym] = holdings_value.get(sym, 0) + (val or 0)
            
            for rec in structured_recommendations:
                try:
                    if rec.get('action', '').upper() == 'MOVE':
                        amt = rec.get('amount', 0)
                        if isinstance(amt, str):
                            amt = float(str(amt).replace('$', '').replace(',', '') or 0)
                        ticker_sym = rec.get('ticker')
                        max_allowed = holdings_value.get(ticker_sym, 0)
                        if max_allowed <= 0:
                            # No existing holding, set to 0
                            rec['amount'] = 0
                            rec['comments'] = f"[ADJUSTED] No existing position in {ticker_sym}; amount set to 0. " + rec.get('comments', '')
                        elif amt > max_allowed:
                            rec['amount'] = max_allowed
                            rec['comments'] = f"[ADJUSTED] Move amount reduced to current holding (${max_allowed}). " + rec.get('comments', '')
                except Exception:
                    pass
        
    except Exception as error:
        structured_recommendations = [{
            'ticker': 'ERROR',
            'action': 'UNAVAILABLE',
            'amount': 'UNKNOWN',
            'account': 'Default',
            'comments': f"Recommendations temporarily unavailable: {error}"
        }]
        recurrent_investments = []
        feedback_text = "Unable to generate feedback due to an error."
        # Update debug collector with error
        if 'call_id' in locals():
            debug_collector.update_llm_call_response(
                call_id,
                response_content=None,
                error=str(error),
                duration_ms=int((time.time() - start_time) * 1000)
            )
    
    # Compute asset flux metrics for response
    try:
        net_buys = 0.0
        net_sells = 0.0
        # Prepare portfolio mapping symbol -> list of accounts it currently resides in
        symbol_accounts_map = {}
        for asset in portfolio_data:
            sym = asset.get('symbol')
            acct = asset.get('account', 'Default')
            if sym:
                symbol_accounts_map.setdefault(sym, []).append(acct)
        # Compute BUY / SELL totals and collect MOVE fluxes
        account_move_aggregates = {}
        for rec in ai_recommendations:
            action = str(rec.get('action', '')).upper()
            # Attempt to coerce amount to float if possible
            amt_raw = rec.get('amount', 0)
            try:
                if isinstance(amt_raw, str):
                    amt = float(amt_raw.replace('$', '').replace(',', ''))
                else:
                    amt = float(amt_raw)
            except (ValueError, TypeError):
                amt = 0.0
            if action == 'BUY':
                net_buys += amt
            elif action == 'SELL':
                net_sells += amt
            elif action == 'MOVE':
                target_account = rec.get('account', 'Default')
                ticker = rec.get('ticker')
                # Determine source account from current portfolio holdings (first differing account)
                source_account = None
                if ticker and ticker in symbol_accounts_map:
                    for acct in symbol_accounts_map[ticker]:
                        if acct != target_account:
                            source_account = acct
                            break
                # Fallback if source not determined
                if not source_account:
                    source_account = 'Unknown'
                key = (source_account, target_account)
                account_move_aggregates[key] = account_move_aggregates.get(key, 0.0) + amt
        net_cash_flux = round(net_sells - net_buys, 2)
        asset_flux = {
            'net_buys': round(net_buys, 2),
            'net_sells': round(net_sells, 2),
            'net_cash_flux': net_cash_flux
        }
        # Only include net_account_flux if multiple accounts exist and there are MOVE actions
        if len(set(acct for accts in symbol_accounts_map.values() for acct in accts)) > 1 and account_move_aggregates:
            # If exactly one pair, use it; else summarise as Various
            if len(account_move_aggregates) == 1:
                ((from_acct, to_acct), flux_amt) = next(iter(account_move_aggregates.items()))
                asset_flux['net_account_flux'] = {
                    'amount': round(flux_amt, 2),
                    'from_account': from_acct,
                    'to_account': to_acct
                }
            else:
                # Summarise total amount moved when multiple directions exist
                total_move_amt = round(sum(account_move_aggregates.values()), 2)
                asset_flux['net_account_flux'] = {
                    'amount': total_move_amt,
                    'from_account': 'Various',
                    'to_account': 'Various'
                }
    except Exception as e:
        # In case of any unexpected errors, fall back to zeroed asset_flux
        asset_flux = {
            'net_buys': 0,
            'net_sells': 0,
            'net_cash_flux': 0,
            'error': f'Asset flux computation error: {str(e)}'
        }
        
    # Group recommendations by account
    recommendations_by_account = {}
    for rec in ai_recommendations:
        account = rec.get('account', 'Default')
        if account not in recommendations_by_account:
            recommendations_by_account[account] = []
        recommendations_by_account[account].append(rec)
    
    # Portfolio recommendations response
    response_data = {
        'total_value': total_value,
        'total_portfolio_value': total_portfolio_value,
        'cash': cash,
        'asset_count': asset_count,
        'asset_types': list(asset_types),
        'investment_goals': investment_goals,
        'recommendations_by_account': recommendations_by_account,
        'recommendations': ai_recommendations,  # Keep original format for backward compatibility
        'recurrent_investements': recurrent_investments,
        'feedback': feedback_text,
        'asset_flux': asset_flux,
        'conversation_id': str(conversation.id)
    }
    
    # Inject debug data if enabled
    enhanced_response = inject_debug_data(response_data, debug_collector)
    
    return Response(enhanced_response)

@api_view(['POST'])
@permission_classes([GlobalHardcodedAPIKeyPermission, IsAuthenticatedOrAnonymous])
def chat(request):
    """
    Dedicated chat endpoint for follow-up on conversation threads.
    """
    debug_collector = create_debug_collector()
    message = request.data.get('message')
    if not message:
        return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
    conversation_id = request.data.get('conversation_id')
    
    # Handle anonymous users by passing None for user
    user = request.user if request.user.is_authenticated else None
    
    conversation, created = get_or_create_conversation(
        conversation_id=conversation_id,
        conversation_type='chat',
        user=user
    )
    # Add user message to thread
    add_message_to_thread(conversation.thread_id, message)
    # Prepare for LLM call. If using direct chat.completions, include prior context.
    messages = []
    assistant_id = os.getenv('OPENAI_ASSISTANT_ID', '')
    if not assistant_id:
        try:
            prev_msgs = get_thread_messages(conversation.thread_id)
            # prev_msgs are newest first; reverse to chronological order
            for m in reversed(prev_msgs):
                try:
                    if isinstance(m.content, list):
                        # Extract text from the first content part (usually only one)
                        part = m.content[0]
                        # Newer SDK : part.text.value ; Older : part.text
                        text_val = getattr(getattr(part, 'text', ''), 'value', None) or getattr(part, 'text', '')
                        content_text = text_val if isinstance(text_val, str) else str(text_val)
                    else:
                        content_text = str(m.content)
                except Exception:
                    content_text = str(m.content)
                messages.append({'role': m.role, 'content': content_text})
        except Exception:
            pass  # fallback to empty context
    # Append current user message
    messages.append({'role': 'user', 'content': message})
    # Prepare for LLM call
    client = AIRequestManager()
    # Record LLM call for debug
    assistant_id = os.getenv('OPENAI_ASSISTANT_ID', '')
    
    if assistant_id:
        # Using OpenAI assistant
        model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        provider_name = 'OpenAI'
        prompt_type = 'chat_thread'
    else:
        # Using direct API call - get provider info
        chat_provider = AIRequestManager.get_chat_provider()
        provider_name = chat_provider.get_provider_name()
        model = chat_provider.model if hasattr(chat_provider, 'model') else 'unknown'
        prompt_type = 'chat_direct_with_context'
    
    call_id = debug_collector.record_llm_call(
        model=model,
        provider=provider_name,
        prompt_type=prompt_type,
        messages=messages
    )
    start_time = time.time()  # Initialize start_time for duration tracking
    
    try:
        if assistant_id:
            run_thread_with_assistant(conversation.thread_id, assistant_id)
            assistant_message = get_latest_assistant_message(conversation.thread_id)
            content = assistant_message.content[0].text.value if assistant_message else ''
        else:
            ai_response = client.make_request(
                endpoint_type='chat',
                messages=messages
            )
            
            if ai_response['success']:
                content = ai_response['content']
            else:
                content = f"Chat error: {ai_response['error']}"
            response_tokens = None  # Not available from our abstraction layer
        duration = int((time.time() - start_time) * 1000)
        
        # Update debug call with response
        debug_collector.update_llm_call_response(
            call_id,
            response_content=str(content),
            duration_ms=duration
        )
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        debug_collector.update_llm_call_response(
            call_id,
            response_content=None,
            error=str(e),
            duration_ms=duration
        )
        raise
    # Build and return response with debug data
    response_data = {
        'message': content,
        'conversation_id': str(conversation.id)
    }
    enhanced = inject_debug_data(response_data, debug_collector)
    return Response(enhanced)

@api_view(['POST'])
@permission_classes([GlobalHardcodedAPIKeyPermission, AllowAny])
def register_user(request):
    """
    Register a new user and return their API key.
    
    Required fields:
    - email: User's email address (used as username)
    
    Optional fields:
    - first_name: User's first name
    - last_name: User's last name
    
    Returns:
    - email: User's email
    - api_key: Generated API key for authentication
    """
    User = get_user_model()
    
    # Get email from request data
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'Email is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate email format (basic validation)
    if '@' not in email or '.' not in email.split('@')[-1]:
        return Response(
            {'error': 'Invalid email format'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get optional fields
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    try:
        # Create user with email as username
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_api_active=True
        )
        
        # Return user data with API key
        return Response({
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'api_key': user.api_key,
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except IntegrityError:
        # User with this email already exists
        return Response(
            {'error': 'User with this email already exists'}, 
            status=status.HTTP_409_CONFLICT
        )
    except Exception as e:
        # Handle any other errors
        if os.getenv('DEBUG', 'False').lower() == 'true':
            print(f"Failed to create user: {str(e)}")
        return Response(
            {'error': f'Failed to create user: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([GlobalHardcodedAPIKeyPermission, IsAuthenticated])
def delete_account(request):
    """Delete the authenticated user's account and all related conversations.

    This endpoint requires no request body. It must include:
    - Authorization header with the global API key.
    - Authentication header in the form 'ApiKey <user_api_key>'.
    """
    user = request.user

    # Verify the user is authenticated (not anonymous)
    if user is None or user.is_anonymous:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user_id = user.id  # Preserve ID for response

        # Delete associated conversations first (on_delete=CASCADE would handle this, but we do it explicitly for clarity)
        Conversation.objects.filter(user=user).delete()

        # Delete the user record
        user.delete()

        return Response({'user_id': str(user_id), 'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        if os.getenv('DEBUG', 'False').lower() == 'true':
            print(f'Failed to delete user: {str(e)}')
        return Response({'error': f'Failed to delete account: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
