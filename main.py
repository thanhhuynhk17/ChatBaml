import asyncio
import uuid
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.callbacks import BaseCallbackHandler, StdOutCallbackHandler
from custom_langchain_model.llms.states import GeneralChatState
from custom_langchain_model.llms.graphs import make_general_chat_with_tools_graph

class StreamingCallback(BaseCallbackHandler):
    def on_llm_new_token(self, token, **kwargs):
        print(f"new token: [{token}]", end="", flush=True)



# Define an async function to run the graph
async def serve_graph(        
        input_message: str, 
        system_prompt: str = "You are a helpful assistant.",
        conversation_id: str = None,
        engine="gpt-4o",
) -> str: 
    # Build the graph
    graph = make_general_chat_with_tools_graph()

    # Generate a unique invoke id for this graph execution.
    # This is used for tracking and logging purposes.
    invoke_id = uuid.uuid4().hex



    # Prepare input state
    input_state = GeneralChatState(
        messages=[HumanMessage(input_message)],
        system_prompt=system_prompt 
    )

    # Invoke the graph asynchronously
    resp = await graph.ainvoke(
        input_state,
        # config={"callbacks":[StdOutCallbackHandler()]}
    )
    
    # Process the response
    messages = resp.get('messages', [])

    # Extract and return the AI message content
    if messages and isinstance(messages[-1], AIMessage):
        return messages[-1].content
    else:
        raise ValueError("AI message not found in the response.")
    


def main():
    # Example usage
    
    import random
    
    a, b, c, d = random.randint(1, 100), random.randint(1, 100), random.randint(1, 100), random.randint(1, 100)
    question = f"What's the sum of {a} and {b}, and the product of {c} and {d}?"
    # question = f"Write a story"
    print("You asked:", question)

    # Run the graph in an asyncio event loop
    response = asyncio.run(serve_graph(question))
    print("AI response:", response)



if __name__ == "__main__":
    main()
