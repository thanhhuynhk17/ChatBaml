import asyncio
import uuid
from langchain_core.messages import AIMessage, HumanMessage
from custom_langchain_model.llms.contexts import GeneralChatContext
from custom_langchain_model.llms.states import GeneralChatState
from custom_langchain_model.llms.callbacks import AsyncChatCallbackHandler
from custom_langchain_model.llms.graphs import make_general_chat_with_tools_graph



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

    # Prepare context
    context = GeneralChatContext(
        invoke_id=invoke_id,
        engine=engine,
        conversation_id=conversation_id
    )

    # Prepare input state
    input_state = GeneralChatState(
        messages=[HumanMessage(input_message)],
        system_prompt=system_prompt 
    )

    # Setup callback handler for async logging and other purposes
    callback_handler = AsyncChatCallbackHandler(
        context=context,
    )

    # Invoke the graph asynchronously
    resp = await graph.ainvoke(
        input_state,
        # context=context,
        # config={"callbacks": [callback_handler]}
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
    print("You asked:", question)

    # Run the graph in an asyncio event loop
    response = asyncio.run(serve_graph(question))
    print("AI response:", response)



if __name__ == "__main__":
    main()
