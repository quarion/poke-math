from src.app.game.session_manager import SessionManager
from src.app.storage.firestore_storage import FirestoreStorage
from src.app.storage.flask_session_storage import FlaskSessionStorage

def create_session_manager(use_firestore: bool = True) -> SessionManager:
    """
    Factory function to create a SessionManager with the appropriate storage.
    
    Handles creation of either Firestore or Flask session storage based on the parameter.
    """
    if use_firestore:
        # Create Firestore storage - will raise an exception if it fails
        storage = FirestoreStorage()
    else:
        # Create Flask session storage
        storage = FlaskSessionStorage()
        
    # Create and return a SessionManager with the specified storage
    return SessionManager.load_from_storage(storage=storage)