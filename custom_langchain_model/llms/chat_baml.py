import os
from dotenv import load_dotenv, find_dotenv

from custom_langchain_model.helpers.render_agent_wants_to import (
    format_args_no_quote_keys, render_agent_wants_to
)
load_dotenv(find_dotenv())
import uuid
import json
import logging
from typing import Any, Dict, Iterator, List, Literal, Optional, Sequence, Union, Type, Callable, AsyncIterator
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

from custom_langchain_model.helpers.parse_json_schema import convert_to_baml_tool

from custom_langchain_model.llms.types import Provider, Role, BamlAbortError

from langchain_core.language_models import BaseChatModel
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

    # @property
    # def _tb(self) -> TypeBuilder | None:
    #     """Get the _tb value"""
    #     return self.__dict__.get("_tb")
    # @_tb.setter
    # def _tb(self, value: TypeBuilder | None) -> None:
    #     """Set the _tb value"""
    #     self.__dict__["_tb"] = value

    @property
    def _llm_type(self) -> str:
        return "baml-chat-model"

    def _get_client_registry(self) -> ClientRegistry:
        # https://docs.boundaryml.com/ref/baml_client/client-registry
        
        if self.provider != "openai-generic":
            raise ValueError(
                f"ChatBaml currently only supports provider='openai-generic'. "
                f"Received: provider='{self.provider}'. "
                "Use a different wrapper class if you need other providers."
            )

        cr = ClientRegistry()

        api_key = self.api_key
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "No OpenAI API key provided. "
                    "Either pass api_key=... when initializing ChatBaml, "
                    "or set the OPENAI_API_KEY environment variable."
                )

        options = {
            "model": self.model,
            "temperature": self.temperature,
            "api_key": api_key,
        }

        if self.base_url is not None:
            options["base_url"] = self.base_url

        if self.max_tokens is not None:
            options["max_tokens"] = self.max_tokens

        if self.default_role is not None:
            options["default_role"] = self.default_role

        if self.allowed_roles is not None:
            options["allowed_roles"] = self.allowed_roles


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

        Args:
            messages: List of LangChain BaseMessage objects

        Returns:
            List of BAML BaseMessage objects
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
        stop: Optional[List[str]] = None,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
    ) -> Optional[TypeBuilder]:
        
        if tool_choice:
            raise NotImplementedError("Tool choice handling not implemented yet; will be added later")
        if stop:
            raise NotImplementedError("stop handling not implemented yet; will be added later")
        
        tb = None
        
        if tools:
            try:
                tb = convert_to_baml_tool(
                    tools=tools,
                    is_multiple_tools=False, # single / multiple tools
                    property_name=self.property_name,
                    # Predefined "ReplyToUser" tool used to route a tool's output back into the chat as an assistant (AI) message.
                    include_reply_to_user=True
                )
                logger.debug(f"Successfully converted {len(tools)} tools to BAML format")
            except Exception as e:
                logger.error(f"Failed to convert tools: {e}")
                raise ValueError(f"Tool conversion failed: {e}")
        else:
            # No tools provided: create a minimal tool bundle that only includes
            # the ReplyToUser routing tool so tool outputs can be routed back into
            # the chat as assistant (AI) messages.
            try:
                tb = convert_to_baml_tool(
                    tools=[],
                    property_name=self.property_name,
                    is_multiple_tools=False,
                    include_reply_to_user=True
                )
                logger.debug("No external tools provided; using ReplyToUser tool only")
            except Exception as e:
                logger.error(f"Failed to create ReplyToUser tool bundle: {e}")
                raise ValueError(f"Failed to create ReplyToUser tool bundle: {e}")

        return tb

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Synchronous generation using BAML.

        This method calls the asynchronous _agenerate method and returns the result.
        It provides synchronous compatibility for LangChain while using BAML's async API.

        Args:
            messages: List of LangChain BaseMessage objects
            stop: Optional list of stop sequences
            run_manager: Optional callback manager for LLM run
            **kwargs: Additional arguments

        Returns:
            ChatResult containing the generation
        """
        raise NotImplementedError(
            "Synchronous _generate is not implemented for ChatBaml. "
            "This custom chat model only supports async invocation. "
            "Please use the async API (e.g., await chat_baml.ainvoke(messages) "
            "or asyncio.run(chat_baml.ainvoke(messages)))."
        )

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """
        Stream the output of the model using BAML streaming.

        This method implements streaming support by using BAML's streaming API.
        It converts BAML streaming responses to LangChain's ChatGenerationChunk format.

        Args:
            messages: List of LangChain BaseMessage objects
            stop: Optional list of stop sequences
            run_manager: Optional callback manager for LLM run
            **kwargs: Additional arguments

        Returns:
            Iterator of ChatGenerationChunk objects
        """
        context = kwargs.get("context")
        if context:
            raise NotImplementedError("context handling not implemented yet; will be added later")
        if stop:
            raise NotImplementedError("stop handling not implemented yet; will be added later")
        
        
        tools = kwargs.get('tools', [])
        tool_names = [ cls.name if hasattr(cls, 'name') else cls.__name__ for cls in tools ]
        # FIXME: reply_to_user now acting like a simple AIMessage, refactor later!
        tool_names += ['reply_to_user']
        
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
            stream = self.b.stream.ChooseTool(baml_state, {"tb": tb})
            
            async for partial in stream:
                ai_message_chunk = self._convert_to_ai_message(partial, tool_names, is_streaming=True)
                chunk = ChatGenerationChunk(message=ai_message_chunk)
                yield chunk
            final = await stream.get_final_response()
            
            yield ChatGenerationChunk(
                message=self._convert_to_ai_message(final, tool_names, is_streaming=True)
            )
        except BamlAbortError:
            yield "data: [CANCELLED]\n\n"
        # finally:
        #     active_streams.pop(stream_id, None)

    def _convert_to_ai_message(
        self,
        dynamic_schema: Union[DynamicSchema, DynamicSchemaChunk],
        tool_names: List[str],
        is_streaming: bool = False,
    ) -> Union[AIMessage, AIMessageChunk]:

        # Safe extraction – this is the most battle-tested pattern with BAML streaming
        tool_dict = getattr(dynamic_schema, "selected_tool", None)
        if not isinstance(tool_dict, dict):
            tool_dict = {}

        tool_name = tool_dict.get("name")
        arguments = tool_dict.get("arguments") or {}
        
        dynamic_schema_formated = render_agent_wants_to(
            tool_name, 
            dynamic_schema.model_dump()
        )
        if is_streaming:
            # ─────────────── Streaming ───────────────
            if tool_name in (None, ""):
                # undecided → content delta
                return AIMessageChunk(
                    content=getattr(dynamic_schema, "content", "") or ""
                )

            if tool_name == "reply_to_user":
                return AIMessageChunk(
                    content=arguments.get("content", "")
                )

            # real tool call delta (even partial)
            return AIMessageChunk(
                content='',
                tool_call_chunks=[{
                    "name": tool_name,
                    "args": json.dumps(arguments, ensure_ascii=False) if arguments else "{}",
                    "id": str(uuid.uuid4()),
                    "index": 0,
                }]
            )

        else:
            # ─────────────── Final / non-streaming ───────────────
            if tool_name in (None, ""):
                return AIMessage(
                    content=getattr(dynamic_schema, "content", "") or ""
                )

            if tool_name == "reply_to_user":
                return AIMessage(
                    content=arguments.get("content", "")
                )

            # Final tool call → validate
            if tool_name not in tool_names:
                raise ValueError(
                    f"Tool '{tool_name}' selected but not in available tools: {tool_names}"
                )

            return AIMessage(
                content='',
                tool_calls=[{
                    "name": tool_name,
                    "args": arguments,
                    "id": str(uuid.uuid4())
                }]
            )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Asynchronous generation using BAML.

        This method calls the BAML ChooseTool function and converts the response
        to LangChain's ChatResult format.

        Args:
            messages: List of LangChain BaseMessage objects
            stop: Optional list of stop sequences
            run_manager: Optional callback manager for LLM run
            **kwargs: Additional arguments

        Returns:
            ChatResult containing the generation
        """
        context = kwargs.get("context")
        if context:
            raise NotImplementedError("context handling not implemented yet; will be added later")
        
        tools = kwargs.get('tools', [])
        tool_names = [ cls.name if hasattr(cls, 'name') else cls.__name__ for cls in tools ]
        # FIXME: reply_to_user now acting like a simple AIMessage, refactor later!
        tool_names += ['reply_to_user']
        
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
            dynamic_schema = await self.b.ChooseTool(baml_state, {"tb": tb})
            logger.debug(f"BAML ChooseTool response received: {type(dynamic_schema)}")
        except Exception as e:
            logger.error(f"BAML ChooseTool function call failed: {e}")
            raise RuntimeError(f"BAML function execution failed: {e}")

        ai_message = self._convert_to_ai_message(dynamic_schema, tool_names)

        # Create ChatGeneration
        generation = ChatGeneration(
            message=ai_message,
            generation_info={"baml": dynamic_schema}
        )
        # Return ChatResult
        return ChatResult(generations=[generation])

    @property
    def b(self):
        """
        Returns a BAML client instance configured with the current parameters.
        Usage: chat_baml.b.MyBamlFunction(args)
        """
        return baml_root_client.with_options(client_registry=self._get_client_registry())

    def bind_tools(
        self,
        tools: List[Union[Type[BaseModel], Callable]],
        *,
        tool_choice: Optional[str | Dict[str, Any]] = None
    ) -> Runnable:
        """
        Return a new runnable with tools pre-bound for BAML.

        This method follows the LangChain pattern for tool binding but uses BAML's
        tool system directly. The actual BAML conversion happens in _agenerate().

        Args:
            tools: List of Pydantic BaseModel classes and/or callable functions
            tool_choice: Optional tool choice specification (name of tool to use)

        Returns:
            Runnable that uses the bound tools
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

        # Create extra dict as specified by user
        extra: Dict[str, Any] = {
            "tools": tools_to_bind,  # Pass tools through
            "tool_choice": tool_choice
        }

        # Return bound instance - BAML conversion happens later in _agenerate()
        return self.bind(**extra)

    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to the configured BAML client.
        This allows calling BAML functions directly on the ChatBaml instance.
        """
        try:
            return super().__getattribute__(name)
        except AttributeError:
            logger.debug(f"Proxying BAML function call: {name}")
            return getattr(self.b, name)

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
    # result_with_tools = await chat_baml_with_tools.ainvoke(TEST_MESSAGES)

    # print(result_with_tools)
    
    # Async
    # Async streaming
    async for chunk in chat_baml_with_tools.astream(TEST_MESSAGES):
        print(chunk.content, end="\n", flush=True)
    print("\n" + "="*50)
    
if __name__ == "__main__":
    asyncio.run(main())