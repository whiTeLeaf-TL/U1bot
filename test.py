from openai import OpenAI

tools:list = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather of an location, the user shoud supply a location first",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"],
            },
        },
    },
]


def send_messages(messages):
    response = client.chat.completions.create(
        model="deepseek-chat", messages=messages, tools=tools
    )
    return response.choices[0].message


client = OpenAI(
    api_key="sk-edf54dbebb604a0ba33d2c7d84196a39",
    base_url="https://api.deepseek.com",
)
messages = [{"role": "user", "content": "杭州的温度是多少"}]
message = send_messages(messages)
print(f"User>\t {messages[0]['content']}")

tool = message.tool_calls[0]
print(f"Model>\t {message}")
messages.extend((message, {"role": "tool", "tool_call_id": tool.id, "content": "24℃"}))
message = send_messages(messages)
print(f"Model>\t {message.content}")
