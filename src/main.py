import customtkinter as ctk
from gui.main_window import MainWindow
import os

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
