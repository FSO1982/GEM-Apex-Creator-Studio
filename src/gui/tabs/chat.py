import customtkinter as ctk
from tkinter import messagebox

from gui.state import AppState


class ChatController:
    def __init__(self, state: AppState):
        self.state = state

    def start_simulation(self, name: str, age: int, options: dict, writer_key: str):
        if not writer_key:
            return None
        self.state.ai_client.configure(writer_key)
        system_prompt = f"""
        ### SYSTEM INSTRUKTION: CHARAKTER-SIMULATION ###
        Du bist jetzt {name}. Du bist KEINE KI mehr.
        Alter: {age}
        Attribute: {options}

        Verhalte dich exakt wie dieser Charakter.
        """
        self.state.chat_session = self.state.ai_client.start_chat(system_prompt)
        return system_prompt

    def send_message(self, message: str, character_name: str) -> str:
        if not self.state.chat_session:
            raise RuntimeError("Keine aktive Simulation")
        response = self.state.chat_session.send_message(message)
        return response.text


class ChatTab:
    def __init__(self, tab: ctk.CTkFrame, theme: dict, state: AppState, main_window):
        self.tab = tab
        self.theme = theme
        self.state = state
        self.main_window = main_window
        self.controller = ChatController(state)
        self._build_chat_tab()

    def _build_chat_tab(self) -> None:
        self.tab.grid_columnconfigure(0, weight=1)
        self.tab.grid_rowconfigure(0, weight=1)

        self.chat_history = ctk.CTkTextbox(
            self.tab, font=ctk.CTkFont(size=13), fg_color="#111", state="disabled"
        )
        self.chat_history.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_history._textbox.tag_config("user", foreground="#33C9FF")
        self.chat_history._textbox.tag_config("model", foreground="#FF66CC")
        self.chat_history._textbox.tag_config("system", foreground="#888888")

        input_frame = ctk.CTkFrame(self.tab, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        self.chat_input = ctk.CTkEntry(
            input_frame, placeholder_text="Schreibe eine Nachricht..."
        )
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_input.bind("<Return>", self.send_chat_message)

        ctk.CTkButton(
            input_frame,
            text="Senden",
            command=self.send_chat_message,
            fg_color=self.theme["accent"],
            width=100,
        ).pack(side="right")

        ctk.CTkButton(
            self.tab,
            text="▶ SIMULATION STARTEN",
            command=self.start_simulation,
            fg_color=self.theme["neon_blue"],
        ).grid(row=2, column=0, pady=10)

    def start_simulation(self):
        writer_key = self.main_window.sidebar.writer_api_entry.get().strip()
        if not writer_key:
            return
        name = self.main_window.sidebar.char_name_entry.get() or "Unbekannt"
        age = int(self.main_window.sidebar.age_slider.get())
        opts = {}
        for section in self.main_window.option_widgets.values():
            for k, v in section.items():
                opts[k] = v.get()

        self.controller.start_simulation(name, age, opts, writer_key)
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        self.chat_history._textbox.insert(
            "end", "--- SIMULATION GESTARTET ---\n\n", "system"
        )
        self.chat_history.configure(state="disabled")

    def send_chat_message(self, event=None):
        if not self.state.chat_session:
            return
        msg = self.chat_input.get()
        if not msg:
            return

        self.chat_input.delete(0, "end")
        self.chat_history.configure(state="normal")
        self.chat_history._textbox.insert("end", f"Du: {msg}\n\n", "user")

        try:
            response_text = self.controller.send_message(
                msg, self.main_window.sidebar.char_name_entry.get()
            )
            self.chat_history._textbox.insert(
                "end",
                f"{self.main_window.sidebar.char_name_entry.get()}: {response_text}\n\n",
                "model",
            )
        except Exception as exc:  # pragma: no cover - UI warning only
            self.chat_history.insert("end", f"Fehler: {exc}\n")

        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")
