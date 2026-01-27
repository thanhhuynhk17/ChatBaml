# ChatBaml: Custom LangChain Chat Model with BAML Integration

A project that extends a Custom LangChain Chat Model to integrate with BAML, creating a bridge between LangChain's powerful LLM orchestration capabilities and BAML's structured data extraction and function calling features.

**Fork of**: [tranngocphu/custom_langchain_chat_model](https://github.com/tranngocphu/custom_langchain_chat_model)  
**Status**: Active Development ⚠️

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
```

## 📋 Recent Test Results
**Model**: Qwen3-VL-30B-A3B-FP8 — deployed on vLLM.
- Note: the vLLM tool-call parser feature is disabled; tool selection and parsing are handled via BAML.

**Run main.py**

```bash
(ChatBaml) vllm_user@idc-2-97:~/git_repos/ChatBaml$ uv run python main.py
```

**Command Output:**

Multi-step reasoning
```bash
You asked: What's the sum of 73 and 93, and the product of 55 and 55?
// 1. Agent decided to call `add`
2026-01-27T10:23:01.436 [BAML INFO] Function ChooseTool:
    Client: OpenAIGeneric (qwen3-vl) - 340ms. StopReason: stop. Tokens(in/out): 178/40
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
    user: What's the sum of 73 and 93, and the product of 55 and 55?

    ---LLM REPLY---
    ```json
    {
      selected_tool: {
        name: "add",
        arguments: {
          a: 73,
          b: 93
        }
      }
    }
    ```
    ---Parsed Response (class DynamicSchema)---
    {
      "selected_tool": {
        "name": "add",
        "arguments": {
          "a": 73,
          "b": 93
        }
      }
    }

// 2. Agent decided to call `multiply`
2026-01-27T10:23:01.843 [BAML INFO] Function ChooseTool:
    Client: OpenAIGeneric (qwen3-vl) - 351ms. StopReason: stop. Tokens(in/out): 239/45
    user: What's the sum of 73 and 93, and the product of 55 and 55?
    assistant: Tool `add` was selected with arguments:
    {
      selected_tool: {
        name: "add",
        arguments: {
          a: 73,
          b: 93
        }
      }
    }
    tool: 166

    ---LLM REPLY---
    Tool `multiply` was selected with arguments:
    {
      selected_tool: {
        name: "multiply",
        arguments: {
          x: 55,
          y: 55
        }
      }
    }
    ---Parsed Response (class DynamicSchema)---
    {
      "selected_tool": {
        "name": "multiply",
        "arguments": {
          "x": 55,
          "y": 55
        }
      }
    }

// 3. Agent decided to call `reply_to_user` to finish task
2026-01-27T10:23:02.391 [BAML INFO] Function ChooseTool:
    Client: OpenAIGeneric (qwen3-vl) - 506ms. StopReason: stop. Tokens(in/out): 301/68
    user: What's the sum of 73 and 93, and the product of 55 and 55?
    assistant: Tool `add` was selected with arguments:
    {
      selected_tool: {
        name: "add",
        arguments: {
          a: 73,
          b: 93
        }
      }
    }
    tool: 166
    assistant: Tool `multiply` was selected with arguments:
    {
      selected_tool: {
        name: "multiply",
        arguments: {
          x: 55,
          y: 55
        }
      }
    }
    tool: 3025

    ---LLM REPLY---
    {
      selected_tool: {
        name: "reply_to_user",
        arguments: {
          role: "assistant",
          content: "The sum of 73 and 93 is 166, and the product of 55 and 55 is 3025."
        }
      }
    }
    ---Parsed Response (class DynamicSchema)---
    {
      "selected_tool": {
        "name": "reply_to_user",
        "arguments": {
          "role": "assistant",
          "content": "The sum of 73 and 93 is 166, and the product of 55 and 55 is 3025."
        }
      }
    }
AI response: The sum of 73 and 93 is 166, and the product of 55 and 55 is 3025.
```

## 📋 Usage

```python
from langchain.tools import tool
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b
@tool
def multiply(x: int, y: int) -> int:
    """Multiply two integers."""
    return x * y

chat_baml = ChatBaml(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL_NAME")
)
chat_baml_with_tools = chat_baml.bind_tools([add, multiply])

# Streaming usage
async for chunk in chat_baml_with_tools.astream(messages):
    print(chunk)

# Async invoke
result = await chat_baml_with_tools.ainvoke(messages)
```

## 🚀 Key Features

### Multi-Step Reasoning
- BAML correctly breaks down complex questions into multiple tool calls
- Automatic tool selection (`add`, `multiply`, `reply_to_user`)
- Context management across multiple tool calls
- Performance: 189-401ms per call with efficient token usage

### Async-Only Architecture
- Complete async implementation (`_agenerate`, `_astream`, `bind_tools`)
- Full tool conversion system (`convert_to_baml_tool`)
- Transparent BAML logging and debugging

### Tool Integration
- Automatic conversion of Pydantic BaseModel and LangChain `@tool` functions to BAML schemas
- End-to-end testing with real BAML functions

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

- Python >= 3.13
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