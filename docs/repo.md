geo/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 # FastAPI init & routers include
│  │  ├─ routes/
│  │  │  ├─ query.py             # POST /query
│  │  │  ├─ runs.py              # GET /runs, /summary, /trends
│  │  ├─ models/                 # SQLAlchemy/SQLModel tables + Pydantic schemas
│  │  │  ├─ db.py                # engine/session/get_db
│  │  │  ├─ run.py               # Run ORM + schema
│  │  │  ├─ extraction.py        # Extraction ORM + schema
│  │  │  ├─ prompt.py            # Prompt ORM + schema
│  │  ├─ services/
│  │  │  ├─ adapters/            # engine adapters (same interface)
│  │  │  │  ├─ base.py
│  │  │  │  ├─ openai_adapter.py
│  │  │  │  ├─ perplexity_adapter.py
│  │  │  │  └─ gemini_adapter.py
│  │  │  ├─ extractor/
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ v1_stringmatch.py # current logic
│  │  │  │  └─ v2_ner_embed.py   # upgrade later
│  │  │  └─ cache.py             # idempotency hash (query+engine+prompt)
│  │  ├─ utils/
│  │  │  ├─ logging.py
│  │  │  └─ time.py
│  │  └─ settings.py             # env loading (keys, DB url)
│  ├─ requirements.txt
│  ├─ .env.example               # keys placeholders
│  └─ scripts/
│     ├─ seed_queries.json
│     ├─ smoke_run.py            # calls POST /query on sample set
│     └─ migrate.py              # create_all()
├─ frontend/                      # (add when you start Next.js)
│  └─ (nextjs app here)
├─ data/                          # input/output artifacts (not code)
│  ├─ queries/queries.json        # your existing queries file
│  └─ storage/                    # persisted CSV exports if you keep them
├─ docs/
│  ├─ api_contract.md
│  └─ architecture.md
├─ .gitignore
├─ README.md
└─ LICENSE (optional)
