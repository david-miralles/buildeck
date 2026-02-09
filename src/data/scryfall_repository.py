"""
This module provides a Scryfall API repository implementation for retrieving Magic: The Gathering card data.
"""
import requests
from typing import Optional, Any
from src.core.interfaces import CardRepository
from src.data.cache_manager import CacheManager

class ScryfallRepository(CardRepository):
    """
    Implementation of CardRepository using the Scryfall API.
    Includes local caching and multi-language support.
    """
    
    def __init__(self):
        self.base_url = "https://api.scryfall.com/cards/named"
        self.search_url = "https://api.scryfall.com/cards/search"
        self.cache = CacheManager()
        self.lang_codes = {
            "English": "en",
            "Español": "es"
        }

    def get_card_data(self, name: str, lang_name: str = "English") -> Optional[dict[str, Any]]:
        iso_lang = self.lang_codes.get(lang_name, "en")
        
        # 1. Check local cache
        cached_data = self.cache.get_card(name, lang_name)
        if cached_data:
            return cached_data

        # 2. Fetch from Scryfall API
        try:
            # Get the base card (English/Default)
            params = {'exact': name}
            response = requests.get(self.base_url, params=params, timeout=10)

            if response.status_code == 200:
                card_json = response.json()
                
                # If requested language is not English, search for the localized print via Oracle ID
                if iso_lang != "en":
                    final_data = self._get_localized_version(card_json, iso_lang)
                else:
                    final_data = self._parse_card_data(card_json)

                # 3. Save to cache
                if final_data:
                    self.cache.save_card(name, lang_name, final_data)

                return final_data
                
        except requests.RequestException as e:
            print(f"Error connecting to Scryfall API: {e}")

        return None

    def _get_localized_version(self, card_json: dict, iso_lang: str) -> dict:
        """
        Searches for a specific language version using Oracle ID.
        """
        oracle_id = card_json.get("oracle_id")
        if not oracle_id:
            return self._parse_card_data(card_json)

        # Query: Oracle ID + Language + Unique Prints
        query = f'oracleid:{oracle_id} lang:{iso_lang} unique:prints'
        
        try:
            r = requests.get(self.search_url, params={'q': query}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("total_cards", 0) > 0:
                    # Return the first match (most recent printing usually)
                    return self._parse_card_data(data["data"][0])
        except requests.RequestException:
            pass

        # Fallback to base version
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