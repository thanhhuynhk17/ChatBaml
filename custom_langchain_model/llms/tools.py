from langchain.tools import tool

@tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

@tool
def multiply(x: int, y: int) -> int:
    """Multiply two integers."""
    return x * y

simple_tools = [add, multiply]