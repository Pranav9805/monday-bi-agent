# Architectural Decision Log (ADR)

This document details the key technical, architectural, and design choices made during the development of the **Monday.com Business Intelligence Agent**, along with evaluated trade-offs, system limitations, and future roadmap directions.

---

## 📐 Technology Selection & Rationale

### 1. Why FastAPI?
- **Asynchronous Performance & High Throughput**: Built on Starlette and Uvicorn, FastAPI provides asynchronous event loop support (`async/await`), enabling non-blocking execution during external API network requests (Monday.com GraphQL API & Google Gemini LLM API).
- **Automated OpenAPI Documentation**: Automatically generates interactive Swagger UI (`/docs`) and ReDoc (`/redoc`) documentation from Pydantic schemas, reducing documentation overhead.
- **Strict Data Validation with Pydantic**: Guarantees type safety and validation for incoming REST payloads (e.g. `/chat` questions) and outgoing metrics responses.
- **CORS & Middleware Flexibility**: Easily configurable middleware support (`CORSMiddleware`) allowing seamless decoupling between backend services and frontend presentation clients.

### 2. Why Streamlit?
- **Rapid Executive UI Prototyping**: Streamlit allows building clean, production-ready web dashboards directly in pure Python without needing complex React/Vue frontend setups.
- **Built-in Chat UI Primitives**: Standardized chat components (`st.chat_message`, `st.chat_input`, `st.spinner`) streamline the implementation of interactive conversational AI interfaces.
- **Session State Management**: Provides clean state persistence (`st.session_state`) for conversation logs across user interactions and page rerenders.
- **Real-Time Sidebar Metrics**: Built-in metric cards (`st.metric`) allow displaying real-time system health and dataset volume counts alongside the main chat view.

### 3. Why LangChain?
- **Standardized Tool-Calling Architecture**: Abstracts tool definitions via `@tool` decorators, allowing the AI agent to dynamically decide which analytics functions (`get_pipeline_summary`, `get_overdue_work_orders`, etc.) to invoke based on user intent.
- **LangChain 1.3.11 State Graph Architecture**: Uses state graph compilation (`from langchain.agents import create_agent`) for predictable agent state transitions, tool execution loops, and structured response generation.
- **LLM Abstraction**: Decouples prompt engineering and tool binding from specific provider implementations, making it simple to switch underlying LLMs if needed.

### 4. Why Google Gemini?
- **High-Speed Function Calling (`gemini-2.0-flash`)**: Delivers low latency for multi-tool tool choice decisions and natural language reasoning.
- **Large Context Window & Multi-Turn Processing**: Capable of processing large tool outputs and complex tabular datasets without truncating essential context.
- **Cost-Efficiency & Tier Scaling**: Generous free/developer tier pricing with strong function calling accuracy.

### 5. Why Monday.com GraphQL API v2?
- **Precise Data Selection**: GraphQL allows querying exact board column values (`column_values`, `title`, `text`, `value`), preventing over-fetching of unnecessary workspace metadata.
- **Direct Board Lookups (`DEALS_BOARD_ID` & `WORK_ORDERS_BOARD_ID`)**: Eliminates redundant workspace searches by directly querying specified environment board IDs.
- **Cursor Pagination Support**: Efficiently fetches large datasets (e.g. hundreds of deals and work orders) across page boundaries using `items_page` and `next_items_page` cursor tokens.

### 6. Why Pandas?
- **High-Performance In-Memory Analytics**: Offers vectorized operations for filtering, grouping (`groupby`), aggregations (`sum`, `mean`, `count`), and date conversions (`pd.to_datetime`).
- **Flexible Null & Missing Value Handling**: Seamlessly handles missing dates, NaNs, and unexpected string types across unstandardized Monday board columns.
- **Easy Export to Python Dictionaries**: Converts DataFrame outputs into clean Python dictionaries (`df.to_dict(orient="records")`), enabling serialization for FastAPI and LangChain JSON tools.

---

## ⚖️ Trade-offs

| Decision | Trade-off Made | Benefits Gained |
|---|---|---|
| **Streamlit vs. Custom React UI** | Less custom UI styling control | 10x faster development velocity, zero Node/npm dependencies. |
| **In-Memory Pandas Data Processing** | Requires loading board items into RAM per query | Zero database infrastructure complexity; real-time accuracy. |
| **Direct REST Call from UI to FastAPI** | Slightly higher latency than direct python call | Clean separation of concerns; enables non-UI API clients. |
| **Zero-Temperature LLM Setting** | Less creative/conversational variance | Maximum factual precision; prevents hallucinated financial numbers. |

---

## ⚠️ Known Limitations

1. **API Rate Quota Limits**: Google Gemini API free-tier imposes rate limits (`429 RESOURCE_EXHAUSTED`). The agent includes retry logic and user-facing notifications when quotas are exceeded.
2. **Synchronous In-Memory Computation**: Pipeline metrics computation scales in RAM with board size. Extremely large datasets (100k+ items) would benefit from database indexing or caching.
3. **Column Identifier Sensitivity**: Relies on expected column names/types from Monday boards. Major board column deletions require corresponding service mapping updates.

---

## 🔮 Future Improvements

1. **Redis/Memcached Caching Layer**: Cache Monday API responses for 5–15 minutes to reduce API latency and avoid rate limits.
2. **Vector Database Integration (RAG)**: Index workspace documents, project specifications, and item updates into ChromaDB/FAISS for semantic query answering.
3. **Automated Executive Alerts & Webhooks**: Connect Monday.com webhooks to automatically trigger Slack or email alerts when critical work orders become overdue.
4. **Interactive Visualization Widgets**: Render dynamic Plotly charts (e.g. pipeline funnels, revenue trend line graphs) within the Streamlit UI.
