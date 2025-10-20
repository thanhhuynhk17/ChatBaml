# Building a Custom Chat Model Fully Compatible with LangChain and LangGraph

---

## 0. Why Build a Custom Chat Model in LangChain?

LangChain and LangGraph is powerful frameworks for orchestrating language model workflows, but sometimes you need to use a private or proprietary LLM API (for example, your company's internal model, or a paid API with custom authentication). By building a custom model, you can:

- Integrate any LLM backend (private, on-prem, or custom cloud API)
- Make full use of LangChain and LangGraph's orchestration, tools, and graph features
- Add custom logging, security, and extensibility for your use case

This repo shows how to supercharge your custom model with beloved LangChain and LangGraph API.

---
## 1. What is covered

This repo shows you how to
- ✅ Make a wrapper of your private chat API that's **FULLY** compatible with LangChain and LangGraph ecosystem.
- ✅ Define Python functions as tools and bind tools to your chat model, so that LangChain automatically invokes the tools (when called) and passes tools' outputs to the next node in the graph.
- ✅ Use your custom LangChain model in a LangGraph chat flow with custom context.
- ✅ Write your callback handlers and pass callbacks to the graph so that you can perform custom logics when an graph event occurs.
- ✅ And most importantly, **make everything asynchronous** so that the code is readily to be used in your high-performance applications like FastAPI-based backends.

**This tutorial assumes that your LLM API support tool calling and is OpenAI-compatible. For simplicity, this implementation does not support token streaming yet.**

---

## 2. Implementing the Custom Model (`llms/models.py`)

The heart of LangChain integration is subclassing `BaseChatModel`. This makes your model compatible with LangChain's chains, graphs, and tool-calling APIs.

The following methods must be implemented for asynchronous invocation of your LLM API:
- `_chat_completion_request()`: The actual calls to your private LLM API happen here 
- `_agenerate()`: The asynchronous method to invoke the generation process. This method calls the `_chat_completion_request()` method.
- `_generate()`: The synchronous invocation method. We don't actually need this for asynchronous use cases, which is assumed by this tutorial. However, we must declare this method for the model to work, as required by LangChain.  

### 2.1 `_chat_completion_request(self, ...)` method

Sends the request to your private LLM API. Prepares the payload, sets headers (including authentication), and parses the response.   

I assume that the private LLM API uses a bearer token for authentication.

Note that you must use `httpx` here to make API call to your private LLM. Do not use `requests` as it doesn't support async calls.

```python
async def _chat_completion_request(
    self, 
    messages, 
    stop=None, 
    context=None, 
    stream=False, 
    tools=None, 
    tool_choice=None
) -> dict:
    # Feel free to pass message_history via context
    # or use other way to manage memory that fits
    # your use cases 
    message_history = context.message_history or []    
    messages = message_history + messages
    
    payload = {
        "messages": self._prepare_messages(messages),
        "stream": stream,
    }

    if tools:
        payload["tools"] = tools
    if tool_choice:
        payload["tool_choice"] = tool_choice
    
    # setup request header
    # see `core/security.py` for implementation of get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_access_token()}", 
    }
    
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
```

### 2.2 `_agenerate(self, ...)` method

This is the main async generation method, which orchestrates tool calls, context, and response parsing. This method returns a LangChain's ChatResult object.

```python
from langchain_core.outputs import ChatResult

async def _agenerate(
    self, 
    messages, 
    stop=None, 
    run_manager=None, 
    **kwargs
) -> ChatResult:
    
    config = kwargs.get("config") or {}
    configurable = config.get("configurable", {})
    
    tools = kwargs.get("tools") or configurable.get("tools")
    tool_choice = kwargs.get("tool_choice") or configurable.get("tool_choice")
    
    context = kwargs.get("context")
    stream = kwargs.get("stream", False)
    
    data = await self._chat_completion_request(
        messages, 
        stop=stop, 
        context=context, 
        stream=stream, 
        tools=tools, 
        tool_choice=tool_choice
    )
    
    # extract the message
    message_dict = data["choices"][0]["message"]
    # extract tool calls if any
    tool_calls_raw = message_dict.get("tool_calls") or []    
    # parsing tool calls, prepare for automatic tool invocations
    parsed_tool_calls = []    
    for tc in tool_calls_raw:
        if tc.get("type") == "function":
            fn = tc.get("function", {})
            name = fn.get("name")
            raw_args = fn.get("arguments", "") or "{}"
            try:
                args_obj = json.loads(raw_args)
            except Exception:
                args_obj = {"_raw": raw_args}
            parsed_tool_calls.append({
                "name": name, 
                "args": args_obj, 
                "id": tc.get("id", str(uuid.uuid4()))
            })
    
    content = message_dict.get("content") or ""
    
    # If returning an AI message with tool_calls, 
    # LangChain will run the tools for you.
    ai_msg = AIMessage(
        content=content, 
        tool_calls=parsed_tool_calls
    ) if parsed_tool_calls else AIMessage(content=content)
    
    generation = ChatGeneration(message=ai_msg, generation_info={"raw": data})
    
    return ChatResult(generations=[generation])
```

### 2.3 `_generate(self, ...)` method

This method is required for the custom model to run although it does nothing in async mode.

```python
def _generate(
    self, 
    messages, 
    stop=None,  
    **kwargs
) -> ChatResult:
    raise NotImplementedError("This model only supports async calls")   
```

### 2.4 `model_post_init(self, __context)` 

Sets up the model after initialization. Here, it configures the API endpoint using the engine name.

```python
class AzureOpenAICompatibleChat(BaseChatModel):
    def model_post_init(self, __context):
        self.endpoint = settings.API_BASE_URL.format(model=self.engine)
```

### 2.5 `_prepare_messages(self, messages)`

Converts LangChain message objects to the format expected by your API (role/content pairs).

```python
def _prepare_messages(self, messages: List[ChatMessage]) -> Dict[str, Any]:
    payload_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        else:
            role = "system"
        payload_messages.append({"role": role, "content": msg.content})
    return payload_messages
```

### 2.6 `bind_tools(self, ...)` and `_convert_tool(self, ...)`

Enable OpenAI-style tool/function calling by converting LangChain tools to the API's expected format.

**If your API requires other format for tool definition and tool calls, you must modify these method accordingly.**

```python
def bind_tools(self, tools, tool_choice=None):
    tool_specs = [self._convert_tool(tool) for tool in tools]
    extra = {"tools": tool_specs}
    if tool_choice is not None:
        extra["tool_choice"] = tool_choice
    return self.bind(**extra)


def _convert_tool(self, tool):
    if getattr(tool, "args_schema", None):
        schema = tool.args_schema.model_json_schema()
    else:
        schema = getattr(tool, "to_json_schema", lambda: {"type": "object", "properties": {}, "required": []})()
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema,
        },
    }
```


## 3. Event Handlers in `callbacks.py`

Callbacks let you hook into model and graph execution for logging, streaming, and error handling.

```python
class AsyncChatCallbackHandler(AsyncCallbackHandler):
    def __init__(self, context: GeneralChatContext = None):
        super().__init__()
        self.context = context

    async def on_chain_start(self, serialized, inputs: GeneralChatState, **kwargs):
        logger.info(f"Chain started: name {kwargs.get('name')}, run_id {kwargs.get('run_id')}, parent_run_id: {kwargs.get('parent_run_id')}")

    async def on_chain_end(self, outputs, **kwargs):
        logger.info(f"Chain ended: name {kwargs.get('name')}, run_id {kwargs.get('run_id')}, parent_run_id: {kwargs.get('parent_run_id')}")

    async def on_chain_error(self, error, **kwargs):
        logger.error(f"Chain error: {error}")

    async def on_chat_model_start(self, serialized, messages, **kwargs):
        logger.info(f"Chat model started with messages: {messages[0][-1].content}")

    async def on_llm_end(self, response, **kwargs):
        logger.info(f"Chat model ended. Response: {response.generations[0][0].message.content}")

    async def on_llm_error(self, error, **kwargs):
        logger.error(f"LLM error: {error}")

    async def on_tool_start(self, serialized, input_str, **kwargs):
        logger.info(f"Tool {serialized} started with input: {input_str}.")

    async def on_tool_end(self, output, **kwargs):
        logger.info(f"Tool ended with output: {output}")

    async def on_tool_error(self, tool_name, error, **kwargs):
        logger.error(f"Tool error: {tool_name} with error: {error}")
```

There are 2 ways of passing callback handlers to LangGraph.

### 3.1 Passing callback handlers during graph building

In this way, you pass a config object with callback handlers to the graph at compilation.

```python
graph = graph.compile(config={"callbacks": [AsyncChatCallbackHandler()]})
```

Note that we are not passing a context when creating the handler because at compilation time such context doesn't exist. Thus, if your callback handlers require access to context, you must pass the context during graph invocation.

### 3.1 Passing callback handlers during graph invocation

```python
# Prepare input
input_state = GeneralChatState(...)
# Prepare context
context = GeneralChatContext(...)
# Setup callback handler for async logging and other purposes
callback_handler = AsyncChatCallbackHandler(context=context)
# Invoke the graph asynchronously
resp = await graph.ainvoke(
    input_state,
    context=context,
    config={"callbacks": [callback_handler]}
)
```

See [`full_example.py`](full_example.py) for details.