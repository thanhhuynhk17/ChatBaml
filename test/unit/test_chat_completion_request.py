"""
Unit tests for the ChatBaml._chat_completion_request method
"""

import pytest
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from custom_langchain_model.llms.chat_baml import ChatBaml
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

# Test messages
TEST_MESSAGES = [
    SystemMessage(content="You are a helpful assistant that answers concisely."),
    HumanMessage(content="Provide a one-sentence summary of the following paragraph."),
    AIMessage(content="LangChain is a framework for developing applications with large language models. It provides tools for prompt management, chaining calls, and building agents that interact with external tools."),
    HumanMessage(content="summarize that for me.")
]

def test_chat_completion_request_basic():
    """Test basic chat completion request without tools"""
    chat_baml = ChatBaml(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL_NAME")
    )

    # Test that the method can be called without errors
    import asyncio

    async def run_test():
        result = await chat_baml._chat_completion_request(
            messages=TEST_MESSAGES,
            tools=[]
        )
        return result

    result = asyncio.run(run_test())

    assert result is not None
    assert "response" in result
    assert "baml_state" in result
    print("✓ Basic chat completion request test passed")

def test_chat_completion_request_with_empty_tools():
    """Test chat completion request with empty tools list"""
    chat_baml = ChatBaml(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL_NAME")
    )

    import asyncio

    async def run_test():
        result = await chat_baml._chat_completion_request(
            messages=TEST_MESSAGES,
            tools=[]
        )
        return result

    result = asyncio.run(run_test())

    assert result is not None
    print("✓ Empty tools test passed")

def test_chat_completion_request_message_conversion():
    """Test that messages are properly converted to BAML format"""
    chat_baml = ChatBaml(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL_NAME")
    )

    # Test message conversion helper method
    baml_messages = chat_baml._convert_to_baml_messages(TEST_MESSAGES)

    assert baml_messages is not None
    assert len(baml_messages) == len(TEST_MESSAGES)
    assert all(hasattr(msg, 'role') for msg in baml_messages)
    assert all(hasattr(msg, 'content') for msg in baml_messages)
    print("✓ Message conversion test passed")

def test_chat_completion_request_error_handling():
    """Test error handling for invalid inputs"""
    chat_baml = ChatBaml(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL_NAME")
    )

    # Test with empty messages list
    with pytest.raises(Exception):
        import asyncio
        asyncio.run(chat_baml._chat_completion_request(messages=[], tools=[]))

    print("✓ Error handling test passed")

def run_all_tests():
    """Run all unit tests and report results"""
    print("\n=== Running Unit Tests for ChatBaml._chat_completion_request ===")

    test_functions = [
        test_chat_completion_request_basic,
        test_chat_completion_request_with_empty_tools,
        test_chat_completion_request_message_conversion,
        test_chat_completion_request_error_handling
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed")

    return failed == 0

if __name__ == "__main__":
    run_all_tests()