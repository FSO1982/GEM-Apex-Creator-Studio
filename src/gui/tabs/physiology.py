import json
from typing import Dict

import customtkinter as ctk
from tkinter import messagebox

from gui.state import AppState


class SectionTabs:
    def __init__(
        self, tabview: ctk.CTkTabview, theme: dict, options_data: dict, state: AppState
    ):
        self.tabview = tabview
        self.theme = theme
        self.options_data = options_data
        self.state = state
        self.option_widgets: Dict[str, Dict[str, ctk.CTkComboBox]] = {}
        self.text_inputs: Dict[str, ctk.CTkTextbox] = {}

    def create_split_tab(
        self, tab_name: str, header_text: str, section_key: str
    ) -> None:
        tab = self.tabview.tab(tab_name)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            tab,
            text=header_text,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.theme["neon_blue"],
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 10), sticky="w")

        options_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        options_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        self.option_widgets[section_key] = {}
        section_data = self.options_data.get(header_text, {})

        for category, items in section_data.items():
            card = ctk.CTkFrame(
                options_frame, fg_color=self.theme["card_bg"], corner_radius=10
            )
            card.pack(fill="x", pady=10, padx=5)

            ctk.CTkLabel(
                card,
                text=category,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=self.theme["accent"],
            ).pack(pady=10, padx=10, anchor="w")

            for option_name, values in items.items():
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", pady=5, padx=10)

                label_frame = ctk.CTkFrame(row, fg_color="transparent")
                label_frame.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    label_frame, text=option_name, font=ctk.CTkFont(size=12)
                ).pack(side="left")
                info_lbl = ctk.CTkLabel(
                    label_frame,
                    text="ⓘ",
                    font=ctk.CTkFont(size=12),
                    text_color=self.theme["text_sub"],
                    cursor="hand2",
                )
                info_lbl.pack(side="left", padx=5)
                info_lbl.bind(
                    "<Enter>", lambda e, opt=option_name: self._show_tooltip(e, opt)
                )
                info_lbl.bind("<Leave>", self._hide_tooltip)

                combo = ctk.CTkComboBox(
                    row,
                    values=values,
                    width=200,
                    fg_color="#222",
                    border_color="#444",
                    button_color=self.theme["accent"],
                )
                combo.pack(side="right")

                self.option_widgets[section_key][f"{category}::{option_name}"] = combo

        text_frame = ctk.CTkFrame(tab, fg_color=self.theme["card_bg"], corner_radius=10)
        text_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        textbox = ctk.CTkTextbox(
            text_frame, font=ctk.CTkFont(size=13), fg_color="#111", text_color="#eee"
        )
        textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.text_inputs[section_key] = textbox

        gen_btn = ctk.CTkButton(
            text_frame,
            text="✨ GENERIEREN",
            command=lambda s=section_key: self.generate_description(s),
            fg_color=self.theme["accent"],
            height=40,
            font=ctk.CTkFont(weight="bold"),
        )
        gen_btn.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

    def _show_tooltip(self, event, option_name: str) -> None:
        widget = event.widget
        if getattr(self, "_tooltip", None):
            return
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25

        self._tooltip = ctk.CTkToplevel(widget)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(
            self._tooltip,
            text=f"Bestimmt {option_name} des Charakters.",
            fg_color="#333",
            corner_radius=5,
            padx=10,
            pady=5,
        )
        label.pack()

    def _hide_tooltip(self, _event=None) -> None:
        if getattr(self, "_tooltip", None):
            self._tooltip.destroy()
            self._tooltip = None

    def generate_description(self, section_key: str) -> None:
        vision_key = self._get_entry_value("vision")
        writer_key = self._get_entry_value("writer")

        if not writer_key:
            messagebox.showwarning("KI Warnung", "Bitte Writer API Key konfigurieren.")
            return

        vision_summary = "Keine Bilder vorhanden."
        if self.state.uploaded_images and vision_key:
            self.state.ai_client.configure(vision_key)
            vision_prompt = (
                "Du bist ein forensischer Analyst. Beschreibe NUR das Physische..."
            )
            try:
                vision_summary = self.state.ai_client.analyze_images(
                    self.state.uploaded_images, vision_prompt
                )
            except Exception:
                pass

        self.state.ai_client.configure(writer_key)
        selections = {}
        widgets = self.option_widgets.get(section_key, {})
        for key, widget in widgets.items():
            val = widget.get()
            if val not in ["Keine Auswahl", "None"]:
                selections[key] = val
        age_value = int(self._get_age())

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
            generated_text = self.state.ai_client.generate_text(
                writer_prompt, temperature=0.7
            )
            textbox = self.text_inputs.get(section_key)
            if textbox:
                textbox.delete("1.0", "end")
                textbox.insert("1.0", generated_text)
            section = getattr(self.state.character, section_key)
            section.content = generated_text
            options_store = getattr(self.state.character, f"{section_key}_options", {})
            options_store.update(selections)
        except Exception as exc:  # pragma: no cover - messagebox path
            messagebox.showerror("Generierungsfehler", str(exc))

    def _get_entry_value(self, entry_type: str) -> str:
        parent = self.tabview.master
        vision_entry = getattr(parent.sidebar, "vision_api_entry", None)
        writer_entry = getattr(parent.sidebar, "writer_api_entry", None)
        if entry_type == "vision" and vision_entry:
            return vision_entry.get().strip()
        if entry_type == "writer" and writer_entry:
            return writer_entry.get().strip()
        return ""

    def _get_age(self) -> int:
        sidebar = getattr(self.tabview.master, "sidebar", None)
        if sidebar:
            return sidebar.age_slider.get()
        return 0
