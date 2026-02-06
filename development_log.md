# Development Log

**Date:** Feb 06, 2026
**Date:** Feb 06, 2026
**Current Status:** Alpha (Debug Console Implemented)

## Recent Updates
- **Transition to Django**: Migrated from Chainlit/Streamlit to a robust Django backend.
- **UI Redesign**: Implemented a "Medical/FinTech" style 3-column workstation layout using Tailwind CSS.
- **Ajax Integration**: Converted the main form execution to use `fetch` for a non-blocking UI experience.

## Current Task: Debug Console (Completed)
The user requested a real-time Debug Console in the UI.

**Implementation 
**Decisions:**
1.  **Log Capture**: We will configure Django's `LOGGING` to write to a file `system.log`.
2.  **Concurrency**: Since the `convert` view is synchronous and blocking, we rely on Django's `runserver` threading to allow a secondary `/api/logs/` endpoint to be polled while the main conversion runs.
3.  **UI**: A floating, draggable (or fixed absolute) window toggled by a Terminal icon button.
4.  **Ingestion Strategy**: Switched `core/ingestion.py` to prioritize **Firecrawl** for web URLs (`http*`) and reserve **LlamaParse** for local files (`.pdf`), as LlamaParse failed to handle direct web URLs without a loader.
5.  **LLM URL Fix (Feb 6)**: Fixed `generate_structured` in `engine.py`. The code was appending `/v1` to Ollama base URL, causing LiteLLM to hit a malformed endpoint (`/v1/api/generate`). Removed the `/v1` suffix as LiteLLM handles Ollama natively.
6.  **Instructor JSON Mode (Feb 6)**: Switched Instructor to use `mode=instructor.Mode.JSON` for Ollama compatibility, as Tool Calling mode was causing parsing errors.

## Phase 9: UI Configuration Refinement (Feb 6)
Enhanced the configuration panel with user-requested improvements:

### 1. File Upload Dropzone
- Added drag-and-drop area for PDF/TXT file uploads
- Backend now handles file uploads with priority: File > URL > Test mode
- Temp file handling with cleanup

### 2. Vision Strategy Options
- Changed from static mock to functional toggle with 4 options:
  - **AI Gen**: Generate new images with AI
  - **Hybrid**: Use original images + AI enhancements
  - **Original**: Keep original images only
  - **Text Only**: No images, text content only
- Value passed to workflow state for future vision pipeline integration

### 3. Teaching Persona Expansion
- Added 5 persona options with appropriate prompts:
  - 🎒 5th Grader (Simple & Fun)
  - 📚 High School Student
  - 🎓 Undergraduate
  - 💼 Professional/Expert
  - 📊 Executive Summary
- Each has a tailored prompt in `agents/prompts.py`

### 4. Settings Modal (NEW)
- Settings button added to Column 1 footer (gear icon)
- Opens modal with configuration for:
  - **LLM Provider**: Local (Ollama), OpenAI, Anthropic
  - **Ollama Model**: Text input (default: llama3.1:8b)
  - **API Key**: For cloud providers
  - **Image Provider**: ComfyUI, DALL-E, Disabled
  - **ComfyUI URL**: For local image generation
  - **RAG Folder**: Default `./document/`
  - **Output Folder**: Default `./document/convertit_output/`
- Settings persisted to localStorage and .env file
- Backend API endpoint `/api/settings/` for persistence

### 5. Debug Console Restored
- Terminal icon button restored in Column 2 header
- Floating draggable console with live log polling

**Files Modified:**
- `web_ui/templates/converter/index.html` - Settings modal, debug console, UI components
- `static/js/app.js` - Event handlers for dropzone, toggle, settings modal
- `converter/views.py` - File upload handling, settings API endpoint
- `converter/urls.py` - Added settings route, fixed duplicate patterns
- `agents/prompts.py` - New persona prompts
- `agents/workflow.py` - Prompt selection logic

## Phase 10: RAG Document Indexing (Feb 6)
Implemented knowledge base indexing to improve converter output quality.

### How It Works
1. Place PDF, TXT, or MD files in the RAG database folder
2. Click "Index Now" in Settings to scan and index documents
3. Indexed content is chunked and stored in ChromaDB vector store
4. During conversion, relevant chunks are retrieved and injected into prompts

### Components Added
- **`core/indexer.py`**: Document indexer service with:
  - File scanning and hash-based change detection
  - Text chunking with overlap for better retrieval
  - PDF/TXT/MD support
  - Singleton pattern for efficient reuse

### UI Changes
- "Index Now" button in Settings modal
- Updated default folders:
  - RAG Database: `./document/convertit/database`
  - Output: `./document/convertit/output`
- Status feedback showing indexed/skipped/failed counts

### API Endpoints
- `POST /api/index/` - Trigger document indexing

### Workflow Integration
- `node_rewrite` in `workflow.py` now queries RAG knowledge base
- Up to 3 relevant chunks injected as "Relevant Background Knowledge"

## Phase 11: LLM Pipeline Optimization (Feb 6)
Optimized the LLM pipeline for better accuracy and reduced remote API costs.

### Semantic Chunking (Accuracy)
- **Lower threshold**: 15K → 6K chars for more thorough processing
- **Heading-aware splitting**: Preserves document structure
- **Context carryover**: Passes summary between chunks for coherence

### Hybrid LLM Strategy (Cost Reduction)
- **Task-based routing**: Simple tasks (clean, glossary) use local LLM
- **Quality-critical tasks**: (rewrite, critic) use remote LLM when configured
- **Auto-detection**: Checks if Ollama is available before routing

### Files Modified
- `core/engine.py` - Added `get_model_for_task()` method
- `agents/workflow.py` - Improved chunking, added task_type to all LLM calls
