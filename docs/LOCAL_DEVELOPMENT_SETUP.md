# Local Development Setup Guide

A comprehensive guide for setting up DynamoDB Local and Redis locally for cost-effective development and testing of the translation caching system.

## 🎯 Overview

This setup allows you to:
- **Develop without AWS costs** - Test caching logic locally
- **Debug efficiently** - No network latency to cloud services  
- **Work offline** - Full functionality without internet
- **Iterate quickly** - Instant feedback during development

## 📋 Prerequisites

### Required Software
- **Java 8+** (for DynamoDB Local)
- **Python 3.8+** with required packages
- **Docker** (recommended for Redis)
- **Git** (for version control)

### Python Dependencies
```bash
pip install boto3 redis python-dotenv
```

## 🚀 Quick Start

### 1. Clone and Setup Project
```bash
git clone https://github.com/kumarkanhaiya/translation-project-openai.git
cd translation-project-openai
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

### 2. Download DynamoDB Local
```bash
# Download from AWS
wget https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz
tar -xzf dynamodb_local_latest.tar.gz
```

### 3. Start Local Services
```bash
# Terminal 1: Start DynamoDB Local
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

# Terminal 2: Start Redis
docker run --name redis-local -p 6379:6379 -d redis
```

### 4. Configure Environment
```bash
# Create .env.local file
echo "ENVIRONMENT=local" > .env.local
echo "OPENAI_API_KEY=your_api_key_here" >> .env.local
echo "REDIS_HOST=localhost" >> .env.local
echo "DYNAMODB_ENDPOINT=http://localhost:8000" >> .env.local
```

### 5. Test Setup
```bash
PYTHONPATH=src python scripts/test_local_setup.py
```

## 🗄️ DynamoDB Local Setup

### Installation
1. **Download**: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html
2. **Extract** to your project directory
3. **Verify Java** installation: `java -version`

### Starting DynamoDB Local
```bash
# Basic startup
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

# With custom port
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -port 8001

# In-memory only (no persistence)
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -inMemory

# With CORS enabled
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -cors "*"
```

### Verification
- **Web Interface**: http://localhost:8000
- **AWS CLI Test**: 
  ```bash
  aws dynamodb list-tables --endpoint-url http://localhost:8000
  ```

## 🔴 Redis Local Setup

### Option 1: Docker (Recommended)
```bash
# Start Redis container
docker run --name redis-local -p 6379:6379 -d redis

# Verify running
docker ps | grep redis

# Access Redis CLI
docker exec -it redis-local redis-cli

# Test connection
redis-cli ping  # Should return PONG
```

### Option 2: Native Installation
```bash
# Windows: Download from GitHub
# https://github.com/microsoftarchive/redis/releases

# Linux/macOS
sudo apt-get install redis-server  # Ubuntu
brew install redis                 # macOS

# Start Redis
redis-server
```

### Redis Configuration
```bash
# Optional: Create custom Redis config
echo "save 900 1" > redis.conf
echo "save 300 10" >> redis.conf
echo "save 60 10000" >> redis.conf

# Start with custom config
redis-server redis.conf
```

## ⚙️ Configuration Files

### Local Configuration
```python
# config/local_config.py
LOCAL_CONFIG = {
    'dynamodb': {
        'endpoint_url': 'http://localhost:8000',
        'region_name': 'local',
        'aws_access_key_id': 'local',
        'aws_secret_access_key': 'local'
    },
    'redis': {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'decode_responses': True
    }
}
```

### Environment Variables
```bash
# .env.local
ENVIRONMENT=local
OPENAI_API_KEY=your_openai_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
DYNAMODB_ENDPOINT=http://localhost:8000
DYNAMODB_REGION=local
AWS_ACCESS_KEY_ID=local
AWS_SECRET_ACCESS_KEY=local
```

## 🏗️ Database Setup

### Create Translation Table
```python
# scripts/setup_local_db.py
import boto3

def create_translation_table():
    dynamodb = boto3.resource('dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='local',
        aws_access_key_id='local',
        aws_secret_access_key='local'
    )
    
    table = dynamodb.create_table(
        TableName='Translations',
        KeySchema=[
            {'AttributeName': 'pk', 'KeyType': 'HASH'},
            {'AttributeName': 'sk', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'pk', 'AttributeType': 'S'},
            {'AttributeName': 'sk', 'AttributeType': 'S'},
            {'AttributeName': 'last_used', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'LastUsedIndex',
            'KeySchema': [{'AttributeName': 'last_used', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }],
        BillingMode='PAY_PER_REQUEST'
    )
    
    table.wait_until_exists()
    print("✅ Translation table created")

if __name__ == "__main__":
    create_translation_table()
```

### Run Setup Script
```bash
PYTHONPATH=src python scripts/setup_local_db.py
```

## 🧪 Testing Your Setup

### Basic Connectivity Test
```python
# scripts/test_local_setup.py
import redis
import boto3

def test_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        r.set('test', 'success')
        assert r.get('test') == 'success'
        r.delete('test')
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False

def test_dynamodb():
    try:
        dynamodb = boto3.resource('dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='local',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        
        # List tables
        tables = list(dynamodb.tables.all())
        print(f"✅ DynamoDB connected. Tables: {[t.name for t in tables]}")
        return True
    except Exception as e:
        print(f"❌ DynamoDB test failed: {e}")
        return False

def main():
    print("🧪 Testing local setup...")
    redis_ok = test_redis()
    dynamo_ok = test_dynamodb()
    
    if redis_ok and dynamo_ok:
        print("🎉 All services are working!")
    else:
        print("⚠️ Some services need attention")

if __name__ == "__main__":
    main()
```

## 🔧 Development Workflow

### Daily Startup Routine
```bash
# 1. Start services (in separate terminals)
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
docker start redis-local

# 2. Activate environment
source .venv/Scripts/activate
export ENVIRONMENT=local

# 3. Run your application
PYTHONPATH=src python src/examples/context_aware_translation_demo.py
```

### Monitoring Commands
```bash
# Check Redis data
docker exec -it redis-local redis-cli
> KEYS *
> GET translation:en:es:*

# Check DynamoDB data
aws dynamodb scan --table-name Translations --endpoint-url http://localhost:8000

# Monitor Redis memory usage
docker exec -it redis-local redis-cli INFO memory
```

### Cleanup Commands
```bash
# Clear Redis data
docker exec -it redis-local redis-cli FLUSHALL

# Reset DynamoDB (delete and recreate table)
aws dynamodb delete-table --table-name Translations --endpoint-url http://localhost:8000
python scripts/setup_local_db.py

# Stop services
docker stop redis-local
# Stop DynamoDB Local with Ctrl+C
```

## 📊 Monitoring and Debugging

### Redis Monitoring
```bash
# Real-time monitoring
docker exec -it redis-local redis-cli MONITOR

# Check specific keys
docker exec -it redis-local redis-cli
> KEYS translation:*
> TTL your_key
> TYPE your_key
```

### DynamoDB Monitoring
```bash
# List all tables
aws dynamodb list-tables --endpoint-url http://localhost:8000

# Describe table
aws dynamodb describe-table --table-name Translations --endpoint-url http://localhost:8000

# Scan table contents
aws dynamodb scan --table-name Translations --endpoint-url http://localhost:8000 --max-items 10
```

### Application Logs
```python
# Add to your application for debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# In your cache manager
logger = logging.getLogger(__name__)
logger.debug(f"Cache key: {cache_key}")
logger.debug(f"Cache hit: {cache_hit}")
```

## 🚨 Troubleshooting

### Common Issues

#### DynamoDB Local Won't Start
```bash
# Check Java version
java -version

# Check if port 8000 is in use
netstat -an | grep 8000

# Try different port
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -port 8001
```

#### Redis Connection Failed
```bash
# Check if Redis is running
docker ps | grep redis

# Check Redis logs
docker logs redis-local

# Restart Redis
docker restart redis-local
```

#### Table Creation Errors
```bash
# Check if table already exists
aws dynamodb list-tables --endpoint-url http://localhost:8000

# Delete existing table
aws dynamodb delete-table --table-name Translations --endpoint-url http://localhost:8000
```

### Performance Issues
- **DynamoDB Local**: Slower than AWS DynamoDB
- **Redis**: Use `redis.conf` for optimization
- **Java Memory**: Increase with `-Xmx512m` flag

## 💡 Best Practices

### Development Tips
1. **Use separate databases** for different projects
2. **Regular backups** of local data if needed
3. **Environment switching** between local/production
4. **Consistent naming** for cache keys
5. **Monitor resource usage** during development

### Security Notes
- **Local credentials** are dummy values
- **Never commit** real AWS credentials
- **Use environment variables** for configuration
- **Separate configs** for local/production

## 🎯 Benefits Summary

### Cost Savings
- **$0 AWS charges** during development
- **Unlimited testing** without API costs
- **No data transfer** charges

### Development Speed
- **Instant responses** (no network latency)
- **Offline development** capability
- **Fast iteration** cycles
- **Easy debugging** with local access

### Testing Advantages
- **Isolated environment** for testing
- **Reproducible results** with local data
- **Easy data manipulation** for edge cases
- **Version control** of test data

---

## 📚 Additional Resources

- [DynamoDB Local Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html)
- [Redis Documentation](https://redis.io/documentation)
- [Docker Redis Image](https://hub.docker.com/_/redis)
- [AWS CLI DynamoDB Commands](https://docs.aws.amazon.com/cli/latest/reference/dynamodb/)

---

*This setup provides a complete local development environment that mirrors the production caching system while eliminating AWS costs and network dependencies.*
