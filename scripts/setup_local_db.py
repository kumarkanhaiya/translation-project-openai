#!/usr/bin/env python3
"""
Local DynamoDB Setup Script.

This script creates the necessary DynamoDB tables for local development.
"""

import boto3
import sys
import os
from botocore.exceptions import ClientError

def create_translation_table(dynamodb_resource):
    """
    Create the Translations table in local DynamoDB.
    
    Args:
        dynamodb_resource: Boto3 DynamoDB resource
        
    Returns:
        Created table resource or None if failed
    """
    try:
        print("📊 Creating 'Translations' table...")
        
        table = dynamodb_resource.create_table(
            TableName='Translations',
            KeySchema=[
                {
                    'AttributeName': 'pk',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'sk', 
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'pk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'sk',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'last_used',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'LastUsedIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'last_used',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be created
        print("⏳ Waiting for table to be created...")
        table.wait_until_exists()
        
        print("✅ Table 'Translations' created successfully!")
        print(f"   Table ARN: {table.table_arn}")
        print(f"   Table Status: {table.table_status}")
        
        return table
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceInUseException':
            print("ℹ️ Table 'Translations' already exists")
            return dynamodb_resource.Table('Translations')
        else:
            print(f"❌ Failed to create table: {e}")
            return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def verify_table_structure(table):
    """
    Verify the table structure is correct.
    
    Args:
        table: DynamoDB table resource
    """
    try:
        # Reload table metadata
        table.reload()
        
        print("\n📋 Table Structure Verification:")
        print(f"   Table Name: {table.table_name}")
        print(f"   Table Status: {table.table_status}")
        print(f"   Item Count: {table.item_count}")
        
        # Check key schema
        print("   Key Schema:")
        for key in table.key_schema:
            print(f"     - {key['AttributeName']} ({key['KeyType']})")
        
        # Check GSI
        if table.global_secondary_indexes:
            print("   Global Secondary Indexes:")
            for gsi in table.global_secondary_indexes:
                print(f"     - {gsi['IndexName']}")
                for key in gsi['KeySchema']:
                    print(f"       - {key['AttributeName']} ({key['KeyType']})")
        
        print("✅ Table structure verified!")
        return True
        
    except Exception as e:
        print(f"❌ Table verification failed: {e}")
        return False

def test_table_operations(table):
    """
    Test basic table operations.
    
    Args:
        table: DynamoDB table resource
    """
    try:
        print("\n🧪 Testing table operations...")
        
        # Test item creation
        test_item = {
            'pk': 'TEST#en#es#12345',
            'sk': 'CONTEXT#test',
            'source_lang': 'en',
            'target_lang': 'es',
            'source_text': 'Hello world',
            'target_text': 'Hola mundo',
            'context': 'Test translation',
            'created_at': '2024-01-01T00:00:00Z',
            'last_used': '2024-01-01T00:00:00Z',
            'translation_quality': 9.0,
            'usage_count': 1
        }
        
        # Put item
        table.put_item(Item=test_item)
        print("   ✅ Put item successful")
        
        # Get item
        response = table.get_item(
            Key={
                'pk': 'TEST#en#es#12345',
                'sk': 'CONTEXT#test'
            }
        )
        
        if 'Item' in response:
            print("   ✅ Get item successful")
            retrieved_item = response['Item']
            assert retrieved_item['source_text'] == 'Hello world'
            print("   ✅ Data integrity verified")
        else:
            print("   ❌ Get item failed - no item returned")
            return False
        
        # Update item
        table.update_item(
            Key={
                'pk': 'TEST#en#es#12345',
                'sk': 'CONTEXT#test'
            },
            UpdateExpression='SET usage_count = usage_count + :inc',
            ExpressionAttributeValues={':inc': 1}
        )
        print("   ✅ Update item successful")
        
        # Delete test item
        table.delete_item(
            Key={
                'pk': 'TEST#en#es#12345',
                'sk': 'CONTEXT#test'
            }
        )
        print("   ✅ Delete item successful")
        
        print("✅ All table operations working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Table operations test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up local DynamoDB for translation caching...")
    
    # Check if DynamoDB Local is running
    try:
        dynamodb = boto3.resource('dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='local',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        
        # Test connection
        list(dynamodb.tables.all())
        print("✅ Connected to DynamoDB Local")
        
    except Exception as e:
        print("❌ Cannot connect to DynamoDB Local")
        print("   Make sure DynamoDB Local is running:")
        print("   java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb")
        print(f"   Error: {e}")
        sys.exit(1)
    
    # Create translation table
    table = create_translation_table(dynamodb)
    if not table:
        print("❌ Failed to create or access table")
        sys.exit(1)
    
    # Verify table structure
    if not verify_table_structure(table):
        print("❌ Table structure verification failed")
        sys.exit(1)
    
    # Test table operations
    if not test_table_operations(table):
        print("❌ Table operations test failed")
        sys.exit(1)
    
    print("\n🎉 Local DynamoDB setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Start Redis: docker run --name redis-local -p 6379:6379 -d redis")
    print("   2. Test the setup: python scripts/test_local_setup.py")
    print("   3. Run your application with ENVIRONMENT=local")

if __name__ == "__main__":
    main()
