import google.generativeai as genai
from PIL import Image
import os

import requests


class AIClient:
    def __init__(self):
        self.api_key = None
        self.model = None
        self.vision_model = None

    def configure(self, api_key):
        # Clean the API key (remove whitespace)
        self.api_key = api_key.strip()
        genai.configure(api_key=self.api_key)
        # Use latest stable model
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.vision_model = genai.GenerativeModel("gemini-2.5-flash")

    def test_connection(self):
        """Test if the API key works"""
        if not self.model:
            return False, "API-Schlüssel nicht konfiguriert."

        try:
            # Simple test prompt
            response = self.model.generate_content("Say 'API connected' in one word.")
            return True, "Verbindung erfolgreich!"
        except Exception as e:
            return False, f"Verbindung fehlgeschlagen: {str(e)}"

    def generate_text(self, prompt, system_instruction=None, temperature=0.7):
        if not self.model:
            return "Fehler: API-Schlüssel nicht konfiguriert."

        try:
            # Configure generation config
            generation_config = genai.types.GenerationConfig(temperature=temperature)

            full_prompt = prompt
            if system_instruction:
                # If the model supports system_instruction in generate_content, use it,
                # otherwise prepend. Gemini 1.5 Flash supports it in constructor,
                # but we can also pass it here if we re-instantiated or just prepend.
                # For safety and compatibility with the single instance we have:
                full_prompt = f"{system_instruction}\n\nUser Request: {prompt}"

            response = self.model.generate_content(
                full_prompt, generation_config=generation_config
            )
            return response.text
        except Exception as e:
            return f"Fehler bei der Textgenerierung: {str(e)}"

    def analyze_images(self, image_paths, prompt):
        """Analyze multiple images and generate description based on prompt"""
        if not self.vision_model:
            return "Fehler: API-Schlüssel nicht konfiguriert."

        try:
            content = [prompt]
            for path in image_paths:
                if os.path.exists(path):
                    img = Image.open(path)
                    content.append(img)

            response = self.vision_model.generate_content(content)
            return response.text
        except Exception as e:
            return f"Fehler bei der Bildanalyse: {str(e)}"

    def generate_image(self, prompt, api_key):
        """Generate an image using Google Imagen 4.0"""
        if not api_key:
            return False, "Fehler: Google Image API-Schlüssel fehlt."

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            response = client.models.generate_images(
                model="imagen-4.0-generate-001",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                    safety_filter_level="block_low_and_above",
                    person_generation="allow_adult",
                ),
            )

            if response.generated_images:
                return True, response.generated_images[0]

            return False, "Keine Bilder generiert."

        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg and "safety" in error_msg.lower():
                return (
                    False,
                    "Sicherheitsrichtlinie blockiert. (Error 400). Bitte Prompt entschärfen.",
                )
            return False, f"Fehler bei Imagen 4.0 Generierung: {error_msg}"

    def start_chat(self, system_instruction):
        """Start a chat session with system instruction"""
        if not self.model:
            return None

        # Configure model with system instruction if possible
        # Gemini 1.5/2.5 supports system_instruction in constructor
        try:
            chat_model = genai.GenerativeModel(
                "gemini-2.5-flash", system_instruction=system_instruction
            )
            chat = chat_model.start_chat(history=[])
            return chat
        except Exception:
            # Fallback if system_instruction fails
            chat = self.model.start_chat(history=[])
            # Send system instruction as first message
            chat.send_message(system_instruction)
            return chat
