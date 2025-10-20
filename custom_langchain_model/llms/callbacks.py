from typing import Any
import logging
from uuid import UUID
from langchain_core.messages import BaseMessage
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from custom_langchain_model.llms.states import GeneralChatState
from custom_langchain_model.llms.contexts import GeneralChatContext


logger = logging.getLogger(__name__)


class AsyncChatCallbackHandler(AsyncCallbackHandler):
    context: GeneralChatContext = None  # to be set by the runtime

    def __init__(self, context: GeneralChatContext = None):
        super().__init__()
        self.context = context        

    # Chain callbacks
    async def on_chain_start(self, serialized, inputs: GeneralChatState, **kwargs):
        logger.info(f"Chain started: name {kwargs.get('name')}, run_id {kwargs.get('run_id')}, parent_run_id: {kwargs.get('parent_run_id')}")


    async def on_chain_end(self, outputs, **kwargs):
        logger.info(f"Chain ended: name {kwargs.get('name')}, run_id {kwargs.get('run_id')}, parent_run_id: {kwargs.get('parent_run_id')}")


    async def on_chain_error(self, error, **kwargs):
        logger.info(f"Chain error  : run_id {kwargs.get('run_id')}, {kwargs.get('name')}, parent_run_id: {kwargs.get('parent_run_id')}")
        logger.error(f"Error: {error}")
   
        
    # Chat model callbacks
    async def on_chat_model_start(self, serialized: dict[str, Any], messages: list[list[BaseMessage]], **kwargs: Any):
        logger.info(f"Chat model started: name {kwargs.get('metadata').get('ls_model_name')}, run_id {kwargs.get('run_id')}, parent_run_id: {kwargs.get('parent_run_id')}")        
        logger.info(f"Chat model started with messages: {messages[0][-1].content}")



    async def on_llm_end(self, response: LLMResult, **kwargs):
        logger.info(f"Chat model ended: name {kwargs.get('name')}, run_id {kwargs.get('run_id')}, parent_run_id: {kwargs.get('parent_run_id')}")
        message = response.generations[0][0].message.content or None
        tool_calls = response.generations[0][0].message.tool_calls or []
        assert not (message and tool_calls), "AI message cannot have both content and tool_calls"


    # Error callbacks
    async def on_llm_error(self, error, **kwargs):
        logger.error(f"LLM error: {error}")

    
    # Tool callbacks
    async def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs):
        logger.info(f"Tool {serialized} started with input: {input_str}.")


    async def on_tool_end(self, output: str, **kwargs):
        logger.info(f"Tool {kwargs['name']} ended with output: {output}")


    async def on_tool_error(self, tool_name: str, error: str, **kwargs):
        logger.error(f"Tool error: {tool_name} with error: {error}")


    def _normalize_args(self, run_id=None, parent_run_id=None):        
        if isinstance(run_id, UUID):
            run_id = str(run_id)
        if isinstance(parent_run_id, UUID):
            parent_run_id = str(parent_run_id)
        return run_id, parent_run_id
    

    async def _persist_graph_run(self):
        """
        Persist the entire graph run including user messages, tool calls, and AI messages in database.        
        """
        raise NotImplementedError("Graph run persistence not implemented yet.")
        
        
