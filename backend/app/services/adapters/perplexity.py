import requests
import os
from dotenv import load_dotenv

load_dotenv()

def run_query(prompt: str, temperature: float = 0.2, model: str = 'sonar'):
    """Run a query through Perplexity API"""
    api_key = os.getenv('PERPLEXITY_API_KEY')
    if not api_key:
        raise ValueError("PERPLEXITY_API_KEY environment variable not set")
    
    # Enhanced prompt for better source citation
    enhanced_prompt = f"""You are a competitive intelligence researcher. When answering, ALWAYS include the full URLs and sources you find.

IMPORTANT: For every fact, statistic, or claim you make, include the complete URL where you found this information. Include whatever sources you discover - company websites, news articles, press releases, industry reports, etc.

Format citations as:
- "Source: [https://full-url-here.com/page]"
- "Reference: [https://full-url-here.com/article]"
- "Found at: [https://full-url-here.com/report]"
- "According to: [https://full-url-here.com/news]"

Do NOT use numbered citations like [1][2][3]. Instead, include the actual URLs inline with your text.

Question: {prompt}"""
    
    try:
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model or 'sonar',
                'messages': [
                    {
                        'role': 'user',
                        'content': enhanced_prompt
                    }
                ],
                'temperature': temperature
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "text": f"Error: {response.status_code} - {response.text}",
                "model": "perplexity",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0}
            }
    except Exception as e:
        return {
            "text": f"Error: {str(e)}",
            "model": "perplexity", 
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0}
        }