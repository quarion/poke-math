from typing import Dict, Any
import os
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from .storage_interface import UserStorageInterface

class FirestoreStorage(UserStorageInterface):
    """Stores user data in Firestore."""
    
    def __init__(self, collection_name: str = 'users'):
        """
        Initialize Firestore client.
        
        Args:
            collection_name: The name of the collection to store user data in
        """
        self.db = self._initialize_firebase()
        self.collection_name = collection_name
        
    def _initialize_firebase(self):
        """
        Initialize Firebase app and return Firestore client.
        
        Returns:
            Firestore client instance
        """
        # Check if already initialized
        if len(firebase_admin._apps) > 0:
            return firestore.client()
        
        # Use environment variables for credentials in production
        # or service account file in development
        cred = None
        if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            cred = credentials.ApplicationDefault()
        else:
            # Path to service account file - preferably use env vars pointing to this
            service_account_path = os.environ.get(
                'FIREBASE_SERVICE_ACCOUNT',
                os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'firebase-credentials.json')
            )
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
        
        # If we couldn't get credentials, raise an error
        if cred is None:
            raise RuntimeError(
                "Firebase credentials not found. Either set GOOGLE_APPLICATION_CREDENTIALS "
                "environment variable, or provide a firebase-credentials.json file."
            )
            
        initialize_app(cred)
        return firestore.client()
    
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