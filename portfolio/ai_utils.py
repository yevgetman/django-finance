"""
AI utilities for the portfolio application.

This module provides helper functions for AI-powered analysis
and integrates with the prompt management system.
"""

import os
from openai import OpenAI
from typing import Dict, Any, Optional
from .prompts import PromptManager


class AIAnalyzer:
    """Helper class for AI-powered financial analysis."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.default_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    def analyze_with_prompt(self, prompt_name: str, model: Optional[str] = None, **data) -> str:
        """
        Generic method to analyze data using a specified prompt template.
        
        Args:
            prompt_name: Name of the prompt template to use
            model: OpenAI model to use (optional, defaults to env setting)
            **data: Data to inject into the prompt template
        
        Returns:
            AI-generated analysis text
        
        Raises:
            ValueError: If prompt template is not found
            Exception: If OpenAI API call fails
        """
        prompt_template = PromptManager.get_prompt(prompt_name)
        
        if not prompt_template:
            available_prompts = PromptManager.list_available_prompts()
            raise ValueError(
                f"Prompt '{prompt_name}' not found. Available prompts: {available_prompts}"
            )
        
        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=prompt_template.get_messages(**data),
                max_tokens=prompt_template.max_tokens,
                temperature=prompt_template.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")
    
    def get_available_prompts(self) -> list:
        """Get list of available prompt templates."""
        return PromptManager.list_available_prompts()


# Convenience function for quick AI analysis
def get_ai_analysis(prompt_name: str, **data) -> str:
    """
    Convenience function to get AI analysis using a prompt template.
    
    Args:
        prompt_name: Name of the prompt template
        **data: Data to inject into the prompt
    
    Returns:
        AI-generated analysis or error message
    """
    try:
        analyzer = AIAnalyzer()
        return analyzer.analyze_with_prompt(prompt_name, **data)
    except Exception as e:
        return f"AI analysis temporarily unavailable: {str(e)}"
