import json
import os
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, cache_file="cache_cards.json"):
        self.cache_file = cache_file
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
        # Creamos una clave única que combine nombre e idioma
        key = f"{name}_{lang}".lower()
        if key in self.data:
            cached_item = self.data[key]
            # Verificar si han pasado más de 24 horas
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
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)