import json
import os

import customtkinter as ctk
from PIL import Image
from tkinter import messagebox

from ai.client import AIClient
from exporters.markdown_exporter import MarkdownExporter
from gui.sidebar import Sidebar
from gui.state import AppState
from gui.tabs.chat import ChatTab
from gui.tabs.physiology import SectionTabs
from models.character import Character

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

THEME = {
    "bg_dark": "#1a1a1a",
    "card_bg": "#2d2d2d",
    "accent": "#7C3AED",
    "accent_hover": "#6D28D9",
    "neon_blue": "#06b6d4",
    "neon_pink": "#ec4899",
    "text_main": "#ffffff",
    "text_sub": "#a3a3a3",
    "danger": "#ef4444",
}


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GEM-Apex Creator Studio")
        self.geometry("1600x900")
        self.configure(fg_color=THEME["bg_dark"])

        self.state = AppState(
            ai_client=AIClient(),
            character=Character(),
            exporter=MarkdownExporter(output_dir=os.path.join(os.getcwd(), "output")),
        )
        self.state.ensure_directories()
        self.uploaded_images = self.state.uploaded_images

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, THEME, self.state, self.reset_character)

        self.tabview = ctk.CTkTabview(
            self,
            fg_color=THEME["bg_dark"],
            segmented_button_fg_color=THEME["card_bg"],
            segmented_button_selected_color=THEME["accent"],
        )
        self.tabview.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")

        self.tabs = [
            "Physiologie",
            "Psychologie",
            "Sensorik",
            "Historie",
            "GEM-Matrix",
            "Dossier",
            "Chat-Labor",
        ]
        for tab in self.tabs:
            self.tabview.add(tab)

        from models.options_data import CHARACTER_OPTIONS

        self.options_data = CHARACTER_OPTIONS
        self.section_tabs = SectionTabs(
            self.tabview, THEME, self.options_data, self.state
        )
        self.section_tabs.create_split_tab(
            "Physiologie", "I. Physiologische Mikroanalyse", "physiology"
        )
        self.section_tabs.create_split_tab(
            "Psychologie", "II. Psycho-Neurologische Tiefenanalyse", "psychology"
        )
        self.section_tabs.create_split_tab(
            "Sensorik", "III. Sensorische Mikroprofile", "sensory"
        )
        self.section_tabs.create_split_tab(
            "Historie", "IV. Entwicklungsgeschichte", "history"
        )
        self.section_tabs.create_split_tab(
            "GEM-Matrix", "XI. GEM V1.3 STEUERUNGS-MATRIX", "gem_matrix"
        )

        self.option_widgets = self.section_tabs.option_widgets
        self.text_inputs = self.section_tabs.text_inputs

        self.create_dossier_tab()
        self.chat_tab = ChatTab(self.tabview.tab("Chat-Labor"), THEME, self.state, self)

        self.sidebar.controller.load_config(
            self.sidebar.vision_api_entry,
            self.sidebar.writer_api_entry,
            self.sidebar.image_api_entry,
        )

    def create_dossier_tab(self):
        tab = self.tabview.tab("Dossier")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.image_container = ctk.CTkLabel(
            container,
            text="[Kein Bild generiert]",
            height=300,
            fg_color="#111",
            corner_radius=10,
        )
        self.image_container.pack(fill="x", pady=(0, 10))

        self.dossier_preview = ctk.CTkTextbox(
            container, font=ctk.CTkFont(size=13), fg_color="#111", height=500
        )
        self.dossier_preview.pack(fill="both", expand=True)

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="🔄 Dossier Aktualisieren",
            command=self.update_dossier_preview,
            fg_color=THEME["accent"],
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_frame,
            text="🖼 BILD GENERIEREN",
            command=self.generate_visual,
            fg_color=THEME["neon_pink"],
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            btn_frame,
            text="JSON Export",
            command=self.save_dossier_from_tab,
            fg_color="#F59E0B",
        ).pack(side="right", padx=5)

    def reset_character(self):
        if messagebox.askyesno("Reset", "Bist du sicher? Alle Daten gehen verloren."):
            self.state.character = Character()
            self.sidebar.char_name_entry.delete(0, "end")
            self.sidebar.age_slider.set(25)
            self.state.uploaded_images.clear()
            for widget in self.sidebar.gallery_frame.winfo_children():
                widget.destroy()

            for section in self.option_widgets.values():
                for combo in section.values():
                    combo.set("Keine Auswahl")

            for textbox in self.text_inputs.values():
                textbox.delete("1.0", "end")

            self.tabview.set("Physiologie")
            messagebox.showinfo("Reset", "Neuer Charakter gestartet.")

    def update_dossier_preview(self):
        self.sync_ui_to_model()
        md = self.state.character.get_full_markdown()
        self.dossier_preview.delete("1.0", "end")
        self.dossier_preview.insert("1.0", md)

    def generate_visual(self):
        image_key = self.sidebar.image_api_entry.get().strip()
        writer_key = self.sidebar.writer_api_entry.get().strip()

        if not image_key:
            messagebox.showerror("Fehler", "Bitte Imagen API Key eingeben.")
            return

        name = self.sidebar.char_name_entry.get() or "Character"
        age = int(self.sidebar.age_slider.get())

        self.state.ai_client.configure(writer_key)

        all_options = {}
        for section in self.option_widgets.values():
            for k, v in section.items():
                if v.get() not in ["Keine Auswahl", "None"]:
                    all_options[k] = v.get()

        translation_prompt = f"""
        Construct an Imagen 4.0 prompt for this character:
        Name: {name}, Age: {age}
        Attributes: {json.dumps(all_options, ensure_ascii=False)}

        Format: "Full body shot of {{NAME}}, a {{AGE}} year old woman, {{ETHNICITY}}..."
        Translate all German attributes to English visual descriptions.
        Include terms: "8k", "photorealistic", "masterpiece", "best quality".
        Output ONLY the raw prompt string.
        """

        try:
            image_prompt = self.state.ai_client.generate_text(translation_prompt)
            success, result_image = self.state.ai_client.generate_image(
                image_prompt, image_key
            )

            if success:
                try:
                    img = result_image.image
                    output_filename = f"{name.replace(' ', '_')}_{age}.png"
                    output_path = os.path.join("output", output_filename)
                    if not os.path.exists("output"):
                        os.makedirs("output")
                    img.save(output_path)

                    self.state.character.generated_image_path = output_path

                    img.thumbnail((400, 400))
                    self.state.generated_image_ctk = ctk.CTkImage(
                        light_image=img, dark_image=img, size=img.size
                    )
                    self.image_container.configure(
                        image=self.state.generated_image_ctk, text=""
                    )

                    messagebox.showinfo(
                        "Erfolg", f"Bild generiert und gespeichert: {output_path}"
                    )
                    self.update_dossier_preview()
                except Exception as dl_err:
                    messagebox.showerror("Verarbeitungsfehler", str(dl_err))
            else:
                messagebox.showerror(
                    "Fehler", f"Bildgenerierung fehlgeschlagen: {result_image}"
                )

        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))

    def sync_ui_to_model(self):
        if "physiology" in self.text_inputs:
            self.state.character.physiology.content = self.text_inputs[
                "physiology"
            ].get("1.0", "end-1c")
        if "psychology" in self.text_inputs:
            self.state.character.psychology.content = self.text_inputs[
                "psychology"
            ].get("1.0", "end-1c")
        if "sensory" in self.text_inputs:
            self.state.character.sensory.content = self.text_inputs["sensory"].get(
                "1.0", "end-1c"
            )
        if "history" in self.text_inputs:
            self.state.character.history.content = self.text_inputs["history"].get(
                "1.0", "end-1c"
            )
        if "gem_matrix" in self.text_inputs:
            self.state.character.gem_matrix.content = self.text_inputs[
                "gem_matrix"
            ].get("1.0", "end-1c")

    def save_dossier_from_tab(self):
        name = self.sidebar.char_name_entry.get()
        try:
            self.sync_ui_to_model()
            filepath = self.sidebar.controller.save_dossier(name)
            messagebox.showinfo("Erfolg", f"Dossier gespeichert unter:\n{filepath}")
            self.sidebar.refresh_dossiers()
        except ValueError as exc:
            messagebox.showerror("Fehler", str(exc))
        except Exception as exc:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {exc}")

    def export_character(self):
        self.sync_ui_to_model()
        try:
            filepath = self.state.exporter.export(self.state.character)
            messagebox.showinfo("Erfolg", f"Charakter exportiert nach:\n{filepath}")
        except Exception as exc:
            messagebox.showerror("Fehler", f"Export fehlgeschlagen: {exc}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
