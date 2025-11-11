#!/usr/bin/env python3
"""
Debug script to test the vendas AI directly
"""

import asyncio
import os
import sys
sys.path.append('/app/backend')

from vendas_ai_humanized import humanized_vendas_ai
from motor.motor_asyncio import AsyncIOMotorClient

async def test_ai_directly():
    """Test the AI service directly"""
    print("🔍 Testing vendas AI directly...")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['support_chat']
    
    # Test the AI response by calling the method directly and catching internal errors
    print("🔍 Testing AI components...")
    
    # Check API key
    api_key = humanized_vendas_ai.get_api_key()
    print(f"API Key: {'Set' if api_key else 'Missing'}")
    if api_key:
        print(f"API Key length: {len(api_key)}")
    
    # Test emergentintegrations import
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        print("✅ emergentintegrations import OK")
        
        # Test creating chat instance
        chat = LlmChat(
            api_key=api_key,
            session_id="test-session",
            system_message="Test system message",
            initial_messages=None
        ).with_model("openai", "gpt-4o-mini")
        print("✅ LlmChat instance created OK")
        
        # Test sending a message
        message = UserMessage(text="Hello, this is a test")
        response = await chat.send_message(message)
        print(f"✅ AI Response: {response}")
        
    except Exception as e:
        print(f"❌ Error in AI components: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_ai_directly())