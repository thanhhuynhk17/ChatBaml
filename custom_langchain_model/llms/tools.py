from langchain.tools import tool

@tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return f"\nAddition result: {a + b}\n"

@tool
def multiply(x: int, y: int) -> int:
    """Multiply two integers."""
    return f"\nMultiplication result: {x * y}\n"

simple_tools = [add, multiply]