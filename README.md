# Aegis SDK — Enterprise AI Agent Governance & Observability

**Aegis SDK** is a developer-facing governance and observability control plane designed for autonomous AI agents. It provides real-time monitoring, multi-layer policy enforcement, dynamic risk tracking, and detailed execution logging for agentic applications.

---

## 🌟 Key Features

- **4-Layer Governance**: Multi-tier control flow (Request Intelligence, Execution Governance, Runtime Control, Observability).
- **Real-Time Execution Observability**: Live tracing, tool call breakdowns, latency monitoring, and token consumption tracking.
- **Policy Engine**: Evaluate natural-language and deterministic policy rules before agent execution.
- **API Key & Project Governance**: Secure project-based API key lifecycle management with full audit trails.
- **Risk Feed & Scoring**: Deterministic 0-100 governance scoring and risk assessment across tool invocations.

---

## 🏗️ Repository Architecture

- **`aegis/`**: The core Aegis Python SDK for runtime governance and tracking.
- **`backend/`**: FastAPI backend service providing REST API endpoints for telemetry, authentication, workspaces, analytics, and policy evaluation.
- **`frontend/`**: Enterprise-grade dark mode dashboard built with Next.js, Tailwind CSS, and TypeScript.

---

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.10+
- **Node.js**: 18+
- **npm** / **pnpm** / **yarn**

---

### Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

---

### Frontend Setup

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```

4. Open `http://localhost:3000` in your browser.

---

### Aegis SDK Usage

Install and initialize the Python SDK in your agent application:

```python
from aegis import AegisCloudExecutionStore

# Initialize the Aegis client
client = AegisCloudExecutionStore(api_key="ag_your_api_key_here")

# Trace agent executions and tool calls seamlessly
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
