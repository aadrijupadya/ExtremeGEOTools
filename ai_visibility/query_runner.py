import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import re
import pandas as pd
from datetime import datetime
import asyncio

# ----------------------------
# CONFIGURATION
# ----------------------------
load_dotenv()  # load env variables like API key
client = OpenAI()

COST_PER_1K_INPUT = 0.0025    # GPT-4o pricing
COST_PER_1K_OUTPUT = 0.010    # GPT-4o pricing
CSV_PATH = "storage/responses.csv"  # where we save outputs

# Known competitors list (for extraction), simple for now
COMPETITORS = [
    "Cisco", "Juniper", "Huawei", "Arista", "HPE", "Aruba",
    "Dell", "Fortinet", "Ubiquiti", "Nokia"
]

# customizable function to call api and get response
def run_query(prompt: str, model="gpt-4o", temperature=0.2):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,  # low temp = less randomness, better reproducibility
        top_p=1.0  # standard nucleus sampling
    )
    return response

# simple keyword checking method
def extract_competitors(response_text: str):
    found = []
    for vendor in COMPETITORS:
        if vendor.lower() in response_text.lower():
            found.append(vendor)
    return found

#using regex to extract and store links
def extract_links(response_text: str):
    return re.findall(r'https?://[^\s]+', response_text)

#using secondary LLM pass to extract sources
def extract_sources_llm(response_text: str):
    prompt = f"Extract a JSON array of all named sources, publications, or reports mentioned in this text:\n\n{response_text}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    try:
        return json.loads(response.choices[0].message.content)
    except:
        return []

#function to handle JSON input
def load_queries(filename: str):
    with open(filename, 'r') as file:
        data = json.load(file)
    queries = [i['query'] for i in data]
    intents = [i.get('intent', 'unlabeled') for i in data]  # safer with .get()
    return queries, intents

# logging to storage csv
def log_response(query, intent, model, response_text, competitors, extreme_rank, completion_tokens, total_tokens, links, sources):
    extreme_mentioned = "Extreme Networks" in response_text

    # Calculate cost
    input_tokens = total_tokens - completion_tokens
    cost = (input_tokens / 1000 * COST_PER_1K_INPUT) + (completion_tokens / 1000 * COST_PER_1K_OUTPUT)

    # Prepare record (row for CSV)
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "model": model,
        "extreme_mentioned": extreme_mentioned,
        "extreme_rank": extreme_rank,
        "competitors": ", ".join(competitors),
        "links_cited": ", ".join(links),
        "sources_cited": ", ".join(sources),
        "intent": intent,
        "response_excerpt": response_text[:300].replace("\n", " "),
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "approx_cost_usd": round(cost, 4),
    }

    # Append to CSV (with safe quoting to avoid parser errors)
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    df = pd.DataFrame([record])
    df.to_csv(CSV_PATH, mode='a', header=not os.path.exists(CSV_PATH), index=False, quoting=1)
    print(f"✅ Logged response for query: {query}")

# ----------------------------
# MAIN EXECUTION LOOP
# ----------------------------
if __name__ == "__main__":
    queries, intents = load_queries("queries.json")

    # use zip to loop over both queries and intents together
    for query, intent in zip(queries, intents):
        print(f"\n🔎 Running query: {query}")
        response = run_query(query)
        response_text = response.choices[0].message.content

        # Extract competitors & rank
        competitors = extract_competitors(response_text)
        extreme_rank = None
        if "extreme networks" in response_text.lower():
            all_vendors = [v for v in COMPETITORS + ["Extreme Networks"] if v.lower() in response_text.lower()]
            ordered = sorted(all_vendors, key=lambda v: response_text.lower().find(v.lower()))
            extreme_rank = ordered.index("Extreme Networks") + 1

        # Extract links & sources (do this regardless of mention)
        links = extract_links(response_text)
        sources = extract_sources_llm(response_text)

        # Log the result
        log_response(
            query=query,
            intent=intent,
            model=response.model,
            response_text=response_text,
            competitors=competitors,
            extreme_rank=extreme_rank,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            links=links,
            sources=sources
        )

        # Display response
        print(f"Response:\n{response_text}\n")
