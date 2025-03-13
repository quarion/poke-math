from typing import Any, Dict


class UserStorageInterface:
    """Interface for user data storage implementations."""
    
    def load_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Load data for a specific user_id.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            A dictionary containing the user's data
        """
        raise NotImplementedError
    
    def save_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """
        Save data for a specific user_id.
        
        Args:
            user_id: The unique identifier for the user
            data: The data to save
        """
        raise NotImplementedError
        
    def user_exists(self, user_id: str) -> bool:
        """
        Check if a user exists in storage.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            True if the user exists, False otherwise
        """
        raise NotImplementedError 