# Custom LangChain Chat Model

LangChain and LangGraph is powerful frameworks for orchestrating language model workflows, but sometimes you need to use a private or proprietary LLM API (for example, your company's internal model, or a paid API with custom authentication). This repository provides working code that builds a custom chat model **fully compatible** with LangChain and LangGraph APIs.

## Tutorial

See [Tutorial](tutorial.md) for detailed steps to create custom LangChain model.


## Requirements

- Python >= 3.13
- Key dependencies
	- langchain >= 1.0.0
	- langgraph >= 1.0.0
	- pydantic >= 2.12.3
	- pydantic-settings >= 2.11.0

## Installation

Clone this repo, create and activate a virtual environment, then install the package in editable mode:

```bash
git clone https://github.com/tranngocphu/custom_langchain_chat_model.git
cd custom_langchain_chat_model
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

## Environment variables

The project uses `pydantic-settings` to load configuration from environment variables or a `.env` file. Create a `.env` file at the project root with these variables:

<pre style="white-space: pre; overflow-x: auto;">
API_OAUTH_URL="https://your_base_api_url/oauth/token"
API_BASE_URL="https://your_base_api_url/openai/deployments/{model}/chat/completions"
API_KEY="your_api_key"
API_SECRET="your_api_secret"
</pre>

- `API_BASE_URL` is used in `custom_langchain_model/llms/models.py` and is expected to be a format string with a `{model}` placeholder. You must update your custom model if this pattern doesn't apply in your case.
- This repo assumes you need API key and API secret to request a bearer token via `API_OAUTH_URL`. You must update authentication mechanism in the custom model according to the specs of your private LLM API.

## Quick run

Run the example runner in `main.py` (this uses the graph-based example and prints an AI response):

```bash
python main.py
```

## Full example walkthrough: [full_example.py](full_example.py)
```bash
python full_example.py
```

In this example, the private LLM is provided with 2 simple math tools: `add` and `multiply`. A user prompt requests the graph to calculate sum and product of 2 integers. The callback handlers will log the full execution events of a graph invocation as follows.

<pre style="white-space: pre; overflow-x: auto;">
You asked: What's the sum of 47 and 42, and the product of 33 and 18?
[21:00:56,275] [INFO] custom_langchain_model.llms.callbacks: Chain started: name LangGraph, run_id ee694423-5fb9-4d45-83bc-eb9f48fe2dba, parent_run_id: None
[21:00:56,276] [INFO] custom_langchain_model.llms.callbacks: Chain started: name llm, run_id 49a5bb4d-67b3-43a1-b39e-76c67ed3e459, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:56,277] [INFO] custom_langchain_model.llms.callbacks: Chat model started: name AzureOpenAI_gpt-4o, run_id b54776f3-4bdc-4ecc-8dbc-81a41a4f8794, parent_run_id: 49a5bb4d-67b3-43a1-b39e-76c67ed3e459
[21:00:56,277] [INFO] custom_langchain_model.llms.callbacks: Chat model started with messages: What's the sum of 47 and 42, and the product of 33 and 18?
[21:00:56,970] [INFO] custom_langchain_model.core.security: Fetched new access token
[21:00:58,460] [INFO] custom_langchain_model.llms.callbacks: Chat model ended: name None, run_id b54776f3-4bdc-4ecc-8dbc-81a41a4f8794, parent_run_id: 49a5bb4d-67b3-43a1-b39e-76c67ed3e459
[21:00:58,461] [INFO] custom_langchain_model.llms.callbacks: Chain started: name router, run_id 2f9b27fc-ba4f-42ad-83f1-ad9ba9516081, parent_run_id: 49a5bb4d-67b3-43a1-b39e-76c67ed3e459
[21:00:58,462] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id 2f9b27fc-ba4f-42ad-83f1-ad9ba9516081, parent_run_id: 49a5bb4d-67b3-43a1-b39e-76c67ed3e459
[21:00:58,462] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id 49a5bb4d-67b3-43a1-b39e-76c67ed3e459, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:58,463] [INFO] custom_langchain_model.llms.callbacks: Chain started: name tools, run_id 078ee3fe-cc72-40b0-a4d6-8a10a8be8495, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:58,464] [INFO] custom_langchain_model.llms.callbacks: Tool {'name': 'add', 'description': 'Add two integers.'} started with input: {'a': 47, 'b': 42}.
[21:00:58,465] [INFO] custom_langchain_model.llms.callbacks: Tool {'name': 'multiply', 'description': 'Multiply two integers.'} started with input: {'x': 33, 'y': 18}.
[21:00:58,465] [INFO] custom_langchain_model.llms.callbacks: Tool add ended with output: content='89' name='add' tool_call_id='call_1aiqjdVVmzbZzuK7Q6vDfUkj'
[21:00:58,466] [INFO] custom_langchain_model.llms.callbacks: Tool multiply ended with output: content='594' name='multiply' tool_call_id='call_0XimgvDX3aio2AeDzknfTEAg'
[21:00:58,467] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id 078ee3fe-cc72-40b0-a4d6-8a10a8be8495, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:58,467] [INFO] custom_langchain_model.llms.callbacks: Chain started: name llm, run_id dd4ed834-9ff1-4aec-a007-f0538c38cfdf, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:58,468] [INFO] custom_langchain_model.llms.callbacks: Chat model started: name AzureOpenAI_gpt-4o, run_id 8a3f8b68-f75e-4d5e-a2a9-41c895b4cd47, parent_run_id: dd4ed834-9ff1-4aec-a007-f0538c38cfdf
[21:00:58,468] [INFO] custom_langchain_model.llms.callbacks: Chat model started with messages: 594
[21:00:58,468] [INFO] custom_langchain_model.core.security: Using cached access token
[21:00:59,761] [INFO] custom_langchain_model.llms.callbacks: Chat model ended: name None, run_id 8a3f8b68-f75e-4d5e-a2a9-41c895b4cd47, parent_run_id: dd4ed834-9ff1-4aec-a007-f0538c38cfdf
[21:00:59,761] [INFO] custom_langchain_model.llms.callbacks: Chain started: name router, run_id fd1a1392-7a12-4136-a87b-fb4a2dfc6156, parent_run_id: dd4ed834-9ff1-4aec-a007-f0538c38cfdf
[21:00:59,762] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id fd1a1392-7a12-4136-a87b-fb4a2dfc6156, parent_run_id: dd4ed834-9ff1-4aec-a007-f0538c38cfdf
[21:00:59,762] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id dd4ed834-9ff1-4aec-a007-f0538c38cfdf, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:59,763] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id ee694423-5fb9-4d45-83bc-eb9f48fe2dba, parent_run_id: None
AI response: The sum of 47 and 42 is 89, and the product of 33 and 18 is 594.
</pre>


## Codebase overview
<pre style="white-space: pre; overflow-x: auto;">
|─ custom_langchain_model/  #
|   ├─ core/
|   │  ├─ __init__.py
|   │  ├─ config.py         #  load env variables from .env to settings object
|   │  ├─ logging.py        #  configurate logging for callback handlers
|   │  └─ security.py       #  get and globally store private LLM API access token
|   ├─ llms/
|   │  ├─ __init__.py
|   │  ├─ callbacks.py      #  define callback handlers
|   │  ├─ contexts.py       #  define LangGraph context schema (pydantic object)
|   │  ├─ graphs.py         #  define LangGraph chat flow 
|   │  ├─ models.py         #  define custom LangChain chat mode wrapping private LLM API
|   │  ├─ states.py         #  define LangGaph state schema (pydandic object)
|   │  └─ tools.py          #  define tools used with LangGraph model
|   └─ __init__.py
├─ .env.sample              #  example of .env
├─ full_example.py          #  full example of using the custom model with LangGraph
├─ README.md
├─ main.py                  #  code quick run
├─ pyproject.toml           #  project configuration and dependencies
└─ tutorial.md              #  tutorial for building custom chat model
</pre>

## Tool Definition Guide for Pydantic Models

This section explains how to properly define tools using Pydantic models for use with the ChatBaml system.

### Basic Tool Structure

```python
from pydantic import BaseModel, Field

class MyTool(BaseModel):
    """Use this tool when you need to [describe purpose]."""
    param1: type = Field(..., description="Description of param1")
    param2: type = Field(..., description="Description of param2")
    # Optional parameters without default values will be marked as optional in BAML
    optional_param: type = Field(None, description="Optional parameter")
```

### Key Requirements

1. **Class Description**: The docstring becomes the tool description in BAML
2. **Field Descriptions**: Each parameter needs a description via `Field(..., description="...")`
3. **Required vs Optional**: 
   - Required: `Field(..., description="...")`
   - Optional: `Field(None, description="...")` or `Field(default_value, description="...")`

### Example: Math Tools

```python
class AddTool(BaseModel):
    """Use this tool when you found that you need to quickly add two integers."""
    a: int = Field(..., description="First integer to add")
    b: int = Field(..., description="Second integer to add")

class MultiplyTool(BaseModel):
    """Use this tool when you found that you need to quickly multiply two integers."""
    a: int = Field(..., description="First integer to multiply")
    b: int = Field(..., description="Second integer to multiply")
```

### Usage with parse_json_schema.py

```python
from langchain_core.utils.function_calling import convert_to_openai_tool
from custom_langchain_model.helpers.parse_json_schema import parse_json_schema
from baml_client.type_builder import TypeBuilder

# Convert Pydantic model to OpenAI tool format
add_schema = convert_to_openai_tool(AddTool)
multiply_schema = convert_to_openai_tool(MultiplyTool)

# Create BAML type builder
tb = TypeBuilder()

# Parse each tool
add_tool_type = parse_json_schema(add_schema, tb)
multiply_tool_type = parse_json_schema(multiply_schema, tb)

# Create union for multiple tools
tools_union = tb.list(tb.union([add_tool_type, multiply_tool_type]))
tb.DynamicSchema.add_property("data", tools_union)
```

This automatically generates the proper BAML schema with:
- Action property with `tool_<name>` pattern
- Proper field types and descriptions
- Union types for multiple tools
- Integration with the BAML type system

### Advanced Features

- **Nested Objects**: Use `Field(..., description="...")` for nested Pydantic models
- **Enum Types**: Use `Literal` types for enum-like behavior
- **Default Values**: Include default values in `Field(default_value, description="...")`
- **Validation**: Pydantic validation rules are preserved in the BAML schema

## License

This project is licensed under the MIT License - see the LICENSE file for details.

If you find this project helpful, please consider:

⭐ Starring the repository   
🔗 Sharing it with others who might benefit   
💬 Contributing improvements or reporting issues
