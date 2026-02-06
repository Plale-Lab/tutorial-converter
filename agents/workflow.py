from typing import TypedDict, Optional
import json
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from core.engine import LLMEngine
from core.vision import VisionClient
from database.vector_store import VectorDB
from agents.prompts import (
    CLEAN_PROMPT, 
    REWRITE_KIDS_PROMPT, 
    REWRITE_HIGHSCHOOL_PROMPT,
    REWRITE_UNDERGRAD_PROMPT,
    REWRITE_PRO_PROMPT, 
    REWRITE_EXECUTIVE_PROMPT,
    CRITIC_PROMPT, 
    GLOSSARY_EXTRACT_PROMPT
)
import re
import os

class AgentState(TypedDict):
    raw_content: str
    cleaned_content: Optional[str]
    rewritten_content: Optional[str]
    style: str # "kids", "highschool", "undergrad", "pro", "executive"
    vision_strategy: Optional[str]  # "ai_gen", "hybrid", "original", "text_only"
    custom_prompt: Optional[str]  # User's additional instructions
    output_options: Optional[list]  # List of enabled output options
    critique_feedback: Optional[str]
    iteration_count: int
    glossary_terms: Optional[list]

class CriticResponse(BaseModel):
    approved: bool
    feedback: str

class GlossaryResponse(BaseModel):
    terms: list[dict]

# Nodes
def node_clean(state: AgentState):
    print("--- Node: Cleaning Content ---")
    engine = LLMEngine()
    result = engine.generate_text(
        prompt=f"Clean this content:\n\n{state['raw_content']}",
        system_prompt=CLEAN_PROMPT,
        task_type="clean"  # Uses local LLM to save costs
    )
    return {"cleaned_content": result, "iteration_count": 0}

def node_glossary(state: AgentState):
    print("--- Node: Glossary Extraction ---")
    engine = LLMEngine()
    try:
        response = engine.generate_structured(
            prompt=f"Extract terms from:\n {state['cleaned_content'][:4000]}", # Truncate for safety
            response_model=GlossaryResponse,
            system_prompt=GLOSSARY_EXTRACT_PROMPT,
            task_type="glossary"  # Uses local LLM to save costs
        )
        
        # Store in VectorDB
        db = VectorDB()
        terms = [item.get('term') for item in response.terms]
        definitions = [item.get('definition') for item in response.terms]
        metadatas = [{"type": "glossary", "definition":defn} for defn in definitions]
        ids = [f"term_{i}" for i in range(len(terms))]
        
        if terms:
            db.add_documents(documents=terms, metadatas=metadatas, ids=ids)
            
        return {"glossary_terms": response.terms}
    except Exception as e:
        print(f"Glossary Error: {e}")
        return {"glossary_terms": []}

def node_rewrite(state: AgentState):
    print(f"--- Node: Rewriting ({state['style']}) ---")
    engine = LLMEngine()
    
    # RAG Retrieval: Get relevant terms for the content
    glossary_context = ""
    if state.get("glossary_terms"):
        glossary_context = "\nKey Terms:\n" + "\n".join([f"- {t.get('term')}: {t.get('definition')}" for t in state["glossary_terms"]])
    
    # Query RAG Knowledge Base for additional context
    rag_context = ""
    try:
        from core.indexer import get_indexer
        indexer = get_indexer()
        
        # Use first 500 chars of content as query
        query_text = state['cleaned_content'][:500] if state.get('cleaned_content') else ""
        if query_text:
            rag_results = indexer.query_knowledge(query_text, n_results=3)
            if rag_results:
                rag_context = "\n\nRelevant Background Knowledge:\n"
                for i, result in enumerate(rag_results):
                    content = result.get('content', '')[:500]  # Limit each result
                    rag_context += f"[{i+1}] {content}...\n\n"
                print(f"--- RAG Context: {len(rag_results)} relevant chunks found ---")
    except Exception as e:
        print(f"RAG query failed (non-critical): {e}")
    
    # Select appropriate prompt based on style
    style_prompts = {
        "kids": REWRITE_KIDS_PROMPT,
        "highschool": REWRITE_HIGHSCHOOL_PROMPT,
        "undergrad": REWRITE_UNDERGRAD_PROMPT,
        "pro": REWRITE_PRO_PROMPT,
        "executive": REWRITE_EXECUTIVE_PROMPT,
    }
    prompt_template = style_prompts.get(state['style'], REWRITE_PRO_PROMPT)
    formatted_prompt = prompt_template.format(content=state['cleaned_content'])
    
    if glossary_context:
        formatted_prompt += f"\n\n{glossary_context}"
    
    if rag_context:
        formatted_prompt += f"\n\n{rag_context}"
    
    # If user provided custom instructions, add them
    if state.get('custom_prompt'):
        formatted_prompt += f"\n\n**Additional User Instructions:**\n{state['custom_prompt']}"
        print(f"--- Custom instructions added: {len(state['custom_prompt'])} chars ---")
    
    # Add output options instructions based on enabled toggles
    output_options = state.get('output_options', [])
    if output_options:
        options_instructions = "\n\n**Required Output Sections:**"
        
        # Define option-to-instruction mapping (maintainable registry)
        OPTION_INSTRUCTIONS = {
            "code_examples": "\n- Include practical code examples where applicable. Use proper syntax highlighting.",
            "summary_table": "\n- Add a summary table at the end with key concepts and their descriptions.",
            "key_takeaways": "\n- Include a 'Key Takeaways' section at the end with 3-5 bullet points highlighting the most important concepts.",
            "glossary": "\n- Add a 'Glossary' section at the end defining all technical terms used in the document.",
        }
        
        for option in output_options:
            if option in OPTION_INSTRUCTIONS:
                options_instructions += OPTION_INSTRUCTIONS[option]
        
        formatted_prompt += options_instructions
        print(f"--- Output options enabled: {output_options} ---")
    
    # If there's feedback, append it
    if state.get('critique_feedback'):
        formatted_prompt += f"\n\nAddress this feedback: {state['critique_feedback']}"

    # Map-Reduce for long content (> 6000 chars - lower threshold for better quality)
    content_len = len(state['cleaned_content'])
    CHUNK_THRESHOLD = 6000  # ~1500 tokens, allows thorough processing
    CHUNK_SIZE = 3000  # Target size per chunk
    
    if content_len > CHUNK_THRESHOLD:
        print(f"--- Long Content detected ({content_len} chars). Using Semantic Chunking. ---")
        
        # Semantic chunking: Split by headings first, then paragraphs
        content = state['cleaned_content']
        
        # Try to split by markdown headings (## or ###) for better structure preservation
        heading_pattern = r'\n(?=#{1,3}\s)'
        sections = re.split(heading_pattern, content)
        
        # If no headings found, fall back to paragraph splitting
        if len(sections) <= 1:
            sections = content.split("\n\n")
        
        # Group sections into chunks respecting size limits
        grouped_chunks = []
        current_chunk = ""
        current_heading = ""  # Track section context
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # Detect if this is a heading
            if section.startswith('#'):
                lines = section.split('\n', 1)
                current_heading = lines[0] if lines else ""
                section_content = lines[1] if len(lines) > 1 else ""
            else:
                section_content = section
            
            # Check if adding this section exceeds chunk size
            if len(current_chunk) + len(section) < CHUNK_SIZE:
                current_chunk += "\n\n" + section
            else:
                if current_chunk.strip():
                    grouped_chunks.append(current_chunk.strip())
                # Start new chunk with heading context
                current_chunk = section
        
        if current_chunk.strip():
            grouped_chunks.append(current_chunk.strip())
        
        print(f"--- Split into {len(grouped_chunks)} semantic chunks ---")
        
        # Process each chunk with context carryover
        rewritten_parts = []
        previous_summary = ""
        
        for i, section in enumerate(grouped_chunks):
            print(f"Processing chunk {i+1}/{len(grouped_chunks)} ({len(section)} chars)")
            
            # Build chunk-specific prompt with full context
            chunk_prompt = prompt_template.format(content=section)
            
            # Add context carryover from previous chunk
            if previous_summary and i > 0:
                chunk_prompt += f"\n\n**Context from previous section:**\n{previous_summary}"
            
            # Add all additional context
            if glossary_context:
                chunk_prompt += f"\n\n{glossary_context}"
            if rag_context:
                chunk_prompt += f"\n\n{rag_context}"
            if state.get('custom_prompt'):
                chunk_prompt += f"\n\n**Additional Instructions:**\n{state['custom_prompt']}"
            if output_options:
                # Only add output options to last chunk
                if i == len(grouped_chunks) - 1:
                    chunk_prompt += options_instructions
            
            part_result = engine.generate_text(
                prompt=chunk_prompt,
                system_prompt="You are a helpful writer maintaining consistency across document sections.",
                task_type="rewrite"  # Quality-critical: uses remote if available
            )
            rewritten_parts.append(part_result)
            
            # Generate brief summary for context carryover (last 200 chars as simple approach)
            previous_summary = part_result[-300:] if len(part_result) > 300 else part_result
        
        result = "\n\n---\n\n".join(rewritten_parts)  # Clear section breaks
        
    else: 
        # Standard Single Pass for shorter content
        result = engine.generate_text(
            prompt=formatted_prompt,
            system_prompt="You are a helpful writer.",
            task_type="rewrite"  # Quality-critical: uses remote if available
        )

    return {"rewritten_content": result, "iteration_count": state["iteration_count"] + 1}

def node_critic(state: AgentState):
    print("--- Node: Critic ---")
    engine = LLMEngine()
    
    prompt = f"""
    Original Goal: Rewrite for {state['style']} style.
    
    Current Draft:
    {state['rewritten_content']}
    """
    
    response = engine.generate_structured(
        prompt=prompt,
        response_model=CriticResponse,
        system_prompt=CRITIC_PROMPT,
        task_type="critic"  # Quality-critical: uses remote if available
    )
    
    return {
        "critique_feedback": response.feedback, 
        "approved": response.approved
    }

def node_generate_images(state: AgentState):
    print("--- Node: Generating Images ---")
    content = state['rewritten_content']
    vision = VisionClient()
    
    # Regex to find [[IMG_SUGGESTION: ...]]
    # Pattern: \[\[IMG_SUGGESTION:(.*?)\]\]
    matches = re.findall(r"\[\[IMG_SUGGESTION:(.*?)\]\]", content)
    
    for i, match in enumerate(matches):
        prompt = match.strip()
        print(f"Generating image for: {prompt}")
        try:
            image_bytes = vision.generate_image(prompt)
            # Save to file
            filename = f"image_{state['style']}_{i}.png"
            filepath = os.path.join("static", filename)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            # Replace tag with Markdown image link
            # We assume static is accessible relative to where markdown is rendered or app root
            content = content.replace(f"[[IMG_SUGGESTION:{match}]]", f"![{prompt}](static/{filename})")
        except Exception as e:
            print(f"Image Gen failed: {e}")
            
    return {"rewritten_content": content}

# Conditional Logic
def should_continue(state: AgentState):
    if state.get("approved"):
        return "end"
    
    if state["iteration_count"] >= 3:
        print("--- Max iterations reached ---")
        return "end"
        
    return "rewrite"

# Graph Construction
workflow = StateGraph(AgentState)

workflow.add_node("clean", node_clean)
workflow.add_node("glossary", node_glossary)
workflow.add_node("rewrite", node_rewrite)
workflow.add_node("critic", node_critic)
workflow.add_node("images", node_generate_images)

workflow.set_entry_point("clean")

workflow.add_edge("clean", "glossary")
workflow.add_edge("glossary", "rewrite")
workflow.add_edge("rewrite", "critic")

workflow.add_conditional_edges(
    "critic",
    should_continue,
    {
        "rewrite": "rewrite",
        "end": "images"
    }
)
workflow.add_edge("images", END)

app = workflow.compile()

if __name__ == "__main__":
    # Test
    initial_state = {
        "raw_content": "This is some messy raw content with ads. BUY NOW! Learn Python here.",
        "style": "kids",
        "iteration_count": 0
    }
    result = app.invoke(initial_state)
    print("Final Result:")
    print(result.get("rewritten_content"))
