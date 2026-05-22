import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["CBORG_API_KEY"],
    base_url="https://api.cborg.lbl.gov",
)

model = os.getenv("CBORG_MODEL", "lbl/cborg-chat")

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": "Reply with one short sentence: CBorg API is working."}
    ],
    temperature=0.0,
    max_tokens=80,
)

print("Model:", model)
print("Response:", response.choices[0].message.content)