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
        
        # Initialize instructor client wrapping LiteLLM
        # Use JSON mode for Ollama compatibility (tool calling doesn't work well)
        if self.provider == "local":
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
        
        # For local Ollama, pass api_base (LiteLLM handles Ollama natively, no /v1 needed)
        if self.provider == "local":
            call_kwargs["api_base"] = self.ollama_base_url
        else:
            call_kwargs["api_key"] = self.remote_api_key

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
