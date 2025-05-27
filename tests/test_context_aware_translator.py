#!/usr/bin/env python3
"""
Tests for the ContextAwareTranslator class.
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translators.context_aware_translator import ContextAwareTranslator

class TestContextAwareTranslator(unittest.TestCase):
    """Test cases for the ContextAwareTranslator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()

        # Create mock translator and evaluator
        self.mock_translator = MagicMock()
        self.mock_evaluator = MagicMock()

        # Create the translator with mocked components
        self.translator = ContextAwareTranslator(
            client=self.mock_client,
            translation_model="gpt-3.5-turbo",
            evaluation_model="gpt-4o"
        )

        # Replace the real components with mocks
        self.translator.translator = self.mock_translator
        self.translator.evaluator = self.mock_evaluator

        # Set up mock translation response
        self.mock_translation = {
            'success': True,
            'original_text': 'Hello world',
            'translated_text': 'Hola mundo',
            'source_language': 'English',
            'target_language': 'Spanish',
            'context': 'Greeting context',
            'model_used': 'gpt-3.5-turbo',
            'translation_time': 0.5,
            'tokens_used': 100
        }

        # Set up mock evaluation response
        self.mock_evaluation = {
            'success': True,
            'evaluation': json.dumps({
                "Accuracy": 9,
                "Fluency": 9,
                "Context Relevance": 8,
                "Overall quality": 8.7,
                "explanation": "The translation is accurate and fluent."
            }),
            'overall_score': 8.7,
            'eval_model': 'gpt-4o',
            'eval_time': 0.3,
            'tokens_used': 150
        }

        # Configure mocks to return our responses
        self.mock_translator.translate.return_value = self.mock_translation
        self.mock_evaluator.evaluate_with_context.return_value = self.mock_evaluation

    def test_successful_translation(self):
        """Test successful translation with quality above threshold."""
        result = self.translator.translate(
            text="Hello world",
            source_lang="English",
            target_lang="Spanish",
            context="Greeting context"
        )

        # Check that translator and evaluator were called
        self.mock_translator.translate.assert_called_once()
        self.mock_evaluator.evaluate_with_context.assert_called_once()

        # Check the result
        self.assertTrue(result['success'])
        self.assertEqual(result['translated_text'], 'Hola mundo')
        self.assertEqual(result['quality_score'], 8.7)
        self.assertEqual(result['quality_status'], 'high_quality')
        self.assertEqual(result['attempts_count'], 1)

    def test_low_quality_translation_retry(self):
        """Test retry logic for low-quality translations."""
        # First evaluation below threshold, second above
        low_quality_eval = {
            'success': True,
            'evaluation': json.dumps({
                "Accuracy": 7,
                "Fluency": 7,
                "Context Relevance": 6,
                "Overall quality": 6.5,
                "explanation": "The translation has some issues."
            }),
            'overall_score': 6.5,
            'eval_model': 'gpt-4o',
            'eval_time': 0.3,
            'tokens_used': 150
        }

        # Configure evaluator to return low quality first, then high quality
        self.mock_evaluator.evaluate_with_context.side_effect = [
            low_quality_eval,
            self.mock_evaluation
        ]

        result = self.translator.translate(
            text="Hello world",
            source_lang="English",
            target_lang="Spanish",
            context="Greeting context"
        )

        # Check that translator was called twice (retry)
        self.assertEqual(self.mock_translator.translate.call_count, 2)
        self.assertEqual(self.mock_evaluator.evaluate_with_context.call_count, 2)

        # Check the result
        self.assertTrue(result['success'])
        self.assertEqual(result['translated_text'], 'Hola mundo')
        self.assertEqual(result['quality_score'], 8.7)  # Final score should be high
        self.assertEqual(result['quality_status'], 'high_quality')
        self.assertEqual(result['attempts_count'], 2)

    def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        # Configure evaluator to always return low quality
        low_quality_eval = {
            'success': True,
            'evaluation': json.dumps({
                "Accuracy": 6,
                "Fluency": 6,
                "Context Relevance": 5,
                "Overall quality": 5.5,
                "explanation": "The translation has significant issues."
            }),
            'overall_score': 5.5,
            'eval_model': 'gpt-4o',
            'eval_time': 0.3,
            'tokens_used': 150
        }

        self.mock_evaluator.evaluate_with_context.return_value = low_quality_eval

        result = self.translator.translate(
            text="Hello world",
            source_lang="English",
            target_lang="Spanish",
            context="Greeting context"
        )

        # Check that translator was called max_retries + 1 times
        self.assertEqual(self.mock_translator.translate.call_count, 3)  # max_retries=2, so 3 total attempts
        self.assertEqual(self.mock_evaluator.evaluate_with_context.call_count, 3)

        # Check the result
        self.assertTrue(result['success'])
        self.assertEqual(result['quality_score'], 5.5)
        self.assertEqual(result['quality_status'], 'low_quality')
        self.assertEqual(result['attempts_count'], 3)
        self.assertIn("Could not achieve high-quality", result['message'])

    def test_translation_failure(self):
        """Test handling of translation failures."""
        # Configure translator to fail
        self.mock_translator.translate.return_value = {
            'success': False,
            'error': 'API error occurred'
        }

        result = self.translator.translate(
            text="Hello world",
            source_lang="English",
            target_lang="Spanish",
            context="Greeting context"
        )

        # Check that translator was called once
        self.mock_translator.translate.assert_called_once()
        # Evaluator should not be called if translation fails
        self.mock_evaluator.evaluate_with_context.assert_not_called()

        # Check the result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'API error occurred')
        self.assertIn('attempts', result)
        self.assertIn('total_time', result)

if __name__ == '__main__':
    unittest.main()