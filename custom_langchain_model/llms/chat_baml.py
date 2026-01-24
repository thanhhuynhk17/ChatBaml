import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import json
import logging
from typing import Any, Dict, List, Literal, Optional, Sequence, Union
from baml_py import ClientRegistry
from baml_client import (
    b as baml_root_client
)
from baml_client.types import (
    Message as BamlMessage
)

from custom_langchain_model.llms.types import Provider

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
    
    model: str = "gpt-4o"
    temperature: float = 0.0
    provider: Provider = "openai-generic"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    # Baml special args
    default_role: Optional[str] = None # Baml required default_role='user' when using VLLM
    allowed_roles: Optional[List[str]] = ["system", "user", "assistant", "tool"] # Default: ["system", "user", "assistant"] 
    
    # Additional options
    additional_options: Dict[str, Any] = {}

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # Initialize additional_options with any extra kwargs not explicitly defined
        # Use model_fields for Pydantic v2 compatibility
        # Access from the class to avoid deprecation warnings
        defined_fields = self.__class__.model_fields.keys()
        for key, value in kwargs.items():
            if key not in defined_fields:
                self.additional_options[key] = value
        
        logger.debug(f"Initialized ChatBaml with model={self.model}, provider={self.provider}")
        if self.additional_options:
            logger.debug(f"Additional options: {list(self.additional_options.keys())}")

    @property
    def _llm_type(self) -> str:
        return "baml-chat-wrapper"

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

    def _prepare_baml_input(self, messages: List[BaseMessage]) -> str:
        """
        Converts LangChain messages to a string format for BAML.
        Note: BAML functions usually take specific structured inputs. 
        This helper provides a default string representation of the chat history.
        """
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "User"
            elif isinstance(msg, AIMessage):
                role = "Assistant"
            elif isinstance(msg, SystemMessage):
                role = "System"
            else:
                role = "Other"
            formatted_messages.append(f"{role}: {msg.content}")
        return "\n".join(formatted_messages)

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
