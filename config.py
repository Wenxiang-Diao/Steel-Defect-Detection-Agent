import os
from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")

if not LLM_API_KEY:
    raise RuntimeError("未检测到 LLM_API_KEY，请检查 .env 文件")

if not LLM_MODEL:
    raise RuntimeError("未检测到 LLM_MODEL，请检查 .env 文件")