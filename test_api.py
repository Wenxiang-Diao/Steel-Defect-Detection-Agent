from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from prompts import SYSTEM_PROMPT
import json

client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

visual_result = {
    "defect_type": "scratch",
    "confidence": 0.91,
    "area_ratio": 0.021
}

defect_knowledge = {
    "definition": "钢板表面的线状机械损伤"
}

quality_rules = {
    "rule": "area_ratio > 0.02时需要人工复核"
}

user_input = {
    "visual_result": visual_result,
    "defect_knowledge": defect_knowledge,
    "quality_rules": quality_rules
}


response = client.chat.completions.create(
    model=LLM_MODEL,
    messages=[
        {
            "role": "user",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": json.dumps(user_input)
        }
    ],
)

print(response.choices[0].message.content)