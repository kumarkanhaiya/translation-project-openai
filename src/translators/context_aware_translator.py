#!/usr/bin/env python3
"""
Context-aware translator with quality evaluation and retry logic.

This module combines the OpenAITranslator and TranslationEvaluator to create
a translation system that uses context for better translations and automatically
retries low-quality translations.
"""

import json
import time
from typing import Dict, Any, Optional
from openai import OpenAI

from translators.openai_translator import OpenAITranslator
from evaluators.translation_evaluator import TranslationEvaluator

class ContextAwareTranslator:
    """
    Context-aware translator with quality evaluation and retry logic.

    Features:
    - Uses context for better translations
    - Evaluates translation quality
    - Automatically retries low-quality translations
    - Uses different models for translation and evaluation
    """

    def __init__(
        self,
        client: Optional[OpenAI] = None,
        translation_model: str = "gpt-3.5-turbo",
        evaluation_model: str = "gpt-4o",
        quality_threshold: float = 8.5,
        max_retries: int = 2
    ):
        """
        Initialize the context-aware translator.

        Args:
            client: OpenAI client instance
            translation_model: Model to use for translation
            evaluation_model: Model to use for evaluation (should be different from translation_model)
            quality_threshold: Minimum quality score (1-10) to accept translation
            max_retries: Maximum number of retries for low-quality translations
        """
        self.client = client
        self.translator = OpenAITranslator(model=translation_model)
        self.evaluator = TranslationEvaluator(client=client, eval_model=evaluation_model)
        self.quality_threshold = quality_threshold
        self.max_retries = max_retries

        if translation_model == evaluation_model:
            print("Warning: Using the same model for translation and evaluation may lead to biased results.")

    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: str,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Translate text with context and retry if quality is below threshold.

        Args:
            text: Text to translate
            source_lang: Source language name
            target_lang: Target language name
            context: Context for the translation
            temperature: Model temperature for translation

        Returns:
            Dict containing translation results, evaluation, and metadata
        """
        start_time = time.time()
        attempts = []
        best_translation = None
        best_score = 0

        for attempt in range(self.max_retries + 1):
            # Adjust temperature slightly for each retry to get different outputs
            current_temp = temperature + (attempt * 0.1)

            # Translate the text
            translation = self.translator.translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                context=context,
                temperature=current_temp
            )

            if not translation['success']:
                return {
                    'success': False,
                    'error': translation['error'],
                    'attempts': attempts,
                    'total_time': time.time() - start_time
                }

            # Evaluate the translation
            evaluation = self.evaluator.evaluate_with_context(
                translated_text=translation['translated_text'],
                source_text=text,
                context=context,
                source_lang=source_lang,
                target_lang=target_lang,
                client=self.client
            )

            # Store attempt information
            attempt_info = {
                'translation': translation,
                'evaluation': evaluation,
                'attempt': attempt + 1
            }
            attempts.append(attempt_info)

            # Check if evaluation was successful
            if not evaluation['success']:
                continue

            # Parse evaluation to get overall score
            overall_score = evaluation['overall_score']

            # Update best translation if this one is better
            if overall_score > best_score:
                best_translation = translation
                best_score = overall_score

            # If quality is above threshold, return the result
            if overall_score >= self.quality_threshold:
                break

            # If we've reached max retries, stop
            if attempt >= self.max_retries:
                break

        # Prepare the final result
        total_time = time.time() - start_time

        # Check if we have any successful translation
        if best_translation is None:
            return {
                'success': False,
                'error': 'All translation attempts failed or could not be evaluated',
                'attempts': attempts,
                'total_time': round(total_time, 3)
            }

        if best_score >= self.quality_threshold:
            quality_status = "high_quality"
            message = "Translation meets quality standards."
        else:
            quality_status = "low_quality"
            message = "Could not achieve high-quality translation with the given context."

        return {
            'success': True,
            'original_text': text,
            'translated_text': best_translation['translated_text'],
            'source_language': source_lang,
            'target_language': target_lang,
            'context': context,
            'quality_score': best_score,
            'quality_status': quality_status,
            'message': message,
            'attempts': attempts,
            'attempts_count': len(attempts),
            'translation_model': self.translator.model,
            'evaluation_model': self.evaluator.eval_model,
            'total_time': round(total_time, 3)
        }