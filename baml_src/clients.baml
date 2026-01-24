client<llm> ChatBaml {
  provider "openai-generic"
  options {
    base_url env.OPENAI_BASE_URL
    api_key env.OPENAI_API_KEY
    model env.OPENAI_MODEL_NAME
    default_role "user" // Required for using VLLM
    allowed_roles ["system", "user", "assistant", "tool"]
    temperature 0
    top_p 0.8
    top_k 20
    presence_penalty 1.5
    repetition_penalty 1.0
    seed 3407
    max_tokens 4096
  }
}