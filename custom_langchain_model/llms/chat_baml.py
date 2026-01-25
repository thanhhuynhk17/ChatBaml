import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import json
import logging
from typing import Any, Dict, List, Literal, Optional, Sequence, Union
from pydantic import Field  # Import Field for metadata

from baml_py import ClientRegistry
from baml_client import (
    b as baml_root_client
)
from baml_client.types import (
    BamlState,
    BaseMessage as BamlBaseMessage
)
from custom_langchain_model.helpers.parse_json_schema import convert_to_baml_tool

from custom_langchain_model.llms.types import Provider, Role

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun

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
        default=0.0,
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
    
    # Additional options
    additional_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary for any extra parameters not explicitly defined in the class."
    )

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

    def _prepare_baml_input(self, messages: List[BaseMessage]) -> str:
        """
        Converts LangChain messages to a string format for BAML.
        Note: BAML functions usually take specific structured inputs.
        This helper provides a default string representation of the chat history.
        """
        raise NotImplementedError(
            "ChatBaml._prepare_baml_input is not implemented yet."
        )
        # formatted_messages = []
        # for msg in messages:
        #     if isinstance(msg, HumanMessage):
        #         role = "User"
        #     elif isinstance(msg, AIMessage):
        #         role = "Assistant"
        #     elif isinstance(msg, SystemMessage):
        #         role = "System"
        #     else:
        #         role = "Other"
        #     formatted_messages.append(f"{role}: {msg.content}")
        # return "\n".join(formatted_messages)

    async def _chat_completion_request(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        context: Optional[dict] = None,
        stream: bool = False,
        tools: Optional[List[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronously makes a chat completion request using BAML.

        Args:
            messages: List of LangChain BaseMessage objects
            stop: Optional list of stop sequences
            context: Optional context dictionary
            stream: Whether to stream the response
            tools: Optional list of LangChain tool dictionaries
            tool_choice: Optional tool choice specification (ignored for now)

        Returns:
            Dictionary containing the BAML response
        """
        # Convert LangChain messages to BAML format
        baml_messages = self._convert_to_baml_messages(messages)

        # Handle tools conversion if provided
        tb = None
        if tools:
            try:
                tb = convert_to_baml_tool(
                    tools=tools,
                    is_multiple_tools=True, # single / multiple tools
                    
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
                    is_multiple_tools=False,
                    include_reply_to_user=True
                )
                logger.debug("No external tools provided; using ReplyToUser tool only")
            except Exception as e:
                logger.error(f"Failed to create ReplyToUser tool bundle: {e}")
                raise ValueError(f"Failed to create ReplyToUser tool bundle: {e}")
        # Create BamlState with converted messages
        baml_state = BamlState(messages=baml_messages)

        # Call BAML ChooseTool function asynchronously
        logger.debug("Calling BAML ChooseTool function")
        try:
            response = await self.b.ChooseTool(baml_state, {"tb": tb})
            logger.debug(f"BAML ChooseTool response received: {type(response)}")

            # Return the raw BAML response
            return {
                "response": response,
                "baml_state": baml_state
            }

        except Exception as e:
            logger.error(f"BAML ChooseTool function call failed: {e}")
            raise RuntimeError(f"BAML function execution failed: {e}")
        

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Synchronous generation. 
        Note: This requires a BAML function that acts as a generic chat completion.
        If your BAML functions are specific (e.g., ExtractResume), use them directly.
        """
        # This is a placeholder for how one might call a generic BAML chat function
        # Since BAML is function-centric, a 'BaseChatModel' implementation 
        # usually implies a generic 'Chat' function exists in BAML.
        raise NotImplementedError(
            "BAML is function-centric. Please use the .b property to access "
            "dynamically configured BAML functions directly, e.g., chat_baml.b.MyFunction(args)"
        )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Asynchronous generation."""
        raise NotImplementedError(
            "BAML is function-centric. Please use the .b property to access "
            "dynamically configured BAML functions directly."
        )

    @property
    def b(self):
        """
        Returns a BAML client instance configured with the current parameters.
        Usage: chat_baml.b.MyBamlFunction(args)
        """
        return baml_root_client.with_options(client_registry=self._get_client_registry())

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
