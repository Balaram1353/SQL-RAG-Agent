# SQL RAG Agent

A containerized AI-powered SQL assistant that lets users query a relational database using natural language. The application combines retrieval-augmented generation (RAG), schema-aware SQL generation, read-only query execution, and a locally hosted large language model.

The project uses the UCI Online Retail dataset to demonstrate natural-language data analytics on a real-world transactional dataset.

## Features

- **Natural language to SQL:** Ask questions about retail transactions in plain English.
- **Schema-aware query generation:** Retrieves relevant database schema information to help the LLM generate SQL.
- **Retrieval-augmented generation (RAG):** Uses embedding-based similarity search to retrieve relevant schema documents.
- **Local LLM integration:** Uses Ollama with `qwen2.5:7b-instruct` as the configured default model.
- **Read-only SQL execution:** Validates SQL and executes queries against SQLite in read-only mode.
- **Query timeout and result limits:** Applies execution time limits and caps returned rows.
- **SQL repair attempts:** Retries failed queries with error context.
- **Schema inspection:** Answers supported questions about database tables, columns, and definitions without requiring SQL generation.
- **Profit guardrail:** Rejects profit-related questions when the database lacks recognized cost columns.
- **Interactive interface:** Built with Streamlit.
- **Docker support:** Runs the application using Docker Compose.

## Architecture

```text
User question
     |
     v
Streamlit interface
     |
     v
SQL RAG agent
     |
     +----> Schema discovery
     |
     +----> Schema documents
     |          |
     |          v
     |     Embeddings
     |          |
     |          v
     |     Similarity search
     |
     +----> Ollama LLM
     |          |
     |          v
     |     SQL generation
     |
     v
SQL validation
     |
     v
Read-only SQLite execution
     |
     v
Result explanation
     |
     v
User
```

Schema-related questions can be answered directly from database metadata. Data-related questions use retrieved schema context to guide SQL generation.

## Technology Stack

- Python 3.14
- Streamlit
- SQLite
- Ollama
- Sentence Transformers
- NumPy
- SQLGlot
- Pandas
- uv
- Docker and Docker Compose
- pytest

## Dataset

This project uses the **Online Retail** dataset from the UCI Machine Learning Repository.

- **Source:** https://archive.ics.uci.edu/dataset/352/online+retail
- **Original records:** 541,909 transaction rows
- **Time period:** December 2010 to December 2011
- **Original format:** Excel
- **Database format:** SQLite
- **Database table:** `online_retail`

The import script converts the original dataset into a SQLite table and creates indexes to support common queries.

### Database columns

| Column | Description |
|---|---|
| `invoice_no` | Invoice identifier |
| `stock_code` | Product identifier |
| `description` | Product description |
| `quantity` | Quantity purchased or returned |
| `invoice_date` | Transaction date and time |
| `unit_price` | Unit price |
| `customer_id` | Customer identifier; may be NULL |
| `country` | Customer's country or recorded region |

### Download and import the dataset

1. Download `Online Retail.xlsx` from the [official UCI dataset page](https://archive.ics.uci.edu/dataset/352/online+retail).
2. Place the file in the project's `data/` directory.
3. Install the project dependencies and import the dataset:

```powershell
uv sync
uv run python scripts/import_retail_data.py
```

The script creates `data/retail.db`.

The Excel file and generated database are intentionally excluded from Git to avoid committing large data files. Each user must download and import the dataset locally before running the Docker application.

### Dataset considerations

- Some transactions have negative quantities, including returns and cancellations.
- Some records have missing customer identifiers.
- The dataset represents historical transactions, not current retail performance.
- The dataset does not include product costs. Revenue calculations may be possible, but actual profit cannot be determined from this dataset alone.

## Prerequisites

- Git
- Docker Desktop with Docker Compose
- Ollama installed and running on the host machine
- The configured Ollama model downloaded locally

Download the model:

```powershell
ollama pull qwen2.5:7b-instruct
```

Make sure Ollama is running and reachable before asking questions that require LLM inference.

## Run with Docker

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/SQL-RAG-Agent.git
cd SQL-RAG-Agent
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Prepare the dataset

Download `Online Retail.xlsx` from the UCI link above and place it in `data/`.

Run:

```powershell
uv sync
uv run python scripts/import_retail_data.py
```

### 3. Start the application

```powershell
docker compose up --build -d
```

Docker Compose configures the application to use:

- Database: `/app/data/retail.db`
- Ollama endpoint: `http://host.docker.internal:11434/api/chat`
- Default model: `qwen2.5:7b-instruct`

The `data/` directory is mounted into the container, allowing the container to access the locally generated database.

### 4. Open the application

Visit:

http://localhost:8501

### Useful Docker commands

Check status:

```powershell
docker compose ps
```

View logs:

```powershell
docker compose logs -f sql-rag-agent
```

Stop the application:

```powershell
docker compose down
```

Rebuild after changing application code or configuration:

```powershell
docker compose up --build -d
```

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `OLLAMA_URL` | Ollama chat API endpoint | `http://localhost:11434/api/chat` |
| `OLLAMA_MODEL` | Model used for responses | `qwen2.5:7b-instruct` |
| `DATABASE_PATH` | SQLite database path | `data/shop.db` |

The Docker Compose configuration overrides `DATABASE_PATH` with `/app/data/retail.db`.

For local development in PowerShell, select the retail database before starting the application:

```powershell
$env:DATABASE_PATH = "data/retail.db"
uv run streamlit run app/streamlit_app.py
```

The local Ollama endpoint and the Docker Ollama endpoint differ because the application runs in a container when using Docker.

## Example Questions

Try asking:

- Which countries are present in the retail dataset?
- How many transaction rows are in the database?
- Which products have the highest sales quantities?
- What is the total revenue by country?
- How do transaction volumes change month by month?
- Which customers have the highest purchase totals?
- Show the structure of the database table.
- Which products have the highest average selling prices?

Actual profit and profit-margin questions require suitable cost data, which this dataset does not provide.

## Testing

Run the automated test suite:

```powershell
uv run pytest -v
```

Tests cover selected agent behaviors, LLM handling, and SQL validation and execution. Results can depend on the available database configuration and test fixtures.

## Project Structure

```text
SQL-RAG-Agent/
├── app/
│   ├── agent.py
│   ├── database.py
│   ├── documents.py
│   ├── embeddings.py
│   ├── file_loader.py
│   ├── llm.py
│   ├── query.py
│   ├── schema.py
│   ├── sql_executor.py
│   ├── streamlit_app.py
│   └── vector_store.py
├── data/
│   ├── sample_employees.csv
│   └── schema_descriptions.json
├── scripts/
│   └── import_retail_data.py
├── tests/
├── .dockerignore
├── .gitignore
├── compose.yaml
├── Dockerfile
├── main.py
├── pyproject.toml
├── uv.lock
└── README.md
```

Generated SQLite databases and the downloaded Excel dataset are created locally and are not committed to Git.

## Learning Objectives

This project demonstrates practical implementation of:

- Retrieval-augmented generation
- Embedding-based schema retrieval
- Natural-language-to-SQL workflows
- LLM integration with Ollama
- SQL validation and read-only execution
- Error handling and query repair
- SQLite schema discovery
- Python dependency management
- Docker containerization
- Automated testing

## Limitations and Safety

This project is intended for learning and portfolio demonstration.

- Generated SQL can still be logically incorrect even when it passes validation.
- Read-only access prevents ordinary database modifications through the configured SQLite connection, but SQL validation alone is not a complete security boundary.
- The query timeout and row limit help control execution, but do not guarantee protection against every resource-intensive query.
- Schema retrieval quality depends on the documents generated and the embedding model.
- The application requires an accessible Ollama service for LLM-powered queries.
- Profit cannot be reliably calculated without suitable cost data.

Do not expose the application to an untrusted network without additional authentication, access controls, and security review.

## Dataset Attribution

Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33

The dataset is licensed under the Creative Commons Attribution 4.0 International license (CC BY 4.0). See the [official UCI dataset page](https://archive.ics.uci.edu/dataset/352/online+retail) for details.

This project is an independent educational software project and is not affiliated with the original dataset contributor.

## Project Code License

No license has yet been specified for this project's source code. Until a license is added, do not assume that others have permission to reuse or redistribute the code. The dataset license does not automatically determine the license for the project's code.
