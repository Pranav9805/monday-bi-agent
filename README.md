# Monday.com Business Intelligence Agent

An end-to-end AI-powered executive analytics platform for **Monday.com** workspaces. Built with **LangChain 1.3.11**, **Groq**, **FastAPI**, and **Streamlit**.

---

## 📋 Table of Contents
- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Environment Variables](#-environment-variables)
- [Installation](#-installation)
- [Running the API](#-running-the-api)
- [Running Streamlit](#-running-streamlit)
- [Running Docker](#-running-docker)
- [Sample Questions](#-sample-questions)
- [Future Improvements](#-future-improvements)

---

## 🎯 Project Overview
The **Monday.com Business Intelligence Agent** integrates directly with Monday.com GraphQL API v2 to automatically extract, clean, and analyze enterprise sales deals and work orders datasets.

Using **Groq (`llama-3.3-70b-versatile`)** and **LangChain 1.3.11**, the agent enables executives and decision-makers to ask natural language questions regarding pipeline valuation, revenue collection status, overdue work order deadlines, top client portfolios, and pending invoices without writing custom SQL or manual spreadsheet exports.

---

## 🏗️ Architecture

```text
                                  +-----------------------+
                                  |   Streamlit Web UI    |
                                  |      (Port 8501)      |
                                  +-----------+-----------+
                                              |
                                              v  HTTP REST
                                  +-----------+-----------+
                                  |   FastAPI Backend API |
                                  |      (Port 8000)      |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |   LangChain BI Agent  |
                                  |         (Groq)        |
                                  +-----------+-----------+
                                              |
                                              v
                +-----------------------------+-----------------------------+
                |                                                           |
                v                                                           v
  +-------------+-------------+                               +-------------+-------------+
  |  Monday Tools & Analytics |                               |   Data Cleaning Service   |
  | (Pandas Metrics Computation)|                               |  (Sanitization & Formatting)|
  +-------------+-------------+                               +-------------+-------------+
                |                                                           |
                +-----------------------------+-----------------------------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |   Monday GraphQL API  |
                                  |    (Deals & Orders)   |
                                  +-----------------------+
```

### Core Architecture Layers:
1. **Frontend Presentation**: Interactive Streamlit UI dashboard with workspace metrics and chat interface.
2. **REST API Server**: FastAPI service providing endpoints for health monitoring, board listings, datasets, metrics summaries, and AI agent chat.
3. **AI BI Agent Layer**: LangChain 1.3.11 compiled state graph binding Groq (`llama-3.3-70b-versatile`) with custom tool invocation rules.
4. **Analytics & Services**: Pandas analytics computation engine for pipeline and revenue summaries.
5. **Data Ingestion & Cleaning**: GraphQL pagination layer with automated date/number normalization and missing value filling.

---

## ✨ Features

- **Direct Monday.com GraphQL Ingestion**: Uses `DEALS_BOARD_ID` and `WORK_ORDERS_BOARD_ID` environment variables with cursor-based pagination.
- **Automated Data Sanitization**: Standardizes dates (`YYYY-MM-DD`), converts numeric values to float/int, trims whitespace, and fills null values while preserving raw item data.
- **7 Core BI Analytics Tools**:
  - `get_pipeline_summary`: Total deals, total pipeline value, average deal value.
  - `get_deals_by_stage`: Deals distribution grouped by stage.
  - `get_execution_status_summary`: Work orders grouped by status.
  - `get_overdue_work_orders`: Identifies past-due incomplete work orders.
  - `get_top_customers`: Top clients ranked by active work orders.
  - `get_pending_invoices`: Uncollected pending invoices list.
  - `get_revenue_summary`: Total invoiced, collected, and pending revenue.
- **Executive Streamlit UI**: Real-time sidebar indicators, dataset counters, quick-action suggested questions, and chat history.
- **Ultra-Fast Groq Inference**: Powered by `ChatGroq` from `langchain-groq` using LLaMA 3.3 70B Versatile for high-speed function calling.

---

## 🛠️ Technology Stack

- **Language**: Python 3.12
- **AI Framework**: LangChain `1.3.11`, `langchain-groq`
- **LLM Engine**: Groq (`llama-3.3-70b-versatile`)
- **Backend API**: FastAPI, Uvicorn, Pydantic
- **Frontend Dashboard**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Containerization**: Docker, Docker Compose (`python:3.12-slim`)

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```ini
# Monday.com API Key
MONDAY_API_KEY=your_monday_api_key_here

# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# Monday.com Board IDs
DEALS_BOARD_ID=5030220806
WORK_ORDERS_BOARD_ID=5030221935

# Optional Settings
GROQ_MODEL=llama-3.3-70b-versatile
API_BASE_URL=http://localhost:8000
```

---

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/monday-bi-agent.git
   cd monday-bi-agent
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚡ Running the API

Start the FastAPI backend server using Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

- **API Root**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **Swagger Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## 🖥️ Running Streamlit

Start the Streamlit executive web application:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🐳 Running Docker

Launch the complete application stack (FastAPI + Streamlit) using Docker Compose:

```bash
docker compose up --build
```

- **FastAPI API**: `http://localhost:8000`
- **Streamlit UI**: `http://localhost:8501`

To stop the containers:
```bash
docker compose down
```

---

## 💡 Sample Questions

You can ask the AI BI Agent questions such as:

1. *"How many deals do we currently have?"*
2. *"What is the total pipeline value?"*
3. *"Which work orders are overdue?"*
4. *"Show revenue summary."*
5. *"Show pending invoices."*
6. *"Who are our top 10 customers by work order count?"*
7. *"What is the distribution of deals by stage?"*

---

## 🔮 Future Improvements

- **Vector Database Integration**: Store workspace documentation and item comments in ChromaDB/FAISS for semantic retrieval.
- **Automated Alerts & Scheduling**: Trigger email or Slack notifications for overdue work orders or high-value pipeline changes.
- **Custom Visualizations**: Render dynamic Chart.js / Plotly interactive charts directly inside the Streamlit UI.
- **Multi-Tenant Workspace Support**: Allow switching between multiple Monday.com accounts or boards dynamically via dropdowns.
