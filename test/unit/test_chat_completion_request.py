"""
Unit tests for the ChatBaml._chat_completion_request method
"""

import pytest
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import json

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
    assert json.loads(result)
    assert json.loads(result)["selected_tool"] is not None
    print("✓ Basic chat completion request test passed")


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

def test_invoke_request():
    """Test the invoke method with various scenarios"""
    chat_baml = ChatBaml(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL_NAME")
    )

    # Test 1: Basic invoke without tools
    result = chat_baml.invoke(TEST_MESSAGES)
    assert result is not None
    assert hasattr(result, 'content')
    print("✓ Basic invoke test passed")

    # Test 2: Invoke with bound tools
    from test.fixtures.sample_tools import CalculatorAdd, get_weather

    # Bind tools and test invoke
    chat_baml_with_tools = chat_baml.bind_tools([CalculatorAdd, get_weather])
    result_with_tools = chat_baml_with_tools.invoke(TEST_MESSAGES)
    assert result_with_tools is not None
    print("✓ Invoke with tools test passed")

    # Test 3: Error handling for empty messages
    with pytest.raises(ValueError):
        chat_baml.invoke([])

    print("✓ Invoke error handling test passed")


def run_all_tests():
    """Run all unit tests and report results"""
    print("\n=== Running Unit Tests for ChatBaml._chat_completion_request ===")

    test_functions = [
        test_chat_completion_request_basic,
        test_chat_completion_request_error_handling,
        test_invoke_request
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