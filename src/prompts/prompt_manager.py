#!/usr/bin/env python3
"""
Centralized prompt management system for the OpenAI Translation Project.

This module provides a clean interface for managing all prompts used across
the translation and evaluation components, making them easier to maintain,
version, and optimize.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PromptType(Enum):
    """Enumeration of different prompt types."""
    TRANSLATION_SYSTEM = "translation_system"
    TRANSLATION_USER = "translation_user"
    EVALUATION_SYSTEM_WITH_REFERENCE = "evaluation_system_with_reference"
    EVALUATION_SYSTEM_WITHOUT_REFERENCE = "evaluation_system_without_reference"
    EVALUATION_SYSTEM_WITH_CONTEXT = "evaluation_system_with_context"
    EVALUATION_USER_WITH_REFERENCE = "evaluation_user_with_reference"
    EVALUATION_USER_WITHOUT_REFERENCE = "evaluation_user_without_reference"
    EVALUATION_USER_WITH_CONTEXT = "evaluation_user_with_context"


@dataclass
class PromptTemplate:
    """Template for storing prompt information."""
    content: str
    description: str
    variables: list
    version: str = "1.0"


class PromptManager:
    """
    Centralized manager for all prompts used in the translation system.
    
    Features:
    - Centralized prompt storage
    - Template variable substitution
    - Version management
    - Easy prompt updates and A/B testing
    """
    
    def __init__(self):
        """Initialize the prompt manager with all prompts."""
        self._prompts = self._initialize_prompts()
    
    def _initialize_prompts(self) -> Dict[PromptType, PromptTemplate]:
        """Initialize all prompts used in the system."""
        return {
            # Translation Prompts
            PromptType.TRANSLATION_SYSTEM: PromptTemplate(
                content="You are a professional translator. Provide accurate, natural translations that preserve the meaning and tone of the original text.",
                description="System prompt for translation tasks",
                variables=[],
                version="1.0"
            ),
            
            PromptType.TRANSLATION_USER: PromptTemplate(
                content="Translate the following text from {source_lang} to {target_lang}:\n\n{text}{context_section}\n\nProvide only the translation, nothing else.",
                description="User prompt for translation with optional context",
                variables=["source_lang", "target_lang", "text", "context_section"],
                version="1.0"
            ),
            
            # Evaluation Prompts - With Reference
            PromptType.EVALUATION_SYSTEM_WITH_REFERENCE: PromptTemplate(
                content="""You are a professional translation evaluator fluent in both {source_lang} and {target_lang}.
Assess the quality of the machine translation compared to the reference translation.

Score on a scale of 1-10 for:
1. Accuracy (meaning preservation compared to reference)
2. Fluency (natural {target_lang} usage)
3. Terminology (appropriate use of domain-specific terms)
4. Overall quality

Provide only JSON output with these scores and a brief explanation.""",
                description="System prompt for evaluation with reference translation",
                variables=["source_lang", "target_lang"],
                version="1.0"
            ),
            
            PromptType.EVALUATION_USER_WITH_REFERENCE: PromptTemplate(
                content="Source text: {source_text}\n\nMachine translation: {translated_text}\n\nReference translation: {reference_text}",
                description="User prompt for evaluation with reference",
                variables=["source_text", "translated_text", "reference_text"],
                version="1.0"
            ),
            
            # Evaluation Prompts - Without Reference
            PromptType.EVALUATION_SYSTEM_WITHOUT_REFERENCE: PromptTemplate(
                content="""You are a professional translation evaluator fluent in both {source_lang} and {target_lang}.
Assess the quality of the machine translation from {source_lang} to {target_lang}.

Score on a scale of 1-10 for:
1. Accuracy (meaning preservation)
2. Fluency (natural {target_lang} usage)
3. Terminology (appropriate use of domain-specific terms)
4. Overall quality

Provide only JSON output with these scores and a brief explanation.""",
                description="System prompt for evaluation without reference",
                variables=["source_lang", "target_lang"],
                version="1.0"
            ),
            
            PromptType.EVALUATION_USER_WITHOUT_REFERENCE: PromptTemplate(
                content="Source text ({source_lang}): {source_text}\n\nMachine translation ({target_lang}): {translated_text}",
                description="User prompt for evaluation without reference",
                variables=["source_lang", "target_lang", "source_text", "translated_text"],
                version="1.0"
            ),
            
            # Evaluation Prompts - With Context
            PromptType.EVALUATION_SYSTEM_WITH_CONTEXT: PromptTemplate(
                content="""You are a professional translation evaluator fluent in both {source_lang} and {target_lang}.
Assess the quality of the machine translation from {source_lang} to {target_lang}.
The translation should accurately reflect the meaning of the source text while using appropriate terminology from the provided context.

Score on a scale of 1-10 for:
1. Accuracy (meaning preservation)
2. Fluency (natural {target_lang} usage)
3. Context Relevance (appropriate use of domain-specific terminology from context)
4. Overall quality

Provide only JSON output with these scores and a brief explanation.""",
                description="System prompt for evaluation with context",
                variables=["source_lang", "target_lang"],
                version="1.0"
            ),
            
            PromptType.EVALUATION_USER_WITH_CONTEXT: PromptTemplate(
                content="Source text ({source_lang}): {source_text}\n\nMachine translation ({target_lang}): {translated_text}\n\nContext: {context}",
                description="User prompt for evaluation with context",
                variables=["source_lang", "target_lang", "source_text", "translated_text", "context"],
                version="1.0"
            ),
        }
    
    def get_prompt(self, prompt_type: PromptType, **kwargs) -> str:
        """
        Get a formatted prompt with variable substitution.
        
        Args:
            prompt_type: Type of prompt to retrieve
            **kwargs: Variables to substitute in the prompt template
            
        Returns:
            Formatted prompt string
            
        Raises:
            KeyError: If prompt type doesn't exist
            ValueError: If required variables are missing
        """
        if prompt_type not in self._prompts:
            raise KeyError(f"Prompt type {prompt_type} not found")
        
        template = self._prompts[prompt_type]
        
        # Check for missing required variables
        missing_vars = set(template.variables) - set(kwargs.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables for {prompt_type}: {missing_vars}")
        
        # Format the prompt
        try:
            return template.content.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Error formatting prompt {prompt_type}: {e}")
    
    def get_translation_prompts(
        self, 
        source_lang: str, 
        target_lang: str, 
        text: str, 
        context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get formatted translation prompts (system and user).
        
        Args:
            source_lang: Source language name
            target_lang: Target language name
            text: Text to translate
            context: Optional context for translation
            
        Returns:
            Dict with 'system' and 'user' prompts
        """
        # Prepare context section
        context_section = ""
        if context:
            context_section = f"\n\nContext for this translation: {context}\nUse this context to ensure accurate translation of domain-specific terms and concepts."
        
        return {
            "system": self.get_prompt(PromptType.TRANSLATION_SYSTEM),
            "user": self.get_prompt(
                PromptType.TRANSLATION_USER,
                source_lang=source_lang,
                target_lang=target_lang,
                text=text,
                context_section=context_section
            )
        }
    
    def get_evaluation_prompts_with_reference(
        self,
        source_lang: str,
        target_lang: str,
        source_text: str,
        translated_text: str,
        reference_text: str
    ) -> Dict[str, str]:
        """Get formatted evaluation prompts for reference-based evaluation."""
        return {
            "system": self.get_prompt(
                PromptType.EVALUATION_SYSTEM_WITH_REFERENCE,
                source_lang=source_lang,
                target_lang=target_lang
            ),
            "user": self.get_prompt(
                PromptType.EVALUATION_USER_WITH_REFERENCE,
                source_text=source_text,
                translated_text=translated_text,
                reference_text=reference_text
            )
        }
    
    def get_evaluation_prompts_without_reference(
        self,
        source_lang: str,
        target_lang: str,
        source_text: str,
        translated_text: str
    ) -> Dict[str, str]:
        """Get formatted evaluation prompts for evaluation without reference."""
        return {
            "system": self.get_prompt(
                PromptType.EVALUATION_SYSTEM_WITHOUT_REFERENCE,
                source_lang=source_lang,
                target_lang=target_lang
            ),
            "user": self.get_prompt(
                PromptType.EVALUATION_USER_WITHOUT_REFERENCE,
                source_lang=source_lang,
                target_lang=target_lang,
                source_text=source_text,
                translated_text=translated_text
            )
        }
    
    def get_evaluation_prompts_with_context(
        self,
        source_lang: str,
        target_lang: str,
        source_text: str,
        translated_text: str,
        context: str
    ) -> Dict[str, str]:
        """Get formatted evaluation prompts for context-based evaluation."""
        return {
            "system": self.get_prompt(
                PromptType.EVALUATION_SYSTEM_WITH_CONTEXT,
                source_lang=source_lang,
                target_lang=target_lang
            ),
            "user": self.get_prompt(
                PromptType.EVALUATION_USER_WITH_CONTEXT,
                source_lang=source_lang,
                target_lang=target_lang,
                source_text=source_text,
                translated_text=translated_text,
                context=context
            )
        }
    
    def list_prompts(self) -> Dict[str, Dict[str, Any]]:
        """List all available prompts with their metadata."""
        return {
            prompt_type.value: {
                "description": template.description,
                "variables": template.variables,
                "version": template.version,
                "content_preview": template.content[:100] + "..." if len(template.content) > 100 else template.content
            }
            for prompt_type, template in self._prompts.items()
        }
    
    def update_prompt(self, prompt_type: PromptType, content: str, description: str = None, version: str = None):
        """
        Update an existing prompt.
        
        Args:
            prompt_type: Type of prompt to update
            content: New prompt content
            description: Optional new description
            version: Optional new version
        """
        if prompt_type not in self._prompts:
            raise KeyError(f"Prompt type {prompt_type} not found")
        
        template = self._prompts[prompt_type]
        template.content = content
        if description:
            template.description = description
        if version:
            template.version = version


# Global instance for easy access
prompt_manager = PromptManager()
