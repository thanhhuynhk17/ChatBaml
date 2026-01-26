from typing import Literal, Any

Provider = Literal[
    "openai",
    "anthropic",
    "google-ai",
    "vertex-ai",
    "aws-bedrock",
    "openai-generic",
    "fallback",
    "round-robin",
]

Role = Literal[
    "system",
    "user",
    "assistant",
    "tool"
]

class BamlAbortError(Exception):
    """Error raised when a BAML operation is aborted"""
    
    def __init__(self, message: str, reason: Any = None, detailed_message: str = ''):
        super().__init__(message)
        self.reason = reason
        self.detailed_message = detailed_message
        self.name = 'BamlAbortError'
