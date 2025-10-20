# Custom LangChain Chat Model

LangChain and LangGraph is powerful frameworks for orchestrating language model workflows, but sometimes you need to use a private or proprietary LLM API (for example, your company's internal model, or a paid API with custom authentication). This repository provides working code that builds a custom chat model **fully compatible** with LangChain and LangGraph APIs.

## Tutorial

See [Tutorial](tutorial.md) for detailed steps to create custom LangChain model.


## Requirements

- Python >= 3.13
- Key dependencies
	- langchain >= 1.0.0
	- langgraph >= 1.0.0
	- pydantic >= 2.12.3
	- pydantic-settings >= 2.11.0

## Installation

Create and activate a virtual environment, then install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

## Environment variables

The project uses `pydantic-settings` to load configuration from environment variables or a `.env` file. Create a `.env` file at the project root with these variables:

<pre style="white-space: pre; overflow-x: auto;">
API_OAUTH_URL="https://your_base_api_url/oauth/token"
API_BASE_URL="https://your_base_api_url/openai/deployments/{model}/chat/completions"
API_KEY="your_api_key"
API_SECRET="your_api_secret"
</pre>

- `API_BASE_URL` is used in `custom_langchain_model/llms/models.py` and is expected to be a format string with a `{model}` placeholder. You must update your custom model if this pattern doesn't apply in your case.
- This repo assumes you need API key and API secret to request a bearer token via `API_OAUTH_URL`. You must update authentication mechanism in the custom model according to the specs of your private LLM API.

## Quick run

Run the example runner in `main.py` (this uses the graph-based example and prints an AI response):

```bash
python main.py
```

## Full example walkthrough: [full_example.py](full_example.py)
```bash
python full_example.py
```

In this example, the private LLM is provided with 2 simple math tools: `add` and `multiply`. A user prompt requests the graph to calculate sum and product of 2 integers. The callback handlers will log the full execution events of a graph invocation as follows.

<pre style="white-space: pre; overflow-x: auto;">
You asked: What's the sum of 47 and 42, and the product of 33 and 18?
[21:00:56,275] [INFO] custom_langchain_model.llms.callbacks: Chain started: name LangGraph, run_id ee694423-5fb9-4d45-83bc-eb9f48fe2dba, parent_run_id: None
[21:00:56,276] [INFO] custom_langchain_model.llms.callbacks: Chain started: name llm, run_id 49a5bb4d-67b3-43a1-b39e-76c67ed3e459, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:56,277] [INFO] custom_langchain_model.llms.callbacks: Chat model started: name AzureOpenAI_gpt-4o, run_id b54776f3-4bdc-4ecc-8dbc-81a41a4f8794, parent_run_id: 49a5bb4d-67b3-43a1-b39e-76c67ed3e459
[21:00:56,277] [INFO] custom_langchain_model.llms.callbacks: Chat model started with messages: What's the sum of 47 and 42, and the product of 33 and 18?
[21:00:56,970] [INFO] custom_langchain_model.core.security: Fetched new access token
[21:00:58,460] [INFO] custom_langchain_model.llms.callbacks: Chat model ended: name None, run_id b54776f3-4bdc-4ecc-8dbc-81a41a4f8794, parent_run_id: 49a5bb4d-67b3-43a1-b39e-76c67ed3e459
[21:00:58,461] [INFO] custom_langchain_model.llms.callbacks: Chain started: name router, run_id 2f9b27fc-ba4f-42ad-83f1-ad9ba9516081, parent_run_id: 49a5bb4d-67b3-43a1-b39e-76c67ed3e459
[21:00:58,462] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id 2f9b27fc-ba4f-42ad-83f1-ad9ba9516081, parent_run_id: 49a5bb4d-67b3-43a1-b39e-76c67ed3e459
[21:00:58,462] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id 49a5bb4d-67b3-43a1-b39e-76c67ed3e459, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:58,463] [INFO] custom_langchain_model.llms.callbacks: Chain started: name tools, run_id 078ee3fe-cc72-40b0-a4d6-8a10a8be8495, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:58,464] [INFO] custom_langchain_model.llms.callbacks: Tool {'name': 'add', 'description': 'Add two integers.'} started with input: {'a': 47, 'b': 42}.
[21:00:58,465] [INFO] custom_langchain_model.llms.callbacks: Tool {'name': 'multiply', 'description': 'Multiply two integers.'} started with input: {'x': 33, 'y': 18}.
[21:00:58,465] [INFO] custom_langchain_model.llms.callbacks: Tool add ended with output: content='89' name='add' tool_call_id='call_1aiqjdVVmzbZzuK7Q6vDfUkj'
[21:00:58,466] [INFO] custom_langchain_model.llms.callbacks: Tool multiply ended with output: content='594' name='multiply' tool_call_id='call_0XimgvDX3aio2AeDzknfTEAg'
[21:00:58,467] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id 078ee3fe-cc72-40b0-a4d6-8a10a8be8495, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:58,467] [INFO] custom_langchain_model.llms.callbacks: Chain started: name llm, run_id dd4ed834-9ff1-4aec-a007-f0538c38cfdf, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:58,468] [INFO] custom_langchain_model.llms.callbacks: Chat model started: name AzureOpenAI_gpt-4o, run_id 8a3f8b68-f75e-4d5e-a2a9-41c895b4cd47, parent_run_id: dd4ed834-9ff1-4aec-a007-f0538c38cfdf
[21:00:58,468] [INFO] custom_langchain_model.llms.callbacks: Chat model started with messages: 594
[21:00:58,468] [INFO] custom_langchain_model.core.security: Using cached access token
[21:00:59,761] [INFO] custom_langchain_model.llms.callbacks: Chat model ended: name None, run_id 8a3f8b68-f75e-4d5e-a2a9-41c895b4cd47, parent_run_id: dd4ed834-9ff1-4aec-a007-f0538c38cfdf
[21:00:59,761] [INFO] custom_langchain_model.llms.callbacks: Chain started: name router, run_id fd1a1392-7a12-4136-a87b-fb4a2dfc6156, parent_run_id: dd4ed834-9ff1-4aec-a007-f0538c38cfdf
[21:00:59,762] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id fd1a1392-7a12-4136-a87b-fb4a2dfc6156, parent_run_id: dd4ed834-9ff1-4aec-a007-f0538c38cfdf
[21:00:59,762] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id dd4ed834-9ff1-4aec-a007-f0538c38cfdf, parent_run_id: ee694423-5fb9-4d45-83bc-eb9f48fe2dba
[21:00:59,763] [INFO] custom_langchain_model.llms.callbacks: Chain ended: name None, run_id ee694423-5fb9-4d45-83bc-eb9f48fe2dba, parent_run_id: None
AI response: The sum of 47 and 42 is 89, and the product of 33 and 18 is 594.
</pre>


## Codebase overview
<pre style="white-space: pre; overflow-x: auto;">
|─ custom_langchain_model/  #
|   ├─ core/
|   │  ├─ __init__.py
|   │  ├─ config.py         #  load env variables from .env to settings object
|   │  ├─ logging.py        #  configurate logging for callback handlers
|   │  └─ security.py       #  get and globally store private LLM API access token
|   ├─ llms/
|   │  ├─ __init__.py
|   │  ├─ callbacks.py      #  define callback handlers
|   │  ├─ contexts.py       #  define LangGraph context schema (pydantic object)
|   │  ├─ graphs.py         #  define LangGraph chat flow 
|   │  ├─ models.py         #  define custom LangChain chat mode wrapping private LLM API
|   │  ├─ states.py         #  define LangGaph state schema (pydandic object)
|   │  └─ tools.py          #  define tools used with LangGraph model
|   └─ __init__.py
├─ .env.sample              #  example of .env
├─ full_example.py          #  full example of using the custom model with LangGraph
├─ README.md
├─ main.py                  #  code quick run
├─ pyproject.toml           #  project configuration and dependencies
└─ tutorial.md              #  tutorial for building custom chat model
</pre>

## License

This project is licensed under the MIT License - see the LICENSE file for details.

If you find this project helpful, please consider:

⭐ Starring the repository   
🔗 Sharing it with others who might benefit   
💬 Contributing improvements or reporting issues
