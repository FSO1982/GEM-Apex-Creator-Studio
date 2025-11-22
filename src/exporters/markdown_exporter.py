import os
from models.character import Character

class MarkdownExporter:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def export(self, character: Character, filename=None):
        if not filename:
            filename = f"Rolle_{character.name.replace(' ', '_')}.md"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(character.get_full_markdown())
        
        return filepath
