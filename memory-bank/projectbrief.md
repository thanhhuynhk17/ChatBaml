# Project Brief: BAML + LangChain Integration

**Project Name**: ChatBaml - Custom LangChain Chat Model with BAML Integration  
**Created**: January 25, 2026  
**Status**: Active Development  
**Version**: 0.1.0

## Project Overview

This project extends a Custom LangChain Chat Model to integrate with BAML (BoundaryML), creating a bridge between LangChain's powerful LLM orchestration capabilities and BAML's structured data extraction and function calling features.

## Core Objectives

1. **BAML Integration**: Enable LangChain models to leverage BAML's structured output capabilities
2. **Tool Conversion**: Automatically convert Pydantic models and LangChain tools to BAML schemas
3. **Dynamic Configuration**: Support runtime model and parameter configuration through BAML's ClientRegistry
4. **Enhanced Function Calling**: Improve tool selection and execution with BAML's structured approach

## Project Scope

### In Scope
- Custom LangChain chat model wrapper (`ChatBaml` class)
- Pydantic model to BAML schema conversion (`parse_json_schema.py`)
- BAML function integration with LangChain workflows
- Environment-based configuration management
- Tool selection and execution patterns
- Testing framework for BAML + LangChain integration

### Out of Scope
- Standalone BAML applications (focus is on LangChain integration)
- Non-LangChain LLM integrations
- Production deployment infrastructure
- UI/UX components

## Key Requirements

### Functional Requirements
- [FR-001] LangChain models must be able to call BAML functions seamlessly
- [FR-002] Pydantic models must be automatically convertible to BAML schemas
- [FR-003] BAML client configuration must be dynamically configurable at runtime
- [FR-004] Tool selection must support both single and multiple tool execution patterns
- [FR-005] Environment variables must control API credentials and endpoints

### Technical Requirements
- [TR-001] Support OpenAI-compatible API endpoints
- [TR-002] Maintain LangChain compatibility for existing workflows
- [TR-003] Support VLLM with proper role configuration
- [TR-004] Provide type-safe BAML schema generation
- [TR-005] Enable streaming responses where supported

## Success Criteria

1. **Integration Success**: LangChain workflows can successfully call BAML functions
2. **Tool Conversion**: Pydantic models convert to BAML schemas without manual intervention
3. **Configuration Flexibility**: Runtime model switching works seamlessly
4. **Performance**: No significant performance degradation compared to native LangChain
5. **Developer Experience**: Clear documentation and examples for integration

## Constraints

- **Language**: Python 3.13+
- **Dependencies**: LangChain >= 1.0.0, BAML >= 0.218.0
- **API Compatibility**: Must maintain OpenAI-compatible API structure
- **Security**: API credentials must be environment-based, not hardcoded

## Assumptions

- Users have existing LangChain workflows they want to enhance with BAML
- BAML functions are available and properly configured
- OpenAI-compatible API endpoints are accessible
- Development team is familiar with both LangChain and BAML concepts

## Dependencies

- **Primary**: LangChain, BAML, Pydantic
- **Secondary**: httpx, pydantic-settings
- **Development**: pytest, uv (package manager)

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| BAML API changes | High | Medium | Maintain compatibility layer |
| LangChain breaking changes | Medium | Low | Version pinning and testing |
| Performance overhead | Medium | Medium | Benchmark and optimize |
| Configuration complexity | Low | High | Comprehensive documentation |

## Project Phases

1. **Phase 1**: Core integration (ChatBaml class, basic BAML function calls)
2. **Phase 2**: Tool conversion system (Pydantic to BAML schema conversion)
3. **Phase 3**: Advanced features (streaming, multiple tool selection, validation)
4. **Phase 4**: Testing and documentation (comprehensive test suite, examples)

## Stakeholders

- **Primary**: AI/ML developers integrating LangChain with BAML
- **Secondary**: DevOps teams managing LLM infrastructure
- **Tertiary**: End users of AI applications using the integrated system