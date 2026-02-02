# ChatBaml: Custom LangChain Chat Model with BAML Integration

A project that extends a Custom LangChain Chat Model to integrate with BAML, creating a bridge between LangChain's powerful LLM orchestration capabilities and BAML's structured data extraction and function calling features.

![demo](https://github.com/user-attachments/assets/966896b7-2890-438d-b5a7-80501689f8ac)

**Status**: Active Development ⚠️

## Planned Improvements (Rough Priority Order)
1. Fix streaming support (`astream`) with safe partial parsing ✓
2. Add full support for message dicts / content blocks ✓
  - Set LC_OUTPUT_VERSION="v1" to standardize content_blocks in Langchain, this is required. For more information: https://docs.langchain.com/oss/python/migrate/langchain-v1#standard-content
3. Enable image/multimodal inputs (vision models)
4. Improve parallel tool calling if BAML use-case justifies it
5. Possibly add sync interface (`.invoke`, `.stream`) wrappers for convenience
6. More complex agent/tool examples (LangGraph integration, ReAct-style loops)

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/thanhhuynhk17/ChatBaml.git
cd ChatBaml
uv venv
# source .venv/Scripts/activate  # Windows
source .venv/bin/activate # Linux/macOS
uv pip install -e .
```

### BAML Code Generation

```bash
# Auto-generate the baml_client directory with Python code to call your BAML functions
uv run baml-cli generate
```

### Environment Setup

Create a `.env` file with your API credentials:

```bash
OPENAI_MODEL_NAME="qwen3-vl"
OPENAI_BASE_URL="http://localhost:8000/v1"
OPENAI_API_KEY="sk_some_dummy_text"

# Set the default role in your .env when using an OpenAI-compatible server hosted by vLLM
DEFAULT_ROLE="user"
BAML_LOG=off # to disable Baml log

# Required for standardized content blocks in Langchain
LC_OUTPUT_VERSION="v1"
```

## 📋 Recent Test Results
**Model**: Qwen3-VL-4B — deployed on vLLM.
- Note: the vLLM tool-call parser feature is disabled; tool selection and parsing are handled via BAML.

**Run main.py**

```bash
(ChatBaml) vllm_user@idc-2-97:~/git_repos/ChatBaml$ uv run python main.py
```

**Command Output (last run with reply_to_user tool):**
```bash
2026-02-02T07:55:24.407 [BAML INFO] Function ChooseTool:
    Client: OpenAIGeneric (qwen3-vl) - 2670ms. StopReason: stop. Tokens(in/out): 202/71
    ---PROMPT---
    system: You are a helpful assistant.
          
    Answer in JSON-like string ( no double quotes in keys ) using this schema:
    {
      selected_tool: {
        // Add two integers.
        name: "add",
        arguments: {
          a: int,
          b: int,
        },
      } or {
        // Multiply two integers.
        name: "multiply",
        arguments: {
          x: int,
          y: int,
        },
      } or {
        // Use this tool when you want to send a natural language response shown to the user.
        name: "reply_to_user",
        arguments: {
          role: "assistant",
          content: string,
        },
      },
    }
    user: What's the sum of 2 and 45, and the product of 66 and 34?
    tool: Addition result: 47Multiplication result: 2244
    
    ---LLM REPLY---
    {
      "selected_tool": {
        "name": "reply_to_user",
        "arguments": {
          "role": "assistant",
          "content": "The sum of 2 and 45 is 47, and the product of 66 and 34 is 2244."
        }
      }
    }
    ---Parsed Response (class DynamicSchema)---
    {
      "selected_tool": {
        "name": "reply_to_user",
        "arguments": {
          "role": "assistant",
          "content": "The sum of 2 and 45 is 47, and the product of 66 and 34 is 2244."
        }
      }
    }
AI response: The sum of 2 and 45 is 47, and the product of 66 and 34 is 2244.
```

## 📋 Quick usage example

```python
import asyncio
import time
from langchain.messages import (
    HumanMessage,
    SystemMessage,
)
from custom_langchain_model.llms.chat_baml import ChatBaml
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain.tools import tool
from pydantic import BaseModel, Field

# Recommended: define tool input schemas using Pydantic BaseModel.
# Pydantic models provide validation, type hints, and descriptive fields that simplify BAML conversion.
class AddInput(BaseModel):
    """Add two integers."""
    a: str = Field(description="First integer to add")
    b: int = Field(default=5, description="Second integer to add")
@tool(args_schema=AddInput)
def add(a: int, b: int) -> int:
    return a + b

class MultiplyInput(BaseModel):
    """Multiply two integers."""
    x: str = Field(description="First integer to multiply")
    y: int = Field(default=5, description="Second integer to multiply")
@tool(args_schema=MultiplyInput)
def multiply(x: int, y: int) -> int:
    return x * y

chat_baml = ChatBaml(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL_NAME")
)
chat_baml_with_tools = chat_baml.bind_tools([add, multiply])

messages = [
    SystemMessage(content="You are a helpful assistant that answers concisely."),
    HumanMessage(content="I have a pen, i have 3 others, boom, what result would be when i combined them")
]

async def main():
    # Streaming usage:
    async for chunk in chat_baml_with_tools.astream(messages):
        print(chunk.content, end="", flush=True)  

    # Async invoke
    result = await chat_baml_with_tools.ainvoke(messages)
    
if __name__=="__main__":
    asyncio.run(main())
```

## 🚀 Key Features

### Structure Output Enhancement
- BAML integration for structured output enhancement
- Automatic conversion of Pydantic BaseModel and LangChain `@tool` functions to BAML schemas
- Transparent BAML logging and debugging

### Agent Development
- LangChain integration for agent development
- Complete implementation (`_generate`, `_stream`, `bind_tools`)
- Tool call conversion system (`convert_to_baml_tool`)

### Streaming Support
- Implemented synchronous `_stream()`; async `_astream()` derived automatically via LangChain's `run_in_executor` with zero additional effort
- invoke/ainvoke and stream/astream can be used
- Tool calls will be waited until final response

### Tool Integration
- **Seamless schema generation**: Auto-convert Pydantic `BaseModel` and LangChain `@tool` decorators into BAML function schemas
- **LLM-agnostic tool calling**: Works with virtually any LLM — no native tool-calling support required (BAML handles orchestration). Only requires an LLM capable of following structured instructions for tool invocation.

## convert_to_baml_tool Usage

The `convert_to_baml_tool` function in `custom_langchain_model/helpers/parse_json_schema.py` automatically converts tools to BAML schemas.

### Supported Tool Types

#### 1. Pydantic BaseModel (Recommended)

```python
from pydantic import BaseModel, Field

class AddTool(BaseModel):
    """Use this tool when you need to add two integers."""
    a: int = Field(..., description="First integer to add")
    b: int = Field(..., description="Second integer to add")

class MultiplyTool(BaseModel):
    """Use this tool when you need to multiply two integers."""
    a: int = Field(..., description="First integer to multiply")
    b: int = Field(..., description="Second integer to multiply")
```

#### 2. LangChain @tool Decorated Functions

**Important**: `@tool` functions must use `@tool(parse_docstring=True)` and have well-documented docstrings with Args and Returns sections.

```python
from langchain.tools import tool

@tool(parse_docstring=True)
def count_words(text: str) -> int:
    """Count the number of words in the provided text.
    
    Counts words by splitting on whitespace. Returns the total number of words.
    
    Args:
        text (str): Input text to count words from.
    
    Returns:
        int: Number of words in the input text.
    """
    if text is None:
        return 0
    words = re.findall(r"\S+", text.strip())
    return len(words)
```

### Usage Example

```python
from custom_langchain_model.helpers.parse_json_schema import convert_to_baml_tool
from baml_client import b
from baml_client.types import BamlState, BaseMessage

# Convert tools to BAML schema
tb = convert_to_baml_tool(
    tools=[AddTool, MultiplyTool, count_words],
    property_name="structure_output",
    is_multiple_tools=True
)

# Create BAML state
baml_state = BamlState(
    messages=[
        BaseMessage(
            role='system',
            content="You are an agent that can help with many tasks. Follow instructions and provide concise, useful responses."
        ),
        BaseMessage(
            role='user',
            content='I have a pen, i have 3 others, boom, what result would be when i combined them'
        )
    ]
)

# Call BAML function
response = await b.ChooseTool(baml_state, {"tb": tb}) # b is async client
print(f"Selected tool: {response.structure_output}") # response with property_name="structure_output"
```

**Real Test Output**:
```
Selected tool: [{'action': 'tool_AddTool', 'a': 1, 'b': 3}]
```

### BAML Logging (Transparent)

The BAML integration provides transparent logging that shows exactly what's happening under the hood:

```bash
(ChatBaml) vllm_user@idc-2-97:~/git_repos/ChatBaml$ PYTHONPATH=. uv run python custom_langchain_model/helpers/parse_json_schema.py
2026-01-25T12:33:40.428 [BAML INFO] Function ChooseTool:
    Client: ChatBaml (qwen3-vl) - 319ms. StopReason: stop. Tokens(in/out): 289/42
    ---PROMPT---
    system: Answer in JSON using this schema:
    {
      structure_output: [
        {
          // Use this tool when you found that you need to quickly add two integers.
          action: "tool_AddTool",
          // First integer to add
          a: int,
          // Second integer to add
          b: int,
        } or {
          // Use this tool when you found that you need to quickly multiply two integers.
          action: "tool_MultiplyTool",
          // First integer to multiply
          a: int,
          // Second integer to multiply
          b: int,
        } or {
          // Count the number of words in the provided text. Counts words by splitting on whitespace. Returns the total number of words.
          action: "tool_count_words",
          // Input text to count words from.
          text: string,
        } or {
          // Use this tool when you want to send a natural language response shown to the user. Write naturally, kindly, concisely when possible.
          action: "reply_to_user",
          message: {
            role: "assistant",
            content: string,
          },
        }
      ],
    }
              
    You are an agent that can help with many tasks. Follow instructions and provide concise, useful responses.
    user: I have a pen, i have 3 others, boom, what result would be when i combined them
    
    ---LLM REPLY---
    ```json
    {
      "structure_output": [
        {
          "action": "tool_AddTool",
          "a": 1,
          "b": 3
        }
      ]
    }
    ```
    ---Parsed Response (class DynamicSchema)---
    {
      "structure_output": [
        {
          "action": "tool_AddTool",
          "a": 1,
          "b": 3
        }
      ]
    }
response:
structure_output=[{'action': 'tool_AddTool', 'a': 1, 'b': 3}]
```


## Requirements

- Key dependencies:
  - `baml-py>=0.218.0`
  - `langchain>=1.0.0`
  - `langgraph>=1.0.0`
  - `pydantic>=2.12.3`
  - `pydantic-settings>=2.11.0`

## References

For more implementation details:

- **Original repository**: [tranngocphu/custom_langchain_chat_model](https://github.com/tranngocphu/custom_langchain_chat_model)
- **Connect to a custom model**: https://docs.langchain.com/langsmith/custom-endpoint
- **custom_chat_model.py from Langchain**: https://github.com/langchain-ai/langsmith-model-server/blob/main/app/custom_chat_model.py
