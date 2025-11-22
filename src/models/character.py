from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Section:
    title: str
    content: str = ""
    subsections: List['Section'] = field(default_factory=list)

    def to_markdown(self, level=1) -> str:
        md = f"{'#' * level} {self.title}\n\n"
        if self.content:
            md += f"{self.content}\n\n"
        
        for sub in self.subsections:
            md += sub.to_markdown(level + 1)
        return md

@dataclass
class Character:
    name: str = "Unbenannt"
    physiology: Section = field(default_factory=lambda: Section("I. PHYSIOLOGISCHE MIKROANALYSE"))
    psychology: Section = field(default_factory=lambda: Section("II. PSYCHO-NEUROLOGISCHE TIEFENANALYSE"))
    sensory: Section = field(default_factory=lambda: Section("III. SENSORISCHE MIKROPROFILE"))
    history: Section = field(default_factory=lambda: Section("IV. ENTWICKLUNGSGESCHICHTE"))
    gem_matrix: Section = field(default_factory=lambda: Section("XI. GEM V1.3 STEUERUNGS-MATRIX"))
    
    # Storage for selected options (Dictionaries)
    physiology_options: Dict = field(default_factory=dict)
    psychology_options: Dict = field(default_factory=dict)
    sensory_options: Dict = field(default_factory=dict)
    history_options: Dict = field(default_factory=dict)
    gem_options: Dict = field(default_factory=dict)
    generated_image_path: str = None

    def get_full_markdown(self) -> str:
        md = f"# CHARAKTER-DOSSIER {self.name.upper()}\n\n"
        if self.generated_image_path:
            md += f"![Charakterbild]({self.generated_image_path})\n\n"
        md += "---\n\n"
        md += self.physiology.to_markdown(2)
        md += "---\n\n"
        md += self.psychology.to_markdown(2)
        md += "---\n\n"
        md += self.sensory.to_markdown(2)
        md += "---\n\n"
        md += self.history.to_markdown(2)
        md += "---\n\n"
        md += self.gem_matrix.to_markdown(2)
        return md

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "generated_image_path": self.generated_image_path,
            "physiology_content": self.physiology.content,
            "psychology_content": self.psychology.content,
            "sensory_content": self.sensory.content,
            "history_content": self.history.content,
            "gem_matrix_content": self.gem_matrix.content,
            "physiology_options": self.physiology_options,
            "psychology_options": self.psychology_options,
            "sensory_options": self.sensory_options,
            "history_options": self.history_options,
            "gem_options": self.gem_options
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Character':
        char = cls(name=data.get("name", "Unbenannt"))
        char.generated_image_path = data.get("generated_image_path")
        char.physiology.content = data.get("physiology_content", "")
        char.psychology.content = data.get("psychology_content", "")
        char.sensory.content = data.get("sensory_content", "")
        char.history.content = data.get("history_content", "")
        char.gem_matrix.content = data.get("gem_matrix_content", "")
        
        char.physiology_options = data.get("physiology_options", {})
        char.psychology_options = data.get("psychology_options", {})
        char.sensory_options = data.get("sensory_options", {})
        char.history_options = data.get("history_options", {})
        char.gem_options = data.get("gem_options", {})
        return char
