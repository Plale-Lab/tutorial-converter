### Design Concept: "Convertit"

**Design Philosophy:**
The goal is to transition from a "toy app" feel to a "professional workstation." The UI will adopt the **Modular Card System** seen in your reference. It uses soft shadows, rounded corners (`border-radius: 12px`), and a clean hierarchy of typography to organize complex information without clutter. The color palette will shift to a **Medical/FinTech Clean** look: white backgrounds, light gray canvas (`#F3F4F6`), and distinct Emerald Green (`#10B981`) or Teal branding accents.

---

### Layout Architecture (The 3-Column Grid)

The screen is divided into three distinct vertical zones, exactly mirroring the reference image:

#### 1. Left Column: The Control Deck (Inputs & Config)

*Purpose: Static configuration. The user sets everything up here before running.*

* **Top Card: "Target Asset" (Input)**
  * Instead of a stock ticker, we have the  **Input Source** .
  * A clean input field for URL with a toggle switch for "Upload File" (PDF/Text).
* **Middle Card: "Transformation Logic" (Parameters)**
  * **Teaching Persona:** A dropdown menu (e.g., "5th Grader", "Expert").
  * **Image Strategy:** A segment selector (pill shape) for `[Keep Original] [Hybrid] [AI Gen]`.
* **Bottom Card: "Model Configuration"**
  * Dropdowns for the LLM Engine (Ollama/OpenAI) and Vision Model.
* **Action Button:**
  * A large, full-width button at the bottom: **"Start Processing"** (styled like the green "Processing..." button in the reference).

#### 2. Center Column: The Live Pipeline (Progress Stream)

*Purpose: Real-time feedback. Instead of a simple progress bar, this is a "Activity Feed" showing the backend logic step-by-step.*

* **Header:** "Live Transformation" (mimicking "Live Intelligence").
* **The Stream (Vertical Flow):**
  * This area displays a timeline of cards that appear or update as the Python backend runs.
  * **Card 1: Ingestion Agent:** Shows "Parsing URL..." -> turns green when done. Has a small button "View Parsed Text".
  * **Card 2: Rewriting Agent:** Shows the thinking process. "Refactoring Section 1...", "Simplifying terms...".
  * **Card 3: Vision Agent:** Shows thumbnails of generated images appearing in real-time.
  * **Card 4: Assembly Agent:** The final step compiling the HTML.
* **Visual Cues:**
  * Use status indicators (spinning loaders for active, green checkmarks for done).
  * "View Generated Report" buttons (from your reference) can be used to peek at intermediate results (e.g., "View JSON Map").

#### 3. Right Column: The Result Vault (Output Display)

*Purpose: The deliverable. A static view of the final product.*

* **Header:** "Document Viewer" (mimicking "Report Viewer").
* **Main Area:**
  * A scrollable `<iframe>` or preview window rendering the final HTML.
  * It should look like a mini-browser window.
* **Verdict/Summary Card:**
  * Below the preview, a summary card (like "Risk Verdict") showing stats: "Original Word Count: 2000" -> "New Word Count: 800", "Reading Level: Grade 5".
* **Export Actions:**
  * Floating buttons or a bottom toolbar to "Download PDF" or "Open HTML".

---

### Visual Style Guide (Reference Matching)

* **Background:** `#F4F6F8` (Light Blue-Grey).
* **Cards:** Pure White `#FFFFFF` with `box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1)`.
* **Typography:** Inter or Roboto. Headings are uppercase and bold (e.g.,  **TARGET ASSET** ,  **LIVE INTELLIGENCE** ).
* **Accents:**
  * **Primary Action:** Teal/Mint Green (matching the "Processing" button).
  * **Tags/Badges:** Light green backgrounds with dark green text for active states.
