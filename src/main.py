import customtkinter as ctk
from dotenv import load_dotenv
from gui.main_window import MainWindow
import os

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def main():
    load_dotenv()
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
