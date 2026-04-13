from langchain.agents import create_agent
from custom_langchain_model.llms.chat_baml import ChatBaml
from react_agent.tools import (
    add,
    multiply
)
from langchain_community.tools import DuckDuckGoSearchRun

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
search = DuckDuckGoSearchRun()
tools = [add, multiply, search]

from textwrap import dedent
# Import datetime to giving agent exact time for better reasoning
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")
agent = create_agent(
    chat_baml, 
    tools=tools,
    system_prompt=dedent("""
        You are a helpful assistant with tools for math and web search.
        
        ALWAYS use a tool when:
        - Any math operation → add or multiply tool
        - Any fact, current info, or external data → search tool
        
        Answer directly ONLY for casual conversation.
    """)
    )