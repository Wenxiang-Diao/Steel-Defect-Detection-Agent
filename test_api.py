from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

response = client.chat.completions.create(
    model=LLM_MODEL,
    messages=[
        {
            "role": "user",
            "content": "只回复：API调用成功"
        }
    ],
    stream=False
)

print(response.choices[0].message.content)