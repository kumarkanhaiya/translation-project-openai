#!/usr/bin/env python3
"""
Cost Analysis Demo Script.

This script demonstrates how to use the cost analyzer to track and analyze
translation costs, providing insights for optimization.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cost_analyzer import CostAnalyzer, TranslationCost


def simulate_translation_data(analyzer: CostAnalyzer):
    """Simulate some translation data for demonstration."""
    print("📊 Simulating translation data...")
    
    # Simulate various translation scenarios
    scenarios = [
        # Medical translations (higher quality, more expensive)
        {
            "translation_result": {
                "original_text": "The patient presents with elevated troponin levels.",
                "translated_text": "El paciente presenta niveles elevados de troponina.",
                "source_language": "English",
                "target_language": "Spanish",
                "tokens_used": 85,
                "model_used": "gpt-3.5-turbo",
                "quality_score": 9.5,
                "attempts_count": 1,
                "cache_hit": False
            },
            "evaluation_result": {
                "tokens_used": 120,
                "eval_model": "gpt-4o"
            },
            "domain": "medical"
        },
        
        # Legal translations (complex, multiple attempts)
        {
            "translation_result": {
                "original_text": "The defendant moved to dismiss the case based on lack of standing.",
                "translated_text": "Le défendeur a demandé le rejet du dossier pour défaut de qualité pour agir.",
                "source_language": "English", 
                "target_language": "French",
                "tokens_used": 95,
                "model_used": "gpt-3.5-turbo",
                "quality_score": 8.8,
                "attempts_count": 2,
                "cache_hit": False
            },
            "evaluation_result": {
                "tokens_used": 140,
                "eval_model": "gpt-4o"
            },
            "domain": "legal"
        },
        
        # Technical translations (challenging, multiple retries)
        {
            "translation_result": {
                "original_text": "The model exhibits high perplexity when evaluated on out-of-distribution data.",
                "translated_text": "Das Modell zeigt eine hohe Verwirrung bei der Bewertung von Out-of-Distribution-Daten.",
                "source_language": "English",
                "target_language": "German", 
                "tokens_used": 110,
                "model_used": "gpt-3.5-turbo",
                "quality_score": 6.2,
                "attempts_count": 3,
                "cache_hit": False
            },
            "evaluation_result": {
                "tokens_used": 160,
                "eval_model": "gpt-4o"
            },
            "domain": "technical"
        },
        
        # Cached translation (very cheap)
        {
            "translation_result": {
                "original_text": "Hello, how are you?",
                "translated_text": "Hola, ¿cómo estás?",
                "source_language": "English",
                "target_language": "Spanish",
                "tokens_used": 0,  # No tokens used for cached result
                "model_used": "gpt-3.5-turbo",
                "quality_score": 9.0,
                "attempts_count": 1,
                "cache_hit": True
            },
            "evaluation_result": None,  # No evaluation for cached result
            "domain": "general"
        },
        
        # Simple general translations
        {
            "translation_result": {
                "original_text": "Good morning, have a nice day!",
                "translated_text": "Buongiorno, buona giornata!",
                "source_language": "English",
                "target_language": "Italian",
                "tokens_used": 65,
                "model_used": "gpt-3.5-turbo",
                "quality_score": 8.5,
                "attempts_count": 1,
                "cache_hit": False
            },
            "evaluation_result": {
                "tokens_used": 90,
                "eval_model": "gpt-4o"
            },
            "domain": "general"
        }
    ]
    
    # Record multiple instances of each scenario to simulate usage
    for scenario in scenarios:
        for _ in range(3):  # Simulate 3 instances of each
            analyzer.record_translation(
                scenario["translation_result"],
                scenario["evaluation_result"],
                scenario["domain"]
            )
    
    print(f"✅ Simulated {len(scenarios) * 3} translation operations")


def main():
    """Run the cost analysis demo."""
    print("=== Cost Analysis Demo ===\n")
    
    # Initialize cost analyzer
    analyzer = CostAnalyzer()
    
    # Simulate some translation data
    simulate_translation_data(analyzer)
    
    # 1. Show daily summary
    print("\n1. Daily Cost Summary:")
    print("-" * 40)
    today = datetime.utcnow().strftime('%Y-%m-%d')
    daily_summary = analyzer.get_daily_summary(today)
    
    for key, value in daily_summary.items():
        if key == "date":
            continue
        formatted_key = key.replace('_', ' ').title()
        if 'cost' in key and isinstance(value, (int, float)):
            print(f"{formatted_key}: ${value}")
        elif 'rate' in key:
            print(f"{formatted_key}: {value}%")
        else:
            print(f"{formatted_key}: {value}")
    
    # 2. Domain analysis
    print("\n2. Domain Cost Analysis:")
    print("-" * 40)
    domain_analysis = analyzer.get_domain_analysis()
    
    for domain, stats in domain_analysis.items():
        print(f"\n📁 {domain.title()} Domain:")
        print(f"   Translations: {stats['count']}")
        print(f"   Total Cost: ${stats['total_cost']}")
        print(f"   Average Cost: ${stats['avg_cost']}")
        print(f"   Average Quality: {stats['avg_quality']}/10")
        print(f"   Average Attempts: {stats['avg_attempts']}")
    
    # 3. Cost optimization suggestions
    print("\n3. Cost Optimization Suggestions:")
    print("-" * 40)
    suggestions = analyzer.get_cost_optimization_suggestions()
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")
    
    # 4. Model pricing information
    print("\n4. Current Model Pricing (per 1K tokens):")
    print("-" * 40)
    for model, pricing in analyzer.model_pricing.items():
        print(f"{model}:")
        print(f"   Input: ${pricing['input']}")
        print(f"   Output: ${pricing['output']}")
    
    # 5. Generate comprehensive report
    print("\n5. Comprehensive Cost Report:")
    print("-" * 40)
    report = analyzer.generate_report()
    print(report)
    
    # 6. Export data demonstration
    print("\n6. Data Export Example:")
    print("-" * 40)
    
    # Export to CSV
    csv_filename = f"cost_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    analyzer.export_to_csv(csv_filename)
    
    # Show file info
    if os.path.exists(csv_filename):
        file_size = os.path.getsize(csv_filename)
        print(f"📄 CSV file created: {csv_filename} ({file_size} bytes)")
        
        # Clean up demo file
        os.remove(csv_filename)
        print("🗑️ Demo file cleaned up")
    
    # 7. Cost calculation examples
    print("\n7. Cost Calculation Examples:")
    print("-" * 40)
    
    examples = [
        {"tokens": 100, "model": "gpt-3.5-turbo", "description": "Simple translation"},
        {"tokens": 250, "model": "gpt-4o", "description": "Quality evaluation"},
        {"tokens": 500, "model": "gpt-4-turbo", "description": "Complex translation"},
    ]
    
    for example in examples:
        cost = analyzer.calculate_cost(example["tokens"], example["model"])
        print(f"{example['description']}: {example['tokens']} tokens with {example['model']} = ${cost}")
    
    print("\n" + "=" * 60)
    print("🎯 Key Insights from Cost Analysis:")
    print("   • Medical translations: High quality, reasonable cost")
    print("   • Legal translations: Good quality, moderate cost")
    print("   • Technical translations: Challenging, higher cost due to retries")
    print("   • Cached translations: Near-zero cost, excellent ROI")
    print("   • GPT-4o evaluation adds significant cost but ensures quality")
    print("\n💡 Optimization Recommendations:")
    print("   • Implement caching for frequently translated content")
    print("   • Use GPT-3.5-turbo for translation, GPT-4o for evaluation")
    print("   • Consider domain-specific quality thresholds")
    print("   • Monitor retry rates and adjust prompts accordingly")


if __name__ == "__main__":
    main()
