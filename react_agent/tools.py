from langchain.tools import tool
from pydantic import BaseModel, Field

class AddInput(BaseModel):
    """Add two integers."""
    a: int = Field(description="First integer to add")
    b: int = Field(default=5, description="Second integer to add")
@tool(args_schema=AddInput)
def add(a: int, b: int) -> int:
    return a + b

class MultiplyInput(BaseModel):
    """Multiply two integers."""
    x: int = Field(description="First integer to multiply")
    y: int = Field(default=5, description="Second integer to multiply")
@tool(args_schema=MultiplyInput)
def multiply(x: int, y: int) -> int:
    return x * y