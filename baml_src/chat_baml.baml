class DynamicSchema {
  @@dynamic
}


class BaseMessage {
  role "system" | "user" | "assistant" | "tool"
  content string
}

class AIMessage {
  role "assistant"
  content string
}

template_string RenderMessages(messages: BaseMessage[]) ##"
  {% for m in messages %}
    {% if loop.first %}
      {% if m.role=="system" %}
        {{ _.role( m.role ) }}
        {{ m.content }}
        {{ ctx.output_format(prefix="\nAnswer in JSON-like string ( no double quotes in keys ) using this schema:\n") }}
      {% else %}
        {{ _.role( "system" ) }}
        {{ ctx.output_format}}
        {{ _.role( m.role ) }}
        {{ m.content }}
      {% endif %}
    {% else %}
      {# normal render #}
      {{ _.role( m.role ) }}
      {{ m.content }}
    {% endif %}
    
  {% endfor %}
"##


// === Tool Definitions ===
class ReplyToUser {
  name "reply_to_user" @description(#"
    Use this tool when you want to send a natural language response shown to the user.
  "#)
  arguments AIMessage
}

// The state of the conversation that will be sent
// to the agent. The client is responsible for updating
// it with the result of tool calls.
class BamlState {
  messages BaseMessage[] @description(#"
    The list of messages exchanged so far in the conversation.
    Each message has a role (User, Assistant, Tool) and content.
  "#)
}

function ChooseTool(state: BamlState) -> DynamicSchema {
    client ChatBaml
    prompt #"
        {{RenderMessages(state.messages) }}
    "#
}

test TestName {
  functions [ChooseTool]
  args {
    state {
        messages [
        {
            role "user"
            content #"
            Hi
          "#
        },
        {
            role "tool"
            content #"
            How can I help you?
          "#
        },
        {
            role "user"
            content #"
            Hi, what's the weather like?
          "#
        },
      ]
    }
  }
}
