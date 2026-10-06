# Document Analyst cu RAG

Agent care răspunde la întrebări despre un document bancar (comisioane CEC),
folosind **RAG** (Retrieval-Augmented Generation) peste PostgreSQL + pgvector.

## Ce face

Ingestează un PDF cu comisioane bancare (9 pachete CEC), îl extrage structurat,
îl stochează cu embeddings în pgvector, și permite întrebări în limbaj natural:
„Cât costă retragerea de la ATM la pachetul PREMIUM?”. Agentul caută semantic în
document și răspunde citând pachetul, pe baza datelor reale (nu inventează).

## Arhitectură

Document → **extracție** (text + tabele) → **chunking** → **embeddings** →
**pgvector** → **similarity search** (cu filtrare pe pachet) → **LLM** → răspuns.

## Structura proiectului

```
document-analyst-rag/
├── agent.py              # agentul QA existent + tool-ul search_documents
├── langchain_agent.py    # agent alternativ cu LangChain (create_agent)
├── ingest.py             # ingestare: rulează pipeline-ul pe un document
├── extraction/           # L3 — procesarea documentelor
│   ├── schemas.py        # Pydantic: Comision, Pachet, DocumentComisioane
│   ├── loaders.py        # loaders PDF/DOCX/TXT + split pe pachete
│   ├── registry.py       # registry de extractoare per doc_type
│   ├── chunker.py        # împărțirea textului în chunks (800/100)
│   └── pipeline.py       # load → chunk → extract → store + JSON
│   └── doc_types/
│       └── cec.py        # SPECIFIC CEC: split pe pachete, prompt, meta, assemble
├── db/                   # L4 — storage
│   ├── database.py       # engine, sesiuni, tranzacții
│   ├── models.py         # Document (1) → DocumentChunk (N), Vector(384)
│   └── repository.py     # CRUD + similarity_search (cosine + filtru pachet)
├── rag/                  # L4 — RAG
│   └── service.py        # embeddings (sentence-transformers) + search
├── tools/                # tool-uri agent existente + search_documents
├── prompts/              # system prompturi (YAML + Jinja2)
├── alembic/              # migrări DB (tabele + extensie vector + index HNSW)
├── data/                 # documentele sursă + JSON-ul extras
├── requirements.txt
└── .env                  # DATABASE_URL
```

## Concepte implementate

- **Extracție structurată cu LLM** — fiecare pachet e trecut prin
  `with_structured_output(Pachet)` → date tipate (serviciu, categorie, valoare),
  salvate ca JSON.
- **Extracție generică pe `doc_type`** — framework-ul (`pipeline.py`, `loaders.py`)
  e generic; tot ce e specific CEC (regex-ul de split pe pachete, prompt-ul de
  extracție, detectarea băncii, asamblarea documentului) e izolat în
  `extraction/doc_types/cec.py` și înregistrat în registry pe `doc_type`. Alt
  document = un plugin nou, fără să atingi pipeline-ul. Loaderele de fișier rămân
  generice, mapate pe extensie cu `@register_loader`.
- **Chunking** — text împărțit în bucăți de ~800 caractere cu overlap 100;
  fiecare chunk e etichetat cu pachetul de care aparține.
- **Postgres + pgvector + Alembic** — `Document` → `DocumentChunk` (one-to-many),
  coloană `Vector(384)`, index HNSW (`vector_cosine_ops`), schemă versionată prin
  migrări Alembic. Indexul HNSW e adăugat prin SQL brut într-o migrație Alembic, pentru că
  autogenerate nu detectează indexurile pgvector.
- **Embeddings multilingve** — `paraphrase-multilingual-MiniLM-L12-v2` (384 dim),
  potrivit pentru text românesc; lazy loading (model încărcat o singură dată).
- **Similarity search + metadata filtering** — cosine distance în pgvector, cu
  filtru opțional pe pachet pentru întrebări specifice (ex: doar PREMIUM).
- **Tool RAG în agent** — `search_documents(query, package)` înregistrat cu
  `@register_tool`; agentul existent îl cheamă și decide singur parametrul
  `package` când întrebarea menționează un pachet (pattern ReAct).
- **Doi agenți, un singur registry de tool-uri** — pe lângă agentul manual ReAct,
  `langchain_agent.py` folosește `create_agent` (LangChain v1), alimentat din
  ACELAȘI `TOOL_REGISTRY` prin `ToolWrapper.to_langchain_tools()`. Un singur
  `@register_tool`, folosit de ambii agenți.  

## Cerințe

- Python 3.10+ (testat pe 3.14)
- Docker (PostgreSQL cu pgvector + LiteLLM)

## Setup

1. Mediu virtual + dependințe:
```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
```

2. Pornește infrastructura (din folderul `infrastructure`, separat de proiect):
```bash
   docker-compose up -d
```
   Pornește Postgres (pgvector, port 5432) și LiteLLM (port 4000, pentru LLM).

3. Configurează `.env` în proiect:
```
   DATABASE_URL=postgresql+psycopg://skillab:skillab_dev@localhost:5432/skillab
```
   (cheile API — Claude/Gemini — stau în `.env`-ul din `infrastructure/`)

4. Creează schema bazei de date:
```bash
   alembic upgrade head
```

## Utilizare

**Ingestează documentul** (load → chunk → extract → store):
```bash
python ingest.py data/cec_comisioane.pdf
```
Rezultat: ~9 pachete extrase, chunks cu embeddings în DB, JSON în
`data/cec_comisioane_extracted.json`.

**Întreabă agentul:**
```bash
python agent.py -m claude "Cât costă retragerea de la ATM la pachetul PREMIUM?"
python agent.py -m claude "Ce comision lunar are pachetul STUDENT FREE?"
python agent.py -m claude "Ce conține pachetul INFINITE?"
```

## Exemplu

```
USER: Cât costă retragerea de la ATM la pachetul PREMIUM?

  [tool] search_documents({"query": "retragere ATM", "package": "PREMIUM"})
         -> [PREMIUM | 0.66] Retrageri de numerar de la ATM-ul altor bănci — 0 lei ...

AGENT: La pachetul PREMIUM, retragerile de numerar în lei de la ATM-ul altor
bănci costă 0 lei. Pentru pachetul gratuit (0 lei/lună) trebuie îndeplinite
condițiile de rulaj; altfel pachetul costă 50 lei/lună.
```

**Sau prin agentul LangChain:**
```bash
python langchain_agent.py "Cât costă retragerea de la ATM la pachetul PREMIUM?"
```

## Exemplu

```text
Tool-uri încărcate în agent: ['calculator', 'get_datetime', 'get_weather', 'web_search', 'search_documents']
Încărcare model paraphrase-multilingual-MiniLM-L12-v2...

============================================================
RĂSPUNS:
============================================================
La pachetul PREMIUM, retragerile de numerar în lei de la ATM-urile altor bănci
costă 0 lei (sunt gratuite).

Retragerile de la ATM-urile CEC Bank sunt, de asemenea, incluse gratuit în pachet.

Costurile apar doar pentru retragerile de la ghișeul băncii, cu comisioane
variabile în funcție de sumă și dacă sunt programate sau nu.
```

## Modele disponibile

Prin LiteLLM: `claude`, `gemini` (cloud) și `qwen`, `mistral` (locale).
Schimbă modelul cu `-m <model>`. Embeddings: `paraphrase-multilingual-MiniLM-L12-v2`
(local, fără cheie).