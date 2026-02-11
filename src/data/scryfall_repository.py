"""
This module provides a Scryfall API repository implementation for retrieving Magic: The Gathering card data.
"""
import json
import os
import requests

from typing import Optional, Any, Callable
from src.core.interfaces import CardRepository
from src.data.cache_manager import CacheManager

class ScryfallRepository(CardRepository):
    """
    Implementation of CardRepository using the Scryfall API.
    Includes local caching, bulk data loading, and multi-language support.
    """
    
    def __init__(self):
        self.base_url = "https://api.scryfall.com/cards/named"
        self.search_url = "https://api.scryfall.com/cards/search"
        self.bulk_url = "https://api.scryfall.com/bulk-data"
        self.bulk_file = "scryfall_oracle_cards.json"
        
        self.cache = CacheManager()
        self.lang_codes = {"English": "en", "Español": "es"}
        
        # In-memory index for the bulk database
        self.bulk_index = {}
        self._load_bulk_index()

    def _load_bulk_index(self):
        """Loads the massive JSON file into memory for instant lookups."""
        if os.path.exists(self.bulk_file):
            print("[SYSTEM] Loading bulk database into memory... this may take a moment.")
            try:
                with open(self.bulk_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    # Create a fast lookup dictionary mapping lowercase names to card data
                    for card in cards:
                        name = card.get("name", "").lower()
                        self.bulk_index[name] = card
                print(f"[SYSTEM] Bulk database loaded. {len(self.bulk_index)} cards ready.")
            except Exception as e:
                print(f"[ERROR] Failed to load bulk data: {e}")

    def download_bulk_data(self, progress_callback: Callable[[str, float], None]):
        """
        Downloads the 'Oracle Cards' bulk file from Scryfall.
        Run this in a separate thread.
        """
        try:
            # 1. Get the download URL
            progress_callback("Fetching metadata...", 0.1)
            meta_response = requests.get(self.bulk_url, timeout=10)
            meta_data = meta_response.json()
            
            download_uri = None
            for item in meta_data.get("data", []):
                if item["type"] == "oracle_cards":
                    download_uri = item["download_uri"]
                    break
            
            if not download_uri:
                progress_callback("Error: Bulk URI not found.", 0)
                return

            # 2. Download the huge file stream
            progress_callback("Downloading database...", 0.2)
            with requests.get(download_uri, stream=True) as r:
                r.raise_for_status()
                total_length = int(r.headers.get('content-length', 0))
                dl = 0
                
                with open(self.bulk_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        dl += len(chunk)
                        f.write(chunk)
                        if total_length:
                            pct = 0.2 + (0.7 * (dl / total_length))
                            progress_callback(f"Downloading... {int(pct*100)}%", pct)

            # 3. Reload into memory
            progress_callback("Indexing data...", 0.95)
            self._load_bulk_index()
            progress_callback("Database updated!", 1.0)
            
        except Exception as e:
            progress_callback(f"Error: {str(e)}", 0)

    def get_card_data(self, name: str, lang_name: str = "English") -> Optional[dict[str, Any]]:
        print(f"\n[REPO] Requesting: {name} ({lang_name})")
        iso_lang = self.lang_codes.get(lang_name, "en")
        
        # 1. Check local small cache (Historical queries)
        cached_data = self.cache.get_card(name, lang_name)
        if cached_data:
            print(f"[REPO] Found in Cache: {name}")
            return cached_data

        # 2. Check Bulk Database (The big offline file)
        # Only valid for English usually
        if iso_lang == "en" and name.lower() in self.bulk_index:
            print(f"[REPO] Found in Bulk DB: {name}")
            raw_data = self.bulk_index[name.lower()]
            parsed = self._parse_card_data(raw_data)
            self.cache.save_card(name, lang_name, parsed)
            return parsed

        # 3. Fetch from Scryfall API (Fallback or for Translations)
        try:
            print(f"[REPO] Fetching from API: {name}...")
            params = {'exact': name}
            response = requests.get(self.base_url, params=params, timeout=10)

            if response.status_code == 200:
                card_json = response.json()
                
                if iso_lang != "en":
                    final_data = self._get_localized_version(card_json, iso_lang)
                else:
                    final_data = self._parse_card_data(card_json)

                if final_data:
                    self.cache.save_card(name, lang_name, final_data)

                return final_data
            else:
                 print(f"[REPO] API Error {response.status_code} for {name}")
                
        except requests.RequestException as e:
            print(f"[REPO] Error connecting to Scryfall API: {e}")

        return None

    def _get_localized_version(self, card_json: dict, iso_lang: str) -> dict:
        """Searches for a specific language version using Oracle ID."""
        oracle_id = card_json.get("oracle_id")
        if not oracle_id:
            return self._parse_card_data(card_json)

        query = f'oracleid:{oracle_id} lang:{iso_lang} unique:prints'
        try:
            r = requests.get(self.search_url, params={'q': query}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("total_cards", 0) > 0:
                    return self._parse_card_data(data["data"][0])
        except requests.RequestException:
            pass
        return self._parse_card_data(card_json)

    def _parse_card_data(self, data: dict) -> dict[str, Any]:
        """
        Parses Scryfall JSON into internal format.
        Robust logic for Split/Transform/MDFC and Standard cards.
        """
        parsed = {
            "name": data.get("printed_name") or data.get("name"),
            "mana": data.get("mana_cost", ""),
            "type": data.get("printed_type_line") or data.get("type_line"),
            "desc": data.get("printed_text") or data.get("oracle_text", ""),
            "pt": "N/A",
            "image_url": None
        }

        # --- IMAGE EXTRACTION LOGIC ---
        if "image_uris" in data:
            parsed["image_url"] = data["image_uris"].get("normal")
        elif "card_faces" in data:
            # For double-faced cards, try to get the front face image
            faces = data["card_faces"]
            if len(faces) > 0 and "image_uris" in faces[0]:
                parsed["image_url"] = faces[0]["image_uris"].get("normal")
        
        # Log URL finding for debug
        if parsed["image_url"]:
            # print(f"[REPO] Image URL found: {parsed['image_url']}") # Uncomment if needed
            pass
        else:
            print(f"[REPO] Warning: No image URL found for {parsed['name']}")

        # Handle Power/Toughness for single cards
        if "power" in data and "toughness" in data:
             parsed["pt"] = f"{data['power']}/{data['toughness']}"

        # --- MULTI-FACE LOGIC (Split, Transform, MDFC) ---
        if "card_faces" in data:
            faces = data["card_faces"]
            
            # 1. MANA
            mana_list = [f.get("mana_cost", "") for f in faces]
            combined_mana = " // ".join([m for m in mana_list if m])
            if combined_mana:
                parsed["mana"] = combined_mana

            # 2. DESC
            desc_lines = []
            for f in faces:
                name = f.get("printed_name") or f.get("name")
                text = f.get("printed_text") or f.get("oracle_text", "")
                if text:
                    desc_lines.append(f"[{name}]:\n{text}")
            
            if desc_lines:
                parsed["desc"] = "\n\n--- // ---\n\n".join(desc_lines)
            
            # 3. TYPE
            if not parsed["type"]:
                 parsed["type"] = " // ".join([f.get("type_line", "") for f in faces])

            # 4. P/T
            pt_list = []
            has_pt = False
            for f in faces:
                if "power" in f and "toughness" in f:
                    pt_list.append(f"{f['power']}/{f['toughness']}")
                    has_pt = True
                else:
                    pt_list.append("-")
            
            if has_pt:
                parsed["pt"] = " // ".join(pt_list)

        return parsed