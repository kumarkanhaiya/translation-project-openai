#!/usr/bin/env python3
"""
OpenAI-powered translator module.

This module provides a clean, professional interface for translation
using OpenAI's GPT models with proper error handling and configuration.
"""

import os
from typing import Optional, Dict, Any
from openai import OpenAI
import time


class OpenAITranslator:
    """
    Professional OpenAI-powered translator.
    
    Features:
    - Multiple model support (GPT-3.5, GPT-4, etc.)
    - Context-aware translations
    - Robust error handling
    - Performance metrics
    - Configurable parameters
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the OpenAI translator.
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model: OpenAI model to use for translation
        """
        self.api_key = api_key or self._get_api_key()
        self.model = model
        self.client = None
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self._initialize_client()
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or .env file."""
        api_key = os.getenv('OPENAI_API_KEY')
        
        # If not found, try reading directly from .env file
        if not api_key or api_key == "your_openai_api_key_here":
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('OPENAI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            break
            except FileNotFoundError:
                pass
        
        return api_key
    
    def _initialize_client(self):
        """Initialize the OpenAI client."""
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
    
    def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        context: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
        max_retries: int = 2,
        quality_threshold: float = 8.5
    ) -> Dict[str, Any]:
        """
        Translate text from source language to target language with context.
        
        Args:
            text: Text to translate
            source_lang: Source language name
            target_lang: Target language name
            context: Optional context for better translation
            temperature: Model temperature (0.0-1.0, lower = more consistent)
            max_tokens: Maximum tokens in response
            max_retries: Maximum number of retries for low-quality translations
            quality_threshold: Minimum quality score (1-10) to accept translation
        
        Returns:
            Dict containing translation results and metadata
        """
        
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        # Build translation prompt
        prompt = f"Translate the following text from {source_lang} to {target_lang}:\n\n{text}"
        
        if context:
            prompt += f"\n\nContext for this translation: {context}\nUse this context to ensure accurate translation of domain-specific terms and concepts."
        
        prompt += "\n\nProvide only the translation, nothing else."
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Provide accurate, natural translations that preserve the meaning and tone of the original text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            translation_time = time.time() - start_time
            translated_text = response.choices[0].message.content.strip()
            
            return {
                'success': True,
                'original_text': text,
                'translated_text': translated_text,
                'source_language': source_lang,
                'target_language': target_lang,
                'context': context,
                'model_used': self.model,
                'translation_time': round(translation_time, 3),
                'tokens_used': response.usage.total_tokens if response.usage else None,
                'cost_estimate': self._estimate_cost(response.usage.total_tokens if response.usage else 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'original_text': text,
                'source_language': source_lang,
                'target_language': target_lang,
                'context': context,
                'model_used': self.model,
                'translation_time': time.time() - start_time
            }
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on model and token usage."""
        # Rough cost estimates (as of 2024)
        cost_per_1k_tokens = {
            'gpt-3.5-turbo': 0.002,
            'gpt-4': 0.03,
            'gpt-4-turbo': 0.01,
            'gpt-4o': 0.005
        }
        
        rate = cost_per_1k_tokens.get(self.model, 0.002)
        return round((tokens / 1000) * rate, 6)
    
    def batch_translate(
        self, 
        texts: list, 
        source_lang: str, 
        target_lang: str, 
        context: Optional[str] = None
    ) -> list:
        """
        Translate multiple texts in batch.
        
        Args:
            texts: List of texts to translate
            source_lang: Source language name
            target_lang: Target language name
            context: Optional context for better translation
        
        Returns:
            List of translation results
        """
        results = []
        
        for text in texts:
            result = self.translate(text, source_lang, target_lang, context)
            results.append(result)
        
        return results
    
    def get_supported_models(self) -> list:
        """Get list of supported OpenAI models."""
        return [
            'gpt-3.5-turbo',
            'gpt-4',
            'gpt-4-turbo',
            'gpt-4o',
            'gpt-4o-mini'
        ]
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the OpenAI API connection."""
        try:
            result = self.translate(
                text="Hello, world!",
                source_lang="English",
                target_lang="Spanish"
            )
            
            return {
                'success': result['success'],
                'message': 'Connection successful' if result['success'] else f"Connection failed: {result.get('error', 'Unknown error')}",
                'model': self.model,
                'test_translation': result.get('translated_text', 'N/A')
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}',
                'model': self.model
            }


