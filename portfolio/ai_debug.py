"""
AI Debug Module for Django Finance Application

This module provides debugging capabilities for AI-powered features.
When AI_DEBUG is enabled in environment variables, it captures and returns
detailed information about LLM model calls, prompts, and responses.
"""

import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class LLMCall:
    """Represents a single LLM API call with debugging information."""
    model: str
    prompt_type: str
    messages: List[Dict[str, str]]
    max_tokens: int
    temperature: float
    timestamp: str
    response_content: Optional[str] = None
    response_tokens: Optional[int] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class AIDebugCollector:
    """Collects debugging information for AI operations."""
    
    def __init__(self):
        self.llm_calls: List[LLMCall] = []
        self.enabled = self._is_debug_enabled()
        self.start_time = time.time()
    
    def _is_debug_enabled(self) -> bool:
        """Check if AI debug mode is enabled."""
        return os.getenv('AI_DEBUG', 'False').lower() == 'true'
    
    def record_llm_call(
        self,
        model: str,
        prompt_type: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Record an LLM call for debugging.
        Returns a call_id that can be used to update the call with response data.
        """
        if not self.enabled:
            return None
            
        call = LLMCall(
            model=model,
            prompt_type=prompt_type,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timestamp=datetime.now().isoformat()
        )
        
        self.llm_calls.append(call)
        return str(len(self.llm_calls) - 1)  # Return index as call_id
    
    def update_llm_call_response(
        self,
        call_id: str,
        response_content: str,
        response_tokens: Optional[int] = None,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Update an LLM call with response information."""
        if not self.enabled or not call_id:
            return
            
        try:
            call_index = int(call_id)
            if 0 <= call_index < len(self.llm_calls):
                call = self.llm_calls[call_index]
                call.response_content = response_content
                call.response_tokens = response_tokens
                call.duration_ms = duration_ms
                call.error = error
        except (ValueError, IndexError):
            pass
    
    def get_debug_data(self) -> Dict[str, Any]:
        """Get all collected debug data."""
        if not self.enabled:
            return {}
        
        total_duration = int((time.time() - self.start_time) * 1000)
        
        return {
            "enabled": True,
            "total_request_duration_ms": total_duration,
            "llm_calls": [
                {
                    "model": call.model,
                    "prompt_type": call.prompt_type,
                    "timestamp": call.timestamp,
                    "config": {
                        "max_tokens": call.max_tokens,
                        "temperature": call.temperature
                    },
                    "messages": call.messages,
                    "response": {
                        "content_length": len(call.response_content) if call.response_content else 0,
                        "tokens": call.response_tokens,
                        "duration_ms": call.duration_ms,
                        "error": call.error
                    } if call.response_content or call.error else None
                }
                for call in self.llm_calls
            ],
            "summary": {
                "total_llm_calls": len(self.llm_calls),
                "models_used": list(set(call.model for call in self.llm_calls)),
                "prompt_types": list(set(call.prompt_type for call in self.llm_calls)),
                "total_llm_duration_ms": sum(
                    call.duration_ms for call in self.llm_calls 
                    if call.duration_ms is not None
                ),
                "errors": [
                    {"prompt_type": call.prompt_type, "error": call.error}
                    for call in self.llm_calls if call.error
                ]
            }
        }


def create_debug_collector() -> AIDebugCollector:
    """Factory function to create a new debug collector."""
    return AIDebugCollector()


def inject_debug_data(response_data: Dict[str, Any], debug_collector: AIDebugCollector) -> Dict[str, Any]:
    """
    Inject debug data into the response if AI_DEBUG is enabled.
    
    Args:
        response_data: The original response data
        debug_collector: The debug collector instance
        
    Returns:
        Enhanced response data with debug information (if enabled)
    """
    if not debug_collector.enabled:
        return response_data
    
    # Create a copy of the response data and add debug info
    enhanced_response = response_data.copy()
    enhanced_response["ai_debug"] = debug_collector.get_debug_data()
    
    return enhanced_response
