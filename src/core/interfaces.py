from abc import ABC, abstractmethod

class CardRepository(ABC):
    @abstractmethod
    def get_card_data(self, name: str) -> dict:
        """Debe devolver un diccionario con: name, mana, type, desc, pt"""
        pass

class CacheProvider(ABC):
    @abstractmethod
    def get(self, key: str):
        pass
    
    @abstractmethod
    def set(self, key: str, value: dict):
        pass