import csv
import re
from tkinter import filedialog, messagebox

import customtkinter as ctk  # type: ignore
import pyperclip  # type: ignore

from assets.locales import LANGUAGES

class MainWindow(ctk.CTk):
    def __init__(self, card_repo):
        super().__init__()
        
        self.repo = card_repo
        self.current_lang = "English"
        self.extracted_data = [] # List of dictionaries

        self.geometry("650x800")
        self.setup_ui()
        self.update_ui_text()

    def setup_ui(self):
        # ... (Misma configuración UI que antes) ...
        self.lang_menu = ctk.CTkOptionMenu(
            self, values=list(LANGUAGES.keys()), command=self.change_language
        )
        self.lang_menu.pack(pady=10, padx=20, anchor="ne")

        self.label = ctk.CTkLabel(self, text="", font=("Arial", 14, "bold"))
        self.label.pack(pady=10)

        self.txt_input = ctk.CTkTextbox(self, width=550, height=350)
        self.txt_input.pack(pady=10)

        self.btn_process = ctk.CTkButton(self, text="", command=self.process_list)
        self.btn_process.pack(pady=5)

        self.btn_copy = ctk.CTkButton(self, text="", command=self.copy_to_clipboard, state="disabled")
        self.btn_copy.pack(pady=5)

        self.btn_download = ctk.CTkButton(self, text="", command=self.download_csv, state="disabled")
        self.btn_download.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="", text_color="#3498db")
        self.status_label.pack(pady=20)

    def change_language(self, new_lang):
        self.current_lang = new_lang
        self.update_ui_text()

    def update_ui_text(self):
        lang = LANGUAGES[self.current_lang]
        self.title(lang["title"])
        self.label.configure(text=lang["label_input"])
        self.btn_process.configure(text=lang["btn_process"])
        self.btn_copy.configure(text=lang["btn_copy"])
        self.btn_download.configure(text=lang["btn_download"])

    def process_list(self):
        lang = LANGUAGES[self.current_lang]
        raw_text = self.txt_input.get("1.0", "end-1c")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            messagebox.showwarning("Buildeck", lang["msg_empty"])
            return

        self.extracted_data = []
        # Mensaje inicial
        self.status_label.configure(text=lang["status_wait"])
        self.update()

        # --- STEP 1: Aggregation Logic ---
        card_totals = {}

        for line in lines:
            match = re.match(r"^(\d+)[xX]?\s+(.+)$", line)
            
            if match:
                qty = int(match.group(1))
                name = match.group(2).strip()
            else:
                qty = 1
                name = line.strip()

            key = name.lower()
            
            if key in card_totals:
                card_totals[key]["qty"] += qty
            else:
                card_totals[key] = {"qty": qty, "name": name}

        # --- STEP 2: Fetch Data ---
        total_unique = len(card_totals)
        processed_count = 0

        for key, info in card_totals.items():
            processed_count += 1
            
            # --- CORRECCIÓN: USAMOS LAS VARIABLES AQUÍ ---
            # Actualizamos la etiqueta para mostrar (1/5), (2/5), etc.
            self.status_label.configure(text=f"{lang['status_wait']} ({processed_count}/{total_unique})")
            # Importante: .update() fuerza a la ventana a repintarse en mitad del bucle
            self.update() 
            # ---------------------------------------------

            original_name = info["name"]
            total_qty = info["qty"]
            
            # Fetch data from Repository
            data = self.repo.get_card_data(original_name, lang_name=self.current_lang)
            
            if data:
                data["quantity"] = total_qty
                self.extracted_data.append(data)

        self.status_label.configure(text=lang["status_done"].format(len(self.extracted_data)))
        self.btn_copy.configure(state="normal")
        self.btn_download.configure(state="normal")

    def copy_to_clipboard(self):
        lang = LANGUAGES[self.current_lang]
        # Headers: Qty, Name, Mana...
        header = "\t".join(lang["columns"])
        body = ""
        for d in self.extracted_data:
            # Construct row with Quantity first
            body += f"\n{d['quantity']}\t{d['name']}\t{d['mana']}\t{d['type']}\t{d['desc']}\t{d['pt']}"
        
        pyperclip.copy(header + body)
        messagebox.showinfo("Buildeck", lang["msg_copy"])

    def download_csv(self):
        lang = LANGUAGES[self.current_lang]
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            # Map dictionary keys to CSV columns
            # Note: "quantity" key was added in process_list, others come from repo
            field_order = ["quantity", "name", "mana", "type", "desc", "pt"]
            
            with open(path, mode="w", newline="", encoding="utf-16") as f:
                writer = csv.DictWriter(f, fieldnames=field_order)
                
                # Write custom header (translated)
                # We can't use writer.writeheader() because fieldnames are internal keys, not display names
                f.write("\t".join(lang["columns"]) + "\n")
                
                writer.writerows(self.extracted_data)
                
            messagebox.showinfo("Buildeck", lang["msg_save"])