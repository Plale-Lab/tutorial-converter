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
            return "ollama/llama3" # Default local model, can be configured
        else:
            return "gpt-4o" # Default remote model

    def generate_text(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        """
        Generates simple text response.
        """
        model = self.get_model_name()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                api_base=self.ollama_base_url if self.provider == "local" else None,
                api_key=self.remote_api_key if self.provider == "remote" else None
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Generation Error: {e}")
            raise e

    def generate_structured(self, prompt: str, response_model: Type[T], system_prompt: str = "You are a helpful assistant.") -> T:
        """
        Generates defined Pydantic object using instructor.
        """
        model = self.get_model_name()
        
        # Create client for Instructor
        # Note: Instructor typically wraps an OpenAI client. 
        # For LiteLLM, we can use instructor.from_litellm or similar if available, 
        # or patch the client.
        
        # For simplicity in this plan, we will use the patch logic or LiteLLM's `acompletion` 
        # compatible client if supported by recent instructor versions.
        # Alternatively, Instructor works best with OpenAI-like API. 
        # Ollama provides an OpenAI compatible endpoint at /v1.
        
        if self.provider == "local":
             base_url = f"{self.ollama_base_url}/v1"
             api_key = "ollama" # required but unused
        else:
             base_url = None # Default OpenAI
             api_key = self.remote_api_key

        # Initialize instructor client
        client = instructor.from_litellm(litellm.completion)

        response = client.chat.completions.create(
            model=model,
            response_model=response_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            api_base=base_url if self.provider == "local" else None, # instructor might need specific handling for base_url passing
            # Depending on instructor version, passing api_base might be via kwargs or client init.
            # safe fallback:
        )
        
        return response

if __name__ == "__main__":
    # Test
    engine = LLMEngine()
    try:
        # print(engine.generate_text("Hello, who are you?"))
        pass
    except Exception as e:
        print(f"Error: {e}")
