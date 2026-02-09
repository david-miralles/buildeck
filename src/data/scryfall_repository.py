import requests
from src.core.interfaces import CardRepository

class ScryfallRepository(CardRepository):
    def get_card_data(self, name: str):
        url = "https://api.scryfall.com/cards/named"
        try:
            r = requests.get(url, params={'exact': name})
            if r.status_code == 200:
                data = r.json()
                return {
                    "name": data.get("name"),
                    "mana": data.get("mana_cost"),
                    "type": data.get("type_line"),
                    "desc": data.get("oracle_text", ""),
                    "pt": f"{data.get('power', '?')}/{data.get('toughness', '?')}" if "power" in data else "N/A"
                }
        except:
            return None
        return None