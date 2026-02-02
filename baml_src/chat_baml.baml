class DynamicSchema {
  @@dynamic
}

class ContentBlock{
  text string
  img image?
  tool_call ToolCall?
}

class ToolCall {
  name string
  args string
}

class BaseMessage {
  role "system" | "user" | "assistant" | "tool"
  content_block ContentBlock
}

// FIXME: Duplicated message rendering logic should be removed
template_string RenderMessages(messages: BaseMessage[]) ##"
  {% for m in messages %}
    {% if loop.first %}
      {% if m.role=="system" %}
        {{ _.role( "system" ) }}
        {{ m.content_block.text }}
        {{ ctx.output_format(prefix="\nAnswer in JSON-like string ( no double quotes in keys ) using this schema:\n") }}
      {% else %}
        {{ _.role( "system" ) }}
        {{ ctx.output_format(prefix="\nAnswer in JSON-like string ( no double quotes in keys ) using this schema:\n") }}

        {# normal render #}
        {{ _.role( m.role ) }}
        {{ m.content_block.text }}
        
        {# multimodal support #}
        {% if m.content_block.img %}
          {{ m.content_block.img }}
        {% endif %}

        {# tool call support #}
        {% if m.content_block.tool_call %}
          {{- '\n<tool_call>\n{"name": "' ~ m.content_block.tool_call.name ~ '", "arguments": ' ~ m.content_block.tool_call.args ~ '}\n</tool_call>' -}}
        {% endif %}

      {% endif %}
    
    {% else %}
      {# normal render #}
      {{ _.role( m.role ) }}
      {{ m.content_block.text }}

      {# multimodal support #}
      {% if m.content_block.img %}
        {{ m.content_block.img }}
      {% endif %}

      {# tool call support #}
      {% if m.content_block.tool_call %}
        {{- '\n<tool_call>\n{"name": "' ~ m.content_block.tool_call.name ~ '", "arguments": ' ~ m.content_block.tool_call.args ~ '}\n</tool_call>' -}}
      {% endif %}
    {% endif %}
    
  {% endfor %}
"##


// === Tool Definitions ===
class AIMessage {
  role "assistant"
  content string
}

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

test DynamicClassTest {
  functions [ChooseTool]
  type_builder {
    dynamic class DynamicSchema {
        selected_tool ReplyToUser
    }
  }
  args {
    state {
      messages [
      {
        role "system"
        content_block {
          text "You are a helpful assistant that provides information about images."
        }
      },
      {
        role "user"
        content_block {
          text "Extract all text from the image without any description."
          img {
            file "../images/1732261281369.jfif"
          }
        }
      }]
    }
  }
}
