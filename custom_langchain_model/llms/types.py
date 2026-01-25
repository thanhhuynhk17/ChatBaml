from typing import Literal

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