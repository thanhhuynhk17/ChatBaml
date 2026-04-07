# ReactBaml Architecture & Implementation Guide

This document provides a comprehensive overview of the **ReactBaml** architecture within the `ChatBaml` repository. It is designed to help coding agents understand how the system bridges LangChain's agentic workflows with BAML's structured data extraction and prompt management.

## 1. Core Concept

**ReactBaml** is an implementation of the ReAct (Reason + Act) pattern that leverages **BAML (BoundaryML)** as the primary engine for:
- **Prompt Management**: Moving prompts out of Python code into `.baml` files.
- **Structured Output**: Ensuring LLM responses strictly follow defined schemas without complex parsing logic.
- **Tool Calling**: Converting LangChain tools/Pydantic models into BAML dynamic types at runtime.

The system acts as a custom LangChain `BaseChatModel` (the `ChatBaml` class), making it a drop-in replacement for standard LLM providers like `ChatOpenAI` or `ChatAnthropic`.

## 2. System Architecture

The architecture follows a layered approach:

| Layer | Component | Responsibility |
| :--- | :--- | :--- |
| **Orchestration** | LangGraph / LangChain Agents | Manages the high-level loop (Reasoning -> Action -> Observation). |
| **Adapter** | `ChatBaml` Class | Implements `BaseChatModel` interface. Handles message conversion and tool binding. |
| **Bridge** | `parse_json_schema.py` | Converts Pydantic/OpenAI tool schemas into BAML `TypeBuilder` types. |
| **Engine** | BAML Runtime | Executes functions, manages prompts, and ensures type-safe extraction. |
| **LLM** | OpenAI / VLLM / etc. | The underlying model providing the intelligence. |

## 3. Key Components

### 3.1 `ChatBaml` Class (`custom_langchain_model/llms/chat_baml.py`)
This is the heart of the integration.
- **`bind_tools()`**: Captures LangChain tools and stores them for later conversion.
- **`_generate()` / `_agenerate()`**: The main execution loop. It detects if tools are bound:
    - **No Tools**: Calls BAML `Chat()` function (simple text response).
    - **With Tools**: Calls BAML `ChooseTool()` function with a dynamic schema.
- **`_prepare_tb()`**: Uses the helper to build a BAML `TypeBuilder` from the bound tools.

### 3.2 Tool Conversion Pipeline (`custom_langchain_model/helpers/parse_json_schema.py`)
This module enables "Just-in-Time" schema generation for BAML.
- **`convert_to_baml_tool()`**: Takes a list of LangChain tools, converts them to OpenAI-style JSON schemas, and then maps those schemas to BAML `FieldType`s.
- **`SchemaAdder`**: A recursive parser that maps JSON types (string, object, array, etc.) to BAML's type system.
- **Dynamic Class**: It adds the tool definitions to BAML's `DynamicSchema` class at runtime.

### 3.3 BAML Definitions (`baml_src/chat_baml.baml`)
Defines the protocol between the Python code and the LLM.
- **`BamlState`**: Represents the conversation history.
- **`ChooseTool` Function**:
    - **Input**: `BamlState` + `DynamicSchema`.
    - **Output**: `string | DynamicSchema`.
    - **Prompt**: Uses `RenderMessages` template to inject the tool schema and format the history.
- **`RenderMessages` Template**: Handles multimodal content (images) and formats prior tool calls in a structured way (e.g., `<tool_call>` tags).

## 4. Data Flow (Tool Calling)

1. **Initialization**: User binds tools to `ChatBaml`.
2. **Invocation**: LangChain agent calls `invoke([messages])`.
3. **Conversion**: `ChatBaml` converts messages to `BamlState` and tools to a BAML `TypeBuilder`.
4. **BAML Call**: `ChooseTool(state, tb)` is executed.
5. **LLM Prompting**: BAML renders the prompt, including the tool schema in the `ctx.output_format`.
6. **Extraction**: BAML parses the LLM's JSON response into the dynamic tool class.
7. **Mapping Back**: `ChatBaml` converts the BAML result back into a LangChain `AIMessage` with `tool_calls`.

## 5. Implementation Details for Coding Agents

### Handling Messages
- BAML expects a specific `BaseMessage` structure.
- Use `custom_langchain_model/helpers/messages.py` to convert LangChain messages.
- **Important**: Ensure `LC_OUTPUT_VERSION=v1` is set in environment variables to use the standardized content block format in LangChain.

### Multimodal Support
- The system supports images.
- Images are converted to base64 or passed as URLs and rendered in the BAML prompt via the `img` property in `ContentBlock`.

### Tool Format
- Tools are rendered as BAML classes with two properties: `name` (a literal string) and `arguments` (a nested class containing the tool's parameters).
- This structure mimics the OpenAI tool calling format but is enforced by BAML's type system.

## 6. Development Workflow

1. **Modify BAML**: Edit `.baml` files in `baml_src/` for prompt or schema changes.
2. **Generate Client**: Run `baml generate` to update the Python client.
3. **Update Adapter**: Modify `ChatBaml` if new LangChain features are needed.
4. **Test**: Use `pytest` or the "Quick test" section in `chat_baml.py`.

---
*Note: This architecture is designed to be provider-agnostic. While it currently defaults to `openai-generic`, it can support any provider BAML supports (Anthropic, Gemini, etc.) by updating the `ClientRegistry` in `ChatBaml`.*
