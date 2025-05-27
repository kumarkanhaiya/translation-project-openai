#!/usr/bin/env python3
"""
Local Setup Testing Script.

This script tests the local DynamoDB and Redis setup to ensure
everything is working correctly for development.
"""

import redis
import boto3
import sys
import time
from botocore.exceptions import ClientError, NoCredentialsError

def test_redis_connection():
    """
    Test Redis connection and basic operations.
    
    Returns:
        bool: True if Redis is working correctly
    """
    print("🔴 Testing Redis connection...")
    
    try:
        # Connect to Redis
        r = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        # Test ping
        response = r.ping()
        if not response:
            print("   ❌ Redis ping failed")
            return False
        print("   ✅ Redis ping successful")
        
        # Test basic operations
        test_key = 'test_translation_cache'
        test_value = 'test_value_12345'
        
        # Set value
        r.set(test_key, test_value, ex=60)  # 60 seconds expiry
        print("   ✅ Redis SET operation successful")
        
        # Get value
        retrieved_value = r.get(test_key)
        if retrieved_value != test_value:
            print(f"   ❌ Redis GET failed. Expected: {test_value}, Got: {retrieved_value}")
            return False
        print("   ✅ Redis GET operation successful")
        
        # Test TTL
        ttl = r.ttl(test_key)
        if ttl <= 0:
            print(f"   ❌ Redis TTL failed. TTL: {ttl}")
            return False
        print(f"   ✅ Redis TTL working (TTL: {ttl} seconds)")
        
        # Test JSON storage (common for translation cache)
        import json
        json_data = {
            'source_text': 'Hello world',
            'translated_text': 'Hola mundo',
            'quality_score': 9.5
        }
        r.set('test_json', json.dumps(json_data))
        retrieved_json = json.loads(r.get('test_json'))
        
        if retrieved_json['source_text'] != 'Hello world':
            print("   ❌ Redis JSON storage failed")
            return False
        print("   ✅ Redis JSON storage working")
        
        # Cleanup
        r.delete(test_key, 'test_json')
        print("   ✅ Redis cleanup successful")
        
        # Get Redis info
        info = r.info()
        print(f"   📊 Redis version: {info.get('redis_version', 'unknown')}")
        print(f"   📊 Used memory: {info.get('used_memory_human', 'unknown')}")
        
        return True
        
    except redis.ConnectionError:
        print("   ❌ Cannot connect to Redis")
        print("   💡 Make sure Redis is running:")
        print("      docker run --name redis-local -p 6379:6379 -d redis")
        return False
    except Exception as e:
        print(f"   ❌ Redis test failed: {e}")
        return False

def test_dynamodb_connection():
    """
    Test DynamoDB Local connection and operations.
    
    Returns:
        bool: True if DynamoDB is working correctly
    """
    print("\n📊 Testing DynamoDB Local connection...")
    
    try:
        # Connect to DynamoDB Local
        dynamodb = boto3.resource('dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='local',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        
        # Test connection by listing tables
        tables = list(dynamodb.tables.all())
        table_names = [table.name for table in tables]
        print(f"   ✅ Connected to DynamoDB Local")
        print(f"   📋 Available tables: {table_names}")
        
        # Check if Translations table exists
        if 'Translations' not in table_names:
            print("   ⚠️ 'Translations' table not found")
            print("   💡 Run: python scripts/setup_local_db.py")
            return False
        
        # Test table operations
        table = dynamodb.Table('Translations')
        
        # Test put operation
        test_item = {
            'pk': 'TEST#en#es#test123',
            'sk': 'CONTEXT#test',
            'source_lang': 'en',
            'target_lang': 'es',
            'source_text': 'Test message',
            'target_text': 'Mensaje de prueba',
            'context': 'Testing context',
            'created_at': '2024-01-01T00:00:00Z',
            'last_used': '2024-01-01T00:00:00Z',
            'translation_quality': 8.5,
            'usage_count': 1,
            'tokens_used': 50,
            'cost_estimate': 0.001
        }
        
        table.put_item(Item=test_item)
        print("   ✅ DynamoDB PUT operation successful")
        
        # Test get operation
        response = table.get_item(
            Key={
                'pk': 'TEST#en#es#test123',
                'sk': 'CONTEXT#test'
            }
        )
        
        if 'Item' not in response:
            print("   ❌ DynamoDB GET operation failed")
            return False
        
        retrieved_item = response['Item']
        if retrieved_item['source_text'] != 'Test message':
            print("   ❌ DynamoDB data integrity check failed")
            return False
        print("   ✅ DynamoDB GET operation successful")
        
        # Test update operation
        table.update_item(
            Key={
                'pk': 'TEST#en#es#test123',
                'sk': 'CONTEXT#test'
            },
            UpdateExpression='SET usage_count = usage_count + :inc, last_used = :timestamp',
            ExpressionAttributeValues={
                ':inc': 1,
                ':timestamp': '2024-01-01T01:00:00Z'
            }
        )
        print("   ✅ DynamoDB UPDATE operation successful")
        
        # Verify update
        response = table.get_item(
            Key={
                'pk': 'TEST#en#es#test123',
                'sk': 'CONTEXT#test'
            }
        )
        
        if response['Item']['usage_count'] != 2:
            print("   ❌ DynamoDB update verification failed")
            return False
        print("   ✅ DynamoDB update verification successful")
        
        # Test scan operation (limited)
        scan_response = table.scan(Limit=1)
        if 'Items' not in scan_response or len(scan_response['Items']) == 0:
            print("   ❌ DynamoDB SCAN operation failed")
            return False
        print("   ✅ DynamoDB SCAN operation successful")
        
        # Cleanup test item
        table.delete_item(
            Key={
                'pk': 'TEST#en#es#test123',
                'sk': 'CONTEXT#test'
            }
        )
        print("   ✅ DynamoDB cleanup successful")
        
        # Get table info
        table.reload()
        print(f"   📊 Table status: {table.table_status}")
        print(f"   📊 Item count: {table.item_count}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"   ❌ DynamoDB ClientError: {error_code}")
        if error_code == 'ResourceNotFoundException':
            print("   💡 Run: python scripts/setup_local_db.py")
        return False
    except Exception as e:
        print(f"   ❌ Cannot connect to DynamoDB Local: {e}")
        print("   💡 Make sure DynamoDB Local is running:")
        print("      java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb")
        return False

def test_integration():
    """
    Test integration between Redis and DynamoDB for caching workflow.
    
    Returns:
        bool: True if integration test passes
    """
    print("\n🔗 Testing Redis + DynamoDB integration...")
    
    try:
        # Initialize connections
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        dynamodb = boto3.resource('dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='local',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        
        table = dynamodb.Table('Translations')
        
        # Simulate cache workflow
        import json
        import hashlib
        
        # Create test translation data
        source_text = "Integration test message"
        target_text = "Mensaje de prueba de integración"
        context = "Integration testing"
        
        # Generate cache key (similar to real implementation)
        text_hash = hashlib.sha256(source_text.encode()).hexdigest()[:16]
        context_hash = hashlib.sha256(context.encode()).hexdigest()[:16]
        cache_key = f"en:es:{text_hash}:{context_hash}"
        
        # Generate DynamoDB keys
        db_keys = {
            'pk': f"TRANSLATION#en#es#{text_hash}",
            'sk': f"CONTEXT#{context_hash}"
        }
        
        # Step 1: Store in DynamoDB (simulating new translation)
        translation_data = {
            **db_keys,
            'source_text': source_text,
            'target_text': target_text,
            'context': context,
            'created_at': '2024-01-01T00:00:00Z',
            'last_used': '2024-01-01T00:00:00Z',
            'translation_quality': 9.0,
            'usage_count': 1
        }
        
        table.put_item(Item=translation_data)
        print("   ✅ Stored translation in DynamoDB")
        
        # Step 2: Cache in Redis
        redis_client.setex(cache_key, 3600, json.dumps(translation_data))
        print("   ✅ Cached translation in Redis")
        
        # Step 3: Simulate cache hit
        cached_data = redis_client.get(cache_key)
        if cached_data:
            parsed_data = json.loads(cached_data)
            if parsed_data['source_text'] == source_text:
                print("   ✅ Cache hit successful")
            else:
                print("   ❌ Cache hit data mismatch")
                return False
        else:
            print("   ❌ Cache hit failed")
            return False
        
        # Step 4: Simulate cache miss and DynamoDB fallback
        redis_client.delete(cache_key)
        print("   ✅ Simulated cache expiry")
        
        # Try cache first (should miss)
        cached_data = redis_client.get(cache_key)
        if cached_data:
            print("   ❌ Cache should have been empty")
            return False
        
        # Fallback to DynamoDB
        response = table.get_item(Key=db_keys)
        if 'Item' in response:
            fallback_data = response['Item']
            if fallback_data['source_text'] == source_text:
                print("   ✅ DynamoDB fallback successful")
            else:
                print("   ❌ DynamoDB fallback data mismatch")
                return False
        else:
            print("   ❌ DynamoDB fallback failed")
            return False
        
        # Step 5: Re-cache from DynamoDB
        redis_client.setex(cache_key, 3600, json.dumps(fallback_data))
        print("   ✅ Re-cached from DynamoDB")
        
        # Cleanup
        redis_client.delete(cache_key)
        table.delete_item(Key=db_keys)
        print("   ✅ Integration test cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Local Development Setup")
    print("=" * 50)
    
    # Test Redis
    redis_ok = test_redis_connection()
    
    # Test DynamoDB
    dynamodb_ok = test_dynamodb_connection()
    
    # Test integration if both services are working
    integration_ok = False
    if redis_ok and dynamodb_ok:
        integration_ok = test_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"   Redis: {'✅ PASS' if redis_ok else '❌ FAIL'}")
    print(f"   DynamoDB: {'✅ PASS' if dynamodb_ok else '❌ FAIL'}")
    print(f"   Integration: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    
    if redis_ok and dynamodb_ok and integration_ok:
        print("\n🎉 All tests passed! Your local setup is ready for development.")
        print("\n📋 Next steps:")
        print("   1. Set ENVIRONMENT=local in your .env file")
        print("   2. Run your translation application")
        print("   3. Monitor cache performance with the cost analyzer")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check the setup:")
        if not redis_ok:
            print("   • Start Redis: docker run --name redis-local -p 6379:6379 -d redis")
        if not dynamodb_ok:
            print("   • Start DynamoDB Local and run: python scripts/setup_local_db.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
