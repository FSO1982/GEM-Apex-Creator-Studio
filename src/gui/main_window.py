import customtkinter as ctk
from ai.client import AIClient
from exporters.markdown_exporter import MarkdownExporter
from gui.tab_config import DEFAULT_TABS, all_tab_names
from models.character import Character
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import json
import threading
import requests
from io import BytesIO

# --- THEME SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

THEME = {
    "bg_dark": "#1a1a1a",
    "card_bg": "#2d2d2d",
    "accent": "#7C3AED",  # Purple
    "accent_hover": "#6D28D9",
    "neon_blue": "#06b6d4",
    "neon_pink": "#ec4899",
    "text_main": "#ffffff",
    "text_sub": "#a3a3a3",
    "danger": "#ef4444",
}


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(
            self.tooltip_window, text=self.text, fg_color="#333", corner_radius=5, padx=10, pady=5
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GEM-Apex Creator Studio")
        self.geometry("1600x900")
        self.configure(fg_color=THEME["bg_dark"])

        # Initialize AI Client and Data Model
        self.ai_client = AIClient()
        self.character = Character()
        self.exporter = MarkdownExporter(output_dir=os.path.join(os.getcwd(), "output"))
        self.uploaded_images = []
        self.image_thumbnails = []
        self.chat_session = None
        self.generated_image_ctk = None  # Prevent garbage collection

        # Config Persistence
        self.config_file = "config.json"
        self.saved_dossiers_dir = "saved_dossiers"
        if not os.path.exists(self.saved_dossiers_dir):
            os.makedirs(self.saved_dossiers_dir)

        # Layout configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.create_sidebar()

        # Main Content Area (Tabview)
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=THEME["bg_dark"],
            segmented_button_fg_color=THEME["card_bg"],
            segmented_button_selected_color=THEME["accent"],
        )
        self.tabview.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")

        self.tabs = all_tab_names()
        for tab in self.tabs:
            self.tabview.add(tab)

        # Load Options Data
        from models.options_data import CHARACTER_OPTIONS

        self.options_data = CHARACTER_OPTIONS

        # Create Tabs
        for tab_name, header_text, section_key in DEFAULT_TABS:
            self.create_split_tab(tab_name, header_text, section_key)

        self.create_dossier_tab()
        self.create_chat_tab()

        # Load Config
        self.load_config()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkScrollableFrame(
            self,
            width=300,
            corner_radius=0,
            fg_color=THEME["card_bg"],
            label_text="KONTROLLZENTRUM",
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        # Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="GEM-Apex\nCREATOR STUDIO",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=THEME["neon_blue"],
        )
        self.logo_label.pack(pady=(20, 20))

        # Character Name
        self.create_sidebar_section("IDENTITÄT")
        self.char_name_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Name / Alias")
        self.char_name_entry.pack(pady=5, padx=10, fill="x")

        # Age Slider
        ctk.CTkLabel(self.sidebar_frame, text="Alter:", font=ctk.CTkFont(size=12)).pack(
            pady=(5, 0), anchor="w", padx=10
        )
        self.age_slider = ctk.CTkSlider(
            self.sidebar_frame,
            from_=18,
            to=70,
            number_of_steps=52,
            button_color=THEME["accent"],
            progress_color=THEME["accent"],
        )
        self.age_slider.set(25)
        self.age_slider.pack(pady=5, padx=10, fill="x")
        self.age_label = ctk.CTkLabel(
            self.sidebar_frame, text="25 Jahre", text_color=THEME["neon_pink"]
        )
        self.age_label.pack(pady=0)
        self.age_slider.configure(
            command=lambda v: self.age_label.configure(text=f"{int(v)} Jahre")
        )

        # Image Gallery
        self.create_sidebar_section("VISUALS")
        self.gallery_frame = ctk.CTkScrollableFrame(self.sidebar_frame, height=120, fg_color="#222")
        self.gallery_frame.pack(pady=5, padx=10, fill="x")

        self.upload_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Bilder Upload (+)",
            command=self.upload_image,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
        )
        self.upload_btn.pack(pady=5, padx=10, fill="x")

        # API Config
        self.create_sidebar_section("SYSTEM LINK")

        ctk.CTkLabel(
            self.sidebar_frame, text="Google Gemini API Key (Vision)", font=ctk.CTkFont(size=10)
        ).pack(anchor="w", padx=10)
        self.vision_api_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text="Vision Key", show="*"
        )
        self.vision_api_entry.pack(pady=(0, 5), padx=10, fill="x")

        ctk.CTkLabel(
            self.sidebar_frame, text="Google Gemini API Key (Writer)", font=ctk.CTkFont(size=10)
        ).pack(anchor="w", padx=10)
        self.writer_api_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text="Writer Key", show="*"
        )
        self.writer_api_entry.pack(pady=(0, 5), padx=10, fill="x")

        ctk.CTkLabel(
            self.sidebar_frame, text="Google Imagen API Key (Images)", font=ctk.CTkFont(size=10)
        ).pack(anchor="w", padx=10)
        self.image_api_entry = ctk.CTkEntry(
            self.sidebar_frame, placeholder_text="Imagen Key", show="*"
        )
        self.image_api_entry.pack(pady=(0, 5), padx=10, fill="x")

        self.save_config_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="System Verbinden",
            command=self.save_and_connect,
            fg_color="#10B981",
        )
        self.save_config_btn.pack(pady=5, padx=10, fill="x")

        # Dossier Management
        self.create_sidebar_section("SPEICHER")
        self.dossier_list = ctk.CTkComboBox(
            self.sidebar_frame, values=["Lade..."], command=self.load_selected_dossier
        )
        self.dossier_list.pack(pady=5, padx=10, fill="x")
        self.refresh_dossiers()

        self.save_dossier_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="Dossier Speichern",
            command=self.save_dossier,
            fg_color="#F59E0B",
        )
        self.save_dossier_btn.pack(pady=5, padx=10, fill="x")

        # Reset Button
        ctk.CTkFrame(self.sidebar_frame, height=20, fg_color="transparent").pack()  # Spacer
        self.reset_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="♻ NEUER CHARAKTER",
            command=self.reset_character,
            fg_color=THEME["danger"],
            hover_color="#b91c1c",
        )
        self.reset_btn.pack(pady=20, padx=10, fill="x")

    def create_sidebar_section(self, title):
        ctk.CTkLabel(
            self.sidebar_frame,
            text=title,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=THEME["text_sub"],
        ).pack(pady=(15, 5), anchor="w", padx=10)

    def create_split_tab(self, tab_name, header_text, section_key):
        tab = self.tabview.tab(tab_name)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(1, weight=1)

        # Header
        lbl = ctk.CTkLabel(
            tab,
            text=header_text,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=THEME["neon_blue"],
        )
        lbl.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 10), sticky="w")

        # --- LEFT: OPTIONS (CARDS) ---
        options_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        options_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        if not hasattr(self, "option_widgets"):
            self.option_widgets = {}
        self.option_widgets[section_key] = {}

        section_data = self.options_data.get(header_text, {})

        for category, items in section_data.items():
            # Card Frame
            card = ctk.CTkFrame(options_frame, fg_color=THEME["card_bg"], corner_radius=10)
            card.pack(fill="x", pady=10, padx=5)

            # Card Header
            ctk.CTkLabel(
                card,
                text=category,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=THEME["accent"],
            ).pack(pady=10, padx=10, anchor="w")

            for option_name, values in items.items():
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", pady=5, padx=10)

                # Label + Info Icon
                label_frame = ctk.CTkFrame(row, fg_color="transparent")
                label_frame.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(label_frame, text=option_name, font=ctk.CTkFont(size=12)).pack(
                    side="left"
                )
                info_lbl = ctk.CTkLabel(
                    label_frame,
                    text="ⓘ",
                    font=ctk.CTkFont(size=12),
                    text_color=THEME["text_sub"],
                    cursor="hand2",
                )
                info_lbl.pack(side="left", padx=5)
                Tooltip(
                    info_lbl, f"Bestimmt {option_name} des Charakters."
                )  # Simple dynamic tooltip

                # ComboBox
                combo = ctk.CTkComboBox(
                    row,
                    values=values,
                    width=200,
                    fg_color="#222",
                    border_color="#444",
                    button_color=THEME["accent"],
                )
                combo.pack(side="right")

                self.option_widgets[section_key][f"{category}::{option_name}"] = combo

        # --- RIGHT: OUTPUT ---
        text_frame = ctk.CTkFrame(tab, fg_color=THEME["card_bg"], corner_radius=10)
        text_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        textbox = ctk.CTkTextbox(
            text_frame, font=ctk.CTkFont(size=13), fg_color="#111", text_color="#eee"
        )
        textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        setattr(self, f"{section_key}_input", textbox)

        # Generate Button
        gen_btn = ctk.CTkButton(
            text_frame,
            text="✨ GENERIEREN",
            command=lambda s=section_key: self.generate_description(s),
            fg_color=THEME["accent"],
            height=40,
            font=ctk.CTkFont(weight="bold"),
        )
        gen_btn.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

    def create_dossier_tab(self):
        tab = self.tabview.tab("Dossier")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Scrollable container for preview and image
        container = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Image Container
        self.image_container = ctk.CTkLabel(
            container, text="[Kein Bild generiert]", height=300, fg_color="#111", corner_radius=10
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
            btn_frame, text="JSON Export", command=self.save_dossier, fg_color="#F59E0B"
        ).pack(side="right", padx=5)

    def create_chat_tab(self):
        tab = self.tabview.tab("Chat-Labor")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.chat_history = ctk.CTkTextbox(
            tab, font=ctk.CTkFont(size=13), fg_color="#111", state="disabled"
        )
        self.chat_history.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Configure Tags for Colors (Accessing underlying tk widget)
        # Note: CTkTextbox uses ._textbox for the underlying tk.Text
        self.chat_history._textbox.tag_config("user", foreground="#33C9FF")  # Neon Blue
        self.chat_history._textbox.tag_config("model", foreground="#FF66CC")  # Neon Pink
        self.chat_history._textbox.tag_config("system", foreground="#888888")  # Grey

        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        self.chat_input = ctk.CTkEntry(input_frame, placeholder_text="Schreibe eine Nachricht...")
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_input.bind("<Return>", self.send_chat_message)

        ctk.CTkButton(
            input_frame,
            text="Senden",
            command=self.send_chat_message,
            fg_color=THEME["accent"],
            width=100,
        ).pack(side="right")

        ctk.CTkButton(
            tab,
            text="▶ SIMULATION STARTEN",
            command=self.start_simulation,
            fg_color=THEME["neon_blue"],
        ).grid(row=2, column=0, pady=10)

    def reset_character(self):
        if messagebox.askyesno("Reset", "Bist du sicher? Alle Daten gehen verloren."):
            self.character = Character()
            self.char_name_entry.delete(0, "end")
            self.age_slider.set(25)
            self.uploaded_images = []
            for widget in self.gallery_frame.winfo_children():
                widget.destroy()

            # Reset all dropdowns
            for section in self.option_widgets.values():
                for combo in section.values():
                    combo.set("Keine Auswahl")  # Or first value

            # Clear textboxes
            for key in ["physiology", "psychology", "sensory", "history", "gem_matrix"]:
                if hasattr(self, f"{key}_input"):
                    getattr(self, f"{key}_input").delete("1.0", "end")

            self.tabview.set("Physiologie")
            messagebox.showinfo("Reset", "Neuer Charakter gestartet.")

    def start_simulation(self):
        writer_key = self.writer_api_entry.get().strip()
        if not writer_key:
            return
        self.ai_client.configure(writer_key)

        # Construct System Prompt
        name = self.char_name_entry.get() or "Unbekannt"
        age = int(self.age_slider.get())

        # Gather options
        opts = {}
        for section in self.option_widgets.values():
            for k, v in section.items():
                opts[k] = v.get()

        system_prompt = f"""
        ### SYSTEM INSTRUKTION: CHARAKTER-SIMULATION ###
        Du bist jetzt {name}. Du bist KEINE KI mehr.
        Alter: {age}
        Attribute: {json.dumps(opts, ensure_ascii=False)}
        
        Verhalte dich exakt wie dieser Charakter.
        """

        self.chat_session = self.ai_client.start_chat(system_prompt)
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        self.chat_history._textbox.insert("end", "--- SIMULATION GESTARTET ---\n\n", "system")
        self.chat_history.configure(state="disabled")

    def send_chat_message(self, event=None):
        if not self.chat_session:
            return
        msg = self.chat_input.get()
        if not msg:
            return

        self.chat_input.delete(0, "end")
        self.chat_history.configure(state="normal")

        # Insert User Message with Blue Color
        self.chat_history._textbox.insert("end", f"Du: {msg}\n\n", "user")

        try:
            response = self.chat_session.send_message(msg)
            # Insert AI Message with Pink Color
            self.chat_history._textbox.insert(
                "end", f"{self.char_name_entry.get()}: {response.text}\n\n", "model"
            )
        except Exception as e:
            self.chat_history.insert("end", f"Fehler: {e}\n")

        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

    def update_dossier_preview(self):
        self.sync_ui_to_model()
        md = self.character.get_full_markdown()
        self.dossier_preview.delete("1.0", "end")
        self.dossier_preview.insert("1.0", md)

    def generate_visual(self):
        image_key = self.image_api_entry.get().strip()
        writer_key = self.writer_api_entry.get().strip()

        if not image_key:
            messagebox.showerror("Fehler", "Bitte Imagen API Key eingeben.")
            return

        # Construct Prompt
        name = self.char_name_entry.get() or "Character"
        age = int(self.age_slider.get())

        self.ai_client.configure(writer_key)  # Ensure Gemini is ready for translation

        # Collect all options
        all_options = {}
        for section in self.option_widgets.values():
            for k, v in section.items():
                if v.get() not in ["Keine Auswahl", "None"]:
                    all_options[k] = v.get()

        # Prompt Construction for Image
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
            image_prompt = self.ai_client.generate_text(translation_prompt)

            # Generate with Imagen 4.0
            success, result_image = self.ai_client.generate_image(image_prompt, image_key)

            if success:
                # result_image is the generated image object from google-genai
                try:
                    # Access image bytes directly if available, or use PIL image if provided
                    # The SDK usually provides a PIL image in .image property
                    img = result_image.image

                    # Save locally
                    output_filename = f"{name.replace(' ', '_')}_{age}.png"
                    output_path = os.path.join("output", output_filename)
                    if not os.path.exists("output"):
                        os.makedirs("output")
                    img.save(output_path)

                    self.character.generated_image_path = output_path

                    # Update UI (store as instance variable to prevent garbage collection)
                    img.thumbnail((400, 400))
                    self.generated_image_ctk = ctk.CTkImage(
                        light_image=img, dark_image=img, size=img.size
                    )
                    self.image_container.configure(image=self.generated_image_ctk, text="")

                    messagebox.showinfo("Erfolg", f"Bild generiert und gespeichert: {output_path}")
                    self.update_dossier_preview()
                except Exception as dl_err:
                    messagebox.showerror("Verarbeitungsfehler", str(dl_err))
            else:
                messagebox.showerror("Fehler", f"Bildgenerierung fehlgeschlagen: {result_image}")

        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def upload_image(self):
        if len(self.uploaded_images) >= 10:
            messagebox.showwarning("Limit erreicht", "Maximal 10 Bilder erlaubt.")
            return
        filepaths = filedialog.askopenfilenames(
            title="Charakterbilder auswählen",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")],
        )
        for filepath in filepaths:
            if len(self.uploaded_images) >= 10:
                break
            if filepath not in self.uploaded_images:
                self.uploaded_images.append(filepath)
                self.add_thumbnail(filepath)

    def add_thumbnail(self, filepath):
        try:
            img = Image.open(filepath)
            img.thumbnail((50, 50))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(50, 50))
            frame = ctk.CTkFrame(self.gallery_frame, fg_color="#333")
            frame.pack(pady=2, fill="x")
            ctk.CTkLabel(frame, image=ctk_img, text="").pack(side="left", padx=5)
            ctk.CTkButton(
                frame,
                text="X",
                width=20,
                fg_color=THEME["danger"],
                command=lambda p=filepath, f=frame: self.remove_image(p, f),
            ).pack(side="right", padx=5)
        except Exception as e:
            print(f"Error loading thumbnail: {e}")

    def remove_image(self, filepath, frame_widget):
        if filepath in self.uploaded_images:
            self.uploaded_images.remove(filepath)
            frame_widget.destroy()

    def save_and_connect(self):
        vision_key = self.vision_api_entry.get().strip()
        writer_key = self.writer_api_entry.get().strip()
        image_key = self.image_api_entry.get().strip()

        if not vision_key or not writer_key or not image_key:
            messagebox.showwarning("Konfiguration", "Bitte ALLE 3 Keys eingeben.")

        config = {"vision_key": vision_key, "writer_key": writer_key, "image_key": image_key}
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f)
            messagebox.showinfo("Erfolg", "Keys gespeichert!")
            self.ai_client.configure(
                writer_key
            )  # Configure main client immediately with writer key
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Config nicht speichern: {e}")

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.vision_api_entry.insert(
                        0, config.get("vision_key", "") or config.get("gemini_key", "")
                    )
                    self.writer_api_entry.insert(
                        0, config.get("writer_key", "") or config.get("gemini_key", "")
                    )
                    self.image_api_entry.insert(0, config.get("image_key", ""))
            except Exception:
                pass

    def refresh_dossiers(self):
        files = [
            f.replace(".json", "")
            for f in os.listdir(self.saved_dossiers_dir)
            if f.endswith(".json")
        ]
        self.dossier_list.configure(values=files)

    def load_selected_dossier(self, name):
        filepath = os.path.join(self.saved_dossiers_dir, f"{name}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.character = Character.from_dict(data)
                self.char_name_entry.delete(0, "end")
                self.char_name_entry.insert(0, self.character.name)
                if hasattr(self, "physiology_input"):
                    self.physiology_input.delete("1.0", "end")
                    self.physiology_input.insert("1.0", self.character.physiology.content)
                if hasattr(self, "psychology_input"):
                    self.psychology_input.delete("1.0", "end")
                    self.psychology_input.insert("1.0", self.character.psychology.content)
                if hasattr(self, "sensory_input"):
                    self.sensory_input.delete("1.0", "end")
                    self.sensory_input.insert("1.0", self.character.sensory.content)
                if hasattr(self, "history_input"):
                    self.history_input.delete("1.0", "end")
                    self.history_input.insert("1.0", self.character.history.content)
                if hasattr(self, "gem_matrix_input"):
                    self.gem_matrix_input.delete("1.0", "end")
                    self.gem_matrix_input.insert("1.0", self.character.gem_matrix.content)
                all_options = {
                    **self.character.physiology_options,
                    **self.character.psychology_options,
                    **self.character.sensory_options,
                    **self.character.history_options,
                    **self.character.gem_options,
                }
                for section_widgets in self.option_widgets.values():
                    for key, widget in section_widgets.items():
                        if key in all_options:
                            widget.set(all_options[key])
                messagebox.showinfo("Erfolg", f"Dossier '{name}' geladen.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Laden fehlgeschlagen: {e}")

    def sync_ui_to_model(self):
        if hasattr(self, "physiology_input"):
            self.character.physiology.content = self.physiology_input.get("1.0", "end-1c")
        if hasattr(self, "psychology_input"):
            self.character.psychology.content = self.psychology_input.get("1.0", "end-1c")
        if hasattr(self, "sensory_input"):
            self.character.sensory.content = self.sensory_input.get("1.0", "end-1c")
        if hasattr(self, "history_input"):
            self.character.history.content = self.history_input.get("1.0", "end-1c")
        if hasattr(self, "gem_matrix_input"):
            self.character.gem_matrix.content = self.gem_matrix_input.get("1.0", "end-1c")

    def save_dossier(self):
        name = self.char_name_entry.get()
        if not name:
            messagebox.showerror("Fehler", "Bitte Namen eingeben.")
            return

        # Sanitize filename
        safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c == " "]).rstrip()
        safe_name = safe_name.replace(" ", "_")

        self.character.name = name
        self.sync_ui_to_model()

        data = self.character.to_dict()
        filepath = os.path.join(self.saved_dossiers_dir, f"{safe_name}.json")

        try:
            if not os.path.exists(self.saved_dossiers_dir):
                os.makedirs(self.saved_dossiers_dir)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Erfolg", f"Dossier gespeichert unter:\n{filepath}")
            self.refresh_dossiers()
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")

    def export_character(self):
        self.sync_ui_to_model()
        try:
            # Ensure output dir exists
            if not os.path.exists(self.exporter.output_dir):
                os.makedirs(self.exporter.output_dir)

            filepath = self.exporter.export(self.character)
            messagebox.showinfo("Erfolg", f"Charakter exportiert nach:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Export fehlgeschlagen: {e}")

    def generate_description(self, section_key):
        vision_key = self.vision_api_entry.get().strip()
        writer_key = self.writer_api_entry.get().strip()

        if not writer_key:
            messagebox.showwarning("KI Warnung", "Bitte Writer API Key konfigurieren.")
            return

        # Vision Phase
        vision_summary = "Keine Bilder vorhanden."
        if self.uploaded_images and vision_key:
            self.ai_client.configure(vision_key)
            vision_prompt = "Du bist ein forensischer Analyst. Beschreibe NUR das Physische..."
            try:
                vision_summary = self.ai_client.analyze_images(self.uploaded_images, vision_prompt)
            except Exception as error:
                vision_summary = f"Visuelle Analyse fehlgeschlagen: {error}"

        # Writer Phase
        self.ai_client.configure(writer_key)
        selections = {}
        widgets = self.option_widgets.get(section_key, {})
        for key, widget in widgets.items():
            val = widget.get()
            if val not in ["Keine Auswahl", "None"]:
                selections[key] = val
        age_value = int(self.age_slider.get())

        writer_prompt = f"""
        ROLE: Du bist der "AI CHARAKTER-ARCHITEKT".
        INPUT:
        1. Visuelle Fakten: {vision_summary}
        2. User-Parameter: {json.dumps(selections, ensure_ascii=False)}
        3. Alter: {age_value}
        
        STYLE GUIDE:
        Do not write clinical reports. Write visceral, poetic, and extremely detailed anatomical descriptions.
        Example: Instead of 'She is muscular', write 'Her physique is a 56kg monument of discipline, muscles shifting under the skin like hydraulic pistons, veins pulsing with adrenaline.'
        
        Generiere NUR den Text für die Sektion: {section_key.upper()}.
        """
        try:
            generated_text = self.ai_client.generate_text(writer_prompt, temperature=0.7)
            textbox = getattr(self, f"{section_key}_input")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", generated_text)
            section = getattr(self.character, section_key)
            section.content = generated_text
            options_store = getattr(self.character, f"{section_key}_options", {})
            options_store.update(selections)
        except Exception as e:
            messagebox.showerror("Generierungsfehler", str(e))
