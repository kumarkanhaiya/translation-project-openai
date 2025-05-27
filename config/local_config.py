#!/usr/bin/env python3
"""
Local Development Configuration.

This module provides configuration settings for local development
with DynamoDB Local and Redis, allowing cost-free development and testing.
"""

import os
from typing import Dict, Any

# Local development configuration
LOCAL_CONFIG = {
    'dynamodb': {
        'endpoint_url': 'http://localhost:8000',
        'region_name': 'local',
        'aws_access_key_id': 'local',
        'aws_secret_access_key': 'local',
        'table_name': 'Translations'
    },
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'decode_responses': True,
        'socket_connect_timeout': 5,
        'socket_timeout': 5
    },
    'cache': {
        'default_ttl': 86400,  # 24 hours
        'max_ttl': 604800,     # 7 days
        'key_prefix': 'translation:'
    }
}

# Production configuration (uses AWS credentials from environment)
PRODUCTION_CONFIG = {
    'dynamodb': {
        'region_name': os.getenv('AWS_REGION', 'us-east-1'),
        'table_name': os.getenv('DYNAMODB_TABLE', 'Translations')
    },
    'redis': {
        'host': os.getenv('REDIS_HOST', 'your-elasticache-endpoint.cache.amazonaws.com'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'db': int(os.getenv('REDIS_DB', 0)),
        'decode_responses': True,
        'ssl': True,  # ElastiCache typically uses SSL
        'socket_connect_timeout': 5,
        'socket_timeout': 5
    },
    'cache': {
        'default_ttl': int(os.getenv('CACHE_TTL', 86400)),
        'max_ttl': int(os.getenv('CACHE_MAX_TTL', 604800)),
        'key_prefix': os.getenv('CACHE_KEY_PREFIX', 'translation:')
    }
}

def get_config(environment: str = None) -> Dict[str, Any]:
    """
    Get configuration based on environment.
    
    Args:
        environment: 'local' or 'production'. If None, auto-detect from ENVIRONMENT env var
        
    Returns:
        Configuration dictionary
    """
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'local').lower()
    
    if environment == 'production':
        return PRODUCTION_CONFIG
    else:
        return LOCAL_CONFIG

def is_local_environment() -> bool:
    """
    Check if running in local development environment.
    
    Returns:
        True if local environment
    """
    return os.getenv('ENVIRONMENT', 'local').lower() == 'local'

def get_dynamodb_config(environment: str = None) -> Dict[str, Any]:
    """Get DynamoDB-specific configuration."""
    config = get_config(environment)
    return config['dynamodb']

def get_redis_config(environment: str = None) -> Dict[str, Any]:
    """Get Redis-specific configuration."""
    config = get_config(environment)
    return config['redis']

def get_cache_config(environment: str = None) -> Dict[str, Any]:
    """Get cache-specific configuration."""
    config = get_config(environment)
    return config['cache']

# Environment validation
def validate_local_environment():
    """
    Validate that local environment is properly configured.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check if DynamoDB Local is accessible
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        dynamodb_config = get_dynamodb_config('local')
        dynamodb = boto3.resource('dynamodb', **dynamodb_config)
        list(dynamodb.tables.all())  # This will fail if DynamoDB Local is not running
    except Exception as e:
        errors.append(f"DynamoDB Local not accessible: {e}")
    
    # Check if Redis is accessible
    try:
        import redis
        
        redis_config = get_redis_config('local')
        r = redis.Redis(**redis_config)
        r.ping()
    except Exception as e:
        errors.append(f"Redis not accessible: {e}")
    
    return errors

def validate_production_environment():
    """
    Validate that production environment is properly configured.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check required environment variables
    required_vars = [
        'AWS_REGION',
        'REDIS_HOST',
        'DYNAMODB_TABLE'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Check AWS credentials
    try:
        import boto3
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            errors.append("AWS credentials not found")
    except Exception as e:
        errors.append(f"AWS credentials error: {e}")
    
    return errors

def print_config_summary(environment: str = None):
    """Print a summary of the current configuration."""
    config = get_config(environment)
    env = environment or os.getenv('ENVIRONMENT', 'local')
    
    print(f"🔧 Configuration Summary ({env.upper()})")
    print("=" * 40)
    
    # DynamoDB config
    dynamo_config = config['dynamodb']
    print("📊 DynamoDB:")
    if 'endpoint_url' in dynamo_config:
        print(f"   Endpoint: {dynamo_config['endpoint_url']}")
    print(f"   Region: {dynamo_config['region_name']}")
    print(f"   Table: {dynamo_config['table_name']}")
    
    # Redis config
    redis_config = config['redis']
    print("\n🔴 Redis:")
    print(f"   Host: {redis_config['host']}")
    print(f"   Port: {redis_config['port']}")
    print(f"   Database: {redis_config['db']}")
    if 'ssl' in redis_config:
        print(f"   SSL: {redis_config['ssl']}")
    
    # Cache config
    cache_config = config['cache']
    print("\n💾 Cache:")
    print(f"   Default TTL: {cache_config['default_ttl']} seconds")
    print(f"   Max TTL: {cache_config['max_ttl']} seconds")
    print(f"   Key Prefix: {cache_config['key_prefix']}")

if __name__ == "__main__":
    # Print configuration for current environment
    current_env = os.getenv('ENVIRONMENT', 'local')
    print_config_summary(current_env)
    
    # Validate environment
    if current_env.lower() == 'local':
        errors = validate_local_environment()
        if errors:
            print(f"\n❌ Local environment validation failed:")
            for error in errors:
                print(f"   • {error}")
        else:
            print(f"\n✅ Local environment validation passed")
    else:
        errors = validate_production_environment()
        if errors:
            print(f"\n❌ Production environment validation failed:")
            for error in errors:
                print(f"   • {error}")
        else:
            print(f"\n✅ Production environment validation passed")
