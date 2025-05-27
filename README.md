# OpenAI Translation Project

A sophisticated context-aware translation system powered by OpenAI's GPT models, featuring automatic quality evaluation and intelligent retry mechanisms.

## 🚀 Features

- **Context-Aware Translation**: Uses domain-specific context to improve translation accuracy
- **Quality Evaluation**: Multi-dimensional scoring (Accuracy, Fluency, Context Relevance)
- **Automatic Retry Logic**: Retries translations below quality threshold
- **Multi-Domain Support**: Optimized for medical, legal, and technical translations
- **Comprehensive Reporting**: Detailed metrics and explanations for each translation
- **Model Separation**: Uses different models for translation and evaluation to prevent bias

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Required packages (see `requirements.txt`)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd translation-project-openai
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # Windows
   # or
   source .venv/bin/activate      # macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## 🔧 Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 🎯 Usage

### Basic Translation

```python
from translators.context_aware_translator import ContextAwareTranslator
from openai import OpenAI

client = OpenAI(api_key="your-api-key")
translator = ContextAwareTranslator(
    client=client,
    translation_model="gpt-3.5-turbo",
    evaluation_model="gpt-4o",
    quality_threshold=8.5
)

result = translator.translate(
    text="The patient presents with elevated troponin levels.",
    source_lang="English",
    target_lang="Spanish",
    context="Medical cardiology report"
)

print(f"Translation: {result['translated_text']}")
print(f"Quality Score: {result['quality_score']}/10")
```

### Running Demo

```bash
PYTHONPATH=src python src/examples/context_aware_translation_demo.py
```

## 🧪 Testing

Run the test suite:

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

## 📁 Project Structure

```
translation-project-openai/
├── src/
│   ├── translators/
│   │   ├── openai_translator.py
│   │   └── context_aware_translator.py
│   ├── evaluators/
│   │   └── translation_evaluator.py
│   └── examples/
│       ├── context_aware_translation_demo.py
│       └── translation_evaluation_demo.py
├── tests/
│   ├── test_context_aware_translator.py
│   └── test_translation_evaluator.py
├── requirements.txt
└── README.md
```

## 🎨 Key Components

### ContextAwareTranslator
- Main translation orchestrator
- Handles retry logic and quality control
- Integrates translation and evaluation components

### OpenAITranslator
- Core translation functionality using OpenAI API
- Supports context-aware prompting
- Configurable temperature and model selection

### TranslationEvaluator
- Multi-dimensional quality assessment
- Context-aware evaluation
- Batch processing capabilities

## 📊 Performance

- **Medical translations**: 10/10 average quality
- **Legal translations**: 9/10 average quality  
- **Technical translations**: Variable (6-9/10)
- **Processing time**: 3-16 seconds depending on complexity

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Project Issues](https://github.com/your-username/translation-project-openai/issues)
