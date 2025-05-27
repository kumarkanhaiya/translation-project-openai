# Translation System Cost Optimization Through Caching

This document outlines a comprehensive caching and storage strategy to significantly reduce OpenAI API costs while maintaining high performance and translation quality.

## 🎯 Overview

The caching system implements a multi-tier approach to store and retrieve translation results, reducing API calls by 80-90% for frequently translated content.

## 🏗️ Architecture Design

### Multi-Tier Caching Strategy
```
User Request → Redis Cache → DynamoDB → OpenAI API
     ↓            ↓            ↓           ↓
   Instant     <1ms         <10ms      1-5s
```

## 🚀 Layer 1: Redis Cache (Primary Cache)

### Configuration
- **Service**: AWS ElastiCache for Redis
- **Purpose**: Ultra-fast in-memory storage
- **TTL**: 24-48 hours for translation results
- **Capacity**: Auto-scaling based on demand

### Benefits
- ⚡ **Sub-millisecond response times**
- 🔄 **Automatic eviction policies**
- 📈 **Distributed across multiple instances**
- ⏰ **TTL support for cache invalidation**

### Implementation
```python
import redis
import json
import hashlib

class RedisTranslationCache:
    def __init__(self, redis_endpoint):
        self.redis_client = redis.Redis(
            host=redis_endpoint,
            port=6379,
            decode_responses=True
        )

    def get_cached_translation(self, cache_key):
        """Retrieve translation from Redis cache"""
        cached_result = self.redis_client.get(cache_key)
        return json.loads(cached_result) if cached_result else None

    def cache_translation(self, cache_key, translation_data, ttl=86400):
        """Store translation in Redis with TTL"""
        self.redis_client.setex(
            cache_key,
            ttl,  # 24 hours default
            json.dumps(translation_data)
        )
```

## 🗄️ Layer 2: DynamoDB (Persistent Storage)

### Schema Design
```python
{
    "pk": "TRANSLATION#en#es#a1b2c3d4...",  # Partition Key
    "sk": "CONTEXT#e5f6g7h8...",            # Sort Key
    "source_lang": "en",
    "target_lang": "es",
    "source_text": "The original text",
    "target_text": "El texto traducido",
    "context": "Medical consultation notes",
    "created_at": "2024-12-27T10:30:00Z",
    "last_used": "2024-12-27T15:45:00Z",
    "translation_quality": 9.2,
    "translation_model": "gpt-3.5-turbo",
    "evaluation_model": "gpt-4o",
    "translation_version": "1.0",
    "usage_count": 15,
    "cost_saved": 0.045
}
```

### Key Design Decisions
- **Partition Key**: `TRANSLATION#{source_lang}#{target_lang}#{text_hash}`
- **Sort Key**: `CONTEXT#{context_hash}` (enables context-aware caching)
- **GSI**: `last_used` for cleanup operations
- **TTL**: Automatic item expiration after 30 days

## 🔧 Complete Cache Manager Implementation

```python
import boto3
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class TranslationCacheManager:
    def __init__(self, redis_endpoint: str, dynamodb_table: str):
        # Redis setup
        self.redis_client = redis.Redis(
            host=redis_endpoint,
            port=6379,
            decode_responses=True
        )

        # DynamoDB setup
        self.dynamodb = boto3.resource('dynamodb')
        self.translation_table = self.dynamodb.Table(dynamodb_table)

    def _generate_cache_key(self, source_lang: str, target_lang: str,
                          text: str, context: Optional[str] = None) -> str:
        """Generate unique cache key for translation"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        context_hash = hashlib.sha256(context.encode()).hexdigest()[:16] if context else "none"
        return f"{source_lang}:{target_lang}:{text_hash}:{context_hash}"

    def _generate_db_keys(self, source_lang: str, target_lang: str,
                         text: str, context: Optional[str] = None) -> Dict[str, str]:
        """Generate DynamoDB partition and sort keys"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        context_hash = hashlib.sha256(context.encode()).hexdigest()[:16] if context else "none"

        return {
            "pk": f"TRANSLATION#{source_lang}#{target_lang}#{text_hash}",
            "sk": f"CONTEXT#{context_hash}"
        }

    def get_translation(self, source_lang: str, target_lang: str,
                       text: str, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve translation with multi-tier caching
        Returns cached translation or None if not found
        """
        # Step 1: Check Redis cache
        cache_key = self._generate_cache_key(source_lang, target_lang, text, context)
        cached_result = self.redis_client.get(cache_key)

        if cached_result:
            print("✅ Cache HIT (Redis)")
            return json.loads(cached_result)

        # Step 2: Check DynamoDB
        db_keys = self._generate_db_keys(source_lang, target_lang, text, context)

        try:
            response = self.translation_table.get_item(Key=db_keys)
            if 'Item' in response:
                print("✅ Cache HIT (DynamoDB)")
                translation_data = response['Item']

                # Update last_used timestamp
                self._update_last_used(db_keys)

                # Cache in Redis for faster future access
                self.redis_client.setex(
                    cache_key,
                    86400,  # 24 hours
                    json.dumps(translation_data)
                )

                return translation_data
        except Exception as e:
            print(f"⚠️ DynamoDB error: {e}")

        print("❌ Cache MISS - API call required")
        return None

    def store_translation(self, source_lang: str, target_lang: str, text: str,
                         translation_result: Dict[str, Any], context: Optional[str] = None):
        """Store translation in both Redis and DynamoDB"""
        cache_key = self._generate_cache_key(source_lang, target_lang, text, context)
        db_keys = self._generate_db_keys(source_lang, target_lang, text, context)

        # Prepare data for storage
        storage_data = {
            **db_keys,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "source_text": text,
            "target_text": translation_result.get('translated_text'),
            "context": context or "",
            "created_at": datetime.utcnow().isoformat(),
            "last_used": datetime.utcnow().isoformat(),
            "translation_quality": translation_result.get('quality_score', 0),
            "translation_model": translation_result.get('translation_model'),
            "evaluation_model": translation_result.get('evaluation_model'),
            "translation_version": "1.0",
            "usage_count": 1,
            "tokens_used": translation_result.get('tokens_used', 0),
            "cost_estimate": translation_result.get('cost_estimate', 0),
            "ttl": int((datetime.utcnow() + timedelta(days=30)).timestamp())
        }

        # Store in Redis
        self.redis_client.setex(
            cache_key,
            86400,  # 24 hours
            json.dumps(storage_data)
        )

        # Store in DynamoDB
        try:
            self.translation_table.put_item(Item=storage_data)
            print("✅ Translation cached successfully")
        except Exception as e:
            print(f"⚠️ Failed to store in DynamoDB: {e}")

    def _update_last_used(self, db_keys: Dict[str, str]):
        """Update last_used timestamp and increment usage_count"""
        try:
            self.translation_table.update_item(
                Key=db_keys,
                UpdateExpression="SET last_used = :timestamp, usage_count = usage_count + :inc",
                ExpressionAttributeValues={
                    ':timestamp': datetime.utcnow().isoformat(),
                    ':inc': 1
                }
            )
        except Exception as e:
            print(f"⚠️ Failed to update last_used: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics"""
        try:
            # Redis stats
            redis_info = self.redis_client.info()

            # DynamoDB stats (approximate)
            response = self.translation_table.scan(
                Select='COUNT',
                FilterExpression='attribute_exists(pk)'
            )

            return {
                "redis_keys": redis_info.get('db0', {}).get('keys', 0),
                "redis_memory_usage": redis_info.get('used_memory_human'),
                "dynamodb_items": response.get('Count', 0),
                "cache_hit_rate": "Monitor through CloudWatch"
            }
        except Exception as e:
            return {"error": str(e)}
```

## 💰 Cost Savings Analysis

### Before Caching
```
1000 translations/day × $0.002/translation = $2.00/day
Monthly cost: $60.00
Annual cost: $730.00
```

### After Caching (90% hit rate)
```
100 new translations/day × $0.002/translation = $0.20/day
900 cached translations/day × $0.0001/retrieval = $0.09/day
Monthly cost: $8.70 (85% savings)
Annual cost: $105.85 (85% savings)
```

### Infrastructure Costs
```
Redis (ElastiCache): ~$15/month
DynamoDB: ~$5/month (with on-demand pricing)
Total infrastructure: ~$20/month

Net savings: $60 - $8.70 - $20 = $31.30/month (52% total savings)
```

## 📊 Performance Metrics

### Response Times
| Cache Layer | Response Time | Use Case |
|-------------|---------------|----------|
| **Redis Hit** | <1ms | Frequent translations |
| **DynamoDB Hit** | <10ms | Recent translations |
| **API Call** | 1-5s | New translations |

### Cache Hit Rates (Target)
- **Redis**: 60-70% of all requests
- **DynamoDB**: 20-25% of all requests
- **API Calls**: 10-15% of all requests

## 🔧 Integration with Translation System

```python
# Enhanced ContextAwareTranslator with caching
class CachedContextAwareTranslator(ContextAwareTranslator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_manager = TranslationCacheManager(
            redis_endpoint=os.getenv('REDIS_ENDPOINT'),
            dynamodb_table=os.getenv('DYNAMODB_TABLE')
        )

    def translate(self, text: str, source_lang: str, target_lang: str,
                 context: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Enhanced translate method with caching"""

        # Check cache first
        cached_result = self.cache_manager.get_translation(
            source_lang, target_lang, text, context
        )

        if cached_result:
            return {
                **cached_result,
                'cache_hit': True,
                'cost_estimate': 0.0001,  # Minimal retrieval cost
                'source': 'cache'
            }

        # If not cached, perform translation
        result = super().translate(text, source_lang, target_lang, context, **kwargs)

        # Store result in cache
        if result.get('success'):
            self.cache_manager.store_translation(
                source_lang, target_lang, text, result, context
            )

        result['cache_hit'] = False
        result['source'] = 'api'
        return result
```

## 🚀 Deployment Strategy

### AWS Infrastructure
```yaml
# CloudFormation template excerpt
Resources:
  TranslationCache:
    Type: AWS::ElastiCache::ReplicationGroup
    Properties:
      ReplicationGroupDescription: Translation cache
      NumCacheClusters: 2
      Engine: redis
      CacheNodeType: cache.t3.micro

  TranslationTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: TranslationCache
      BillingMode: ON_DEMAND
      AttributeDefinitions:
        - AttributeName: pk
          AttributeType: S
        - AttributeName: sk
          AttributeType: S
      KeySchema:
        - AttributeName: pk
          KeyType: HASH
        - AttributeName: sk
          KeyType: RANGE
      TimeToLiveSpecification:
        AttributeName: ttl
        Enabled: true
```

## 📈 Monitoring and Optimization

### Key Metrics to Track
- **Cache hit rate** (target: >85%)
- **Average response time** (target: <100ms)
- **Cost savings** (target: >80%)
- **Storage utilization**
- **Error rates**

### Optimization Strategies
1. **Adjust TTL** based on usage patterns
2. **Implement cache warming** for popular translations
3. **Use compression** for large text storage
4. **Monitor and tune** DynamoDB capacity
5. **Implement cache invalidation** for updated translations

## 🔒 Security Considerations

- **Encryption at rest** for DynamoDB
- **Encryption in transit** for Redis
- **VPC isolation** for cache infrastructure
- **IAM roles** with minimal permissions
- **Data retention policies** compliance

## 🛠️ Quick Start Implementation

### 1. Install Dependencies
```bash
pip install redis boto3 python-dotenv
```

### 2. Environment Configuration
```bash
# Add to .env file
REDIS_ENDPOINT=your-redis-endpoint.cache.amazonaws.com
DYNAMODB_TABLE=TranslationCache
AWS_REGION=us-east-1
```

### 3. Basic Usage Example
```python
from src.translators.cached_translator import CachedContextAwareTranslator
from openai import OpenAI

# Initialize with caching
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
translator = CachedContextAwareTranslator(
    client=client,
    translation_model="gpt-3.5-turbo",
    evaluation_model="gpt-4o"
)

# First call - hits API
result1 = translator.translate(
    text="Hello world",
    source_lang="English",
    target_lang="Spanish"
)
print(f"Source: {result1['source']}")  # Output: api
print(f"Cost: ${result1['cost_estimate']}")  # Output: $0.002

# Second call - hits cache
result2 = translator.translate(
    text="Hello world",
    source_lang="English",
    target_lang="Spanish"
)
print(f"Source: {result2['source']}")  # Output: cache
print(f"Cost: ${result2['cost_estimate']}")  # Output: $0.0001
```

### 4. Cache Statistics
```python
# Monitor cache performance
stats = translator.cache_manager.get_cache_stats()
print(f"Redis keys: {stats['redis_keys']}")
print(f"DynamoDB items: {stats['dynamodb_items']}")
```

## 📋 Implementation Checklist

- [ ] Set up AWS ElastiCache Redis cluster
- [ ] Create DynamoDB table with proper schema
- [ ] Configure IAM roles and permissions
- [ ] Install required Python dependencies
- [ ] Update environment variables
- [ ] Integrate CachedContextAwareTranslator
- [ ] Set up monitoring and alerting
- [ ] Test cache hit rates and performance
- [ ] Configure backup and disaster recovery
- [ ] Document cache invalidation procedures

## 🎯 Expected Results

With proper implementation, you should see:
- **85-90% reduction** in OpenAI API calls
- **Sub-100ms response times** for cached translations
- **80%+ cost savings** on translation operations
- **Improved user experience** with faster responses
- **Scalable architecture** that grows with demand

---

This caching system provides significant cost savings while maintaining high performance and reliability for the translation system.
