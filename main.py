# main.py
from src.ui.main_window import MainWindow
from src.data.scryfall_repository import ScryfallRepository

if __name__ == "__main__":
    # 1. Creamos el repositorio (la "lógica")
    repo = ScryfallRepository()
    
    # 2. Se lo pasamos a la ventana (la "vista")
    app = MainWindow(repo)
    
    # 3. Arrancamos
    app.mainloop()