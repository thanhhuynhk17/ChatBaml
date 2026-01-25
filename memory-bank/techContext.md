# Technical Context: BAML + LangChain Integration

## Technology Stack

### Core Dependencies

#### Primary Frameworks
- **LangChain** >= 1.0.0
  - Purpose: LLM workflow orchestration and tool management
  - Key Features: Agent patterns, tool binding, callback system
  - Integration: BaseChatModel interface for ChatBaml class

- **BAML (BoundaryML)** >= 0.218.0
  - Purpose: Structured data extraction and function calling
  - Key Features: Type-safe schemas, ClientRegistry, function generation
  - Integration: BAML client access through ChatBaml.b property

- **Pydantic** >= 2.12.3
  - Purpose: Data validation and model definitions
  - Key Features: BaseModel for tool definitions, Field descriptions
  - Integration: Automatic conversion to BAML schemas

#### Secondary Dependencies
- **pydantic-settings** >= 2.11.0
  - Purpose: Environment-based configuration management
  - Key Features: Settings classes, .env file loading
  - Integration: Configuration for API endpoints and credentials

- **httpx** (via BAML)
  - Purpose: HTTP client for API requests
  - Key Features: Async support, connection pooling
  - Integration: BAML client HTTP communication

- **langgraph** >= 1.0.0
  - Purpose: State machine and workflow management
  - Key Features: Graph-based workflows, state management
  - Integration: LangGraph workflows with ChatBaml nodes

### Development Tools

#### Package Management
- **uv** (recommended)
  - Python package manager with fast dependency resolution
  - Virtual environment management
  - Lock file generation (uv.lock)

#### Testing Framework
- **pytest** >= 9.0.2
  - Unit testing framework
  - Mock support for external dependencies
  - Integration testing capabilities

#### Code Quality
- **Black** (implied by project structure)
  - Code formatting
  - Consistent style enforcement

- **Ruff** (implied by project structure)
  - Linting and code analysis
  - Fast static analysis

### Supported LLM Providers

#### OpenAI-Compatible
- **OpenAI** (primary)
  - Models: gpt-4o, gpt-4, gpt-3.5-turbo
  - Features: Function calling, streaming, tool use
  - Configuration: API key, base URL, model selection

- **VLLM** (with modifications)
  - Models: Any OpenAI-compatible model
  - Features: High-performance inference
  - Configuration: Custom base URL, role configuration

#### Future Providers
- **Anthropic Claude**
  - Planned support for Claude models
  - Tool calling integration

- **Google Gemini**
  - Planned support for Gemini models
  - Function calling capabilities

## Development Setup

### Prerequisites

#### Python Environment
```bash
# Python version requirement
python >= 3.13

# Virtual environment setup
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

#### Package Installation
```bash
# Using uv (recommended)
uv pip install -e .

# Using pip
pip install -e .
```

### Environment Configuration

#### Required Environment Variables
```bash
# API Configuration
OPENAI_API_KEY="your_openai_api_key"
OPENAI_BASE_URL="https://api.openai.com/v1"
OPENAI_MODEL_NAME="gpt-4o"

# Alternative: Custom API (for private LLMs)
API_OAUTH_URL="https://your_base_api_url/oauth/token"
API_BASE_URL="https://your_base_api_url/openai/deployments/{model}/chat/completions"
API_KEY="your_api_key"
API_SECRET="your_api_secret"
```

#### Optional Configuration
```bash
# Logging
LOG_LEVEL="INFO"

# Performance
HTTP_TIMEOUT=20
CONNECTION_POOL_SIZE=10

# Development
DEBUG_MODE=true
```

### Project Structure

#### Source Code Organization
```
custom_langchain_model/
├── core/                    # Core configuration and utilities
│   ├── config.py           # Environment-based settings
│   ├── logging.py          # Logging configuration
│   └── security.py         # Authentication and token management
├── llms/                   # LangChain integration components
│   ├── callbacks.py        # LangChain callback handlers
│   ├── contexts.py         # LangGraph context schemas
│   ├── graphs.py           # LangGraph workflow definitions
│   ├── models.py           # Custom LangChain chat model
│   ├── states.py           # LangGraph state schemas
│   ├── tools.py            # Example tool definitions
│   ├── types.py            # Type definitions for providers
│   └── chat_baml.py        # BAML integration wrapper
└── helpers/                # Utility functions
    ├── __init__.py
    └── parse_json_schema.py # Pydantic to BAML conversion
```

#### BAML Configuration
```
baml_src/
├── chat_baml.baml          # BAML function definitions
├── clients.baml            # LLM client configurations
└── generators.baml         # Code generation settings
```

#### Testing Structure
```
test/
├── fixtures/               # Test data and mock objects
├── integration/            # Integration tests
├── unit/                   # Unit tests
└── utils/                  # Test utilities
```

### Development Workflow

#### Code Generation
```bash
# Generate BAML client code
baml generate

# Regenerate after schema changes
baml generate --force
```

#### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest test/unit/test_convert_to_baml_tool.py

# Run with coverage
pytest --cov=custom_langchain_model

# Run integration tests
pytest test/integration/
```

#### Code Quality
```bash
# Format code
black custom_langchain_model/

# Lint code
ruff check custom_langchain_model/

# Type checking
mypy custom_langchain_model/
```

### Build and Deployment

#### Package Building
```bash
# Build package
uv build

# Install in development mode
uv pip install -e .
```

#### Docker Support (Future)
```dockerfile
# Planned Dockerfile for containerized deployment
FROM python:3.13-slim
COPY . /app
WORKDIR /app
RUN pip install -e .
CMD ["python", "-m", "custom_langchain_model"]
```

### Performance Considerations

#### Memory Management
- **Connection Pooling**: HTTP connections reused across requests
- **Schema Caching**: BAML schemas cached to avoid regeneration
- **Async Operations**: Non-blocking I/O for better concurrency

#### Scalability
- **Stateless Design**: ChatBaml instances are stateless where possible
- **Configuration Caching**: ClientRegistry instances cached
- **Resource Cleanup**: Proper async context management

#### Monitoring
- **Logging**: Structured logging with appropriate levels
- **Metrics**: Performance metrics for API calls and conversions
- **Error Tracking**: Comprehensive error handling and reporting

### Security Considerations

#### Credential Management
- **Environment Variables**: No hardcoded credentials
- **Token Management**: Automatic token refresh and caching
- **Secure Storage**: Encrypted credential storage for production

#### Input Validation
- **Schema Validation**: All inputs validated against BAML schemas
- **Type Safety**: Pydantic models ensure type correctness
- **Injection Prevention**: Proper escaping and validation

#### Network Security
- **HTTPS**: All API calls use HTTPS
- **Timeouts**: Configurable timeouts prevent hanging requests
- **Rate Limiting**: Built-in rate limiting for API calls

### Troubleshooting

#### Common Issues

1. **BAML Generation Failures**
   ```bash
   # Check BAML syntax
   baml validate
   
   # Regenerate client code
   baml generate --force
   ```

2. **API Authentication Errors**
   ```bash
   # Check environment variables
   echo $OPENAI_API_KEY
   
   # Test token generation
   python -c "from custom_langchain_model.core.security import get_access_token; print(get_access_token())"
   ```

3. **Tool Conversion Failures**
   ```bash
   # Test conversion function
   python -c "from custom_langchain_model.helpers.parse_json_schema import convert_to_baml_tool; print('Conversion works')"
   ```

#### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
from custom_langchain_model.llms.chat_baml import ChatBaml
model = ChatBaml(model="gpt-4o")
print(model.b)  # Should show configured BAML client
```

### Future Enhancements

#### Planned Technologies
- **FastAPI**: REST API endpoints for BAML functions
- **Redis**: Caching layer for schema generation
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Dashboard for performance monitoring

#### Performance Optimizations
- **Lazy Loading**: Load BAML schemas on demand
- **Connection Reuse**: Optimize HTTP connection management
- **Parallel Processing**: Async processing for multiple tool conversions

#### Security Enhancements
- **OAuth2**: Support for OAuth2 authentication
- **JWT**: JSON Web Token support for API authentication
- **Encryption**: End-to-end encryption for sensitive data