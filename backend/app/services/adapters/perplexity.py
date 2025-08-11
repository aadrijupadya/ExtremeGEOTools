import requests

response = requests.post(
    'https://api.perplexity.ai/chat/completions',
    headers={
        'Authorization': 'Bearer YOUR_API_KEY',
        'Content-Type': 'application/json'
    },
    json={
        'model': 'sonar',
        'messages': [
            {
                'role': 'user',
                'content': "What are the major AI developments and announcements from today across the tech industry?"
            }
        ]
    }
)

print(response.json())