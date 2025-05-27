#!/usr/bin/env python3
"""
Context-aware translation demo script.

This script demonstrates how to use the ContextAwareTranslator to translate text
with context, evaluate quality, and automatically retry low-quality translations.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import sys
import time

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translators.context_aware_translator import ContextAwareTranslator

def main():
    """Run the context-aware translation demo."""
    # Load environment variables
    load_dotenv(override=True)

    # Initialize the OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Initialize the context-aware translator
    translator = ContextAwareTranslator(
        client=client,
        translation_model="gpt-3.5-turbo",
        evaluation_model="gpt-4o",
        quality_threshold=8.5,
        max_retries=2
    )

    # Sample texts with context
    test_cases = [
        {
            "text": "The patient presents with elevated troponin levels and ST-segment elevation.",
            "source_lang": "English",
            "target_lang": "Spanish",
            "context": "Medical cardiology report discussing a patient with potential myocardial infarction."
        },
        {
            "text": "The defendant moved to dismiss the case based on lack of standing.",
            "source_lang": "English",
            "target_lang": "French",
            "context": "Legal document from a civil court proceeding discussing procedural matters."
        },
        {
            "text": "The model exhibits high perplexity when evaluated on out-of-distribution data.",
            "source_lang": "English",
            "target_lang": "German",
            "context": "Machine learning research paper discussing language model evaluation metrics."
        }
    ]

    print("=== Context-Aware Translation Demo ===\n")

    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"Source ({test['source_lang']}): {test['text']}")
        print(f"Context: {test['context']}")

        # Perform translation with context
        result = translator.translate(
            text=test['text'],
            source_lang=test['source_lang'],
            target_lang=test['target_lang'],
            context=test['context']
        )

        if result['success']:
            print(f"\nTranslation ({test['target_lang']}): {result['translated_text']}")
            print(f"Quality Score: {result['quality_score']}/10")
            print(f"Quality Status: {result['quality_status']}")
            print(f"Message: {result['message']}")
            print(f"Attempts: {result['attempts_count']}")
            print(f"Total Time: {result['total_time']}s")
        else:
            print(f"\n❌ Translation failed: {result['error']}")
            print(f"Total Time: {result['total_time']}s")
            if 'attempts' in result:
                print(f"Attempts made: {len(result['attempts'])}")

        # Show evaluation details for the final translation
        if result.get('success') and result.get('attempts'):
            final_attempt = result['attempts'][-1]
            if final_attempt['evaluation']['success']:
                evaluation = json.loads(final_attempt['evaluation']['evaluation'])
                print("\nEvaluation Details:")

                # Print all fields except explanation-related ones
                for key, value in evaluation.items():
                    if key.lower() not in ["explanation"]:
                        print(f"- {key}: {value}")

                # Print explanation (check both lowercase and capitalized versions)
                explanation = (evaluation.get('explanation') or
                             evaluation.get('Explanation') or
                             'No explanation provided')
                print(f"- Explanation: {explanation}")
            else:
                print(f"\n⚠️ Evaluation failed: {final_attempt['evaluation'].get('error', 'Unknown error')}")

        print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    main()