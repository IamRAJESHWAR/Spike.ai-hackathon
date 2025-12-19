"""Utilities for LLM interactions with retry logic."""

import time
from typing import Any, Dict, List
from openai import OpenAI, APIError
import config


class LLMClient:
    """Client for interacting with LiteLLM proxy with exponential backoff."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=config.LITELLM_API_KEY,
            base_url=config.LITELLM_BASE_URL
        )
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = config.LITELLM_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Make a chat completion request with exponential backoff retry logic.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use for completion
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            The response content as a string
        """
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            
            except APIError as e:
                if e.status_code == 429:
                    wait_time = config.BASE_DELAY * (2 ** attempt)
                    print(f"Rate limited (429). Retrying in {wait_time}s (attempt {attempt + 1}/{config.MAX_RETRIES})...")
                    time.sleep(wait_time)
                else:
                    print(f"API Error (Status: {e.status_code}): {e}")
                    raise
            
            except Exception as e:
                print(f"Unexpected error in LLM call: {e}")
                raise
        
        raise Exception("Failed to make API call after multiple retries due to rate limiting")


# Global LLM client instance
llm_client = LLMClient()
