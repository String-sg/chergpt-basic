#!/usr/bin/env python3
"""
Test script to verify user_name storage in chat logs
"""

import sys
from unittest.mock import patch, MagicMock
from datetime import datetime
import uuid

# Mock streamlit secrets
mock_secrets = {
    "OPENAI_API_KEY": "test-key",
    "ADMIN_PASSWORD": "test-admin"
}

with patch('streamlit.secrets', mock_secrets):
    from app.chatlog.chatlog_handler import insert_chat_log, initialize_chatlog_table
    from app.db.database_connection import connect_to_db

def test_user_name_storage():
    """Test that user names are properly stored in chat logs"""
    print("🧪 Testing user_name storage in chat logs...")
    
    # Test data
    test_prompt = "What is market failure?"
    test_response = "Market failure occurs when..."
    test_conversation_id = str(uuid.uuid4())
    test_user_name = "John Doe"
    
    try:
        # Initialize the table (this will add user_name column if it doesn't exist)
        print("📝 Initializing chatlog table...")
        initialize_chatlog_table()
        
        # Insert a test chat log with user_name
        print("💾 Inserting test chat log...")
        insert_chat_log(test_prompt, test_response, test_conversation_id, test_user_name)
        
        # Query the database to verify the insertion
        print("🔍 Verifying insertion...")
        conn = connect_to_db()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT prompt, response, conversation_id, user_name 
                    FROM chat_logs 
                    WHERE conversation_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (test_conversation_id,))
                
                result = cur.fetchone()
                
                if result:
                    stored_prompt, stored_response, stored_conv_id, stored_user_name = result
                    
                    print(f"✅ Chat log found:")
                    print(f"   Prompt: {stored_prompt}")
                    print(f"   Response: {stored_response[:50]}...")
                    print(f"   Conversation ID: {stored_conv_id}")
                    print(f"   User Name: {stored_user_name}")
                    
                    if stored_user_name == test_user_name:
                        print("🎉 SUCCESS: User name stored correctly!")
                        return True
                    else:
                        print(f"❌ FAIL: Expected user name '{test_user_name}', got '{stored_user_name}'")
                        return False
                else:
                    print("❌ FAIL: No chat log found with the test conversation ID")
                    return False
            
            conn.close()
        else:
            print("❌ FAIL: Could not connect to database")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_null_user_name():
    """Test insertion without user_name (should work with NULL)"""
    print("\n🧪 Testing chat log insertion without user_name...")
    
    test_prompt = "Test prompt without user"
    test_response = "Test response"
    test_conversation_id = str(uuid.uuid4())
    
    try:
        # Insert without user_name
        insert_chat_log(test_prompt, test_response, test_conversation_id)
        
        # Verify insertion
        conn = connect_to_db()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_name FROM chat_logs 
                    WHERE conversation_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (test_conversation_id,))
                
                result = cur.fetchone()
                if result:
                    stored_user_name = result[0]
                    print(f"✅ Insertion successful, user_name: {stored_user_name}")
                    return True
                else:
                    print("❌ FAIL: Chat log not found")
                    return False
            
            conn.close()
        else:
            print("❌ FAIL: Could not connect to database")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing User Name Storage System\n")
    
    success1 = test_user_name_storage()
    success2 = test_null_user_name()
    
    print(f"\n📋 Test Results:")
    print(f"   User name storage: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   NULL user name handling: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! User name storage is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check your database schema and connection.")

if __name__ == "__main__":
    main()