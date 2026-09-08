from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from prompts import SYSTEM_PROMPT
import json
from openai import OpenAI
from report_validation import finalize_report

client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

def generate_report(visual_result, rag_entries):
    agent_input = {
        "visual_result": visual_result,
        "rag_entries": rag_entries,
    }

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": json.dumps(
                    agent_input,
                    ensure_ascii=False,
                ),
            },
        ],
        temperature=0,
    )
    content = response.choices[0].message.content
    return finalize_report(json.loads(content), visual_result, rag_entries)
