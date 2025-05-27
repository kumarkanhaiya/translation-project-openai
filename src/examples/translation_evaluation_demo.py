#!/usr/bin/env python3
"""
Translation evaluation demo script.

This script demonstrates how to use the OpenAITranslator and TranslationEvaluator
together to translate text and evaluate the quality of translations.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import sys
import time

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translators.openai_translator import OpenAITranslator
from evaluators.translation_evaluator import TranslationEvaluator

def main():
    """Run the translation evaluation demo."""
    # Load environment variables
    load_dotenv()
    
    # Initialize the OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Initialize translator and evaluator
    translator = OpenAITranslator(model="gpt-3.5-turbo")
    evaluator = TranslationEvaluator(client=client, eval_model="gpt-4o")
    
    # Sample texts with reference translations (gold standard)
    test_cases = [
        {
            "source_text": "The artificial intelligence revolution has transformed many industries.",
            "source_lang": "English",
            "target_lang": "Spanish",
            "reference": "La revolución de la inteligencia artificial ha transformado muchas industrias."
        },
        {
            "source_text": "Climate change poses significant challenges to global ecosystems.",
            "source_lang": "English",
            "target_lang": "French",
            "reference": "Le changement climatique pose des défis importants aux écosystèmes mondiaux."
        }
    ]
    
    print("=== Translation Evaluation Demo ===\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"Source ({test['source_lang']}): {test['source_text']}")
        print(f"Reference ({test['target_lang']}): {test['reference']}")
        
        # Perform translation
        translation = translator.translate(
            text=test['source_text'],
            source_lang=test['source_lang'],
            target_lang=test['target_lang']
        )
        
        print(f"Translation: {translation['translated_text']}")
        print(f"Translation time: {translation['translation_time']}s")
        
        # Evaluate with reference
        eval_result = evaluator.evaluate_with_reference(
            translated_text=translation['translated_text'],
            reference_text=test['reference'],
            source_text=test['source_text']
        )
        
        if eval_result['success']:
            print("\nEvaluation Results:")
            evaluation = json.loads(eval_result['evaluation'])
            print(f"Accuracy: {evaluation.get('Accuracy', 'N/A')}/10")
            print(f"Fluency: {evaluation.get('Fluency', 'N/A')}/10")
            print(f"Overall: {evaluation.get('Overall quality', 'N/A')}/10")
            print(f"Explanation: {evaluation.get('explanation', 'N/A')}")
        else:
            print(f"Evaluation failed: {eval_result.get('error', 'Unknown error')}")
        
        print("\n" + "-" * 50 + "\n")
    
    # Demonstrate batch translation and evaluation
    print("Batch Translation and Evaluation:")
    source_texts = [test["source_text"] for test in test_cases]
    source_lang = "English"
    target_lang = "German"
    
    # Batch translate
    translations = translator.batch_translate(
        texts=source_texts,
        source_lang=source_lang,
        target_lang=target_lang
    )
    
    # Batch evaluate (without references)
    evaluations = evaluator.batch_evaluate(translations)
    
    for i, (translation, evaluation) in enumerate(zip(translations, evaluations), 1):
        print(f"\nBatch Item {i}:")
        print(f"Source: {translation['original_text']}")
        print(f"Translation: {translation['translated_text']}")
        
        if evaluation['success']:
            eval_data = json.loads(evaluation['evaluation'])
            print(f"Quality Score: {eval_data.get('Overall quality', 'N/A')}/10")
        else:
            print(f"Evaluation failed: {evaluation.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()