import csv
import re
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk  # type: ignore
import pyperclip  # type: ignore

from assets.locales import LANGUAGES

class MainWindow(ctk.CTk):
    def __init__(self, card_repo):
        super().__init__()
        
        self.repo = card_repo
        self.current_lang = "English"
        self.extracted_data = [] 

        # Increased height to accommodate the new button and progress bar
        self.geometry("650x850")
        self.setup_ui()
        self.update_ui_text()

    def setup_ui(self):
        # Language Selector
        self.lang_menu = ctk.CTkOptionMenu(
            self, values=list(LANGUAGES.keys()), command=self.change_language
        )
        self.lang_menu.pack(pady=10, padx=20, anchor="ne")

        # Title Label
        self.label = ctk.CTkLabel(self, text="", font=("Arial", 14, "bold"))
        self.label.pack(pady=10)

        # --- DATABASE CONTROLS ---
        # Button to trigger offline database download
        self.btn_db = ctk.CTkButton(
            self, 
            text="", 
            command=self.start_download, 
            fg_color="#7f8c8d", 
            hover_color="#95a5a6"
        )
        self.btn_db.pack(pady=5)
        
        # Progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        self.progress_bar.pack_forget() 
        # -------------------------

        # Input Text Area
        self.txt_input = ctk.CTkTextbox(self, width=550, height=350)
        self.txt_input.pack(pady=10)

        # Action Buttons
        self.btn_process = ctk.CTkButton(self, text="", command=self.process_list)
        self.btn_process.pack(pady=5)

        self.btn_copy = ctk.CTkButton(self, text="", command=self.copy_to_clipboard, state="disabled")
        self.btn_copy.pack(pady=5)

        self.btn_download = ctk.CTkButton(self, text="", command=self.download_csv, state="disabled")
        self.btn_download.pack(pady=5)

        # Status Bar
        self.status_label = ctk.CTkLabel(self, text="", text_color="#3498db")
        self.status_label.pack(pady=20)

    def change_language(self, new_lang):
        self.current_lang = new_lang
        self.update_ui_text()

    def update_ui_text(self):
        """Updates all UI text elements based on the selected language."""
        lang = LANGUAGES[self.current_lang]
        
        self.title(lang["title"])
        self.label.configure(text=lang["label_input"])
        
        # Update buttons including the new DB button
        self.btn_db.configure(text=lang["btn_db"])
        self.btn_process.configure(text=lang["btn_process"])
        self.btn_copy.configure(text=lang["btn_copy"])
        self.btn_download.configure(text=lang["btn_download"])

    # --- DOWNLOAD LOGIC (THREADING) ---
    def start_download(self):
        """Starts the download process in a separate thread."""
        lang = LANGUAGES[self.current_lang]
        
        self.btn_db.configure(state="disabled")
        self.progress_bar.pack(pady=5) # Show progress bar
        self.status_label.configure(text=lang["status_downloading"])
        
        # Run the heavy task in a background thread to keep UI responsive
        thread = threading.Thread(target=self.run_download_task, daemon=True)
        thread.start()

    def run_download_task(self):
        """Worker function that runs in background."""
        # The repository handles the logic, we just pass the UI callback
        self.repo.download_bulk_data(self.update_download_progress)

    def update_download_progress(self, status_text, progress_float):
        """Callback to update UI from the background thread."""
        self.status_label.configure(text=status_text)
        self.progress_bar.set(progress_float)
        
        # Check for completion (1.0 means 100%)
        if progress_float >= 1.0:
            lang = LANGUAGES[self.current_lang]
            self.status_label.configure(text=lang["status_db_ok"])
            self.btn_db.configure(state="normal")
            # We keep the bar visible to show completion, or pack_forget() it here
    # ----------------------------------

    def process_list(self):
        lang = LANGUAGES[self.current_lang]
        raw_text = self.txt_input.get("1.0", "end-1c")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            messagebox.showwarning("Buildeck", lang["msg_empty"])
            return

        self.extracted_data = []
        self.status_label.configure(text=lang["status_wait"])
        self.update()

        # Step 1: Aggregation Logic
        card_totals = {}
        for line in lines:
            # Regex handles: "4x Bolt", "4 Bolt", "Bolt"
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

        # Step 2: Fetch Data
        total_unique = len(card_totals)
        processed_count = 0

        for key, info in card_totals.items():
            processed_count += 1
            
            # Progress update in format (1/5)
            self.status_label.configure(text=f"{lang['status_wait']} ({processed_count}/{total_unique})")
            self.update() 

            original_name = info["name"]
            total_qty = info["qty"]
            
            # Fetch data using repo (Cache -> Bulk DB -> API)
            data = self.repo.get_card_data(original_name, lang_name=self.current_lang)
            
            if data:
                data["quantity"] = total_qty
                self.extracted_data.append(data)

        self.status_label.configure(text=lang["status_done"].format(len(self.extracted_data)))
        self.btn_copy.configure(state="normal")
        self.btn_download.configure(state="normal")

    def copy_to_clipboard(self):
        lang = LANGUAGES[self.current_lang]
        header = "\t".join(lang["columns"])
        body = ""
        for d in self.extracted_data:
            body += f"\n{d['quantity']}\t{d['name']}\t{d['mana']}\t{d['type']}\t{d['desc']}\t{d['pt']}"
        
        pyperclip.copy(header + body)
        messagebox.showinfo("Buildeck", lang["msg_copy"])

    def download_csv(self):
        lang = LANGUAGES[self.current_lang]
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        
        if path:
            # Internal keys match the dictionary keys in self.extracted_data
            field_order = ["quantity", "name", "mana", "type", "desc", "pt"]
            
            # Map internal keys to display names (Translated)
            # Example: {"quantity": "Qty", "name": "Name", ...}
            header_map = dict(zip(field_order, lang["columns"]))
            
            # Use 'utf-8-sig' for best compatibility with Excel (Windows/Mac) and Editors
            with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=field_order)
                
                # Write the header using the writer to ensure correct CSV formatting
                # We pass the dictionary mapping internal keys to display names
                writer.writerow(header_map)
                
                # Write the data rows
                writer.writerows(self.extracted_data)
                
            messagebox.showinfo("Buildeck", lang["msg_save"])