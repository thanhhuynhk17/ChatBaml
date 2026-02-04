from langchain.agents import create_agent
from custom_langchain_model.llms.chat_baml import ChatBaml
from react_agent.tools import (
    add,
    multiply
)

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

chat_baml = ChatBaml(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL_NAME"),
    streaming=True,
    temperature=0.7,
    
)

tools = [add, multiply]

agent = create_agent(
    chat_baml, 
    tools=tools,
    system_prompt="You are a helpful assistant.\n\n# Tools\n\nYou may call one or more functions to assist with the user query.",
)
