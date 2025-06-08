"""
AI Provider abstraction layer for supporting multiple AI services
Supports OpenAI and Anthropic Claude APIs
"""

import os
import openai
from anthropic import Anthropic
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate a chat completion response"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the AI provider"""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self, api_key: str, model: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate a chat completion using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def get_provider_name(self) -> str:
        return "OpenAI"


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider implementation"""
    
    def __init__(self, api_key: str, model: str):
        self.client = Anthropic(api_key=api_key)
        self.model = model
    
    def chat_completion(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate a chat completion using Anthropic API"""
        try:
            # Convert OpenAI format messages to Anthropic format
            system_message = ""
            user_messages = []
            
            for message in messages:
                if message["role"] == "system":
                    system_message = message["content"]
                elif message["role"] == "user":
                    user_messages.append({"role": "user", "content": message["content"]})
                elif message["role"] == "assistant":
                    user_messages.append({"role": "assistant", "content": message["content"]})
            
            # Create the request
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message if system_message else None,
                messages=user_messages
            )
            
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def get_provider_name(self) -> str:
        return "Anthropic"


class AIProviderFactory:
    """Factory class for creating AI providers"""
    
    @staticmethod
    def create_provider(provider_type: str, model_type: str) -> AIProvider:
        """
        Create an AI provider instance based on configuration
        
        Args:
            provider_type: 'OPENAI' or 'ANTHROPIC'
            model_type: 'CHAT', 'ANALYSIS', or 'RECOMMENDATIONS'
        
        Returns:
            AIProvider instance
        """
        provider_type = provider_type.upper()
        model_type = model_type.upper()
        
        if provider_type == 'OPENAI':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            
            # Select the appropriate model based on type
            if model_type == 'CHAT':
                model = os.getenv('OPENAI_MODEL', 'gpt-4o')
            elif model_type == 'ANALYSIS':
                model = os.getenv('OPENAI_MODEL', 'gpt-4o')
            elif model_type == 'RECOMMENDATIONS':
                model = os.getenv('OPENAI_RECOMMENDATIONS_MODEL', 'gpt-4o')
            else:
                model = os.getenv('OPENAI_MODEL', 'gpt-4o')
            
            return OpenAIProvider(api_key, model)
        
        elif provider_type == 'ANTHROPIC':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
            # Select the appropriate model based on type
            if model_type == 'CHAT':
                model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20240620')
            elif model_type == 'ANALYSIS':
                model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20240620')
            elif model_type == 'RECOMMENDATIONS':
                model = os.getenv('ANTHROPIC_RECOMMENDATIONS_MODEL', 'claude-3-5-sonnet-20240620')
            else:
                model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20240620')
            
            return AnthropicProvider(api_key, model)
        
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")


class AIRequestManager:
    """Manager class for handling AI requests across different providers"""
    
    @staticmethod
    def get_chat_provider() -> AIProvider:
        """Get the AI provider for chat endpoint"""
        provider_type = os.getenv('CHAT_MODEL', 'OPENAI')
        return AIProviderFactory.create_provider(provider_type, 'CHAT')
    
    @staticmethod
    def get_analysis_provider() -> AIProvider:
        """Get the AI provider for analysis endpoint"""
        provider_type = os.getenv('ANALYSIS_MODEL', 'OPENAI')
        return AIProviderFactory.create_provider(provider_type, 'ANALYSIS')
    
    @staticmethod
    def get_recommendations_provider() -> AIProvider:
        """Get the AI provider for recommendations endpoint"""
        provider_type = os.getenv('RECOMMENDATIONS_MODEL', 'OPENAI')
        return AIProviderFactory.create_provider(provider_type, 'RECOMMENDATIONS')
    
    @staticmethod
    def make_request(endpoint_type: str, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Make an AI request for a specific endpoint type
        
        Args:
            endpoint_type: 'chat', 'analysis', or 'recommendations'
            messages: List of message dictionaries in OpenAI format
            max_tokens: Maximum tokens for response
            temperature: Temperature for response generation
        
        Returns:
            Dictionary containing response and metadata
        """
        endpoint_type = endpoint_type.lower()
        
        # Get the appropriate provider
        if endpoint_type == 'chat':
            provider = AIRequestManager.get_chat_provider()
        elif endpoint_type == 'analysis':
            provider = AIRequestManager.get_analysis_provider()
        elif endpoint_type == 'recommendations':
            provider = AIRequestManager.get_recommendations_provider()
        else:
            raise ValueError(f"Unsupported endpoint type: {endpoint_type}")
        
        try:
            # Make the request
            response_content = provider.chat_completion(messages, max_tokens, temperature)
            
            return {
                'content': response_content,
                'provider': provider.get_provider_name(),
                'model': provider.model if hasattr(provider, 'model') else 'unknown',
                'success': True,
                'error': None
            }
        
        except Exception as e:
            return {
                'content': None,
                'provider': provider.get_provider_name() if 'provider' in locals() else 'unknown',
                'model': provider.model if 'provider' in locals() and hasattr(provider, 'model') else 'unknown',
                'success': False,
                'error': str(e)
            }
