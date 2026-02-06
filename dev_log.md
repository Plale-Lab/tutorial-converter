# Developer Log - ConvertIt

**Date:** Feb 06, 2026
**Status:** Alpha (Django Verification Phase)

## 1. Project Overview
"ConvertIt" is an AI-powered pipeline that converts raw tutorials (web URLs or PDFs) into tailored educational materials (e.g., "5th Grader" or "Professional" styles) with custom AI-generated illustrations.

## 2. Architecture & Stack
The system has evolved from a simple script to a micro-service-like Django monolith.

| Component | Tech | Responsibility |
| :--- | :--- | :--- |
| **Frontend** | Django + Tailwind CSS | Request handling, 3-column "Workstation" UI. |
| **Orchestration** | LangGraph | Managing the state machine (Ingest -> Rewrite -> Logic -> Assemble). |
| **LLM Engine** | LiteLLM + Ollama | Unified interface for Local (Llama 3) or Remote (OpenAI) models. |
| **Ingestion** | Firecrawl / LlamaParse | Converting HTML/PDF to Markdown. |
| **Storage (RAG)** | ChromaDB | Local vector store for glossary terms and context. |
| **Vision** | ComfyUI / API | Image generation (Currently mocked/stubbed in parts). |
| **Assembly** | Jinja2 + WeasyPrint | Rendering final HTML and PDF. |

## 3. Implementation Log

### Phase 1-4: Core Logic (Python Modules)
- **`core/ingestion.py`**: Added support for Firecrawl (scraping) and LlamaParse (docs).
- **`core/engine.py`**: Wrapper around LiteLLM. Supports `generate_structured` using `instructor` lib for JSON outputs.
- **`agents/workflow.py`**: Implemented LangGraph StateGraph.
    - Nodes: `node_clean`, `node_glossary`, `node_rewrite`, `node_critique`, `node_generate_images`.
    - Logic: Map-Reduce strategy implemented for long content (>15k chars).

### Phase 5: Django Integration
- Created `web_ui` project and `converter` app.
- **Views**: `converter/views.py` contains the main `convert` controller.
    - **CRITICAL**: The workflow execution (`workflow_app.invoke`) is largely **Synchronous/Blocking**. This currently hangs the Django worker thread until completion.
- **Settings**: Configured to look for templates in root `templates/` and static headers in `static/`.

### Phase 6: UI Redesign (The Workstation)
- Moved from simple Form to **3-Column Layout** (Config | Feed | Result).
- **Frontend Logic (`static/js/app.js`)**:
    - Uses `fetch` (AJAX) to post data to Django.
    - **Simulation**: Because the backend is blocking, the frontend *simulates* the "Live Intelligence" feed (Ingesting... Rewriting...) with timers while waiting for the response. This is a UX hack.
    - **AJAX Response**: Returns JSON with `{ success: true, pdf_url: "...", markdown_content: "..." }`.

## 4. Key Files & Locations

- **Controller**: `converter/views.py` - Main interaction point between UI and Logic.
- **Template**: `templates/converter/index.html` - The UI structure.
- **Frontend Logic**: `static/js/app.js` - UI behavior and state management.
- **Core Pipeline**: `agents/workflow.py` - The brain of the operation.
- **PDF Gen**: `core/assembly.py` - Handles WeasyPrint.

## 5. Known Issues & Technical Debt

1.  **Blocking Sync Views**: 
    - *Issue*: The `workflow_app.invoke()` runs on the main thread. Long tutorials will time out standard HTTP requests (e.g., Gunicorn defaults).
    - *Fix Required*: Move workflow execution to **Celery** or **Django Q**. Poll for status via API.

2.  **Dependency Fallbacks**:
    - *Issue*: `WeasyPrint` requires GTK3 (DLLs on Windows). `ChromaDB` had Pydantic version conflicts.
    - *Current State*: `core/assembly.py` and `database/vector_store.py` have `try...except` blocks. If libs fail, they print Warnings and return mocked/skipped results.
    - *Action*: Ensure production env (Docker) has correct binaries.

3.  **Vision Integration**:
    - *Issue*: `core/vision.py` has a placeholder `_generate_comfy` method returning fake bytes.
    - *Action*: Needs real integration with a running ComfyUI instance's API endpoint.

4.  **Static Files**:
    - Initially, files were trapped in `web_ui/`. They have been moved to root `templates/` and `static/` to simplify finding them.

## 6. Development Tips
- **Run Server**: `python manage.py runserver`
- **Virtual Env**: `.venv\Scripts\Activate.ps1`
- **PDF Output**: Generated PDFs currently dump into `static/` with a UUID. A periodic cleanup task is needed.
