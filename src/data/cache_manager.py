import json
import os
from datetime import datetime, timedelta
from src.core.paths import get_user_data_dir

class CacheManager:
    def __init__(self, cache_file="cache_cards.json"):
        # Use the system's secure data directory
        self.data_dir = get_user_data_dir()
        self.cache_file = os.path.join(self.data_dir, cache_file)
        self.data = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def get_card(self, name, lang):
        key = f"{name}_{lang}".lower()
        if key in self.data:
            cached_item = self.data[key]
            # Check if cache is older than 24 hours
            timestamp = datetime.fromisoformat(cached_item['timestamp'])
            if datetime.now() - timestamp < timedelta(hours=24):
                return cached_item['payload']
        return None

    def save_card(self, name, lang, payload):
        key = f"{name}_{lang}".lower()
        self.data[key] = {
            'timestamp': datetime.now().isoformat(),
            'payload': payload
        }
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[CACHE ERROR] Could not save cache: {e}")