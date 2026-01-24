// baml_src/example.baml
class DynamicSchema {
  @@dynamic
}

function ChooseTool(state: BamlState) -> DynamicSchema {
    client ChatBaml
    prompt #"
        {{_.role("system")}}
        {{ ctx.output_format }}
        JSON but no colons like above
        -
        
        {{ RenderMessages(state.messages) }}
    "#
}

class BaseMessage {
  role "system" | "user" | "assistant" | "tool"
  content string
}

class AIMessage {
  role "assistant"
  content string
}

class ToolMessage {
  role "tool"
//   content string
}

template_string RenderMessages(messages: BaseMessage[]) #"
  {% for m in messages %}
    {{ _.role( m.role ) }}
    {{ m.content }}
  {% endfor %}
"#


// === Tool Definitions ===

class ReplyToUser {
  action "reply_to_user" @description(#"
    Use this tool when you want to send a natural language response shown to the user. Write naturally, kindly, concisely when possible.
  "#)
  message AIMessage @stream.with_state
}

class CheckWeather {
  action "check_weather" @description(#"
    Use this tool when you want to check current weather.
  "#)
  message ToolMessage @stream.with_state
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

// function ChooseTool(state: BamlState) -> (  ReplyToUser | CheckWeather ) {

//   client ChatBaml
//   prompt #"
//     {{_.role("system")}}
//     {{ ctx.output_format }}
        
//     {{ RenderMessages(state.messages) }}

//   "#
// }


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
