"""
Conversation thread utilities for AI provider integration.

This module provides functions for creating and managing conversation threads
with various AI providers (OpenAI and Anthropic) for portfolio analysis and recommendations.
"""

from typing import Dict, Any, Optional, Tuple
import os
import uuid
from openai import OpenAI
from .models import Conversation


def get_or_create_conversation(
    conversation_id: Optional[str] = None, 
    conversation_type: str = 'analysis',
    user = None
) -> Tuple[Conversation, bool]:
    """
    Get an existing conversation or create a new one.
    
    Args:
        conversation_id: UUID of an existing conversation
        conversation_type: Type of conversation ('analysis' or 'recommendations')
        user: User object to associate with the conversation
        
    Returns:
        Tuple of (Conversation object, boolean indicating if it was created)
    """
    created = False
    
    if conversation_id:
        try:
            # Try to get the existing conversation for this user
            conversation = Conversation.objects.get(
                id=conversation_id, 
                user=user,
                is_active=True
            )
            # For OpenAI, verify that the thread still exists
            chat_model = os.getenv('CHAT_MODEL', 'OPENAI')
            if chat_model.upper() == 'OPENAI':
                try:
                    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                    client.beta.threads.retrieve(conversation.thread_id)
                    return conversation, created
                except Exception:
                    # Thread doesn't exist anymore, create a new one
                    openai_thread = client.beta.threads.create()
                    conversation.thread_id = openai_thread.id
                    conversation.save(update_fields=['thread_id'])
                    return conversation, created
            else:
                # For Anthropic, thread_id is just a UUID, no need to verify
                return conversation, created
        except Conversation.DoesNotExist:
            # Invalid conversation ID, fall through to create a new one
            pass
    
    # Create a new conversation thread
    chat_model = os.getenv('CHAT_MODEL', 'OPENAI')
    if chat_model.upper() == 'OPENAI':
        # Create OpenAI thread
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        openai_thread = client.beta.threads.create()
        thread_id = openai_thread.id
    else:
        # For Anthropic, generate a UUID-based thread ID
        thread_id = f"anthropic_{uuid.uuid4().hex}"
    
    conversation = Conversation.objects.create(
        user=user,
        thread_id=thread_id,
        conversation_type=conversation_type
    )
    created = True
    
    return conversation, created


def add_message_to_thread(
    thread_id: str, 
    content: str
) -> Dict[str, Any]:
    """
    Add a message to an existing thread.
    
    Args:
        thread_id: Thread ID
        content: Message content to add
        
    Returns:
        Created message data
    """
    chat_model = os.getenv('CHAT_MODEL', 'OPENAI')
    if chat_model.upper() == 'OPENAI':
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content
        )
        return message
    else:
        # For Anthropic, implement message creation logic here
        pass


def run_thread_with_assistant(
    thread_id: str, 
    assistant_id: str,
    max_wait_seconds: int = 60
) -> Dict[str, Any]:
    """
    Run an assistant on a thread and wait for completion.
    
    Args:
        thread_id: Thread ID
        assistant_id: Assistant ID
        max_wait_seconds: Maximum time to wait for completion
        
    Returns:
        Run data with status
    """
    chat_model = os.getenv('CHAT_MODEL', 'OPENAI')
    if chat_model.upper() == 'OPENAI':
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Create a run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Poll for completion (simplified version)
        import time
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == 'completed':
                break
                
            if run_status.status in ['failed', 'cancelled', 'expired']:
                raise Exception(f"Run failed with status: {run_status.status}")
                
            time.sleep(1)  # Wait before polling again
        
        return run_status
    else:
        # For Anthropic, implement run logic here
        pass


def get_thread_messages(thread_id: str) -> list:
    """
    Get all messages from a thread.
    
    Args:
        thread_id: Thread ID
        
    Returns:
        List of messages
    """
    chat_model = os.getenv('CHAT_MODEL', 'OPENAI')
    if chat_model.upper() == 'OPENAI':
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        return messages.data
    else:
        # For Anthropic, implement message retrieval logic here
        pass


def get_latest_assistant_message(thread_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the most recent assistant message from a thread.
    
    Args:
        thread_id: Thread ID
        
    Returns:
        Latest assistant message or None
    """
    messages = get_thread_messages(thread_id)
    
    for message in messages:
        if message.role == "assistant":
            return message
            
    return None


def format_message_for_thread(
    portfolio_data: list,
    total_value: float,
    cash: float,
    investment_goals: str,
    chat: str,
    conversation_type: str
) -> str:
    """
    Format portfolio data as a message for a conversation thread.
    
    Args:
        portfolio_data: List of portfolio assets
        total_value: Total portfolio value
        cash: Available cash
        investment_goals: User's investment goals
        chat: User's conversational context
        conversation_type: Type of conversation ('analysis' or 'recommendations')
        
    Returns:
        Formatted message content
    """
    # Asset count and types for summary
    asset_count = len(portfolio_data)
    asset_types = set(asset.get('type') for asset in portfolio_data if asset.get('type'))
    
    # Format the message based on conversation type
    if conversation_type == 'analysis':
        request_type = "Please provide a detailed analysis of"
    else:
        request_type = "Please provide specific recommendations for"
    
    message = f"""{request_type} my investment portfolio:

Portfolio Summary:
- Total Portfolio Value: ${total_value + cash:,.2f}
- Investment Assets Value: ${total_value:,.2f}
- Available Cash: ${cash:,.2f}
- Number of Assets: {asset_count}
- Asset Types: {', '.join(asset_types) if asset_types else 'Not specified'}

"""
    
    # Add investment goals if provided
    if investment_goals:
        message += f"""Investment Goals:
{investment_goals}

"""
    
    # Add conversational context if provided
    if chat:
        message += f"Conversation Context:\n{chat}\n\n"

    message += "Detailed Holdings:\n"
    
    # Add each asset
    for asset in portfolio_data:
        ticker = asset.get('symbol', 'Unknown')
        message += f"- TICKER: {ticker} | Type: {asset.get('type', 'Unknown')} | Value: ${asset.get('value', 0):,.2f}\n"
        message += f"  Shares: {asset.get('shares', 'N/A')} | Current Price: ${asset.get('current_price', 'N/A')}\n"
    
    return message
