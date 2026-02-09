import customtkinter as ctk
from src.ui.main_window import MainWindow
from src.data.scryfall_repository import ScryfallRepository

if __name__ == "__main__":
    # Inyectamos la dependencia (Scryfall)
    repo = ScryfallRepository()
    
    app = MainWindow(repo)
    app.mainloop()