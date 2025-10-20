from typing import Dict, List, Union
from pydantic import BaseModel, ConfigDict


class GeneralChatContext(BaseModel):
    """
    Dynamic context to be passed to the graph in LangGraph.
    This context dict carries information of the chat conversation
    such as user information, conversation ID, chat engine selected,
    tools, etc. 
    
    Unlike State, this context is immutable during a run 
    (per LangGraph convention), but is re-injected each run 
    by the backend.

    In some specific scenarios, the context could be changed
    only if there's a request from the frontend, for example 
    when the user switch conversation. 

    That means, context never changes per one cycle 
    of graph execution.
    """
    
    invoke_id: str  # unique id per graph invocation, for logging/tracing
    engine: str
    conversation_id: Union[str, None] = None
    message_history: List[Dict[str, str]] = []

    model_config = ConfigDict(
        arbitrary_types_allowed = True
    )
