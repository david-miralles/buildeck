from abc import ABC, abstractmethod
from typing import Optional, Any

class CardRepository(ABC):
    """
    Interface (Contract) that any Card Repository must follow.
    """
    
    @abstractmethod
    def get_card_data(self, name: str, lang_name: str = "English") -> Optional[dict[str, Any]]:
        """
        Retrieves data for a specific card.
        
        Args:
            name: The name of the card.
            lang_name: The desired language (default: "English").
            
        Returns:
            A dictionary with card data if found, None otherwise.
        """
        pass