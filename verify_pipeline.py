import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from agents.workflow import app as workflow_app
from core.assembly import Assembler

def test_pipeline():
    print("Starting Pipeline Test...")
    
    # Mock Data
    raw_content = """
    # Understanding AI
    AI is like a robot brain. It learns from data.
    [[IMG_SUGGESTION: A robot reading a book]]
    It helps us everywhere.
    """
    
    initial_state = {
        "raw_content": raw_content,
        "style": "kids",
        "iteration_count": 0,
        "glossary_terms": [],
        "cleaned_content": "",
        "rewritten_content": "",
        "critique_feedback": ""
    }
    
    print("Running Workflow...")
    final_state = workflow_app.invoke(initial_state)
    content = final_state.get("rewritten_content")
    
    print("Workflow Output:")
    print(content[:200] + "...")
    
    print("Assembling PDF...")
    assembler = Assembler()
    html = assembler.render_html(content, "Test Doc", "kids")
    
    output = "test_output.pdf"
    assembler.generate_pdf(html, output)
    
    if os.path.exists(output):
        print(f"SUCCESS: PDF generated at {output}")
        # Clean up
        # os.remove(output)
    else:
        print("FAILURE: PDF not found")

if __name__ == "__main__":
    test_pipeline()
