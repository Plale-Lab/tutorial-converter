import os
from typing import Any, Type, TypeVar
import litellm
import instructor
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class LLMEngine:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "local")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.remote_api_key = os.getenv("OPENAI_API_KEY")
        
        # Configure LiteLLM
        if self.provider == "local":
            # For Ollama, we typically use 'ollama/model_name'
            # We assume the user creates the client with the base_url logic or LiteLLM handles it.
            # LiteLLM supports ollama as a provider.
            pass

    def get_model_name(self) -> str:
        """Returns the default model string based on provider."""
        if self.provider == "local":
            return "ollama/llama3.1:8b" # Updated to match installed model
        else:
            return "gpt-4o" # Default remote model
    
    def get_model_for_task(self, task_type: str = "default") -> tuple[str, str, str]:
        """
        Returns (model_name, api_base, api_key) based on task complexity.
        
        For remote providers: Use local for simple tasks to save costs.
        Task types: 'clean', 'glossary', 'rewrite', 'critic'
        
        Quality-critical tasks (rewrite, critic) use remote if available.
        Simple tasks (clean, glossary) prefer local to save costs.
        """
        # Define which tasks are quality-critical
        QUALITY_CRITICAL = {'rewrite', 'critic'}
        SIMPLE_TASKS = {'clean', 'glossary'}
        
        # If using local provider, always use local
        if self.provider == "local":
            return ("ollama/llama3.1:8b", self.ollama_base_url, None)
        
        # For remote provider: route simple tasks to local if available
        if task_type in SIMPLE_TASKS:
            # Try to use local for simple tasks to save API costs
            # Check if Ollama is available
            try:
                import requests
                resp = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
                if resp.status_code == 200:
                    print(f"--- Using local LLM for '{task_type}' to save API costs ---")
                    return ("ollama/llama3.1:8b", self.ollama_base_url, None)
            except:
                pass  # Ollama not available, use remote
        
        # Quality-critical tasks or fallback: use remote
        return ("gpt-4o", None, self.remote_api_key)

    def generate_text(self, prompt: str, system_prompt: str = "You are a helpful assistant.", task_type: str = "default") -> str:
        """
        Generates simple text response.
        task_type: 'clean', 'glossary', 'rewrite', 'critic' for smart model routing
        """
        model, api_base, api_key = self.get_model_for_task(task_type)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                api_base=api_base,
                api_key=api_key
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Generation Error: {e}")
            raise e

    def generate_structured(self, prompt: str, response_model: Type[T], system_prompt: str = "You are a helpful assistant.", task_type: str = "default") -> T:
        """
        Generates defined Pydantic object using instructor.
        task_type: 'clean', 'glossary', 'rewrite', 'critic' for smart model routing
        """
        model, api_base, api_key = self.get_model_for_task(task_type)
        
        # Initialize instructor client wrapping LiteLLM
        # Use JSON mode for Ollama/local compatibility (tool calling doesn't work well)
        is_local = api_base is not None  # Local if api_base is set
        if is_local:
            client = instructor.from_litellm(litellm.completion, mode=instructor.Mode.JSON)
        else:
            client = instructor.from_litellm(litellm.completion)

        # Build kwargs for the call
        call_kwargs = {
            "model": model,
            "response_model": response_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
        }
        
        # Add api_base or api_key based on routing
        if api_base:
            call_kwargs["api_base"] = api_base
        if api_key:
            call_kwargs["api_key"] = api_key

        response = client.chat.completions.create(**call_kwargs)
        
        return response

if __name__ == "__main__":
    # Test
    engine = LLMEngine()
    try:
        # print(engine.generate_text("Hello, who are you?"))
        pass
    except Exception as e:
        print(f"Error: {e}")
