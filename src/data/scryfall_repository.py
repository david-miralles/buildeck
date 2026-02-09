"""
This module provides a Scryfall API repository implementation for retrieving Magic: The Gathering card data.
"""
import requests
import json
import os
import threading
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
        # Structure: { "name_lowercase": {card_data} }
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
                        # Only store if not present (or overwrite, doesn't matter much for Oracle)
                        self.bulk_index[name] = card
                print(f"[SYSTEM] Bulk database loaded. {len(self.bulk_index)} cards ready.")
            except Exception as e:
                print(f"[ERROR] Failed to load bulk data: {e}")

    def download_bulk_data(self, progress_callback: Callable[[str, float], None]):
        """
        Downloads the 'Oracle Cards' bulk file from Scryfall.
        Run this in a separate thread.
        
        Args:
            progress_callback: A function(status_text, progress_float) to update UI.
        """
        try:
            # 1. Get the download URL
            progress_callback("Fetching metadata...", 0.1)
            meta_response = requests.get(self.bulk_url, timeout=10)
            meta_data = meta_response.json()
            
            # Find the 'oracle_cards' object (smaller and faster than 'default_cards')
            # 'oracle_cards' has one entry per unique card mechanic (good for deck building)
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
                        # Calculate percentage (0.2 to 0.9 range)
                        if total_length:
                            done = int(50 * dl / total_length)
                            pct = 0.2 + (0.7 * (dl / total_length))
                            progress_callback(f"Downloading... {done*2}%", pct)

            # 3. Reload into memory
            progress_callback("Indexing data...", 0.95)
            self._load_bulk_index()
            progress_callback("Database updated!", 1.0)
            
        except Exception as e:
            progress_callback(f"Error: {str(e)}", 0)

    def get_card_data(self, name: str, lang_name: str = "English") -> Optional[dict[str, Any]]:
        iso_lang = self.lang_codes.get(lang_name, "en")
        
        # 1. Check local small cache (Historical queries)
        cached_data = self.cache.get_card(name, lang_name)
        if cached_data:
            return cached_data

        # 2. Check Bulk Database (The big offline file)
        # Note: Bulk data is usually English only. If user asks for Spanish,
        # we skip this and go to API to find the translation.
        if iso_lang == "en" and name.lower() in self.bulk_index:
            print(f"[BULK] Found '{name}' in offline database.")
            raw_data = self.bulk_index[name.lower()]
            parsed = self._parse_card_data(raw_data)
            # Save to small cache for consistency
            self.cache.save_card(name, lang_name, parsed)
            return parsed

        # 3. Fetch from Scryfall API (Fallback or for Translations)
        try:
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
                
        except requests.RequestException as e:
            print(f"Error connecting to Scryfall API: {e}")

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
        return {
            "name": data.get("printed_name") or data.get("name"),
            "mana": data.get("mana_cost", ""),
            "type": data.get("printed_type_line") or data.get("type_line"),
            "desc": data.get("printed_text") or data.get("oracle_text", ""),
            "pt": f"{data.get('power', '?')}/{data.get('toughness', '?')}" 
                  if "power" in data else "N/A"
        }