# GbEnterprise AI Platform

A **FastAPI-based Enterprise AI orchestration platform** that manages AI initiatives, bots, and capabilities with multi-tenant support. The platform validates and dispatches AI execution requests to external analyzer services, logs every execution, and returns structured results.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Core Concepts](#core-concepts)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Services](#services)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)

---

## Architecture Overview

```
┌──────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
│   Client     │──────▶│  GbEnterprise AI API  │──────▶│  Report Analyzer     │
│  (REST)      │◀──────│  (FastAPI + SQLAlchemy)│◀──────│  (External Service)  │
└──────────────┘       └──────────┬───────────┘       └──────────────────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │    PostgreSQL DB      │
                       │  (Execution Logs,     │
                       │   Bots, Capabilities, │
                       │   Initiatives)        │
                       └──────────────────────┘
```

**Request Flow:**

1. Client sends an execution request with initiative, bot, and capability codes.
2. The API validates the initiative, capability, and bot against the database.
3. An execution log is created with an initial pending status.
4. The request is dispatched to the external Report Analyzer service.
5. The execution log is updated with the result (success or failure).
6. The structured response is returned to the client.

---

## Tech Stack

| Technology       | Purpose                          |
|------------------|----------------------------------|
| **FastAPI**      | Web framework / REST API         |
| **Pydantic**     | Request/response validation      |
| **SQLAlchemy**   | ORM / database interaction       |
| **PostgreSQL**   | Relational database (via psycopg2) |
| **Uvicorn**      | ASGI server                      |
| **Requests**     | HTTP client for external services |
| **python-dotenv**| Environment variable management  |

---

## Project Structure

```
app/
├── main.py                          # FastAPI app entry point (port 8006)
├── api/
│   ├── __init__.py
│   ├── ai.py                        # AI execution endpoints (/api/ai/*)
│   └── health.py                    # Health check endpoints (/health, /health/db)
├── core/
│   ├── config.py                    # Environment config (DATABASE_URL)
│   └── database.py                  # SQLAlchemy engine & session management
├── models/
│   ├── base.py                      # SQLAlchemy declarative base
│   ├── bot.py                       # MAIbot model
│   ├── capability.py                # MAIcapability model
│   ├── execution.py                 # TAIexecution model
│   └── initiative.py                # MAIinitiative model
├── schemas/
│   ├── __init__.py
│   └── executes.py                  # Pydantic request/response schemas
├── services/
│   ├── capability_dispatcher.py     # Capability dispatch logic
│   └── report_service_adapter.py    # External Report Analyzer HTTP adapter
requirements.txt                     # Python dependencies
```

---

## Core Concepts

### Initiative (`MAIinitiative`)
An **initiative** represents a high-level AI project or program. Each initiative has a unique code, name, maturity level, and is scoped to a tenant.

### Bot (`MAIbot`)
A **bot** is an AI agent tied to a specific initiative. Bots have a read-only flag that controls whether they are allowed to execute. Only read-only bots (`isreadonly = 1`) can be invoked through the API.

### Capability (`MAIcapability`)
A **capability** defines a specific AI function (e.g., `QUESTION_ANSWER`, file upload analysis, JSON data analysis). Capabilities are dispatched to the appropriate external service endpoint.

### Execution (`TAIexecution`)
An **execution** is a log record of every AI invocation. It tracks the user, tenant, initiative, bot, capability, and the outcome status:
- `0` — Pending
- `1` — Success
- `-1` — Failed

---

## API Endpoints

### Health

| Method | Endpoint      | Description                       |
|--------|---------------|-----------------------------------|
| GET    | `/health`     | Returns platform running status   |
| GET    | `/health/db`  | Tests database connectivity       |

### AI Execution

| Method | Endpoint                        | Description                                 |
|--------|---------------------------------|---------------------------------------------|
| POST   | `/api/ai/execute`               | Execute an AI capability                    |
| GET    | `/api/ai/execution/{id}`        | Retrieve a specific execution log by ID     |

#### `POST /api/ai/execute`

**Request Body:**
```json
{
  "tenantId": 1,
  "userId": 42,
  "initiativeCode": "INIT_001",
  "botCode": "BOT_REPORT",
  "capabilityCode": "QUESTION_ANSWER",
  "input": {
    "session_id": "abc-123",
    "message": "What are the key findings?"
  }
}
```

**Response:**
```json
{
  "executionId": 101,
  "result": {
    "session_id": "abc-123",
    "answer": "The key findings are..."
  }
}
```

**Validation Flow:**
1. Validates `initiativeCode` exists in `maiinitiative`
2. Validates `capabilityCode` exists in `maicapability`
3. Validates `botCode` exists in `maibot` and belongs to the initiative
4. Confirms the bot is read-only (`isreadonly = 1`)

---

## Database Schema

### `maiinitiative`
| Column              | Type         | Constraints          |
|---------------------|--------------|----------------------|
| aiinitiativeid      | BIGINT       | PK, Indexed          |
| aiinitiativecode    | VARCHAR(50)  | Unique, Not Null     |
| aiinitiativename    | VARCHAR(150) | Not Null             |
| maturitylevel       | SMALLINT     |                      |
| status              | SMALLINT     |                      |
| tenantid            | INTEGER      |                      |

### `maibot`
| Column           | Type         | Constraints          |
|------------------|--------------|----------------------|
| aibotid          | BIGINT       | PK, Indexed          |
| aibotcode        | VARCHAR(50)  | Unique, Not Null     |
| name             | VARCHAR(150) |                      |
| aiinitiativeid   | BIGINT       |                      |
| description      | TEXT         |                      |
| isreadonly       | SMALLINT     |                      |
| status           | SMALLINT     |                      |
| version          | SMALLINT     |                      |
| tenantid         | INTEGER      |                      |

### `maicapability`
| Column             | Type         | Constraints          |
|--------------------|--------------|----------------------|
| aicapabilityid     | BIGINT       | PK, Indexed          |
| aicapabilitycode   | VARCHAR(50)  | Unique, Not Null     |
| aicapabilityname   | VARCHAR(100) | Not Null             |
| maxmaturitylevel   | SMALLINT     |                      |
| status             | SMALLINT     |                      |
| tenantid           | INTEGER      |                      |

### `taiexecution`
| Column           | Type         | Constraints          |
|------------------|--------------|----------------------|
| aiexecutionid    | BIGINT       | PK, Indexed          |
| userid           | INTEGER      |                      |
| tenantid         | INTEGER      |                      |
| aiinitiativeid   | BIGINT       |                      |
| aibotid          | BIGINT       |                      |
| aicapabilityid   | BIGINT       |                      |
| outcomestatus    | SMALLINT     |                      |

---

## Services

### Report Service Adapter (`report_service_adapter.py`)
Handles communication with the external **Report Analyzer** microservice. Supports three dispatch modes based on the capability and input:

| Capability Code     | Analyzer Endpoint   | Description                         |
|---------------------|---------------------|-------------------------------------|
| `QUESTION_ANSWER`   | `POST /chat`        | Conversational Q&A with session     |
| *(file provided)*   | `POST /upload-file` | File-based analysis                 |
| *(default)*         | `POST /upload-json` | JSON payload analysis               |

---

## Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL database
- External Report Analyzer service running

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd GbEnterpriseAi

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/enterprise_ai
REPORT_ANALYZER_URL=http://localhost:8000
```

### Running the Server

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8006 --reload
```

Or directly:

```bash
cd app
python main.py
```

The API will be available at `http://localhost:8006. Interactive API docs are at `http://localhost:8006/docs`.

---

## Environment Variables

| Variable              | Required | Description                                    |
|-----------------------|----------|------------------------------------------------|
| `DATABASE_URL`        | ✅       | PostgreSQL connection string                   |
| `REPORT_ANALYZER_URL` | ✅       | Base URL of the external Report Analyzer service |

---

## License

Proprietary — © GbEnterprise

