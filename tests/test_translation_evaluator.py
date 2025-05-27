#!/usr/bin/env python3
"""
Tests for the TranslationEvaluator class.
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluators.translation_evaluator import TranslationEvaluator

class TestTranslationEvaluator(unittest.TestCase):
    """Test cases for the TranslationEvaluator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.evaluator = TranslationEvaluator(client=self.mock_client)
        
        # Mock response for OpenAI API
        self.mock_response = MagicMock()
        self.mock_response.choices = [MagicMock()]
        self.mock_response.choices[0].message.content = json.dumps({
            "Accuracy": 8,
            "Fluency": 9,
            "Terminology": 7,
            "Overall quality": 8,
            "explanation": "The translation is accurate and fluent."
        })
        self.mock_response.usage = MagicMock()
        self.mock_response.usage.total_tokens = 150
        
        # Set up the mock client to return our mock response
        self.mock_client.chat.completions.create.return_value = self.mock_response
    
    def test_evaluate_with_reference(self):
        """Test evaluation with reference translation."""
        result = self.evaluator.evaluate_with_reference(
            translated_text="Hola mundo",
            reference_text="Hola mundo",
            source_text="Hello world"
        )
        
        # Check that the client was called with correct parameters
        self.mock_client.chat.completions.create.assert_called_once()
        call_args = self.mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], self.evaluator.eval_model)
        self.assertEqual(len(call_args['messages']), 2)
        
        # Check the result
        self.assertTrue(result['success'])
        self.assertEqual(result['eval_model'], self.evaluator.eval_model)
        self.assertEqual(result['tokens_used'], 150)
        
        # Parse the evaluation JSON
        evaluation = json.loads(result['evaluation'])
        self.assertEqual(evaluation['Accuracy'], 8)
        self.assertEqual(evaluation['Fluency'], 9)
        self.assertEqual(evaluation['Overall quality'], 8)
    
    def test_evaluate_without_reference(self):
        """Test evaluation without reference translation."""
        result = self.evaluator.evaluate_without_reference(
            translated_text="Hola mundo",
            source_text="Hello world",
            source_lang="English",
            target_lang="Spanish"
        )
        
        # Check that the client was called
        self.mock_client.chat.completions.create.assert_called_once()
        
        # Check the result
        self.assertTrue(result['success'])
        self.assertEqual(result['eval_model'], self.evaluator.eval_model)
        
    def test_batch_evaluate(self):
        """Test batch evaluation."""
        translations = [
            {
                'success': True,
                'original_text': 'Hello world',
                'translated_text': 'Hola mundo',
                'source_language': 'English',
                'target_language': 'Spanish'
            },
            {
                'success': True,
                'original_text': 'Good morning',
                'translated_text': 'Buenos días',
                'source_language': 'English',
                'target_language': 'Spanish'
            }
        ]
        
        reference_texts = ['Hola mundo', 'Buenos días']
        
        results = self.evaluator.batch_evaluate(
            translations=translations,
            reference_texts=reference_texts
        )
        
        # Check that we got results for both translations
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]['success'])
        self.assertTrue(results[1]['success'])
        
        # Check that the client was called twice
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 2)
    
    def test_failed_translation_evaluation(self):
        """Test handling of failed translations."""
        translations = [
            {
                'success': False,
                'error': 'Translation failed',
                'original_text': 'Hello world',
                'source_language': 'English',
                'target_language': 'Spanish'
            }
        ]
        
        results = self.evaluator.batch_evaluate(translations)
        
        # Check that we got a result
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]['success'])
        self.assertEqual(results[0]['error'], 'Cannot evaluate failed translation')
        
        # Check that the client was not called
        self.mock_client.chat.completions.create.assert_not_called()
    
    def test_client_error_handling(self):
        """Test handling of client errors."""
        # Make the client raise an exception
        self.mock_client.chat.completions.create.side_effect = Exception("API error")
        
        result = self.evaluator.evaluate_with_reference(
            translated_text="Hola mundo",
            reference_text="Hola mundo",
            source_text="Hello world"
        )
        
        # Check the result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "API error")

if __name__ == '__main__':
    unittest.main()