# ConvertIt

**AI-Powered Document Simplification Engine**

ConvertIt transforms complex technical documents (URLs, PDFs, text files) into easy-to-understand educational materials tailored for specific audiences. It uses local or remote LLMs, RAG for context management, and AI-powered image generation.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Source Input** | URLs, PDF files, TXT files via drag-and-drop |
| **5 Teaching Personas** | 5th Grader, High School, Undergrad, Professional, Executive |
| **RAG Knowledge Base** | Index reference documents to enhance output quality |
| **Hybrid LLM Routing** | Local LLM for simple tasks, remote for quality-critical |
| **Semantic Chunking** | Heading-aware splitting with context carryover |
| **AI Illustrations** | Generate relevant images via ComfyUI or DALL-E |
| **Real-time Logs** | Live debug console for monitoring |

## 🏗 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Django    │────▶│  LangGraph   │────▶│   Output    │
│   Web UI    │     │  Workflow    │     │  (MD/PDF)   │
└─────────────┘     └──────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌──────────────┐
│   Settings  │     │  LLM Engine  │
│   & Config  │     │ (Local/API)  │
└─────────────┘     └──────────────┘
```

**Tech Stack:**
- **Backend**: Django + LangGraph workflow
- **LLM**: LiteLLM + Ollama (local) or OpenAI/Anthropic (remote)
- **RAG**: ChromaDB + LlamaIndex
- **Frontend**: Tailwind CSS + Lucide Icons
- **Vision**: ComfyUI / DALL-E

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Ollama (for local LLM)
- Git

### Installation

```bash
# Clone
git clone https://github.com/williamQ96/convertit.git
cd convertit

# Virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Or manual install:
pip install django litellm ollama chromadb langgraph instructor jinja2 pymupdf python-dotenv requests llama-index llama-parse
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env`:
```ini
LLM_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=sk-...          # For remote LLM
CHROMA_DB_PATH=./chroma_db
RAG_FOLDER=./document/convertit/database
```

### Run

```bash
# Start Ollama (if using local)
ollama serve

# Run Django server
python manage.py runserver
```

Open `http://localhost:8000`

## 📁 Project Structure

```
convertit/
├── agents/            # LangGraph workflow & prompts
│   ├── workflow.py    # Clean → Glossary → Rewrite → Critic → Images
│   └── prompts.py     # Persona-specific prompts
├── core/              # Core services
│   ├── engine.py      # LLM engine with task-based routing
│   ├── ingestion.py   # URL/PDF parsing (Firecrawl + PyMuPDF)
│   ├── indexer.py     # RAG document indexer
│   └── vision.py      # Image generation
├── converter/         # Django app
│   ├── views.py       # API endpoints
│   └── urls.py        # Route configuration
├── database/          # ChromaDB vector store
├── web_ui/            # Django project settings
├── templates/         # HTML templates
└── static/            # CSS, JS, generated images
```

## 🔧 Configuration Options

### Teaching Personas
| Persona | Description |
|---------|-------------|
| 🎒 5th Grader | Simple language, fun analogies |
| 📚 High School | Clear explanations with terminology |
| 🎓 Undergraduate | Academic rigor, proper context |
| 💼 Professional | Polished technical writing |
| 📊 Executive | TL;DR with key takeaways |

### Output Options (Toggleable)
- 📝 Include code examples
- 📊 Add summary table
- 💡 Highlight key takeaways
- 📖 Include glossary section

### Vision Strategy
- **AI Gen**: Generate new images with AI
- **Hybrid**: Original + AI enhancements
- **Original**: Keep original images
- **Text Only**: No images

## 🧠 LLM Pipeline

```
Raw Content → Clean → Glossary → Rewrite → Critic → [Loop] → Images → Output
```

**Optimizations:**
- **Semantic Chunking**: 6K char threshold, heading-aware splitting
- **Context Carryover**: Summary passed between chunks
- **Hybrid Routing**: Local LLM for `clean`/`glossary`, remote for `rewrite`/`critic`

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/convert/` | POST | Start conversion |
| `/api/settings/` | POST | Save settings |
| `/api/index/` | POST | Index RAG documents |
| `/logs/` | GET | Stream logs |

## 📝 Development Log

See [development_log.md](development_log.md) for detailed progress tracking.

**Recent Updates (Feb 2026):**
- Phase 11: LLM Pipeline Optimization
- Phase 10: RAG Document Indexing
- Phase 9: UI Configuration Refinement
- Django migration from Chainlit

## 📄 License

[MIT](LICENSE)