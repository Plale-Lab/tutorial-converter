# ConvertIt

**Full-Stack AI Tutorial Converter**

ConvertIt is a modular, micro-service based AI application designed to transform raw tutorial content (URLs, PDFs) into tailored educational materials for specific audiences (e.g., "5th Grader" or "Professional"). It leverages local LLMs, RAG for context management, and generative AI for illustrations.

## 🏗 System Architecture

The project follows a modular architecture as outlined in the development plan:

-   **Frontend**: [Chainlit](https://github.com/Chainlit/chainlit) for a chat-like, interactive UI.
-   **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph) for managing the rewrite workflow (Clean -> Glossary -> Rewrite -> Critic).
-   **Engine**: [LiteLLM](https://github.com/BerriAI/litellm) / [Ollama](https://ollama.com/) for LLM inference (supports both Local and Remote models).
-   **Data / RAG**: [LlamaIndex](https://www.llamaindex.ai/) & [ChromaDB](https://www.trychroma.com/) for parsing and vector storage.
-   **Vision**: [ComfyUI](https://github.com/comfyanonymous/ComfyUI) (or Remote API) for generating custom illustrations.
-   **Assembly**: [Jinja2](https://jinja.palletsprojects.com/) & [WeasyPrint](https://weasyprint.org/) for HTML/PDF rendering.

## 🚀 Features

-   **Dual-Mode Inference**: Run entirely local (Ollama/ComfyUI) or use powerful remote APIs (OpenAI/Stability).
-   **Style Transfer**: Convert technical docs into kid-friendly analogies or polished professional guides.
-   **Glossary Extraction**: Automatically builds a glossary of terms for the specific content using RAG.
-   **Smart Chunking**: Handles long documents using a Map-Reduce strategy.
-   **AI Illustrations**: Generates relevant images where the text needs visual aid.

## 🛠 Prerequisites

-   **Python 3.10+**
-   **Docker** (for ChromaDB)
-   **Ollama** (if running local LLM)
-   **Git**

## 📦 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/williamQ96/convertit.git
    cd convertit
    ```

2.  **Create and Activate Virtual Environment**:
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\Activate.ps1
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install litellm ollama chromadb langgraph langchain pydantic instructor jinja2 weasyprint chainlit python-dotenv requests llama-index llama-parse
    ```
    *Note: WeasyPrint on Windows may require installing GTK3 runtime separately.*

4.  **Configuration**:
    Copy the example environment file and configure your keys:
    ```bash
    cp .env.example .env 
    # (Or manually create .env based on the template below)
    ```
    
    Update `.env`:
    ```ini
    LLM_PROVIDER=local # or 'remote'
    OLLAMA_BASE_URL=http://localhost:11434
    
    # If using Remote:
    OPENAI_API_KEY=sk-...
    STABILITY_API_KEY=...
    
    # Docker Services
    CHROMA_DB_PATH=./chroma_db
    ```

## 🏃 Usage

1.  **Start Background Services**:
    If using ChromaDB via Docker (Recommended for persistence):
    ```bash
    docker-compose up -d
    ```

2.  **Run the Application**:
    ```bash
    chainlit run app.py -w
    ```

3.  **Interact**:
    -   Open `http://localhost:8000`
    -   Enter a URL to convert.
    -   Select your target audience style.
    -   Download your generated PDF!

## 📂 Project Structure

-   `app.py`: Main Chainlit application entry point.
-   `core/`: Core service modules (Ingestion, Engine, Vision, Assembly).
-   `agents/`: LangGraph workflow and prompt definitions.
-   `database/`: Vector store interactions.
-   `templates/`: HTML/CSS templates for PDF generation.
-   `static/`: Generated images storage.

## 📄 License

[MIT](LICENSE)