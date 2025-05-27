#!/usr/bin/env python3
"""
Cost Analysis Utility for OpenAI Translation System.

This module provides tools to analyze and track costs associated with
translation operations, helping optimize spending and monitor usage patterns.
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class TranslationCost:
    """Data class for tracking individual translation costs."""
    timestamp: str
    source_lang: str
    target_lang: str
    text_length: int
    tokens_used: int
    translation_cost: float
    evaluation_cost: float
    total_cost: float
    model_used: str
    quality_score: float
    attempts: int
    cache_hit: bool = False
    domain: str = "general"


class CostAnalyzer:
    """
    Analyzes and tracks translation costs for optimization insights.
    
    Features:
    - Track individual translation costs
    - Generate cost reports and analytics
    - Identify cost optimization opportunities
    - Monitor spending patterns
    - Export data for further analysis
    """
    
    def __init__(self):
        """Initialize the cost analyzer."""
        self.cost_records: List[TranslationCost] = []
        self.model_pricing = {
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            'gpt-4o': {'input': 0.0025, 'output': 0.01},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4': {'input': 0.03, 'output': 0.06}
        }
    
    def calculate_cost(self, tokens_used: int, model: str, 
                      input_ratio: float = 0.7) -> float:
        """
        Calculate cost based on token usage and model.
        
        Args:
            tokens_used: Total tokens consumed
            model: Model name used
            input_ratio: Ratio of input to total tokens (default 0.7)
            
        Returns:
            Estimated cost in USD
        """
        if model not in self.model_pricing:
            return 0.0
        
        pricing = self.model_pricing[model]
        input_tokens = int(tokens_used * input_ratio)
        output_tokens = tokens_used - input_tokens
        
        cost = (input_tokens / 1000 * pricing['input'] + 
                output_tokens / 1000 * pricing['output'])
        
        return round(cost, 6)
    
    def record_translation(self, translation_result: Dict[str, Any], 
                          evaluation_result: Optional[Dict[str, Any]] = None,
                          domain: str = "general") -> None:
        """
        Record a translation operation for cost tracking.
        
        Args:
            translation_result: Result from translation operation
            evaluation_result: Result from evaluation operation
            domain: Domain category (medical, legal, technical, etc.)
        """
        # Calculate costs
        translation_tokens = translation_result.get('tokens_used', 0)
        translation_model = translation_result.get('model_used', 'gpt-3.5-turbo')
        translation_cost = self.calculate_cost(translation_tokens, translation_model)
        
        evaluation_cost = 0.0
        if evaluation_result:
            eval_tokens = evaluation_result.get('tokens_used', 0)
            eval_model = evaluation_result.get('eval_model', 'gpt-4o')
            evaluation_cost = self.calculate_cost(eval_tokens, eval_model)
        
        # Create cost record
        cost_record = TranslationCost(
            timestamp=datetime.utcnow().isoformat(),
            source_lang=translation_result.get('source_language', ''),
            target_lang=translation_result.get('target_language', ''),
            text_length=len(translation_result.get('original_text', '')),
            tokens_used=translation_tokens + evaluation_result.get('tokens_used', 0) if evaluation_result else translation_tokens,
            translation_cost=translation_cost,
            evaluation_cost=evaluation_cost,
            total_cost=translation_cost + evaluation_cost,
            model_used=translation_model,
            quality_score=translation_result.get('quality_score', 0),
            attempts=translation_result.get('attempts_count', 1),
            cache_hit=translation_result.get('cache_hit', False),
            domain=domain
        )
        
        self.cost_records.append(cost_record)
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cost summary for a specific day.
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
            
        Returns:
            Dictionary with daily cost summary
        """
        if date is None:
            date = datetime.utcnow().strftime('%Y-%m-%d')
        
        daily_records = [
            record for record in self.cost_records
            if record.timestamp.startswith(date)
        ]
        
        if not daily_records:
            return {"date": date, "total_cost": 0, "translations": 0}
        
        total_cost = sum(record.total_cost for record in daily_records)
        translation_cost = sum(record.translation_cost for record in daily_records)
        evaluation_cost = sum(record.evaluation_cost for record in daily_records)
        cache_hits = sum(1 for record in daily_records if record.cache_hit)
        
        return {
            "date": date,
            "total_translations": len(daily_records),
            "total_cost": round(total_cost, 4),
            "translation_cost": round(translation_cost, 4),
            "evaluation_cost": round(evaluation_cost, 4),
            "cache_hits": cache_hits,
            "cache_hit_rate": round(cache_hits / len(daily_records) * 100, 1),
            "avg_cost_per_translation": round(total_cost / len(daily_records), 4),
            "total_tokens": sum(record.tokens_used for record in daily_records)
        }
    
    def get_domain_analysis(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze costs by domain category.
        
        Returns:
            Dictionary with cost analysis by domain
        """
        domain_stats = defaultdict(lambda: {
            'count': 0, 'total_cost': 0, 'total_tokens': 0,
            'avg_quality': 0, 'avg_attempts': 0
        })
        
        for record in self.cost_records:
            stats = domain_stats[record.domain]
            stats['count'] += 1
            stats['total_cost'] += record.total_cost
            stats['total_tokens'] += record.tokens_used
            stats['avg_quality'] += record.quality_score
            stats['avg_attempts'] += record.attempts
        
        # Calculate averages
        for domain, stats in domain_stats.items():
            if stats['count'] > 0:
                stats['avg_cost'] = round(stats['total_cost'] / stats['count'], 4)
                stats['avg_quality'] = round(stats['avg_quality'] / stats['count'], 1)
                stats['avg_attempts'] = round(stats['avg_attempts'] / stats['count'], 1)
                stats['total_cost'] = round(stats['total_cost'], 4)
        
        return dict(domain_stats)
    
    def get_cost_optimization_suggestions(self) -> List[str]:
        """
        Generate cost optimization suggestions based on usage patterns.
        
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        if not self.cost_records:
            return ["No data available for analysis"]
        
        # Analyze cache hit rate
        cache_hits = sum(1 for record in self.cost_records if record.cache_hit)
        cache_hit_rate = cache_hits / len(self.cost_records) * 100
        
        if cache_hit_rate < 50:
            suggestions.append(f"Low cache hit rate ({cache_hit_rate:.1f}%). Consider implementing caching system.")
        
        # Analyze retry patterns
        high_retry_records = [r for r in self.cost_records if r.attempts > 2]
        if len(high_retry_records) > len(self.cost_records) * 0.2:
            suggestions.append("High retry rate detected. Consider lowering quality threshold or improving prompts.")
        
        # Analyze model usage
        expensive_models = [r for r in self.cost_records if r.model_used in ['gpt-4', 'gpt-4-turbo']]
        if len(expensive_models) > len(self.cost_records) * 0.5:
            suggestions.append("Consider using GPT-3.5-turbo for translation and GPT-4o for evaluation only.")
        
        # Analyze domain costs
        domain_analysis = self.get_domain_analysis()
        for domain, stats in domain_analysis.items():
            if stats['avg_cost'] > 0.01:
                suggestions.append(f"High costs in {domain} domain (${stats['avg_cost']}/translation). Consider domain-specific optimization.")
        
        return suggestions if suggestions else ["Cost usage appears optimized!"]
    
    def export_to_csv(self, filename: str) -> None:
        """
        Export cost records to CSV file.
        
        Args:
            filename: Output CSV filename
        """
        if not self.cost_records:
            print("No cost records to export")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = list(asdict(self.cost_records[0]).keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in self.cost_records:
                writer.writerow(asdict(record))
        
        print(f"✅ Exported {len(self.cost_records)} records to {filename}")
    
    def load_from_csv(self, filename: str) -> None:
        """
        Load cost records from CSV file.
        
        Args:
            filename: Input CSV filename
        """
        try:
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Convert string values back to appropriate types
                    row['text_length'] = int(row['text_length'])
                    row['tokens_used'] = int(row['tokens_used'])
                    row['translation_cost'] = float(row['translation_cost'])
                    row['evaluation_cost'] = float(row['evaluation_cost'])
                    row['total_cost'] = float(row['total_cost'])
                    row['quality_score'] = float(row['quality_score'])
                    row['attempts'] = int(row['attempts'])
                    row['cache_hit'] = row['cache_hit'].lower() == 'true'
                    
                    self.cost_records.append(TranslationCost(**row))
            
            print(f"✅ Loaded {len(self.cost_records)} records from {filename}")
        except FileNotFoundError:
            print(f"❌ File {filename} not found")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive cost analysis report.
        
        Returns:
            Formatted report string
        """
        if not self.cost_records:
            return "No cost data available for analysis."
        
        total_cost = sum(record.total_cost for record in self.cost_records)
        total_translations = len(self.cost_records)
        avg_cost = total_cost / total_translations
        
        # Get recent data (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_records = [
            record for record in self.cost_records
            if datetime.fromisoformat(record.timestamp.replace('Z', '+00:00')) > week_ago
        ]
        
        cache_hits = sum(1 for record in self.cost_records if record.cache_hit)
        cache_hit_rate = cache_hits / total_translations * 100
        
        domain_analysis = self.get_domain_analysis()
        suggestions = self.get_cost_optimization_suggestions()
        
        report = f"""
📊 TRANSLATION COST ANALYSIS REPORT
{'=' * 50}

📈 OVERALL STATISTICS
Total Translations: {total_translations:,}
Total Cost: ${total_cost:.4f}
Average Cost per Translation: ${avg_cost:.4f}
Cache Hit Rate: {cache_hit_rate:.1f}%

📅 RECENT ACTIVITY (Last 7 days)
Recent Translations: {len(recent_records):,}
Recent Cost: ${sum(r.total_cost for r in recent_records):.4f}

🏷️ DOMAIN BREAKDOWN
"""
        
        for domain, stats in domain_analysis.items():
            report += f"{domain.title()}: {stats['count']} translations, ${stats['total_cost']:.4f} total, ${stats['avg_cost']:.4f} avg\n"
        
        report += f"\n💡 OPTIMIZATION SUGGESTIONS\n"
        for i, suggestion in enumerate(suggestions, 1):
            report += f"{i}. {suggestion}\n"
        
        return report


# Global cost analyzer instance
cost_analyzer = CostAnalyzer()
