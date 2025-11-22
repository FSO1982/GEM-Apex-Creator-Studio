from dataclasses import dataclass, field
import os
from typing import Any

from ai.client import AIClient
from exporters.markdown_exporter import MarkdownExporter
from models.character import Character


@dataclass
class AppState:
    ai_client: AIClient
    character: Character
    exporter: MarkdownExporter
    config_file: str = "config.json"
    saved_dossiers_dir: str = "saved_dossiers"
    uploaded_images: list[str] = field(default_factory=list)
    chat_session: Any = None
    generated_image_ctk: Any = None

    def ensure_directories(self) -> None:
        os.makedirs(self.saved_dossiers_dir, exist_ok=True)
        os.makedirs(self.exporter.output_dir, exist_ok=True)
