import csv
import re
import threading
import os
import requests
import sys
from tkinter import filedialog, messagebox

# Image handling imports
from PIL import Image
import customtkinter as ctk  # type: ignore
import pyperclip  # type: ignore

from assets.locales import LANGUAGES

class MainWindow(ctk.CTk):
    def __init__(self, card_repo):
        super().__init__()
        
        self.repo = card_repo
        self.current_lang = "English"
        self.extracted_data = [] 
        
        # --- Concurrency & State Management ---
        self.current_image_token = 0   
        self.current_process_token = 0 
        self.selected_button = None    
        
        # --- MEMORY CACHE (RAM) ---
        # Stores { "url_string": CTkImage_object }
        # This prevents garbage collection errors and speeds up navigation
        self.ram_image_cache = {}

        # Geometry and Setup
        self.geometry("1100x750")
        self.setup_ui()
        self.update_ui_text()

    def setup_ui(self):
        # --- TOP SECTION ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=(10, 0))

        self.label = ctk.CTkLabel(self.top_frame, text="", font=("Arial", 16, "bold"))
        self.label.pack(side="left")

        self.lang_menu = ctk.CTkOptionMenu(
            self.top_frame, values=list(LANGUAGES.keys()), command=self.change_language
        )
        self.lang_menu.pack(side="right")

        # --- MAIN CONTAINER ---
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. LEFT PANEL (Tabs)
        self.left_panel = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

        self.tabs = ctk.CTkTabview(self.left_panel)
        self.tabs.pack(fill="both", expand=True)
        self.tabs.add("Input")
        self.tabs.add("Results")

        # --- TAB 1: INPUT ---
        self.btn_db = ctk.CTkButton(
            self.tabs.tab("Input"), text="", command=self.start_download, 
            fg_color="#7f8c8d", hover_color="#95a5a6"
        )
        self.btn_db.pack(pady=5, fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(self.tabs.tab("Input"))
        self.progress_bar.set(0)

        self.txt_input = ctk.CTkTextbox(self.tabs.tab("Input"))
        self.txt_input.pack(pady=10, fill="both", expand=True)

        self.btn_process = ctk.CTkButton(self.tabs.tab("Input"), text="", command=self.start_processing_thread)
        self.btn_process.pack(pady=5, fill="x")

        # --- TAB 2: RESULTS ---
        self.scroll_frame = ctk.CTkScrollableFrame(self.tabs.tab("Results"), label_text="Processed Cards")
        self.scroll_frame.pack(fill="both", expand=True, pady=10)
        
        self.btn_copy = ctk.CTkButton(self.tabs.tab("Results"), text="", command=self.copy_to_clipboard, state="disabled")
        self.btn_copy.pack(pady=5, fill="x")

        self.btn_download = ctk.CTkButton(self.tabs.tab("Results"), text="", command=self.download_csv, state="disabled")
        self.btn_download.pack(pady=5, fill="x")

        # Status Bar
        self.status_label = ctk.CTkLabel(self.left_panel, text="", text_color="#3498db")
        self.status_label.pack(pady=5)

        # 2. RIGHT PANEL (Image & Details)
        self.right_panel = ctk.CTkFrame(self.main_container, width=320)
        self.right_panel.pack(side="right", fill="y", padx=(5, 10), pady=10)
        self.right_panel.pack_propagate(False)

        # Image Label
        self.image_label = ctk.CTkLabel(self.right_panel, text="Select a card", width=240, height=335)
        self.image_label.pack(pady=(20, 10))

        # Details
        self.details_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.details_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.lbl_name = ctk.CTkLabel(self.details_frame, text="", font=("Arial", 14, "bold"), wraplength=280)
        self.lbl_name.pack(pady=(5, 0))

        self.lbl_type = ctk.CTkLabel(self.details_frame, text="", font=("Arial", 12, "italic"), wraplength=280)
        self.lbl_type.pack(pady=(0, 5))
        
        self.lbl_mana = ctk.CTkLabel(self.details_frame, text="")
        self.lbl_mana.pack(pady=2)

        self.txt_desc = ctk.CTkTextbox(self.details_frame, height=120, wrap="word")
        self.txt_desc.pack(fill="x", pady=10)
        self.txt_desc.configure(state="disabled")

        self.lbl_pt = ctk.CTkLabel(self.details_frame, text="", font=("Arial", 12, "bold"))
        self.lbl_pt.pack(pady=5, side="bottom")

        # --- GLOBAL SCROLL BINDING FOR MAC ---
        if sys.platform == "darwin":
            self.bind_all("<MouseWheel>", self._on_global_mouse_wheel)

    def change_language(self, new_lang):
        self.current_lang = new_lang
        self.update_ui_text()

    def update_ui_text(self):
        lang = LANGUAGES[self.current_lang]
        self.title(lang["title"])
        self.label.configure(text=lang["label_input"])
        self.btn_db.configure(text=lang["btn_db"])
        self.btn_process.configure(text=lang["btn_process"])
        self.btn_copy.configure(text=lang["btn_copy"])
        self.btn_download.configure(text=lang["btn_download"])
        self.scroll_frame.configure(label_text=lang.get("results_title", "Cards Found"))

    # --- SCROLL HANDLING ---
    def _on_global_mouse_wheel(self, event):
        try:
            if self.tabs.get() != "Results": return
            x, y = self.winfo_pointerxy()
            widget = self.scroll_frame
            wx = widget.winfo_rootx()
            wy = widget.winfo_rooty()
            w_width = widget.winfo_width()
            w_height = widget.winfo_height()

            if wx <= x <= wx + w_width and wy <= y <= wy + w_height:
                self.scroll_frame._parent_canvas.yview_scroll(int(-1 * event.delta), "units")
        except Exception:
            pass

    def _on_mouse_wheel_windows(self, event):
        self.scroll_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mouse_wheel_recursive(self, widget):
        if sys.platform != "darwin":
            widget.bind("<MouseWheel>", self._on_mouse_wheel_windows)
            for child in widget.winfo_children():
                self._bind_mouse_wheel_recursive(child)

    # --- DOWNLOAD DB LOGIC ---
    def start_download(self):
        lang = LANGUAGES[self.current_lang]
        self.btn_db.configure(state="disabled")
        self.progress_bar.pack(pady=5, fill="x", before=self.txt_input)
        self.status_label.configure(text=lang["status_downloading"])
        thread = threading.Thread(target=self.run_download_task, daemon=True)
        thread.start()

    def run_download_task(self):
        self.repo.download_bulk_data(self.update_download_progress)

    def update_download_progress(self, status_text, progress_float):
        self.status_label.configure(text=status_text)
        self.progress_bar.set(progress_float)
        if progress_float >= 1.0:
            lang = LANGUAGES[self.current_lang]
            self.status_label.configure(text=lang["status_db_ok"])
            self.btn_db.configure(state="normal")
            self.progress_bar.pack_forget()

    # --- PROCESSING LOGIC ---
    def start_processing_thread(self):
        lang = LANGUAGES[self.current_lang]
        raw_text = self.txt_input.get("1.0", "end-1c")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not lines:
            messagebox.showwarning("Buildeck", lang["msg_empty"])
            return

        self.current_process_token += 1
        current_token = self.current_process_token

        self.btn_process.configure(state="disabled")
        self.status_label.configure(text=lang["status_wait"])
        
        thread = threading.Thread(target=self._run_processing_task, args=(lines, current_token), daemon=True)
        thread.start()

    def _run_processing_task(self, lines, token):
        lang = LANGUAGES[self.current_lang]
        card_totals = {}
        for line in lines:
            if line.startswith("//"): continue
            match = re.match(r"^(\d+)[xX]?\s+(.+)$", line)
            if match:
                qty = int(match.group(1))
                name = match.group(2).strip()
            else:
                qty = 1
                name = line.strip()
            name = name.split("(")[0].strip()
            key = name.lower()
            if key in card_totals:
                card_totals[key]["qty"] += qty
            else:
                card_totals[key] = {"qty": qty, "name": name}

        total_unique = len(card_totals)
        processed_count = 0
        temp_results = []

        for key, info in card_totals.items():
            if self.current_process_token != token: return

            processed_count += 1
            msg = f"{lang['status_wait']} ({processed_count}/{total_unique})"
            self.after(0, lambda m=msg: self.status_label.configure(text=m))

            data = self.repo.get_card_data(info["name"], lang_name=self.current_lang)
            if data:
                data["quantity"] = info["qty"]
                temp_results.append(data)

        if self.current_process_token == token:
            self.after(0, lambda: self._finish_processing(temp_results))

    def _finish_processing(self, results):
        lang = LANGUAGES[self.current_lang]
        self.extracted_data = results
        self.render_card_list()
        self.tabs.set("Results")
        self.status_label.configure(text=lang["status_done"].format(len(self.extracted_data)))
        self.btn_process.configure(state="normal")
        self.btn_copy.configure(state="normal")
        self.btn_download.configure(state="normal")
        self._clear_details_panel()

    def render_card_list(self):
        print(f"[UI] Rendering {len(self.extracted_data)} cards to list.")
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.selected_button = None

        for card in self.extracted_data:
            display_text = f"{card['quantity']}x {card['name']}"
            btn = ctk.CTkButton(
                self.scroll_frame, 
                text=display_text, 
                anchor="w", 
                fg_color="transparent", 
                border_width=1,
                border_color="#34495e",
                text_color=("black", "white"),
            )
            btn.configure(command=lambda c=card, b=btn: self.on_card_selected(c, b))
            btn.pack(fill="x", pady=2)
            
            self._bind_mouse_wheel_recursive(btn)

    def on_card_selected(self, card_data, button_widget):
        print(f"[UI] Card Selected: {card_data.get('name')}")
        
        if self.selected_button is not None:
            try:
                self.selected_button.configure(fg_color="transparent")
            except Exception:
                pass
        
        button_widget.configure(fg_color=["#3B8ED0", "#1F6AA5"]) 
        self.selected_button = button_widget

        self.lbl_name.configure(text=card_data.get("name", "Unknown"))
        self.lbl_type.configure(text=card_data.get("type", ""))
        self.lbl_mana.configure(text=card_data.get("mana", ""))
        self.lbl_pt.configure(text=f"P/T: {card_data.get('pt', '-')}")
        
        self.txt_desc.configure(state="normal")
        self.txt_desc.delete("1.0", "end")
        self.txt_desc.insert("1.0", card_data.get("desc", ""))
        self.txt_desc.configure(state="disabled")

        self.display_card_image(card_data.get("image_url"))

    def _clear_details_panel(self):
        self.image_label.configure(image=None, text="Select a card")
        self.lbl_name.configure(text="")
        self.lbl_type.configure(text="")
        self.lbl_mana.configure(text="")
        self.lbl_pt.configure(text="")
        self.txt_desc.configure(state="normal")
        self.txt_desc.delete("1.0", "end")
        self.txt_desc.configure(state="disabled")

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
            field_order = ["quantity", "name", "mana", "type", "desc", "pt"]
            header_map = dict(zip(field_order, lang["columns"]))
            with open(path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=field_order)
                writer.writerow(header_map)
                writer.writerows(self.extracted_data)
            messagebox.showinfo("Buildeck", lang["msg_save"])

    # --- IMAGE LOGIC (WITH RAM CACHE) ---
    def display_card_image(self, url):
        if not url:
            self.image_label.configure(image=None, text="No Image Available")
            return

        # 1. CHECK RAM CACHE FIRST (Instant Load)
        if url in self.ram_image_cache:
            print(f"[UI] Loaded from RAM cache: {url}")
            self.image_label.configure(image=self.ram_image_cache[url], text="")
            return
        
        # 2. If not in RAM, proceed to load from Disk/Web
        print(f"[UI] Requesting Image: {url}")
        self.current_image_token += 1
        my_token = self.current_image_token
        
        self.image_label.configure(image=None, text="Loading...")

        def task():
            try:
                filename = url.split("/")[-1].split("?")[0]
                if "." not in filename: filename += ".jpg"
                
                cache_dir = os.path.join("cache", "images")
                cache_path = os.path.join(cache_dir, filename)
                os.makedirs(cache_dir, exist_ok=True)

                if os.path.exists(cache_path):
                    if os.path.getsize(cache_path) == 0:
                        os.remove(cache_path)

                if not os.path.exists(cache_path):
                    print(f"[UI] Downloading...")
                    res = requests.get(url, timeout=10)
                    if res.status_code == 200:
                        with open(cache_path, "wb") as f:
                            f.write(res.content)
                    else:
                        print(f"[UI ERROR] HTTP {res.status_code}")
                        return

                if self.current_image_token != my_token:
                    return

                # Load PIL Image
                pil_img = Image.open(cache_path)
                pil_img.load() 
                
                print("[UI] Sending PIL image to main thread.")
                # Pass PIL image AND URL (for caching key) to main thread
                self.after(0, lambda: self._update_image_label(pil_img, url, my_token))
                
            except Exception as e:
                print(f"[UI FATAL] Image Task Failed: {e}")
                if self.current_image_token == my_token:
                    self.after(0, lambda: self.image_label.configure(text="Image Error"))

        threading.Thread(target=task, daemon=True).start()

    def _update_image_label(self, pil_image, url, token_at_start):
        # THIS RUNS ON MAIN THREAD
        if self.current_image_token == token_at_start:
            try:
                # Create CTkImage
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(240, 335))
                
                # SAVE TO RAM CACHE (Prevents GC and enables fast reload)
                self.ram_image_cache[url] = ctk_image
                
                self.image_label.configure(image=ctk_image, text="")
                print("[UI] Image rendered and cached successfully.")
            except Exception as e:
                print(f"[UI ERROR] Rendering failed: {e}")