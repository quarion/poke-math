from src.app.game.session_manager import SessionManager
from src.app.storage.firestore_storage import FirestoreStorage
from src.app.storage.flask_session_storage import FlaskSessionStorage

def create_session_manager(use_firestore: bool = True) -> SessionManager:
    """
    Factory function to create a SessionManager with the appropriate storage.
    
    Args:
        use_firestore: Whether to use Firestore storage (True) or Flask session storage (False)
        
    Returns:
        SessionManager instance with the specified storage
        
    Raises:
        Exception: If use_firestore is True and Firestore initialization fails
    """
    if use_firestore:
        # Create Firestore storage - will raise an exception if it fails
        storage = FirestoreStorage()
    else:
        # Create Flask session storage
        storage = FlaskSessionStorage()
        
    # Create and return a SessionManager with the specified storage
    return SessionManager.load_from_storage(storage=storage)