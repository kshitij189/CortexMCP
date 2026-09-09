import os
from typing import List, Optional

from groq import Groq
import google.generativeai as genai

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()

# Preference order, most capable first. Providers retire model ids on their own
# schedule, so these are treated as candidates rather than guarantees: whatever
# the provider actually lists at runtime wins over anything hardcoded here.
GEMINI_CANDIDATES = [
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
]
GROQ_CANDIDATES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


class LLMGenerationError(RuntimeError):
    """Raised when every configured provider and model failed to generate."""


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
        self.groq_model = os.getenv("GROQ_MODEL", "")

        # Initialize Gemini settings
        self.gemini_model = os.getenv("GEMINI_MODEL", "")
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)

    # ─── Model discovery ───
    # A hardcoded model id is a time bomb: the pipeline broke in production when
    # Groq retired llama-3.1-8b-instant and every request started 404ing. Asking
    # the provider what it currently serves keeps the fallback chain working
    # across retirements without a redeploy.

    def available_gemini_models(self) -> List[str]:
        if not GEMINI_API_KEY:
            return []
        models = []
        for model in genai.list_models():
            if "generateContent" not in getattr(model, "supported_generation_methods", []):
                continue
            # The API returns fully qualified names like "models/gemini-2.5-flash".
            models.append(model.name.split("/", 1)[-1])
        return models

    def available_groq_models(self) -> List[str]:
        if not self.groq_client:
            return []
        return [m.id for m in self.groq_client.models.list().data]

    def _resolve(self, preferred: str, candidates: List[str], available: List[str]) -> List[str]:
        """Order the models worth trying, best first, skipping retired ids."""
        wanted = ([preferred] if preferred else []) + candidates

        ordered, seen = [], set()
        for name in wanted:
            if name and name not in seen and (not available or name in available):
                ordered.append(name)
                seen.add(name)

        # Anything the provider offers that we did not name explicitly is still a
        # better outcome than failing the job outright.
        for name in available:
            if name not in seen:
                ordered.append(name)
                seen.add(name)

        return ordered

    def generate_summary(self, system_prompt: str, context: str) -> str:
        """
        Sends the system prompt and context to the LLM and returns the Markdown output.

        Tries every model of the primary provider, then the secondary provider.
        Raises LLMGenerationError only when nothing worked, so the caller can
        record a real failure instead of writing an error string into a report.
        """
        if self.provider == "mock":
            print("Warning: No active LLM provider configured. Returning mock summary.")
            return self._mock_summary(context)

        order = ["gemini", "groq"] if self.provider == "gemini" else ["groq", "gemini"]
        errors: List[str] = []

        for provider in order:
            if provider == "gemini" and GEMINI_API_KEY:
                result = self._try_gemini(system_prompt, context, errors)
            elif provider == "groq" and self.groq_client:
                result = self._try_groq(system_prompt, context, errors)
            else:
                continue

            if result is not None:
                return result

        raise LLMGenerationError(
            "Every LLM provider failed to generate a report. Attempts: "
            + " | ".join(errors)
        )

    def _try_gemini(self, system_prompt: str, context: str, errors: List[str]) -> Optional[str]:
        try:
            available = self.available_gemini_models()
        except Exception as e:
            errors.append(f"gemini:list_models {type(e).__name__}: {e}")
            available = []

        for model_name in self._resolve(self.gemini_model, GEMINI_CANDIDATES, available):
            try:
                print(f"Generating summary using Gemini model: {model_name}")
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt,
                )
                response = model.generate_content(
                    f"Here is the context to synthesize:\n\n{context}",
                    generation_config={"temperature": 0.3},
                )
                text = response.text
                if text:
                    return text
                errors.append(f"gemini:{model_name} returned empty text")
            except Exception as e:
                print(f"Gemini model {model_name} failed: {e}")
                errors.append(f"gemini:{model_name} {type(e).__name__}: {e}")

        return None

    def _try_groq(self, system_prompt: str, context: str, errors: List[str]) -> Optional[str]:
        try:
            available = self.available_groq_models()
        except Exception as e:
            errors.append(f"groq:list_models {type(e).__name__}: {e}")
            available = []

        for model_name in self._resolve(self.groq_model, GROQ_CANDIDATES, available):
            try:
                print(f"Generating summary using Groq model: {model_name}")
                text = self._generate_groq(system_prompt, context, model_name)
                if text:
                    return text
                errors.append(f"groq:{model_name} returned empty text")
            except Exception as e:
                print(f"Groq model {model_name} failed: {e}")
                errors.append(f"groq:{model_name} {type(e).__name__}: {e}")

        return None

    def _generate_groq(self, system_prompt: str, context: str, model: str) -> Optional[str]:
        if not self.groq_client:
            raise ValueError("Groq client not initialized")
        response = self.groq_client.chat.completions.create(
            model=model,
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
