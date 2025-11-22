import json
import os
from typing import Callable, Mapping

import customtkinter as ctk
from PIL import Image
from tkinter import filedialog, messagebox

from gui.state import AppState
from utils.config_loader import load_api_keys, sanitize_key, validate_google_api_key


class SidebarController:
    def __init__(
        self,
        state: AppState,
        filedialog_module=filedialog,
        messagebox_module=messagebox,
    ):
        self.state = state
        self.filedialog = filedialog_module
        self.messagebox = messagebox_module

    def upload_image(self) -> list[str]:
        if len(self.state.uploaded_images) >= 10:
            self.messagebox.showwarning("Limit erreicht", "Maximal 10 Bilder erlaubt.")
            return []

        filepaths = self.filedialog.askopenfilenames(
            title="Charakterbilder auswählen",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")],
        )
        added: list[str] = []
        for filepath in filepaths:
            if len(self.state.uploaded_images) >= 10:
                break
            if filepath not in self.state.uploaded_images:
                self.state.uploaded_images.append(filepath)
                added.append(filepath)
        return added

    def save_and_connect(
        self, vision_key: str, writer_key: str, image_key: str
    ) -> bool:
        cleaned_vision = sanitize_key(vision_key)
        cleaned_writer = sanitize_key(writer_key)
        cleaned_image = sanitize_key(image_key)

        if not cleaned_vision or not cleaned_writer or not cleaned_image:
            self.messagebox.showwarning("Konfiguration", "Bitte ALLE 3 Keys eingeben.")
            return False

        for label, key in (
            ("Vision", cleaned_vision),
            ("Writer", cleaned_writer),
            ("Imagen", cleaned_image),
        ):
            is_valid, reason = validate_google_api_key(key)
            if not is_valid:
                self.messagebox.showerror(
                    "Ungültiger API Key", f"{label} Key ungültig: {reason}"
                )
                return False

        config = {
            "vision_key": cleaned_vision,
            "writer_key": cleaned_writer,
            "image_key": cleaned_image,
        }

        try:
            with open(self.state.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f)
            self.messagebox.showinfo("Erfolg", "Keys gespeichert!")
            self.state.ai_client.configure(cleaned_writer)
            return True
        except Exception as exc:  # pragma: no cover - messagebox path
            self.messagebox.showerror("Fehler", f"Konnte Config nicht speichern: {exc}")
            return False

    def load_config(
        self,
        vision_entry: ctk.CTkEntry,
        writer_entry: ctk.CTkEntry,
        image_entry: ctk.CTkEntry,
    ) -> None:
        keys = load_api_keys(self.state.config_file)

        try:
            vision_entry.delete(0, "end")
            writer_entry.delete(0, "end")
            image_entry.delete(0, "end")

            vision_entry.insert(0, keys.get("vision_key", ""))
            writer_entry.insert(0, keys.get("writer_key", ""))
            image_entry.insert(0, keys.get("image_key", ""))
        except Exception:
            return

    def refresh_dossiers(self) -> list[str]:
        files = [
            f.replace(".json", "")
            for f in os.listdir(self.state.saved_dossiers_dir)
            if f.endswith(".json")
        ]
        return files

    def load_selected_dossier(
        self,
        name: str,
        option_widgets: Mapping[str, Mapping[str, ctk.CTkComboBox]],
        text_inputs: Mapping[str, ctk.CTkTextbox],
    ) -> None:
        filepath = os.path.join(self.state.saved_dossiers_dir, f"{name}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                from models.character import Character

                self.state.character = Character.from_dict(data)
                if "name" in data:
                    # Ensure name consistency
                    self.state.character.name = data.get("name", "")
                self._restore_text_inputs(text_inputs)
                self._restore_option_widgets(option_widgets)
                self.messagebox.showinfo("Erfolg", f"Dossier '{name}' geladen.")
            except Exception as exc:  # pragma: no cover - messagebox path
                self.messagebox.showerror("Fehler", f"Laden fehlgeschlagen: {exc}")

    def save_dossier(self, name: str) -> str:
        if not name:
            raise ValueError("Bitte Namen eingeben.")

        safe_name = "".join(
            [c for c in name if c.isalpha() or c.isdigit() or c == " "]
        ).rstrip()
        safe_name = safe_name.replace(" ", "_")

        self.state.character.name = name
        data = self.state.character.to_dict()
        filepath = os.path.join(self.state.saved_dossiers_dir, f"{safe_name}.json")

        if not os.path.exists(self.state.saved_dossiers_dir):
            os.makedirs(self.state.saved_dossiers_dir)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return filepath

    def _restore_option_widgets(
        self, option_widgets: Mapping[str, Mapping[str, ctk.CTkComboBox]]
    ) -> None:
        all_options = {
            **self.state.character.physiology_options,
            **self.state.character.psychology_options,
            **self.state.character.sensory_options,
            **self.state.character.history_options,
            **self.state.character.gem_options,
        }
        for section_widgets in option_widgets.values():
            for key, widget in section_widgets.items():
                if key in all_options:
                    widget.set(all_options[key])

    def _restore_text_inputs(self, text_inputs: Mapping[str, ctk.CTkTextbox]) -> None:
        mapping = {
            "physiology": self.state.character.physiology.content,
            "psychology": self.state.character.psychology.content,
            "sensory": self.state.character.sensory.content,
            "history": self.state.character.history.content,
            "gem_matrix": self.state.character.gem_matrix.content,
        }
        for key, widget in text_inputs.items():
            if key in mapping:
                widget.configure(state="normal")
                widget.delete("1.0", "end")
                widget.insert("1.0", mapping[key])
                widget.configure(state="normal")


class Sidebar:
    def __init__(
        self,
        master: ctk.CTk,
        theme: dict,
        state: AppState,
        on_reset: Callable[[], None],
    ):
        self.state = state
        self.theme = theme
        self.controller = SidebarController(state)
        self.on_reset = on_reset
        self.frame = ctk.CTkScrollableFrame(
            master,
            width=300,
            corner_radius=0,
            fg_color=theme["card_bg"],
            label_text="KONTROLLZENTRUM",
        )
        self.frame.grid(row=0, column=0, sticky="nsew")

        self._build_sidebar()

    def _build_sidebar(self) -> None:
        ctk.CTkLabel(
            self.frame,
            text="GEM-Apex\nCREATOR STUDIO",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.theme["neon_blue"],
        ).pack(pady=(20, 20))

        self._create_sidebar_section("IDENTITÄT")
        self.char_name_entry = ctk.CTkEntry(self.frame, placeholder_text="Name / Alias")
        self.char_name_entry.pack(pady=5, padx=10, fill="x")

        ctk.CTkLabel(self.frame, text="Alter:", font=ctk.CTkFont(size=12)).pack(
            pady=(5, 0), anchor="w", padx=10
        )
        self.age_slider = ctk.CTkSlider(
            self.frame,
            from_=18,
            to=70,
            number_of_steps=52,
            button_color=self.theme["accent"],
            progress_color=self.theme["accent"],
        )
        self.age_slider.set(25)
        self.age_slider.pack(pady=5, padx=10, fill="x")
        self.age_label = ctk.CTkLabel(
            self.frame, text="25 Jahre", text_color=self.theme["neon_pink"]
        )
        self.age_label.pack(pady=0)
        self.age_slider.configure(
            command=lambda v: self.age_label.configure(text=f"{int(v)} Jahre")
        )

        self._create_sidebar_section("VISUALS")
        self.gallery_frame = ctk.CTkScrollableFrame(
            self.frame, height=120, fg_color="#222"
        )
        self.gallery_frame.pack(pady=5, padx=10, fill="x")

        self.upload_btn = ctk.CTkButton(
            self.frame,
            text="Bilder Upload (+)",
            command=self._upload_image,
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
        )
        self.upload_btn.pack(pady=5, padx=10, fill="x")

        self._create_sidebar_section("SYSTEM LINK")

        ctk.CTkLabel(
            self.frame, text="Google Gemini API Key (Vision)", font=ctk.CTkFont(size=10)
        ).pack(anchor="w", padx=10)
        self.vision_api_entry = ctk.CTkEntry(
            self.frame, placeholder_text="Vision Key", show="*"
        )
        self.vision_api_entry.pack(pady=(0, 5), padx=10, fill="x")

        ctk.CTkLabel(
            self.frame, text="Google Gemini API Key (Writer)", font=ctk.CTkFont(size=10)
        ).pack(anchor="w", padx=10)
        self.writer_api_entry = ctk.CTkEntry(
            self.frame, placeholder_text="Writer Key", show="*"
        )
        self.writer_api_entry.pack(pady=(0, 5), padx=10, fill="x")

        ctk.CTkLabel(
            self.frame, text="Google Imagen API Key (Images)", font=ctk.CTkFont(size=10)
        ).pack(anchor="w", padx=10)
        self.image_api_entry = ctk.CTkEntry(
            self.frame, placeholder_text="Imagen Key", show="*"
        )
        self.image_api_entry.pack(pady=(0, 5), padx=10, fill="x")

        self.save_config_btn = ctk.CTkButton(
            self.frame,
            text="System Verbinden",
            command=self._save_and_connect,
            fg_color="#10B981",
        )
        self.save_config_btn.pack(pady=5, padx=10, fill="x")

        self._create_sidebar_section("SPEICHER")
        self.dossier_list = ctk.CTkComboBox(
            self.frame, values=["Lade..."], command=self._load_selected_dossier
        )
        self.dossier_list.pack(pady=5, padx=10, fill="x")
        self.refresh_dossiers()

        self.save_dossier_btn = ctk.CTkButton(
            self.frame,
            text="Dossier Speichern",
            command=self._save_dossier,
            fg_color="#F59E0B",
        )
        self.save_dossier_btn.pack(pady=5, padx=10, fill="x")

        ctk.CTkFrame(self.frame, height=20, fg_color="transparent").pack()
        self.reset_btn = ctk.CTkButton(
            self.frame,
            text="♻ NEUER CHARAKTER",
            command=self._reset_character,
            fg_color=self.theme["danger"],
            hover_color="#b91c1c",
        )
        self.reset_btn.pack(pady=20, padx=10, fill="x")

    def _create_sidebar_section(self, title: str) -> None:
        ctk.CTkLabel(
            self.frame,
            text=title,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.theme["text_sub"],
        ).pack(pady=(15, 5), anchor="w", padx=10)

    def _upload_image(self) -> None:
        new_files = self.controller.upload_image()
        for filepath in new_files:
            self.add_thumbnail(filepath)

    def add_thumbnail(self, filepath: str) -> None:
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
                fg_color=self.theme["danger"],
                command=lambda p=filepath, f=frame: self._remove_image(p, f),
            ).pack(side="right", padx=5)
        except Exception as exc:  # pragma: no cover - UI preview only
            print(f"Error loading thumbnail: {exc}")

    def _remove_image(self, filepath: str, frame_widget: ctk.CTkFrame) -> None:
        if filepath in self.state.uploaded_images:
            self.state.uploaded_images.remove(filepath)
            frame_widget.destroy()

    def _save_and_connect(self) -> None:
        self.controller.save_and_connect(
            self.vision_api_entry.get().strip(),
            self.writer_api_entry.get().strip(),
            self.image_api_entry.get().strip(),
        )

    def refresh_dossiers(self) -> None:
        files = self.controller.refresh_dossiers()
        self.dossier_list.configure(values=files)

    def _load_selected_dossier(self, name: str) -> None:
        from gui.main_window import MainWindow  # Lazy import to avoid cycle

        if isinstance(self.frame.master, MainWindow):
            self.controller.load_selected_dossier(
                name, self.frame.master.option_widgets, self.frame.master.text_inputs
            )
            self.frame.master.update_dossier_preview()

    def _save_dossier(self) -> None:
        from gui.main_window import MainWindow

        if isinstance(self.frame.master, MainWindow):
            name = self.char_name_entry.get()
            try:
                filepath = self.controller.save_dossier(name)
                self.refresh_dossiers()
                messagebox.showinfo("Erfolg", f"Dossier gespeichert unter:\n{filepath}")
            except ValueError as exc:
                messagebox.showerror("Fehler", str(exc))

    def _reset_character(self) -> None:
        self.on_reset()
        self.refresh_dossiers()
