# Adaptive RAG Platform

This prototype repository contains a multi-service FastAPI deployment that provides authentication, document management, indexing and a LangGraph-powered retrieval-augmented chat experience for clinical-trial content. Each service can be branded via the `BRAND_NAME` environment variable.

### Service map

- **auth_service** – Authentication, JWT issuance, user management, and password reset flows.
- **documents_service** – S3 document administration: folder initialisation, upload/download, and presigned URLs.
- **index_service** – Ingests PDFs from S3 or local storage into PGVector using LangChain chunking.
- **retrieval_service** – Vector-store backed retriever API (PGVector + OpenAI embeddings).
- **chat_service** – LangGraph workflow combining retrieval, grading, and optional web search, serving a streaming chat API/UI.
- **resource_service** – Example protected API that demonstrates role-based guards.

### Repository structure

```
├── auth_service/              # Auth API: routers, schemas, repositories, utils
├── chat_service/              # LangGraph chat workflow, nodes, chains, FastAPI entrypoint
├── documents_service/         # Document management API, S3 utilities, TMF bootstrapper
├── index_service/             # Document ingestion/indexing into PGVector
├── resource_service/          # Sample protected endpoints leveraging auth_service
├── retrieval_service/         # Vector retrieval API backed by PGVector
├── docs/                      # Example SOP PDFs used during indexing/testing
├── static/                    # Lightweight chat UI (served by chat_service)
├── tests/                     # Smoke tests for retrieval and web-search logic
├── docker-compose.yml         # Orchestrates all services + Postgres/pgAdmin
├── requirements.txt           # Pinned Python dependencies for all services
├── s3-cloudformation.yml      # AWS template provisioning the documents bucket + IAM users
├── tmf_structure.txt          # Sample Trial Master File layout for TMF initialisation endpoint
└── readme.md                  # Project documentation (this file)
```

## Prerequisites

- Python 3.10+
- Docker and docker-compose (for containerised runs)
- Access keys for third-party services you intend to use:
  - `OPENAI_API_KEY` for LangChain components
  - `TAVILY_API_KEY` if web search should be enabled
  - AWS credentials when indexing from / storing to S3

## Configuration

1. Copy `.env_example` to `.env` and populate the values, especially:
   - `BRAND_NAME`
   - `SECRET_KEY`
   - `DATABASE_URL`, `VECTORDB_URL`
   - Mail credentials (`MAIL_*`) if password reset emails are required
   - `OPENAI_API_KEY` and optional `TAVILY_API_KEY`
2. Ensure the same `.env` file is available to docker-compose (already referenced).

If you intend to use the S3-backed document workflows, provision the storage stack with CloudFormation:

```bash
aws cloudformation deploy \
  --template-file s3-cloudformation.yml \
  --stack-name documents-stack \
  --parameter-overrides Client=<client> Domain=<domain>
```

The template creates an S3 bucket (`documents.<Client>.<Domain>`) plus paired IAM users with read-only and full-access credentials that map to the document/index services.

After the stack is live you can bootstrap a study folder structure using `tmf_structure.txt` (a sample Trial Master File hierarchy). The `/admin/documents/initialize-tmf` endpoint accepts the file as upload and creates folder prefixes such as `tmf/<study>/Zone 1 - Trial Management/...` directly in S3.

### Key environment variables

| Variable | Purpose |
|----------|---------|
| `BRAND_NAME` | Display name injected into the chat UI and service metadata. |
| `DOMAIN` | Used when constructing S3/PG namespaces; also feeds the CloudFormation template. |
| `AUTH_SERVICE_URL` | Base URL for verifying tokens from other services. |
| `DATABASE_URL` | SQLAlchemy connection string used by auth/index services. |
| `VECTORDB_URL` | PGVector connection string for indexing/retrieval. |
| `RETRIEVAL_SERVICE_URL` | Base URL the chat service calls for vector retrieval. |
| `OPENAI_API_KEY` | API key for embeddings/LLM calls. |
| `TAVILY_API_KEY` | Optional key enabling web-search fallbacks. |
| `MAIL_*` | SMTP configuration consumed by the auth service for password reset emails. |
| `AWS_*` | Credentials used by document/index services when interacting with S3. |

Environment variables are loaded via `python-dotenv`, so values in `.env` are respected for local runs and Docker deployments.

## Running locally

Start the desired service with `uvicorn` (after activating your virtual environment and installing dependencies with `requirements.txt`):

```bash
pip install -r requirements.txt
cd auth_service
uvicorn auth_service.main:app --reload --port 8000
```

Repeat for other services as needed (`documents_service`, `index_service`, `retrieval_service`, `chat_service`, `resource_service`).

### Suggested development workflow

1. Install dependencies and run the smoke tests:
   ```bash
   pip install -r requirements.txt
   pytest
   ```
2. Start backing services via Docker (Postgres/pgAdmin) or `docker-compose` (see below) to avoid manual DB setup.
3. Launch the microservice you are modifying with `uvicorn --reload` for hot reloading.
4. Update `.env` as needed (e.g., swap `OPENAI_API_KEY`, toggle `TAVILY_API_KEY`).
5. When adding new package dependencies, pin them in `requirements.txt` and re-run the tests.

## Running with Docker Compose

Build and launch the full stack:

```bash
docker-compose up --build
```

The compose file provisions Postgres + pgAdmin, all FastAPI applications, and wires service discovery through Docker bridge networking. Host ports:

- Auth: `http://localhost:8000`
- Documents: `http://localhost:8002`
- Retrieval: `http://localhost:8003`
- Chat: `http://localhost:8004`
- Index: `http://localhost:8005`
- Resource: `http://localhost:8006`
- pgAdmin: `http://localhost:8080`

### Adaptive RAG data flow

1. A user submits a question to `chat_service` (`/chat`).
2. The LangGraph workflow routes the question to either the vector store (`retrieval_service`) or web search (Tavily) based on the router chain output.
3. Retrieved documents are graded for relevance; irrelevant chunks trigger a web-search fallback.
4. The generation chain produces a citation-rich answer, which is graded for hallucinations and alignment with the original question.
5. Failing grades cause the workflow to retry (with web search if needed); successful answers stream back to the client.

## Tests

Install dependencies with `pip install -r requirements.txt` (which includes `pytest`) and run from the repository root:

```bash
pytest
```

The current test suite contains smoke checks for the adaptive web-search node and vector retriever configuration, and provides a scaffold for adding service-level tests.

## Notes

- This is a prototype; production hardening (observability, CI/CD, expanded testing, security hardening) still needs to be layered on.
- Web-search is optional: if Tavily is not configured the chat service will fallback gracefully to RAG-only responses.
- Retrieval and indexing rely on PGVector; ensure the target database exists and is reachable (docker-compose creates it automatically).
- Secrets are set through environment variables or secret managers.
