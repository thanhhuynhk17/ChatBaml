import os
from dotenv import load_dotenv, find_dotenv

from custom_langchain_model.helpers.render_agent_wants_to import (
    format_args_no_quote_keys, render_agent_wants_to
)
load_dotenv(find_dotenv())
import uuid
import json
import logging
from typing import Any, Dict, Iterator, List, Literal, Optional, Sequence, Union, Type, Callable
from pydantic import Field  # Import Field for metadata

from baml_py import ClientRegistry
from baml_client import (
    b as baml_root_client
)
from baml_client.types import (
    BamlState,
    BaseMessage as BamlBaseMessage,
    DynamicSchema
)
from baml_client.stream_types import DynamicSchema as DynamicSchemaChunk
from baml_client.type_builder import TypeBuilder
from baml_py import baml_py

from custom_langchain_model.helpers.parse_json_schema import convert_to_baml_tool

from custom_langchain_model.llms.types import Provider, Role, BamlAbortError

from langchain_core.language_models import BaseChatModel
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel

logger = logging.getLogger(__name__)

REPLY_TO_USER='reply_to_user'

class ChatBaml(BaseChatModel):
    """
    A LangChain-compatible Chat Model that wraps BAML.
    Allows runtime modification of model and parameters via BAML's ClientRegistry.
    """
    
    model: str = Field(
        default="gpt-4o",
        description="The name of the language model to use (e.g., 'gpt-4o' for OpenAI)."
    )
    temperature: float = Field(
        default=0.7,
        description="Controls randomness in model outputs (0.0 for deterministic, higher for creative)."
    )
    provider: Provider = Field(
        default="openai-generic",
        description="The LLM provider (e.g., 'openai-generic' for generic OpenAI-compatible endpoints)."
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authenticating with the LLM provider (overrides environment variables if set)."
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for the LLM API endpoint (useful for custom or proxy servers)."
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum number of tokens to generate in the response (limits output length)."
    )
    # Baml special args
    default_role: Optional[Role] = Field(
        default='user',
        description="Default role for messages in BAML (required as 'user' for VLLM compatibility)."
    )
    allowed_roles: Optional[List[str]] = Field(
        default=["system", "user", "assistant", "tool"],
        description="List of allowed roles for messages (defaults to system, user, assistant, tool)."
    )
    
    property_name: str = Field(
        default="selected_tool",
        description=(
            "Name of the property BAML uses to indicate the selected tool in its response. "
            "Defaults to 'selected_tool'. Change this if your BAML tool bundle returns the "
            "chosen tool under a different field name."
        ),
    )
    
    # Additional options
    additional_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary for any extra parameters not explicitly defined in the class."
    )

    @property
    def _llm_type(self) -> str:
        return "baml-chat-model"

    def _get_client_registry(self) -> ClientRegistry:
        """
        Creates and configures a BAML ClientRegistry instance for the current ChatBaml configuration.

        This method validates the provider, retrieves API credentials, and sets up the client registry
        with the appropriate configuration options. It ensures all required parameters are properly
        configured before creating the client.

        Returns:
            ClientRegistry: A configured BAML client registry ready for use

        Raises:
            ValueError: If the provider is not 'openai-generic' or if no API key is provided
        """
        # https://docs.boundaryml.com/ref/baml_client/client-registry
        
        if self.provider != "openai-generic":
            raise ValueError(
                f"ChatBaml currently only supports provider='openai-generic'. "
                f"Received: provider='{self.provider}'. "
                "Use a different wrapper class if you need other providers."
            )

        cr = ClientRegistry()

        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "No OpenAI API key provided. "
                "Either pass api_key=... when initializing ChatBaml, "
                "or set the OPENAI_API_KEY environment variable."
            )

        # options = {
        #     "model": self.model,
        #     "temperature": self.temperature,
        #     "api_key": api_key,
        # }
        options = {
            "model": self.model,
            "temperature": self.temperature,
            "api_key": api_key,
            "default_role": self.default_role,
            "allowed_roles": self.allowed_roles,
        }
        if self.base_url:
            options["base_url"] = self.base_url
        if self.max_tokens:
            options["max_tokens"] = self.max_tokens

        if self.additional_options:
            options.update(self.additional_options)

        # Use a stable, readable client name
        client_name = f"OpenAIGeneric"

        cr.add_llm_client(
            name=client_name,
            provider=self.provider,
            options=options,
        )
        cr.set_primary(client_name)
        return cr

    def _convert_to_baml_messages(self, messages: List[BaseMessage]) -> List[BamlBaseMessage]:
        """
        Converts LangChain messages to BAML BaseMessage format.

        This method maps LangChain message types to their corresponding BAML roles:
        - HumanMessage → "user"
        - AIMessage → "assistant"
        - SystemMessage → "system"
        - ToolMessage → "tool"

        Args:
            messages: List of LangChain BaseMessage objects to convert

        Returns:
            List[BamlBaseMessage]: List of converted BAML BaseMessage objects

        Raises:
            TypeError: If an unsupported message type is encountered
        """
        baml_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, ToolMessage):
                role = "tool"
            else:
                raise TypeError(
                    f"Unsupported message type: {type(msg).__name__}. "
                    "Expected one of: HumanMessage, AIMessage, SystemMessage, ToolMessage."
                )

            baml_messages.append(BamlBaseMessage(
                role=role,
                content=str(msg.content)
            ))

        return baml_messages

    def _prepare_tb(self,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
    ) -> Optional[TypeBuilder]:
        """
        Prepares a BAML TypeBuilder for tool execution.

        This method converts LangChain tools to BAML format using the convert_to_baml_tool helper.
        It includes the special "ReplyToUser" tool that routes tool outputs back into the chat
        as assistant messages. The method currently only supports single tool execution.

        Args:
            tools: List of tool dictionaries to convert to BAML format
            tool_choice: Optional tool choice specification (not yet implemented)

        Returns:
            Optional[TypeBuilder]: A configured BAML TypeBuilder for tool execution, or None if no tools

        Raises:
            ValueError: If tool conversion fails
            NotImplementedError: If tool_choice is provided (feature not yet implemented)
        """
        if tool_choice:
            raise NotImplementedError("Tool choice handling not implemented yet; will be added later")

        try:
            tb = convert_to_baml_tool(
                tools=tools or [],
                is_multiple_tools=False, # single / multiple tools
                property_name=self.property_name,
                # Predefined "ReplyToUser" tool used to route a tool's output back into the chat as an assistant (AI) message.
                include_reply_to_user=True
            )
            logger.debug(f"Successfully converted {len(tools)+1} tools ( ReplyToUser included ) to BAML format")
            return tb
        except Exception as e:
            logger.error(f"Failed to convert tools: {e}")
            raise ValueError(f"Tool conversion failed: {e}")

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """
        Streams BAML responses as LangChain ChatGenerationChunks with proper content accumulation.

        This method handles streaming responses from BAML, accumulating content across chunks
        and properly handling tool call streaming with partial arguments. It includes critical
        fixes for content accumulation and tool call handling.

        Args:
            messages: List of LangChain BaseMessage objects to process
            stop: Optional list of stop sequences (not yet implemented)
            run_manager: Optional callback manager for LLM run
            **kwargs: Additional arguments including tools and context

        Returns:
            Iterator[ChatGenerationChunk]: Iterator of ChatGenerationChunk objects

        Raises:
            NotImplementedError: If context or stop handling is requested (not yet implemented)
            BamlAbortError: If the BAML stream is aborted
        """
        context = kwargs.get("context")
        if context:
            raise NotImplementedError("context handling not implemented yet; will be added later")
        if stop:
            raise NotImplementedError("stop handling not implemented yet; will be added later")
        
        tools = kwargs.get('tools', [])
        tool_names = [ cls.name if hasattr(cls, 'name') else cls.__name__ for cls in tools ]
        # FIXME: REPLY_TO_USER now acting like a simple AIMessage, refactor later!
        tool_names += [REPLY_TO_USER]
        
        # Convert LangChain messages to BAML format
        baml_messages = self._convert_to_baml_messages(messages)
        # Create BamlState with converted messages
        baml_state = BamlState(messages=baml_messages)

        # Prepare type builder with dynamic schema for tools
        tb = self._prepare_tb(
            tools=tools
        )

        try:
            stream = self.b.stream.ChooseTool(
                baml_state, 
                {
                    "tb": tb
                }
            )

            prev_content: Union[str, list] = ""
            ai_message: Optional[AIMessageChunk] = None
            for partial in stream:
                partial_delta = self._extract_partial_delta(
                    partial=partial,
                    prev_content=prev_content
                )
                if partial_delta["tool_name"] not in ("", REPLY_TO_USER): # tool call not REPLY_TO_USER, yield full tool call at end
                    final = stream.get_final_response()
                    ai_message = self._convert_to_ai_message(
                        dynamic_schema=final,
                        is_streaming=True
                    )
                    generation_chunk = ChatGenerationChunk(message=ai_message)
                    yield generation_chunk
                    break
                
                # delta string for reply_to_user
                delta = partial_delta["delta"]
                if not delta:
                    logger.debug("No new delta in this chunk, skipping...")
                    continue
                if not ai_message: # first valid delta
                    ai_message = AIMessageChunk(
                        content=delta
                    )
                else:
                    ai_message = AIMessageChunk(
                        content=delta,
                        id=ai_message.id,
                    )
                generation_chunk = ChatGenerationChunk(message=ai_message)
                yield generation_chunk

                # update prev_content if delta is non-empty
                if delta:
                    if prev_content is None:
                        prev_content = delta
                    else:
                        prev_content += delta
                
        except BamlAbortError:
            yield "data: [CANCELLED]\n\n"
        # finally:
        #     active_streams.pop(stream_id, None)

    # for streaming usage
    def _extract_partial_delta(
        self,
        partial: "DynamicSchemaChunk",
        prev_content: Union[str | list] = ""
    ) -> Dict[str, Union[str, Dict[str, Any]]]:
        """
        Extracts incremental text delta from BAML tool streaming chunks.

        This method processes streaming tool call responses from BAML, extracting only the
        new content since the previous chunk. It handles the special "ReplyToUser" tool
        that routes tool outputs back into the chat as assistant messages.

        Returns a dict with:
          - tool_name: str - Name of the tool making the call
          - delta: str or dict - New content since previous chunk (empty string when no delta)

        Contract:
        - Returns {"tool_name":"", "delta":""} when not ready to stream
        - First chunk: returns initial tokens in delta
        - Subsequent chunks: returns ONLY new tokens since prev_content
        - Validates monotonic growth of content

        Args:
            partial: BAML DynamicSchemaChunk with partial tool call data
            prev_content: Accumulated content from previous chunks (None/"" for first chunk)

        Returns:
            Dict[str, Union[str, Dict[str, Any]]]: Dictionary with "tool_name" and "delta" keys

        Raises:
            ValueError: If content discontinuity is detected or list-type prev_content is used
        """
        EMPTY_DELTA: Dict[str, Union[str, Dict[str, Any]]] = {"tool_name": "", "delta": ""}

        # === Step 1: Safely extract tool_dict ===
        tool_dict = getattr(partial, self.property_name, None)
        if not isinstance(tool_dict, dict):
            return EMPTY_DELTA

        # === Step 2: Validate tool name ===
        tool_name = tool_dict.get("name") or ""
        # If it's not a reply-to-user tool, return with tool_name but no delta
        if not tool_name or tool_name != REPLY_TO_USER:
            return {"tool_name": tool_name, "delta": ""}

        # === Step 3: Extract arguments safely ===
        arguments = tool_dict.get("arguments")
        if not isinstance(arguments, dict) or not arguments:
            return {"tool_name": tool_name, "delta": ""}

        # === Step 4: Extract content (handle None/missing gracefully) ===
        content_raw = arguments.get("content")
        if content_raw is None:  # None means incomplete → block streaming
            return {"tool_name": tool_name, "delta": ""}

        content = str(content_raw)
        # === Step 5: Compute delta ===
        if not content:  # Empty string = no tokens yet
            return {"tool_name": tool_name, "delta": ""}

        # First chunk: emit initial content
        if not prev_content:
            return {"tool_name": tool_name, "delta": content}

        if isinstance(prev_content, list):
            raise ValueError("List-type prev_content not supported in this implementation for now")

        # Subsequent chunks: validate monotonic growth
        if not content.startswith(prev_content):
            raise ValueError(
                f"Content discontinuity detected:\n"
                f"  prev: {repr(prev_content[:50])}...\n"
                f"  curr: {repr(content[:50])}..."
            )

        # Return ONLY the new tokens
        return {"tool_name": tool_name, "delta": content[len(prev_content):]}
        
    def _convert_to_ai_message(
        self,
        dynamic_schema: Union[DynamicSchema, DynamicSchemaChunk],
        is_streaming: bool = False,
    ) -> Union[AIMessage, AIMessageChunk]:
        """
        Converts BAML dynamic schema responses to LangChain AIMessage or AIMessageChunk.

        This method handles both streaming and non-streaming responses from BAML:
        - For streaming: Returns AIMessageChunk with content deltas or tool call chunks
        - For final responses: Returns AIMessage with complete content or tool calls

        Args:
            dynamic_schema: BAML DynamicSchema or DynamicSchemaChunk response
            is_streaming: Whether the response is part of a streaming operation

        Returns:
            Union[AIMessage, AIMessageChunk]: Converted LangChain message object

        Raises:
            ValueError: If an unknown tool is selected in a final response
        """
        # Safe extraction – this is the most battle-tested pattern with BAML streaming
        tool_dict = getattr(dynamic_schema, self.property_name, None)
        if not isinstance(tool_dict, dict):
            tool_dict = {}

        tool_name = tool_dict.get("name")
        arguments = tool_dict.get("arguments") or {}
        if is_streaming:
            # ─────────────── Streaming ───────────────
            if tool_name in (None, ""):
                # undecided → content delta
                return AIMessageChunk(
                    content=''
                )

            if tool_name == REPLY_TO_USER:

                if not arguments.get("content"):
                    return AIMessageChunk(
                        content=''
                    )
                return AIMessageChunk(
                    content=arguments["content"]
                )

            # real tool call delta (even partial)
            return AIMessageChunk(
                content='',
                tool_call_chunks=[{
                    "name": tool_name,
                    "args": json.dumps(arguments, ensure_ascii=False) if arguments else "{}",
                    "id": str(uuid.uuid4())
                }]
            )

        else:
            # ─────────────── Final / non-streaming ───────────────
            if tool_name in (None, ""):
                return AIMessage(
                    content=getattr(dynamic_schema, "content", "") or ""
                )

            if tool_name == REPLY_TO_USER:
                return AIMessage(
                    content=arguments.get("content", "")
                )

            # Final tool call → validate
            if tool_name not in self._tool_names:
                raise ValueError(
                    f"Tool '{tool_name}' selected but not in available tools: {self._tool_names}"
                )

            return AIMessage(
                content='',
                tool_calls=[{
                    "name": tool_name,
                    "args": arguments,
                    "id": str(uuid.uuid4())
                }]
            )

    @property
    def b(self):
        """
        Returns a configured BAML client instance for direct function calls.

        This property provides access to the underlying BAML client with the current
        ChatBaml configuration applied. It allows calling BAML functions directly
        on the ChatBaml instance using the syntax: chat_baml.b.function_name(args).

        Returns:
            BAML client instance: A BAML client configured with the current ChatBaml settings

        Example:
            >>> result = chat_baml.b.ChooseTool(baml_state, {"tb": tb})
        """
        return baml_root_client.with_options(client_registry=self._get_client_registry())

    def bind_tools(
        self,
        tools: List[Union[Type[BaseModel], Callable]],
        *,
        tool_choice: Optional[str | Dict[str, Any]] = None
    ) -> Runnable:
        """
        Returns a new runnable with tools pre-bound for BAML execution.

        This method follows the LangChain pattern for tool binding but uses BAML's
        tool system directly. It prepares the tools for BAML conversion and stores
        tool names for validation during execution. The actual BAML conversion happens
        in the _generate() method.

        Args:
            tools: List of Pydantic BaseModel classes and/or callable functions to bind
            tool_choice: Optional tool choice specification:
                - str: Name of a specific tool to use
                - Dict[str, Any]: Tool choice specification (not yet implemented)

        Returns:
            Runnable: A runnable instance with tools pre-bound for BAML execution

        Raises:
            ValueError: If the specified tool_choice is not found in the provided tools
        """
        # tools is already a List, no conversion needed
        tools_to_bind = tools

        if tool_choice and isinstance(tool_choice, str):
            # Filter to only the selected tool
            tools_to_bind = []
            for tool in tools:
                if isinstance(tool, type) and issubclass(tool, BaseModel):
                    # Pydantic model - check class name
                    if tool.__name__ == tool_choice:
                        tools_to_bind.append(tool)
                elif hasattr(tool, 'name'):
                    # LangChain tool - check name attribute
                    if tool.name == tool_choice:
                        tools_to_bind.append(tool)

            if not tools_to_bind:
                raise ValueError(f"Tool '{tool_choice}' not found in provided tools")

        # self tool names for validation later
        self._tool_names = [ cls.name if hasattr(cls, 'name') else cls.__name__ for cls in tools_to_bind ]
        self._tool_names += [REPLY_TO_USER]
        
        # Create extra dict as specified by user
        extra: Dict[str, Any] = {
            "tools": tools_to_bind,  # Pass tools through
            "tool_choice": tool_choice
        }

        # Return bound instance - BAML conversion happens later in _generate()
        return self.bind(**extra)

    def __getattr__(self, name: str) -> Any:
        """
        Proxies attribute access to the configured BAML client.

        This method allows calling BAML functions directly on the ChatBaml instance
        by proxying attribute access to the underlying BAML client. If an attribute
        is not found on the ChatBaml instance, it attempts to retrieve it from the
        configured BAML client.

        Args:
            name: Name of the attribute to retrieve

        Returns:
            Any: The attribute value from either ChatBaml or the BAML client

        Raises:
            AttributeError: If the attribute is not found on either ChatBaml or the BAML client
        """
        try:
            return super().__getattribute__(name)
        except AttributeError:
            logger.debug(f"Proxying BAML function call: {name}")
            return getattr(self.b, name)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Synchronous generation using BAML with tool support.

        This method handles synchronous chat completion requests using BAML. It converts
        LangChain messages to BAML format, prepares the type builder for tool execution,
        and processes the BAML response into LangChain format. It supports tool execution
        through the bound tools and handles both streaming and non-streaming responses.

        Args:
            messages: List of LangChain BaseMessage objects to process
            stop: Optional list of stop sequences (not yet implemented)
            run_manager: Optional callback manager for LLM run
            **kwargs: Additional arguments including:
                - tools: List of tools to use for the generation
                - context: Context for the generation (not yet implemented)
                - config: RunnableConfig for the generation

        Returns:
            ChatResult: Result containing the generated response and metadata

        Raises:
            NotImplementedError: If context or stop handling is requested (not yet implemented)
            RuntimeError: If BAML function execution fails
        """
        context = kwargs.get("context")
        config: RunnableConfig = kwargs.get("config") or {}
        if context:
            raise NotImplementedError("context handling not implemented yet; will be added later")
        
        tools = kwargs.get('tools', [])
        # Convert LangChain messages to BAML format
        baml_messages = self._convert_to_baml_messages(messages)
        # Create BamlState with converted messages
        baml_state = BamlState(messages=baml_messages)

        # Prepare type builder with dynamic schema for tools
        tb = self._prepare_tb(
            tools=tools
        )
        # Call the chat completion request method
        try:
            dynamic_schema = self.b.ChooseTool(baml_state, {"tb": tb})
            logger.debug(f"BAML ChooseTool response received: {type(dynamic_schema)}")
        except Exception as e:
            logger.error(f"BAML ChooseTool function call failed: {e}")
            raise RuntimeError(f"BAML function execution failed: {e}")

        ai_message = self._convert_to_ai_message(dynamic_schema)

        # Create ChatGeneration
        generation = ChatGeneration(
            message=ai_message,
            generation_info={"baml": dynamic_schema}
        )
        # Return ChatResult
        return ChatResult(generations=[generation])

# Quick test
import asyncio

async def main():
    from langchain_core.messages import (
        AIMessage,
        HumanMessage,
        SystemMessage,
    )

    # Test messages
    TEST_MESSAGES = [
        SystemMessage(content="You are a helpful assistant that answers concisely."),
        HumanMessage(content="Provide a one-sentence summary of the following paragraph."),
        AIMessage(content="LangChain is a framework for developing applications with large language models. It provides tools for prompt management, chaining calls, and building agents that interact with external tools."),
        HumanMessage(content="I have a pen, i have 3 others, boom, what result would be when i combined them")
    ]
    chat_baml = ChatBaml(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL_NAME")
    )
    from test.fixtures.sample_tools import CalculatorAdd, get_weather

    # Bind tools and test invoke
    chat_baml_with_tools = chat_baml.bind_tools([CalculatorAdd, get_weather])
    result_with_tools = await chat_baml_with_tools.ainvoke(TEST_MESSAGES)

    print(result_with_tools)
    
    # # Async streaming
    # async for chunk in chat_baml_with_tools.astream(TEST_MESSAGES):
    #     print(chunk.content, end="\n", flush=True)
    print("\n" + "="*50)
    
if __name__ == "__main__":
    asyncio.run(main())