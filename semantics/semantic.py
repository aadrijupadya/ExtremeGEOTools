import requests  # scraping the website
from bs4 import BeautifulSoup  # parsing the website
import numpy as np  # for vector math
from sentence_transformers import SentenceTransformer, util  # for embedding and similarity
import spacy  # modern NLP tokenizer (replacement for NLTK)

# --- Configuration ---
URL = "https://www.extremenetworks.com/resources/blogs/what-is-ofdma-and-how-does-it-enhance-802-dot-11ax-wi-fi-6-technologies"
EMBEDDING_MODEL = "all-MiniLM-L6-v2" #can personalize, currenlty using a free, locally hosted model
TOP_K = 3           # top chunks to return
TOP_SENTENCES = 25   # top sentences per chunk

# --- Config for file-based ranking ---
RANK_FROM_FILE = True  # Set to True to enable ranking from file
INPUT_FILE = "input_ofdma.txt"
QUERY_FROM_FILE = "OFDMA improvements quantified"

# --- Load spaCy English tokenizer ---
nlp = spacy.load("en_core_web_sm")

# --- 1. Scrape & Parse Website Content ---
def scrape_sections_nested(url):
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")

    result = [] #stack to store the section headers
    current_h1 = None
    current_h2 = None
    current_h3 = None

    for el in soup.find_all(['h1', 'h2', 'h3', 'p']):
        tag = el.name
        text = el.get_text(strip=True)

        if tag == 'h1':
            current_h1 = {"title": text, "children": []}
            result.append(current_h1)
            current_h2 = None
            current_h3 = None

        elif tag == 'h2':
            if current_h1 is None:
                current_h1 = {"title": "Untitled H1", "children": []}
                result.append(current_h1)
            current_h2 = {"title": text, "children": []}
            current_h1["children"].append(current_h2)
            current_h3 = None

        elif tag == 'h3':
            if current_h2 is None:
                if current_h1 is None:
                    current_h1 = {"title": "Untitled H1", "children": []}
                    result.append(current_h1)
                current_h2 = {"title": "Untitled H2", "children": []}
                current_h1["children"].append(current_h2)
            current_h3 = {"title": text, "text": []}
            current_h2["children"].append(current_h3)

        elif tag == 'p':
            if current_h3 is not None:
                current_h3["text"].append(text)
            elif current_h2 is not None:
                # fallback: attach to h2
                current_h2.setdefault("text", []).append(text)
            elif current_h1 is not None:
                # fallback: attach to h1
                current_h1.setdefault("text", []).append(text)

    return result

# --- 2. Flatten Nested Sections ---
def flatten_sections(sections, parent_title=""):
    flat = []
    for sec in sections:
        title = f"{parent_title} > {sec['title']}" if parent_title else sec['title']
        text = " ".join(sec.get("text", []))
        if text:
            flat.append({"title": title, "text": text})
        for child in sec.get("children", []):
            flat.extend(flatten_sections([child], title))
    return flat

# --- 2. Embed Sections ---
def embed_sections(sections, model):
    for sec in sections:
        sec["embedding"] = model.encode(sec["text"], convert_to_tensor=True)
    return sections

# --- 3. Retrieve Top Sections (RAG-style) ---
def retrieve(sections, model, query, top_k=TOP_K):
    q_emb = model.encode(query, convert_to_tensor=True)
    scores = [(float(util.cos_sim(q_emb, sec["embedding"])), sec) for sec in sections]
    scores.sort(key=lambda x: x[0], reverse=True)
    return scores[:top_k]

# --- 4. Rank Sentences within Section using spaCy tokenizer ---
def rank_sentences(text, query, model, top_n=TOP_SENTENCES):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    if not sentences:
        return []

    sent_embs = model.encode(sentences, convert_to_tensor=True)
    query_emb = model.encode(query, convert_to_tensor=True)
    sims = util.cos_sim(query_emb, sent_embs)[0]

    ranked = sorted(zip(sims.tolist(), sentences), key=lambda x: x[0], reverse=True)
    return ranked[:top_n]

# --- Rank Sentences from File ---
def rank_sentences_from_file(file_path, query, model, top_n=TOP_SENTENCES):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Use spaCy to split into sentences
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    if not sentences:
        return []
    sent_embs = model.encode(sentences, convert_to_tensor=True)
    query_emb = model.encode(query, convert_to_tensor=True)
    sims = util.cos_sim(query_emb, sent_embs)[0]
    ranked = sorted(zip(sims.tolist(), sentences), key=lambda x: x[0], reverse=True)
    return ranked[:top_n]


# --- Main Flow ---
if __name__ == "__main__":
    # Step 1: Scrape content
    nested_secs = scrape_sections_nested(URL)
    flat_secs = flatten_sections(nested_secs)

    # Step 2: Load embedding model and vectorize chunks
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    flat_secs = embed_sections(flat_secs, embedder)

    # Step 3: Run query
    user_q = QUERY_FROM_FILE
    top = retrieve(flat_secs, embedder, user_q)

    OUTPUT_FILE = "semantic_evaluation.txt"
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Query: {user_q}\n\n")
        for score, sec in top:
            f.write(f"📌 Section: {sec['title']}\n🔍 Score: {score:.4f}\n")
            f.write(f"🧩 Excerpt: {sec['text'][:200]}…\n\n")

            f.write("💡 Most Relevant Sentences:\n")
            ranked_sents = rank_sentences(sec['text'], user_q, embedder)
            for sim, sent in ranked_sents:
                f.write(f"  - ({sim:.4f}) {sent}\n")
            f.write("\n" + "-" * 80 + "\n\n")

    FILE_EVAL_OUTPUT = "file_evaluation.txt"
    # Step 4: Optionally rank from file
    if RANK_FROM_FILE:
        ranked = rank_sentences_from_file(INPUT_FILE, QUERY_FROM_FILE, embedder)
        with open(FILE_EVAL_OUTPUT, "w", encoding="utf-8") as f:
            f.write(f"Ranking sentences from {INPUT_FILE} for query: {QUERY_FROM_FILE}\n")
            for sim, sent in ranked:
                f.write(f"  - ({sim:.4f}) {sent}\n")
