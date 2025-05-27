# OpenAI Token Counting and Cost Analysis

This document provides comprehensive information about token usage and associated costs in the OpenAI Translation Project.

## 📊 Overview

The translation system uses OpenAI's API for both translation and evaluation, which incurs costs based on token usage. Understanding these costs is crucial for budgeting and optimization.

## 🔢 Token Basics

### What are Tokens?
- **Tokens** are pieces of words used by OpenAI models
- Roughly **4 characters = 1 token** for English text
- **1 word ≈ 1.3 tokens** on average
- Special characters, punctuation, and spaces count as tokens

### Token Counting Examples
```
"Hello world" = 2 tokens
"The patient has elevated blood pressure." = 7 tokens
"Translate from English to Spanish" = 6 tokens
```

## 💰 Current Pricing (as of 2024)

### GPT-3.5-turbo (Translation Model)
- **Input tokens**: $0.0015 per 1K tokens
- **Output tokens**: $0.002 per 1K tokens
- **Average cost per translation**: $0.001 - $0.005

### GPT-4o (Evaluation Model)
- **Input tokens**: $0.0025 per 1K tokens  
- **Output tokens**: $0.01 per 1K tokens
- **Average cost per evaluation**: $0.005 - $0.015

### GPT-4-turbo (Alternative)
- **Input tokens**: $0.01 per 1K tokens
- **Output tokens**: $0.03 per 1K tokens
- **Average cost per operation**: $0.01 - $0.05

## 📈 Cost Breakdown by Operation

### Single Translation (No Retries)
```
Operation: Translate "Hello, how are you?" (EN → ES)
├── Translation (GPT-3.5-turbo)
│   ├── Input: ~50 tokens (system + user prompt)
│   ├── Output: ~10 tokens (translation)
│   └── Cost: ~$0.0001
├── Evaluation (GPT-4o)
│   ├── Input: ~80 tokens (system + evaluation prompt)
│   ├── Output: ~50 tokens (JSON evaluation)
│   └── Cost: ~$0.0007
└── Total Cost: ~$0.0008
```

### Complex Translation with Retries
```
Operation: Technical translation with 3 attempts
├── Translation Attempts (3x GPT-3.5-turbo)
│   ├── Input: ~150 tokens × 3 = 450 tokens
│   ├── Output: ~30 tokens × 3 = 90 tokens
│   └── Cost: ~$0.0009
├── Evaluations (3x GPT-4o)
│   ├── Input: ~120 tokens × 3 = 360 tokens
│   ├── Output: ~60 tokens × 3 = 180 tokens
│   └── Cost: ~$0.0027
└── Total Cost: ~$0.0036
```

## 📋 Token Usage Patterns

### By Text Length
| Text Length | Avg Tokens | Translation Cost | Evaluation Cost | Total Cost |
|-------------|------------|------------------|-----------------|------------|
| Short (1-10 words) | 15-50 | $0.0001 | $0.0005 | $0.0006 |
| Medium (11-50 words) | 50-150 | $0.0003 | $0.0012 | $0.0015 |
| Long (51-200 words) | 150-500 | $0.0008 | $0.0035 | $0.0043 |
| Very Long (200+ words) | 500+ | $0.002+ | $0.008+ | $0.010+ |

### By Domain Complexity
| Domain | Context Length | Avg Total Cost | Retry Rate |
|--------|----------------|----------------|------------|
| **Simple/General** | Short | $0.0008 | 10% |
| **Medical** | Medium | $0.0015 | 15% |
| **Legal** | Long | $0.0025 | 20% |
| **Technical** | Long | $0.0035 | 35% |

## 🎯 Cost Optimization Strategies

### 1. Model Selection
```python
# Cost-effective setup
translator = ContextAwareTranslator(
    translation_model="gpt-3.5-turbo",  # Cheaper for translation
    evaluation_model="gpt-4o",          # Better quality evaluation
    quality_threshold=8.0               # Balanced threshold
)

# Premium setup (higher cost, better quality)
translator = ContextAwareTranslator(
    translation_model="gpt-4o",         # Higher quality translation
    evaluation_model="gpt-4o",          # Consistent evaluation
    quality_threshold=9.0               # Higher quality bar
)
```

### 2. Retry Configuration
```python
# Conservative (lower cost)
translator = ContextAwareTranslator(
    quality_threshold=7.5,  # Lower threshold = fewer retries
    max_retries=1           # Limit retry attempts
)

# Aggressive (higher cost, better quality)
translator = ContextAwareTranslator(
    quality_threshold=9.0,  # Higher threshold = more retries
    max_retries=3           # More retry attempts
)
```

### 3. Batch Processing
```python
# More efficient for multiple translations
results = translator.batch_translate(
    texts=["Text 1", "Text 2", "Text 3"],
    source_lang="English",
    target_lang="Spanish"
)
# Saves on repeated context setup
```

## 📊 Real Usage Examples

### Demo Script Costs
Running the context-aware demo (3 translations):
```
Test Case 1 (Medical): $0.0012
Test Case 2 (Legal): $0.0015  
Test Case 3 (Technical, 3 retries): $0.0045
Total Demo Cost: ~$0.0072
```

### Monthly Usage Estimates
| Usage Level | Translations/Month | Estimated Cost |
|-------------|-------------------|----------------|
| **Light** | 100 | $0.10 - $0.50 |
| **Medium** | 1,000 | $1.00 - $5.00 |
| **Heavy** | 10,000 | $10.00 - $50.00 |
| **Enterprise** | 100,000 | $100.00 - $500.00 |

## 🔍 Monitoring and Tracking

### Built-in Cost Tracking
The system automatically tracks costs:
```python
result = translator.translate(...)
print(f"Translation cost: ${result['cost_estimate']}")
print(f"Tokens used: {result['tokens_used']}")
```

### Cost Monitoring Script
```python
def track_daily_costs():
    total_cost = 0
    total_tokens = 0
    
    for translation in daily_translations:
        total_cost += translation['cost_estimate']
        total_tokens += translation['tokens_used']
    
    print(f"Daily cost: ${total_cost:.4f}")
    print(f"Daily tokens: {total_tokens}")
```

## ⚠️ Cost Considerations

### High-Cost Scenarios
- **Technical translations** with many retries
- **Long documents** (500+ words)
- **High quality thresholds** (9.0+)
- **Premium models** (GPT-4 for translation)

### Cost-Saving Tips
1. **Use appropriate quality thresholds** (8.0-8.5 is usually sufficient)
2. **Limit retries** for non-critical translations
3. **Batch similar translations** together
4. **Use GPT-3.5-turbo** for translation when possible
5. **Monitor token usage** regularly

## 📈 Scaling Considerations

### For Production Use
- Implement **rate limiting** to control costs
- Set up **budget alerts** for monthly spending
- Use **caching** for repeated translations
- Consider **fine-tuning** for domain-specific use cases

### Cost Budgeting Formula
```
Monthly Budget = (Translations/month) × (Avg tokens/translation) × (Cost/token) × (Retry multiplier)

Example:
$50/month = 5,000 translations × 100 tokens × $0.001/token × 1.2 retry factor
```

## 🔗 Additional Resources

- [OpenAI Pricing Page](https://openai.com/pricing)
- [Token Counting Tool](https://platform.openai.com/tokenizer)
- [OpenAI Usage Dashboard](https://platform.openai.com/usage)

## 📝 Notes

- Prices are subject to change by OpenAI
- Costs include both input and output tokens
- Evaluation typically costs 3-5x more than translation
- Context length affects total token count
- Retry logic can significantly impact costs

---

*Last updated: December 2024*
*Prices based on OpenAI's current pricing as of December 2024*
