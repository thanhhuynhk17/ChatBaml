# System Patterns: BAML + LangChain Integration Architecture

## System Overview

The ChatBaml system creates a bridge between LangChain's workflow orchestration and BAML's structured data extraction capabilities. The architecture follows a layered pattern with clear separation of concerns.

## Core Architecture Patterns

### 1. Adapter Pattern: ChatBaml Class

**Purpose**: Wrap BAML functionality within LangChain's BaseChatModel interface

**Implementation**:
```python
class ChatBaml(BaseChatModel):
    # LangChain interface methods
    def _generate(self, messages, **kwargs): ...
    def _agenerate(self, messages, **kwargs): ...
    
    # BAML integration
    @property
    def b(self): return baml_root_client.with_options(...)
```

**Benefits**:
- Zero breaking changes to existing LangChain code
- Familiar interface for LangChain developers
- Automatic compatibility with LangChain tools and agents

### 2. Factory Pattern: Tool Conversion System

**Purpose**: Automatically convert Pydantic models and LangChain tools to BAML schemas

**Implementation**:
```python
def convert_to_baml_tool(tools, property_name, is_multiple_tools):
    # Convert each tool to OpenAI function schema
    # Parse schema to BAML type
    # Create union types for multiple tools
    # Add to DynamicSchema
```

**Benefits**:
- Automatic schema generation
- Type safety through BAML's type system
- Support for both single and multiple tool selection

### 3. Strategy Pattern: Client Configuration

**Purpose**: Support multiple LLM providers and dynamic configuration

**Implementation**:
```python
def _get_client_registry(self):
    cr = ClientRegistry()
    cr.add_llm_client(
        name=client_name,
        provider=self.provider,
        options=options
    )
    return cr
```

**Benefits**:
- Runtime model switching
- Environment-based configuration
- Support for multiple providers (OpenAI, VLLM, etc.)

### 4. Observer Pattern: Callback System

**Purpose**: Provide unified logging and monitoring across LangChain and BAML

**Implementation**:
```python
class AsyncChatCallbackHandler(AsyncCallbackHandler):
    async def on_chain_start(self, serialized, inputs, **kwargs): ...
    async def on_llm_end(self, response, **kwargs): ...
    async def on_tool_start(self, serialized, input_str, **kwargs): ...
```

**Benefits**:
- Unified logging across both frameworks
- Performance monitoring and debugging
- Integration with existing LangChain callback systems

## Data Flow Patterns

### 1. Tool Selection Flow

```
User Input → LangChain Graph → ChatBaml → BAML Function → Response → LangChain
```

**Steps**:
1. User provides input to LangChain workflow
2. LangChain graph routes to ChatBaml model
3. ChatBaml calls BAML function (e.g., ChooseTool)
4. BAML function processes input and selects tools
5. Response flows back through LangChain graph
6. Final output delivered to user

### 2. Schema Conversion Flow

```
Pydantic Model → OpenAI Schema → BAML Schema → Dynamic Type
```

**Steps**:
1. Developer defines Pydantic model with Field descriptions
2. `convert_to_openai_tool()` converts to OpenAI function schema
3. `parse_json_schema()` converts to BAML type system
4. Type added to DynamicSchema for runtime access
5. BAML functions can use the generated types

### 3. Configuration Flow

```
Environment → Settings → ClientRegistry → BAML Client → LLM Provider
```

**Steps**:
1. Environment variables loaded via pydantic-settings
2. Settings object provides configuration
3. ClientRegistry creates configured LLM client
4. BAML client uses configured client for API calls
5. LLM provider receives properly formatted requests

## Integration Patterns

### 1. LangChain Graph Integration

**Pattern**: Use ChatBaml within LangGraph workflows

**Example**:
```python
def llm_node(state: GeneralChatState, runtime: Runtime):
    model = ChatBaml(engine=context.engine).bind_tools(simple_tools)
    ai = await model.ainvoke([sys] + non_system, context=context)
    return {"messages": [ai]}
```

**Benefits**:
- Seamless integration with existing LangGraph patterns
- Support for tool calling and function execution
- Maintains LangGraph's state management

### 2. BAML Function Integration

**Pattern**: Access BAML functions through ChatBaml.b property

**Example**:
```python
response = model.b.ChooseTool(baml_state, {"tb": tb})
```

**Benefits**:
- Direct access to BAML functions
- Type-safe function calls
- Automatic client configuration

### 3. Tool Binding Pattern

**Pattern**: Bind tools to ChatBaml instances for function calling

**Example**:
```python
model_with_tools = model.bind_tools([search_tool, calc_tool])
```

**Benefits**:
- Familiar LangChain tool binding pattern
- Automatic tool schema generation
- Support for both Pydantic and @tool decorated functions

## Error Handling Patterns

### 1. Configuration Validation

**Pattern**: Validate configuration at initialization

**Implementation**:
```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    if self.provider != "openai-generic":
        raise ValueError("ChatBaml currently only supports provider='openai-generic'")
```

**Benefits**:
- Early error detection
- Clear error messages
- Prevents runtime failures

### 2. API Error Handling

**Pattern**: Graceful handling of API failures and timeouts

**Implementation**:
```python
async def _chat_completion_request(self, messages, **kwargs):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API error: {e}")
        raise
```

**Benefits**:
- Robust error handling
- Proper logging and debugging
- Graceful degradation

### 3. Schema Validation

**Pattern**: Validate BAML schema generation

**Implementation**:
```python
def parse_json_schema(json_schema, tb):
    if tools is None or len(tools) == 0:
        raise ValueError("At least one tool must be provided")
    # Schema parsing logic with validation
```

**Benefits**:
- Prevents invalid schema generation
- Clear error messages for developers
- Type safety enforcement

## Performance Patterns

### 1. Caching Strategy

**Pattern**: Cache BAML client configurations and schema generation

**Implementation**:
```python
class SchemaAdder:
    def __init__(self, tb, schema):
        self._ref_cache = {}
        self._class_cache = {}
```

**Benefits**:
- Reduced schema generation overhead
- Faster tool conversion
- Better performance for repeated operations

### 2. Connection Management

**Pattern**: Efficient HTTP connection management

**Implementation**:
```python
async def _chat_completion_request(self, messages, **kwargs):
    async with httpx.AsyncClient(timeout=20) as client:
        # Reuse connections for multiple requests
```

**Benefits**:
- Reduced connection overhead
- Better performance under load
- Proper resource cleanup

### 3. Async Patterns

**Pattern**: Leverage async/await for non-blocking operations

**Implementation**:
```python
async def _agenerate(self, messages, **kwargs):
    # Async implementation for better performance
```

**Benefits**:
- Non-blocking operations
- Better concurrency
- Improved responsiveness

## Security Patterns

### 1. Credential Management

**Pattern**: Environment-based credential management

**Implementation**:
```python
def get_access_token():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No OpenAI API key provided")
```

**Benefits**:
- No hardcoded credentials
- Environment-based configuration
- Secure credential handling

### 2. Input Validation

**Pattern**: Validate all inputs before processing

**Implementation**:
```python
def convert_to_baml_tool(tools, property_name, is_multiple_tools):
    if property_name is None or len(property_name.strip()) == 0:
        raise ValueError("property_name must be provided and non-empty")
```

**Benefits**:
- Prevents injection attacks
- Ensures data integrity
- Clear error handling

## Testing Patterns

### 1. Unit Testing

**Pattern**: Test individual components in isolation

**Implementation**:
```python
def test_convert_to_baml_tool_single_selection():
    tb = convert_to_baml_tool(tools=SMALL_TOOL_LIST, property_name="selected_tool")
    assert tb is not None
```

**Benefits**:
- Isolated component testing
- Fast test execution
- Clear failure identification

### 2. Integration Testing

**Pattern**: Test component interactions

**Implementation**:
```python
def test_baml_execution_with_tools():
    # Test BAML function calls with converted tools
    response = b.ChooseTool(bamlState, {"tb": tb})
    assert response is not None
```

**Benefits**:
- End-to-end functionality testing
- Integration validation
- Real-world scenario testing

### 3. Mock Testing

**Pattern**: Use mocks for external dependencies

**Implementation**:
```python
@patch('httpx.AsyncClient')
def test_api_error_handling(mock_client):
    # Test error handling with mocked HTTP client
```

**Benefits**:
- Isolated testing without external dependencies
- Controlled test environments
- Faster test execution

## Deployment Patterns

### 1. Configuration Management

**Pattern**: Environment-based configuration with fallbacks

**Implementation**:
```python
class Settings(BaseSettings):
    API_OAUTH_URL: str
    API_BASE_URL: str
    API_KEY: str
    API_SECRET: str
    
    model_config = ConfigDict(env_file=".env", extra="allow")
```

**Benefits**:
- Environment-specific configurations
- Secure credential management
- Easy deployment across environments

### 2. Monitoring and Observability

**Pattern**: Comprehensive logging and metrics

**Implementation**:
```python
logger = logging.getLogger(__name__)
async def on_chain_start(self, serialized, inputs, **kwargs):
    logger.info(f"Chain started: {kwargs.get('name')}")
```

**Benefits**:
- Operational visibility
- Performance monitoring
- Debugging capabilities

### 3. Scalability Patterns

**Pattern**: Design for horizontal scaling

**Implementation**:
- Stateless design where possible
- Connection pooling
- Efficient resource usage

**Benefits**:
- High availability
- Performance under load
- Cost-effective scaling

## Documentation Patterns

### README.md Structure
- **Fork Documentation**: Clearly document this as a fork with enhancements
- **Usage Examples**: Provide concrete examples for each major feature
- **Configuration Guide**: Document environment variables and setup
- **API Reference**: Document public interfaces and methods

### Memory Bank System
- **projectbrief.md**: Project scope and objectives
- **productContext.md**: User experience and problem-solving focus
- **systemPatterns.md**: Architecture and design patterns
- **techContext.md**: Technical stack and development setup
- **activeContext.md**: Current development focus and recent changes
- **progress.md**: Development status and milestone tracking

### Code Documentation
- **Type Hints**: Comprehensive type annotations for all functions
- **Docstrings**: Detailed docstrings following Google style
- **Inline Comments**: Explain complex logic and business rules
- **Architecture Comments**: Document design decisions and trade-offs

### BAML Logging Documentation
- **Transparent Logging**: Show real BAML function calls and LLM prompts
- **Performance Metrics**: Include response times and token usage
- **Error Examples**: Document common errors and solutions
- **Integration Examples**: Show end-to-end workflows with logging output
