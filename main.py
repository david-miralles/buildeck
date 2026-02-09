import customtkinter as ctk
import requests
import csv
import pyperclip
from tkinter import filedialog, messagebox

# --- Diccionario de Traducciones ---
LANGUAGES = {
    "English": {
        "title": "Buildeck - Magic Assistant",
        "label_input": "Paste your card list here (one per line):",
        "btn_process": "Process Cards",
        "btn_copy": "Copy to Clipboard",
        "btn_download": "Download CSV",
        "status_wait": "Processing... please wait.",
        "status_done": "Processed {} cards successfully.",
        "msg_empty": "The list is empty",
        "msg_copy": "Data copied to clipboard.",
        "msg_save": "File saved successfully.",
        "cols": ["Name", "Mana", "Type", "Description", "P/T"]
    },
    "Español": {
        "title": "Buildeck - Asistente de Magic",
        "label_input": "Pega aquí tu lista de cartas (una por línea):",
        "btn_process": "Procesar Cartas",
        "btn_copy": "Copiar al Portapapeles",
        "btn_download": "Descargar CSV",
        "status_wait": "Procesando... por favor espera.",
        "status_done": "Se procesaron {} cartas con éxito.",
        "msg_empty": "El listado está vacío",
        "msg_copy": "Datos copiados al portapapeles.",
        "msg_save": "Archivo guardado correctamente.",
        "cols": ["Nombre", "Mana", "Tipo", "Descripcion", "F/R"]
    }
}

class AppMagic(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "English"
        
        # Configuración Ventana
        self.title("Buildeck")
        self.geometry("600x750")

        # --- UI Elements ---
        # Selector de Idioma
        self.lang_menu = ctk.CTkOptionMenu(self, values=["English", "Español"], command=self.change_language)
        self.lang_menu.pack(pady=10, padx=20, anchor="ne")

        self.label = ctk.CTkLabel(self, text="", font=("Arial", 14))
        self.label.pack(pady=5)

        self.txt_input = ctk.CTkTextbox(self, width=500, height=300)
        self.txt_input.pack(pady=10)

        self.btn_procesar = ctk.CTkButton(self, text="", command=self.procesar_cartas)
        self.btn_procesar.pack(pady=5)

        self.btn_copiar = ctk.CTkButton(self, text="", command=self.copiar_portapapeles, state="disabled")
        self.btn_copiar.pack(pady=5)

        self.btn_descargar = ctk.CTkButton(self, text="", command=self.descargar_csv, state="disabled")
        self.btn_descargar.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=10)

        self.datos_extraidos = []
        self.update_ui_text() # Carga inicial de textos

    def change_language(self, new_lang):
        self.current_lang = new_lang
        self.update_ui_text()

    def update_ui_text(self):
        texts = LANGUAGES[self.current_lang]
        self.title(texts["title"])
        self.label.configure(text=texts["label_input"])
        self.btn_procesar.configure(text=texts["btn_process"])
        self.btn_copiar.configure(text=texts["btn_copy"])
        self.btn_descargar.configure(text=texts["btn_download"])

    def obtener_info_scryfall(self, nombre):
        try:
            url = "https://api.scryfall.com/cards/named"
            # Añadimos parámetro de idioma a la API si fuera necesario en el futuro
            response = requests.get(url, params={'exact': nombre})
            if response.status_code == 200:
                data = response.json()
                return {
                    "Nombre": data.get("name"),
                    "Mana": data.get("mana_cost"),
                    "Tipo": data.get("type_line"),
                    "Descripcion": data.get("oracle_text", "").replace("\n", " "),
                    "PT": f"{data.get('power', '?')}/{data.get('toughness', '?')}" if "power" in data else "N/A"
                }
        except: return None
        return None

    def procesar_cartas(self):
        lang = LANGUAGES[self.current_lang]
        contenido = self.txt_input.get("1.0", "end-1c").splitlines()
        nombres = [n.strip() for n in contenido if n.strip()]
        
        if not nombres:
            messagebox.showwarning("Aviso", lang["msg_empty"])
            return

        self.datos_extraidos = []
        self.status_label.configure(text=lang["status_wait"])
        self.update()

        for nombre in nombres:
            info = self.obtener_info_scryfall(nombre)
            if info: self.datos_extraidos.append(info)

        self.status_label.configure(text=lang["status_done"].format(len(self.datos_extraidos)))
        self.btn_copiar.configure(state="normal")
        self.btn_descargar.configure(state="normal")

    def copiar_portapapeles(self):
        lang = LANGUAGES[self.current_lang]
        cols = lang["cols"]
        texto = "\t".join(cols) + "\n"
        for d in self.datos_extraidos:
            texto += f"{d['Nombre']}\t{d['Mana']}\t{d['Tipo']}\t{d['Descripcion']}\t{d['PT']}\n"
        pyperclip.copy(texto)
        messagebox.showinfo("OK", lang["msg_copy"])

    def descargar_csv(self):
        lang = LANGUAGES[self.current_lang]
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if ruta:
            with open(ruta, mode="w", newline="", encoding="utf-16") as f:
                writer = csv.DictWriter(f, fieldnames=["Nombre", "Mana", "Tipo", "Descripcion", "PT"])
                writer.writeheader()
                writer.writerows(self.datos_extraidos)
            messagebox.showinfo("OK", lang["msg_save"])

if __name__ == "__main__":
    app = AppMagic()
    app.mainloop()