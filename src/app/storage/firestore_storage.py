from typing import Dict, Any
import os
from ..firebase.firebase_init import get_firestore_client
from firebase_admin import firestore
from .storage_interface import UserStorageInterface

class FirestoreStorage(UserStorageInterface):
    """Stores user data in Firestore."""
    
    def __init__(self, collection_name: str = 'users'):
        """
        Initialize Firestore client.
        
        Args:
            collection_name: The name of the collection to store user data in
        """
        self.db = get_firestore_client()
        self.collection_name = collection_name
        
    def _get_user_ref(self, user_id: str):
        """
        Get Firestore reference for a user.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            Firestore document reference for the user
        """
        return self.db.collection(self.collection_name).document(user_id)
    
    def load_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Load user data from Firestore.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            User data dictionary or empty dict if not found
        """
        try:
            user_doc = self._get_user_ref(user_id).get()
            if user_doc.exists:
                return user_doc.to_dict() or {}
            return {}
        except Exception as e:
            # Log the error and return empty dict
            print(f"Error loading user data from Firestore: {e}")
            return {}
    
    def save_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """
        Save user data to Firestore.
        
        Args:
            user_id: The unique identifier for the user
            data: The data to save
        """
        try:
            # Add server timestamp
            data_with_timestamp = dict(data)
            data_with_timestamp['last_updated'] = firestore.SERVER_TIMESTAMP
            self._get_user_ref(user_id).set(data_with_timestamp, merge=True)
        except Exception as e:
            # Log the error
            print(f"Error saving user data to Firestore: {e}")
        
    def user_exists(self, user_id: str) -> bool:
        """
        Check if user exists in Firestore.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            True if the user exists, False otherwise
        """
        try:
            return self._get_user_ref(user_id).get().exists
        except Exception as e:
            # Log the error and return False
            print(f"Error checking if user exists in Firestore: {e}")
            return False 