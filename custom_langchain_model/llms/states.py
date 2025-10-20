# State schema
from typing import List, Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel


# Define common state of the graph 
class GeneralChatState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    system_prompt: str
