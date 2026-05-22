import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["CBORG_API_KEY"],
    base_url="https://api.cborg.lbl.gov",
)

model = os.getenv("CBORG_MODEL", "lbl/cborg-chat")

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Answer clearly and concisely."
    }
]

print(f"Chatting with model: {model}")
print("Type 'exit' or 'quit' to stop.\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() in {"exit", "quit"}:
        print("Stopped.")
        break

    if not user_input:
        continue

    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        assistant_reply = response.choices[0].message.content
        print(f"\nModel: {assistant_reply}\n")

        messages.append({"role": "assistant", "content": assistant_reply})

    except Exception as e:
        print(f"\nError: {e}\n")