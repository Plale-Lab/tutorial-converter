from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

# Import core modules
# Ensure project root is in python path
from core.ingestion import IngestionService
from agents.workflow import app as workflow_app
from core.assembly import Assembler

def index(request):
    return render(request, 'converter/index.html')


def logs(request):
    """
    API to retrieve the last 100 lines of the system log.
    """
    log_path = os.path.join(settings.BASE_DIR, 'system.log')
    if not os.path.exists(log_path):
        return JsonResponse({'logs': []})
    
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
            # Return last 100 lines
            last_lines = lines[-100:] if len(lines) > 100 else lines
            return JsonResponse({'logs': last_lines})
    except Exception as e:
        return JsonResponse({'logs': [f"Error reading log: {str(e)}"]})

@csrf_exempt
def convert(request):
    if request.method == 'POST':
        url = request.POST.get('url', '').strip()
        style = request.POST.get('style', 'pro')
        vision_strategy = request.POST.get('vision_strategy', 'ai_gen')
        custom_prompt = request.POST.get('custom_prompt', '').strip()
        uploaded_file = request.FILES.get('file')
        
        logger.info(f"Received conversion request - URL: {url}, Style: {style}, Vision: {vision_strategy}, Custom Prompt: {bool(custom_prompt)}, File: {uploaded_file}")
        
        # 1. Ingestion
        try:
            ingestion = IngestionService()
            
            # Priority: Uploaded file > URL > Test mode
            if uploaded_file:
                logger.info(f"Processing uploaded file: {uploaded_file.name}")
                # Save to temp and parse
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                    for chunk in uploaded_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name
                
                # Read content based on file type
                if uploaded_file.name.endswith('.txt'):
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        raw_content = f.read()
                elif uploaded_file.name.endswith('.pdf'):
                    # Use LlamaParse for PDF
                    raw_content = ingestion.parse_url(tmp_path)  # parse_url handles local files too
                else:
                    raw_content = "Unsupported file type."
                    
                # Cleanup temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
                logger.info("File ingestion complete.")
                
            elif url == "test":
                logger.info("Using TEST mode with dummy content.")
                raw_content = "This is a test tutorial about AI. It has ads. BUY NOW. AI is great."
            elif url:
                logger.info(f"Starting ingestion for {url}...")
                raw_content = ingestion.parse_url(url)
                logger.info("Ingestion complete.")
            else:
                return JsonResponse({'success': False, 'error': 'No URL or file provided.'}, status=400)
                
        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                 return JsonResponse({'success': False, 'error': str(e)}, status=500)
            return render(request, 'converter/index.html', {'error': f"Ingestion failed: {e}"})

        # 2. Workflow
        initial_state = {
            "raw_content": raw_content,
            "style": style,
            "vision_strategy": vision_strategy,
            "custom_prompt": custom_prompt,
            "iteration_count": 0,
            "glossary_terms": [],
            "cleaned_content": "",
            "rewritten_content": "",
            "critique_feedback": ""
        }
        
        # Run Graph (Sync)
        try:
            logger.info("Starting Workflow Execution...")
            final_state = workflow_app.invoke(initial_state)
            logger.info("Workflow execution finished.")
            rewritten_text = final_state.get("rewritten_content")
        except Exception as e:
             logger.error(f"Workflow failed: {e}", exc_info=True)
             if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                 return JsonResponse({'success': False, 'error': f"Workflow failed: {e}"}, status=500)
             return render(request, 'converter/index.html', {'error': f"Workflow failed: {e}"})

        # 3. Assembler
        try:
            logger.info("Starting PDF Assembly...")
            assembler = Assembler()
            html_content = assembler.render_html(rewritten_text, title="Converted Tutorial", style=style)
            
            # Save PDF to static or media? 
            # Ideally Media, but for now we output to static or a temp folder.
            # Let's use PRE-CONFIGURED 'output.pdf' in root for simplicity of existing code, 
            # but for multi-user web app, this should be unique file in media.
            
            # Generate unique filename
            import uuid
            filename = f"tutorial_{uuid.uuid4().hex[:8]}.pdf"
            output_path = os.path.join(settings.BASE_DIR, 'static', filename)
            
            logger.info(f"Generating PDF at {output_path}...")
            assembler.generate_pdf(html_content, output_path)
            logger.info("PDF Generation successful.")
            
            # Check for AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'pdf_url': f"/static/{filename}",
                    'markdown_content': rewritten_text
                })

            context = {
                'success': True,
                'pdf_url': f"/static/{filename}",
                'markdown_content': rewritten_text
            }
            return render(request, 'converter/result.html', context)
            
        except Exception as e:
            logger.error(f"Assembly failed: {e}", exc_info=True)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                 return JsonResponse({'success': False, 'error': str(e)}, status=500)
            return render(request, 'converter/index.html', {'error': f"Assembly failed: {e}"})

    return index(request)

@csrf_exempt
def save_settings(request):
    """
    API to save settings from the frontend Settings modal.
    Persists to .env file and updates runtime environment.
    """
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            
            # Update environment variables at runtime
            env_mapping = {
                'llm_provider': 'LLM_PROVIDER',
                'ollama_model': 'OLLAMA_MODEL',
                'api_key': 'OPENAI_API_KEY',
                'image_provider': 'IMAGE_PROVIDER',
                'comfyui_url': 'COMFYUI_BASE_URL',
                'rag_folder': 'RAG_FOLDER',
                'output_folder': 'OUTPUT_FOLDER'
            }
            
            for key, env_key in env_mapping.items():
                if key in data and data[key]:
                    os.environ[env_key] = str(data[key])
            
            # Optionally persist to .env file
            env_path = os.path.join(settings.BASE_DIR, '.env')
            try:
                # Read existing .env
                existing_lines = []
                if os.path.exists(env_path):
                    with open(env_path, 'r') as f:
                        existing_lines = f.readlines()
                
                # Update or add new values
                updated_keys = set()
                new_lines = []
                for line in existing_lines:
                    key_match = line.split('=')[0].strip() if '=' in line else None
                    if key_match in env_mapping.values():
                        # Find the corresponding data key
                        for dk, ek in env_mapping.items():
                            if ek == key_match and dk in data and data[dk]:
                                new_lines.append(f"{ek}={data[dk]}\n")
                                updated_keys.add(ek)
                                break
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                # Add any new keys not in existing file
                for dk, ek in env_mapping.items():
                    if ek not in updated_keys and dk in data and data[dk]:
                        new_lines.append(f"{ek}={data[dk]}\n")
                
                with open(env_path, 'w') as f:
                    f.writelines(new_lines)
                    
                logger.info(f"Settings saved: {list(data.keys())}")
                
            except Exception as e:
                logger.warning(f"Could not persist settings to .env: {e}")
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

@csrf_exempt
def index_documents(request):
    """
    API to trigger document indexing for the RAG knowledge base.
    """
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body) if request.body else {}
            rag_folder = data.get('rag_folder', os.getenv('RAG_FOLDER', './document/convertit/database'))
            
            # Update environment variable
            os.environ['RAG_FOLDER'] = rag_folder
            
            # Import and run indexer
            from core.indexer import DocumentIndexer
            indexer = DocumentIndexer(rag_folder=rag_folder)
            stats = indexer.index_folder()
            
            logger.info(f"Document indexing complete: {stats}")
            return JsonResponse({
                'success': True,
                'indexed': stats.get('indexed', 0),
                'skipped': stats.get('skipped', 0),
                'failed': stats.get('failed', 0)
            })
            
        except Exception as e:
            logger.error(f"Indexing failed: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
