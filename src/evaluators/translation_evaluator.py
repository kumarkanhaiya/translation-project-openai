#!/usr/bin/env python3
"""
Translation evaluation module.

This module provides functionality to evaluate the quality of translations
using various metrics and OpenAI models as evaluators.
"""

import time
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI

class TranslationEvaluator:
    """
    Evaluates translation quality using various methods including:
    - OpenAI model-based evaluation
    - Reference-based scoring
    - Consistency checks
    """
    
    def __init__(self, client: Optional[OpenAI] = None, eval_model: str = "gpt-4o"):
        """
        Initialize the translation evaluator.
        
        Args:
            client: OpenAI client instance (if None, one must be provided during evaluation)
            eval_model: Model to use for evaluation (preferably more capable than translation model)
        """
        self.client = client
        self.eval_model = eval_model
        
    def evaluate_with_reference(
        self,
        translated_text: str,
        reference_text: str,
        source_text: str,
        client: Optional[OpenAI] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Evaluate translation against a reference (gold-standard) translation.
        
        Args:
            translated_text: The machine translation to evaluate
            reference_text: The reference (gold-standard) translation
            source_text: The original source text
            client: OpenAI client (uses instance client if None)
            temperature: Model temperature for evaluation
            
        Returns:
            Dict containing evaluation results and scores
        """
        client = client or self.client
        if not client:
            raise ValueError("OpenAI client is required for evaluation")
            
        start_time = time.time()
        
        system_prompt = """You are a professional translation evaluator. 
Assess the quality of the machine translation compared to the reference translation.
Score on a scale of 1-10 for:
1. Accuracy (meaning preservation)
2. Fluency (natural language use)
3. Terminology (correct domain-specific terms)
4. Overall quality

Provide only JSON output with these scores and a brief explanation."""
        
        try:
            response = client.chat.completions.create(
                model=self.eval_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Source text: {source_text}\n\nMachine translation: {translated_text}\n\nReference translation: {reference_text}"}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            eval_time = time.time() - start_time
            result = response.choices[0].message.content
            
            return {
                'success': True,
                'evaluation': result,
                'eval_model': self.eval_model,
                'eval_time': round(eval_time, 3),
                'tokens_used': response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'eval_model': self.eval_model,
                'eval_time': time.time() - start_time
            }
    
    def evaluate_without_reference(
        self,
        translated_text: str,
        source_text: str,
        source_lang: str,
        target_lang: str,
        client: Optional[OpenAI] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Evaluate translation quality without a reference translation.
        
        Args:
            translated_text: The machine translation to evaluate
            source_text: The original source text
            source_lang: Source language name
            target_lang: Target language name
            client: OpenAI client (uses instance client if None)
            temperature: Model temperature for evaluation
            
        Returns:
            Dict containing evaluation results and scores
        """
        client = client or self.client
        if not client:
            raise ValueError("OpenAI client is required for evaluation")
            
        start_time = time.time()
        
        system_prompt = f"""You are a professional translation evaluator fluent in both {source_lang} and {target_lang}.
Assess the quality of the machine translation from {source_lang} to {target_lang}.
Score on a scale of 1-10 for:
1. Accuracy (likely meaning preservation)
2. Fluency (natural {target_lang} usage)
3. Overall quality

Provide only JSON output with these scores and a brief explanation."""
        
        try:
            response = client.chat.completions.create(
                model=self.eval_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Source text ({source_lang}): {source_text}\n\nMachine translation ({target_lang}): {translated_text}"}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            eval_time = time.time() - start_time
            result = response.choices[0].message.content
            
            return {
                'success': True,
                'evaluation': result,
                'eval_model': self.eval_model,
                'eval_time': round(eval_time, 3),
                'tokens_used': response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'eval_model': self.eval_model,
                'eval_time': time.time() - start_time
            }
    
    def evaluate_with_context(
        self,
        translated_text: str,
        source_text: str,
        context: str,
        source_lang: str,
        target_lang: str,
        client: Optional[OpenAI] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Evaluate translation quality with provided context.
        
        Args:
            translated_text: The machine translation to evaluate
            source_text: The original source text
            context: The context provided for translation
            source_lang: Source language name
            target_lang: Target language name
            client: OpenAI client (uses instance client if None)
            temperature: Model temperature for evaluation
        
        Returns:
            Dict containing evaluation results and scores
        """
        client = client or self.client
        if not client:
            raise ValueError("OpenAI client is required for evaluation")
        
        start_time = time.time()
        
        system_prompt = f"""You are a professional translation evaluator fluent in both {source_lang} and {target_lang}.
Assess the quality of the machine translation from {source_lang} to {target_lang}.
The translation should accurately reflect the meaning of the source text while using appropriate terminology from the provided context.

Score on a scale of 1-10 for:
1. Accuracy (meaning preservation)
2. Fluency (natural {target_lang} usage)
3. Context Relevance (appropriate use of domain-specific terminology from context)
4. Overall quality

Provide only JSON output with these scores and a brief explanation."""
        
        try:
            response = client.chat.completions.create(
                model=self.eval_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Source text ({source_lang}): {source_text}\n\nContext: {context}\n\nMachine translation ({target_lang}): {translated_text}"}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            eval_time = time.time() - start_time
            result = response.choices[0].message.content
            
            # Parse the result to extract the overall quality score
            try:
                evaluation_data = json.loads(result)
                overall_score = evaluation_data.get("Overall quality", 0)
            except:
                overall_score = 0
            
            return {
                'success': True,
                'evaluation': result,
                'overall_score': overall_score,
                'eval_model': self.eval_model,
                'eval_time': round(eval_time, 3),
                'tokens_used': response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'eval_model': self.eval_model,
                'eval_time': time.time() - start_time
            }
    
    def batch_evaluate(
        self,
        translations: List[Dict[str, Any]],
        reference_texts: Optional[List[str]] = None,
        client: Optional[OpenAI] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple translations in batch.
        
        Args:
            translations: List of translation results from OpenAITranslator
            reference_texts: Optional list of reference translations (if available)
            client: OpenAI client (uses instance client if None)
            
        Returns:
            List of evaluation results
        """
        results = []
        client = client or self.client
        
        for i, translation in enumerate(translations):
            if not translation.get('success', False):
                results.append({
                    'success': False,
                    'error': 'Cannot evaluate failed translation',
                    'original_translation': translation
                })
                continue
                
            if reference_texts and i < len(reference_texts):
                # Evaluate with reference
                eval_result = self.evaluate_with_reference(
                    translated_text=translation['translated_text'],
                    reference_text=reference_texts[i],
                    source_text=translation['original_text'],
                    client=client
                )
            else:
                # Evaluate without reference
                eval_result = self.evaluate_without_reference(
                    translated_text=translation['translated_text'],
                    source_text=translation['original_text'],
                    source_lang=translation['source_language'],
                    target_lang=translation['target_language'],
                    client=client
                )
                
            eval_result['original_translation'] = translation
            results.append(eval_result)
            
        return results

