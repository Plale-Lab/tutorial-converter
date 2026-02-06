import chainlit as cl
import os
import shutil
from agents.workflow import app as workflow_app
from core.ingestion import IngestionService
from core.assembly import Assembler

@cl.on_chat_start
async def start():
    # Settings
    res = await cl.AskUserMessage(content="Welcome to converter! Enter a URL (or type 'test' for demo):", timeout=60).send()
    if not res:
        await cl.Message(content="Timed out.").send()
        return
        
    url = res['output']
    
    # Style Selection
    actions = [
        cl.Action(name="kids", value="kids", label="5th Grader Style"),
        cl.Action(name="pro", value="pro", label="Professional Style")
    ]
    res_style = await cl.AskActionMessage(content="Choose a style:", actions=actions).send()
    style = res_style.get('value')
    
    await process_request(url, style)

async def process_request(url: str, style: str):
    msg = cl.Message(content=f"Processing {url} in '{style}' style...")
    await msg.send()
    
    # 1. Ingestion
    ingestion = IngestionService()
    try:
        if url == "test":
            raw_content = "This is a test tutorial about AI. It has ads. BUY NOW. AI is great."
        else:
            await cl.Message(content="Ingesting content...").send()
            raw_content = ingestion.parse_url(url)
    except Exception as e:
        await cl.Message(content=f"Ingestion failed: {e}").send()
        return

    # 2. Workflow
    await cl.Message(content="Running AI Workflow (Cleaning -> Glossary -> Rewrite -> Vision)...").send()
    
    initial_state = {
        "raw_content": raw_content,
        "style": style,
        "iteration_count": 0,
        "glossary_terms": [],
        "cleaned_content": "",
        "rewritten_content": "",
        "critique_feedback": ""
    }
    
    # Run the graph
    # Note: app.invoke is synchronous. For async chainlit, ideally we run in executor or use async nodes.
    # We'll run sync for now as per LangGraph basic usage.
    final_state = workflow_app.invoke(initial_state)
    
    rewritten_text = final_state.get("rewritten_content")
    
    # 3. Assembly
    await cl.Message(content="Assembling PDF...").send()
    assembler = Assembler()
    html_content = assembler.render_html(rewritten_text, title="Converted Tutorial", style=style)
    
    output_pdf = "output.pdf"
    assembler.generate_pdf(html_content, output_pdf)
    
    # 4. Delivery
    elements = [
        cl.File(name="tutorial.pdf", path=output_pdf, display="inline"),
        cl.Text(name="Markdown", content=rewritten_text, display="inline")
    ]
    
    await cl.Message(content="Conversion Complete! Here is your tutorial:", elements=elements).send()

@cl.on_message
async def main(message: cl.Message):
    # Allow user to start over or process new URL
    url = message.content
    # default style
    await process_request(url, "pro")
