from dataclasses import dataclass
import os
import time
from typing import Any, Callable, Optional

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from PIL import Image
import requests


@dataclass
class Result:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class AIClient:
    def __init__(self):
        self.api_key: Optional[str] = None
        self.model = None
        self.vision_model = None
        self.request_timeout = 30
        self.max_retries = 3
        self.backoff_factor = 2

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        return bool(api_key and len(api_key.strip()) >= 30)

    def configure(self, api_key: str) -> Result:
        if not self.validate_api_key(api_key):
            return Result(False, error="API-Schlüssel ungültig oder unvollständig.")

        self.api_key = api_key.strip()
        genai.configure(
            api_key=self.api_key, client_options={"timeout": self.request_timeout}
        )

        # Use latest stable model
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.vision_model = genai.GenerativeModel("gemini-2.5-flash")

        return Result(True, data="Konfiguration erfolgreich")

    def test_connection(self):
        """Test if the API key works"""
        if not self.model:
            return Result(False, error="API-Schlüssel nicht konfiguriert.")

        return self._call_with_retries(
            lambda: self.model.generate_content(
                "Say 'API connected' in one word.",
                request_options={"timeout": self.request_timeout},
            ).text,
            "Verbindungstest fehlgeschlagen",
        )

    def generate_text(self, prompt, system_instruction=None, temperature=0.7):
        if not self.model:
            return Result(False, error="Fehler: API-Schlüssel nicht konfiguriert.")

        generation_config = genai.types.GenerationConfig(temperature=temperature)

        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\nUser Request: {prompt}"

        return self._call_with_retries(
            lambda: self.model.generate_content(
                full_prompt,
                generation_config=generation_config,
                request_options={"timeout": self.request_timeout},
            ).text,
            "Fehler bei der Textgenerierung",
        )

    def analyze_images(self, image_paths, prompt):
        """Analyze multiple images and generate description based on prompt"""
        if not self.vision_model:
            return Result(False, error="Fehler: API-Schlüssel nicht konfiguriert.")

        def _build_and_send():
            content = [prompt]
            for path in image_paths:
                if os.path.exists(path):
                    img = Image.open(path)
                    content.append(img)

            response = self.vision_model.generate_content(
                content,
                request_options={"timeout": self.request_timeout},
            )
            return response.text

        return self._call_with_retries(_build_and_send, "Fehler bei der Bildanalyse")

    def generate_image(self, prompt, api_key):
        """Generate an image using Google Imagen 4.0"""
        if not api_key:
            return Result(False, error="Fehler: Google Image API-Schlüssel fehlt.")

        if not self.validate_api_key(api_key):
            return Result(False, error="Imagen API-Schlüssel ungültig.")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=api_key.strip(),
                client_options={"timeout": self.request_timeout},
            )

            response = self._call_with_retries(
                lambda: client.models.generate_images(
                    model="imagen-4.0-generate-001",
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="1:1",
                        safety_filter_level="block_low_and_above",
                        person_generation="allow_adult",
                    ),
                    request_options={"timeout": self.request_timeout},
                ),
                "Fehler bei Imagen 4.0 Generierung",
            )

            if not response.success:
                return response

            image_response = response.data
            if image_response and getattr(image_response, "generated_images", None):
                return Result(True, data=image_response.generated_images[0])

            return Result(False, error="Keine Bilder generiert.")

        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg and "safety" in error_msg.lower():
                return Result(
                    False,
                    error="Sicherheitsrichtlinie blockiert. (Error 400). Bitte Prompt entschärfen.",
                )
            return Result(
                False, error=f"Fehler bei Imagen 4.0 Generierung: {error_msg}"
            )

    def start_chat(self, system_instruction):
        """Start a chat session with system instruction"""
        if not self.model:
            return Result(False, error="API-Schlüssel nicht konfiguriert.")

        # Configure model with system instruction if possible
        # Gemini 1.5/2.5 supports system_instruction in constructor
        try:
            chat_model = genai.GenerativeModel(
                "gemini-2.5-flash", system_instruction=system_instruction
            )
            chat = chat_model.start_chat(history=[])
            return Result(True, data=chat)
        except Exception:
            # Fallback if system_instruction fails
            chat = self.model.start_chat(history=[])
            # Send system instruction as first message
            chat.send_message(system_instruction)
            return Result(True, data=chat)

    def _call_with_retries(
        self, operation: Callable[[], Any], error_prefix: str
    ) -> Result:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = operation()
                return Result(True, data=result)
            except (requests.Timeout, google_exceptions.DeadlineExceeded) as exc:
                last_error = f"Timeout: {exc}"
            except google_exceptions.ResourceExhausted as exc:
                last_error = (
                    "Rate Limit erreicht. Bitte kurz warten und erneut versuchen."
                )
            except google_exceptions.Unauthenticated as exc:
                last_error = "Authentifizierungsfehler: API-Schlüssel prüfen."
            except Exception as exc:  # noqa: BLE001
                last_error = f"{error_prefix}: {exc}"

            if attempt < self.max_retries - 1:
                time.sleep(self.backoff_factor**attempt)

        return Result(False, error=last_error or error_prefix)
