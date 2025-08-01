from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = """
You are an AI search assistant.
Provide the most accurate answer based on your training.
Include known sources or citations (industry publications, reports, websites) in-line if relevant.
If unsure, respond conservatively without fabricating.
"""

def run_query(prompt: str, model="gpt-4o", temperature=0.2):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        top_p=1.0
    )
    return response
