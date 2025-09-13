#!/usr/bin/env python3
"""
Simple test script for RAG functionality
Tests the RAG handler without requiring Streamlit secrets
"""

import os
import sys
from unittest.mock import patch, MagicMock

# Mock streamlit secrets for testing
mock_secrets = {
    "OPENAI_API_KEY": "test-key-placeholder"
}

with patch('streamlit.secrets', mock_secrets):
    from app.rag.rag_handler import RAGHandler

def test_economics_detection():
    """Test economics keyword detection"""
    print("🧪 Testing economics keyword detection...")
    
    handler = RAGHandler()
    
    # Test economics-related queries
    economics_queries = [
        "What is market failure?",
        "Explain supply and demand",
        "How does government intervention work?",
        "What are externalities?",
        "Discuss monopoly pricing"
    ]
    
    # Test non-economics queries
    non_economics_queries = [
        "What is the weather today?",
        "How do I cook pasta?",
        "Tell me about history",
        "What is machine learning?"
    ]
    
    print("Economics queries:")
    for query in economics_queries:
        is_econ = handler.is_economics_related(query)
        print(f"  '{query}' -> {is_econ} {'✅' if is_econ else '❌'}")
    
    print("\nNon-economics queries:")
    for query in non_economics_queries:
        is_econ = handler.is_economics_related(query)
        print(f"  '{query}' -> {is_econ} {'❌' if not is_econ else '⚠️'}")

def test_token_counting():
    """Test token counting functionality"""
    print("\n🧪 Testing token counting...")
    
    handler = RAGHandler()
    
    test_texts = [
        "Hello world",
        "This is a longer piece of text with more tokens to count properly",
        "Market failure occurs when the free market fails to allocate resources efficiently."
    ]
    
    for text in test_texts:
        token_count = handler.count_tokens(text)
        print(f"  '{text[:50]}{'...' if len(text) > 50 else ''}' -> {token_count} tokens")

def test_database_connection():
    """Test if database connection and RAG stats work"""
    print("\n🧪 Testing database connection...")
    
    try:
        handler = RAGHandler()
        stats = handler.get_rag_stats()
        print(f"  Database stats: {stats}")
        
        if "error" in stats:
            print("  ⚠️  Database connection issue (expected if not set up)")
        else:
            print("  ✅ Database connection successful")
            
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing RAG Implementation\n")
    
    test_economics_detection()
    test_token_counting()
    test_database_connection()
    
    print("\n✅ RAG tests completed!")
    print("\n📋 Next steps:")
    print("1. Set up your database with pgvector extension")
    print("2. Run: python process_pdf.py")
    print("3. Start the Streamlit app: streamlit run main.py")

if __name__ == "__main__":
    main()