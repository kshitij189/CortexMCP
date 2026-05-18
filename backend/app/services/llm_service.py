import os
from typing import Optional
from groq import Groq
import google.generativeai as genai

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()

class LLMService:
    def __init__(self):
        # Determine provider
        self.provider = LLM_PROVIDER
        if self.provider == "auto":
            if GEMINI_API_KEY:
                self.provider = "gemini"
            elif GROQ_API_KEY:
                self.provider = "groq"
            else:
                self.provider = "mock"
                
        # Initialize Groq client
        self.groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        # Initialize Gemini settings
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            
    def generate_summary(self, system_prompt: str, context: str) -> Optional[str]:
        """
        Sends the system prompt and context to the LLM and returns the Markdown output.
        Handles automatic fallbacks for maximum resilience.
        """
        if self.provider == "gemini" and GEMINI_API_KEY:
            # List of Gemini models to try in sequence of preference
            gemini_models_to_try = [
                self.gemini_model,
                "gemini-2.0-flash",
                "gemini-flash-latest",
                "gemini-2.5-flash-lite",
            ]
            # De-duplicate while preserving order
            seen = set()
            models_to_try = [m for m in gemini_models_to_try if not (m in seen or seen.add(m))]
            
            last_error = None
            for model_name in models_to_try:
                try:
                    print(f"Generating summary using Gemini model: {model_name}")
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_prompt
                    )
                    response = model.generate_content(
                        f"Here is the context to synthesize:\n\n{context}",
                        generation_config={"temperature": 0.3}
                    )
                    return response.text
                except Exception as e:
                    print(f"Gemini model {model_name} failed: {e}")
                    last_error = e
                    continue
            
            # If all Gemini models failed, fall back to Groq
            print(f"All Gemini models failed. Falling back to Groq if available. Last error: {last_error}")
            if self.groq_client:
                return self._generate_groq(system_prompt, context)
            return f"Error during Gemini generation: {str(last_error)}"
                
        elif self.provider == "groq" and self.groq_client:
            try:
                return self._generate_groq(system_prompt, context)
            except Exception as e:
                print(f"Groq generation failed: {e}. Falling back to Gemini if available.")
                if GEMINI_API_KEY:
                    # Switch to gemini for fallback
                    self.provider = "gemini"
                    return self.generate_summary(system_prompt, context)
                return f"Error during Groq generation: {str(e)}"
                
        else:
            print("Warning: No active LLM provider configured. Returning mock summary.")
            return self._mock_summary(context)
            
    def _generate_groq(self, system_prompt: str, context: str) -> Optional[str]:
        if not self.groq_client:
            raise ValueError("Groq client not initialized")
        response = self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the context to synthesize:\n\n{context}"}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content
            
    def _mock_summary(self, context: str) -> str:
        """Mock output for testing when no API key is available."""
        return "# Research Summary\n\nThis is a mock summary generated because no LLM provider is configured.\n\n## Findings\n- Point 1\n- Point 2"

llm_service = LLMService()
