"""
Sample tools for testing BAML-Langchain integration
"""

from pydantic import BaseModel, Field
from langchain.tools import tool

# Pydantic BaseModel tools
class CalculatorAdd(BaseModel):
    """Add two numbers together"""
    x: float = Field(..., description="First number")
    y: float = Field(..., description="Second number")

class CalculatorSubtract(BaseModel):
    """Subtract second number from first"""
    x: float = Field(..., description="First number")
    y: float = Field(..., description="Second number")

class CalculatorMultiply(BaseModel):
    """Multiply two numbers"""
    x: float = Field(..., description="First number")
    y: float = Field(..., description="Second number")

class CalculatorDivide(BaseModel):
    """Divide first number by second"""
    x: float = Field(..., description="First number")
    y: float = Field(..., description="Second number")

# Langchain @tool decorated functions
@tool
def get_weather(location: str, unit: str = "celsius") -> str:
    """Get current weather for a location"""
    return f"Weather for {location}"

@tool
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information"""
    return f"Search results for: {query}"

@tool
def translate_text(text: str, target_language: str = "english") -> str:
    """Translate text to target language"""
    return f"Translated '{text}' to {target_language}"

@tool
def summarize_text(text: str, max_length: int = 100) -> str:
    """Summarize text to specified length"""
    return f"Summary of {len(text)} characters: {text[:max_length]}..."

# Sample tool list for testing
SAMPLE_TOOLS = [
    CalculatorAdd,
    CalculatorSubtract,
    CalculatorMultiply,
    CalculatorDivide,
    get_weather,
    search_web,
    translate_text,
    summarize_text
]

# Small tool list for quick tests
SMALL_TOOL_LIST = [
    CalculatorAdd,
    get_weather
]

# Large tool list for performance testing
LARGE_TOOL_LIST = SAMPLE_TOOLS + [
    CalculatorAdd,  # Duplicate for larger size
    CalculatorSubtract,
    get_weather,
    search_web
]