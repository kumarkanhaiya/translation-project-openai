#!/usr/bin/env python3
"""
Prompt Manager Demo Script.

This script demonstrates the centralized prompt management system,
showing how prompts are organized and can be easily accessed and modified.
"""

import sys
import os
import json

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.prompt_manager import prompt_manager, PromptType

def main():
    """Demonstrate the prompt manager functionality."""
    print("=== Prompt Manager Demo ===\n")
    
    # 1. List all available prompts
    print("1. Available Prompts:")
    print("-" * 40)
    prompts_info = prompt_manager.list_prompts()
    for prompt_name, info in prompts_info.items():
        print(f"📝 {prompt_name}")
        print(f"   Description: {info['description']}")
        print(f"   Variables: {info['variables']}")
        print(f"   Version: {info['version']}")
        print(f"   Preview: {info['content_preview']}")
        print()
    
    # 2. Demonstrate translation prompts
    print("2. Translation Prompts Example:")
    print("-" * 40)
    translation_prompts = prompt_manager.get_translation_prompts(
        source_lang="English",
        target_lang="Spanish",
        text="The patient has elevated blood pressure.",
        context="Medical consultation notes"
    )
    
    print("System Prompt:")
    print(f"'{translation_prompts['system']}'")
    print("\nUser Prompt:")
    print(f"'{translation_prompts['user']}'")
    print()
    
    # 3. Demonstrate evaluation prompts with context
    print("3. Evaluation Prompts (With Context) Example:")
    print("-" * 40)
    eval_prompts = prompt_manager.get_evaluation_prompts_with_context(
        source_lang="English",
        target_lang="Spanish",
        source_text="The patient has elevated blood pressure.",
        translated_text="El paciente tiene presión arterial elevada.",
        context="Medical consultation notes"
    )
    
    print("System Prompt:")
    print(f"'{eval_prompts['system']}'")
    print("\nUser Prompt:")
    print(f"'{eval_prompts['user']}'")
    print()
    
    # 4. Demonstrate evaluation prompts with reference
    print("4. Evaluation Prompts (With Reference) Example:")
    print("-" * 40)
    ref_eval_prompts = prompt_manager.get_evaluation_prompts_with_reference(
        source_lang="English",
        target_lang="Spanish",
        source_text="Hello, how are you?",
        translated_text="Hola, ¿cómo estás?",
        reference_text="Hola, ¿cómo está usted?"
    )
    
    print("System Prompt:")
    print(f"'{ref_eval_prompts['system']}'")
    print("\nUser Prompt:")
    print(f"'{ref_eval_prompts['user']}'")
    print()
    
    # 5. Demonstrate individual prompt access
    print("5. Individual Prompt Access:")
    print("-" * 40)
    try:
        individual_prompt = prompt_manager.get_prompt(
            PromptType.TRANSLATION_SYSTEM
        )
        print(f"Translation System Prompt: '{individual_prompt}'")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # 6. Demonstrate prompt customization
    print("6. Prompt Customization Example:")
    print("-" * 40)
    print("Original translation system prompt:")
    original = prompt_manager.get_prompt(PromptType.TRANSLATION_SYSTEM)
    print(f"'{original}'")
    
    # Update the prompt
    prompt_manager.update_prompt(
        PromptType.TRANSLATION_SYSTEM,
        "You are an expert professional translator with deep knowledge of cultural nuances. Provide accurate, culturally-aware translations that preserve meaning, tone, and context.",
        description="Enhanced system prompt for translation with cultural awareness",
        version="2.0"
    )
    
    print("\nUpdated translation system prompt:")
    updated = prompt_manager.get_prompt(PromptType.TRANSLATION_SYSTEM)
    print(f"'{updated}'")
    
    # Restore original
    prompt_manager.update_prompt(
        PromptType.TRANSLATION_SYSTEM,
        original,
        description="System prompt for translation tasks",
        version="1.0"
    )
    print("\n✅ Prompt restored to original")
    
    print("\n" + "=" * 60)
    print("🎯 Key Benefits of Centralized Prompt Management:")
    print("   • Easy to update and maintain prompts")
    print("   • Consistent prompt formatting across components")
    print("   • Version control for prompt changes")
    print("   • Template variable validation")
    print("   • A/B testing capabilities")
    print("   • Centralized prompt documentation")

if __name__ == "__main__":
    main()
