# Quiz Persistence Implementation Plan

## Original Requirements

```
Feature description - quizzes persistence:
1. Keep quest session, wihtout log-in/registration for now
2. Add new view "my quizzes", with a list of attempted quizzes.
    - Summary with the number of points (number of solved quizzes)
    - For each quiz display:
        - Was solved
        - Date
        - Button: Open
        - Button: Forget
3. Introduce data structure for the above. Remember that it needs to be per-profile
4. Re-name "all exercises" to "Community exercises"
5. Move the data we keep in the session to persistent storage
 - Add firestore conneciton
 - session_manager.py should contineu encapsulate all the session logic. If we have any leaks now into app.py fix them
 - Add logic to store the data we currently store in sesison and the data structure for point 3.
 - I do not know if we should hook firestore to flask session, or eg. only keep user id in flask session, and have "normal" persistence for the user data in firestore

 In the end flow should be:
 - Open the app
 - Get session/user id from flask session. If does not exist, create new one
 - Get data for this user from firestore. If does not exist, initialize with empty one.
 - Pick from pre-defined "community exercises" or generate a random one
 - All progress (taken exercises, if they wre completed) is stored in firestore
```

## Implementation Plan

### 1. Design Philosophy

The implementation will use a **composition pattern** rather than inheritance to handle different storage backends. This approach will:

- Keep a clean separation between the session management logic and storage mechanisms
- Allow easy switching between storage implementations
- Facilitate future extensions without modifying the core SessionManager class

We will also ensure that:
- Complete data for random quizzes is stored to allow proper reconstruction
- Unavailable quizzes are handled gracefully with appropriate user messaging
- Flask session is used only for storing the user ID, with all other state persisted in Firestore

### 2. Component Structure

#### 2.1 Storage Interface and Implementations

```python
# src/app/game/storage/storage_interface.py
from typing import Dict, Any, Optional

class UserStorageInterface:
    """Interface for user data storage implementations."""
    
    def load_user_data(self, user_id: str) -> Dict[str, Any]:
        """Load data for a specific user_id."""
        raise NotImplementedError
    
    def save_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Save data for a specific user_id."""
        raise NotImplementedError
        
    def user_exists(self, user_id: str) -> bool:
        """Check if a user exists in storage."""
        raise NotImplementedError

# src/app/game/storage/flask_session_storage.py
from flask import session as flask_session
from typing import Dict, Any
from .storage_interface import UserStorageInterface

class FlaskSessionStorage(UserStorageInterface):
    """Stores user data in Flask session."""
    
    def load_user_data(self, user_id: str) -> Dict[str, Any]:
        """Load data from Flask session."""
        return flask_session.get('session_state', {})
    
    def save_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Save data to Flask session."""
        flask_session['session_state'] = data
        
    def user_exists(self, user_id: str) -> bool:
        """Check if user data exists in session."""
        return 'session_state' in flask_session

# src/app/game/storage/firestore_storage.py
from typing import Dict, Any
from firebase_admin import credentials, firestore, initialize_app
import os
from .storage_interface import UserStorageInterface

class FirestoreStorage(UserStorageInterface):
    """Stores user data in Firestore."""
    
    def __init__(self):
        """Initialize Firestore client."""
        self.db = self._initialize_firebase()
        
    def _initialize_firebase(self):
        """Initialize Firebase app and return Firestore client."""
        # Check if already initialized
        if len(firebase_admin._apps) > 0:
            return firestore.client()
        
        # Use environment variables for credentials in production
        # or service account file in development
        if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            cred = credentials.ApplicationDefault()
        else:
            # Path to service account file for local development
            cred = credentials.Certificate('path/to/serviceAccountKey.json')
        
        initialize_app(cred)
        return firestore.client()
    
    def _get_user_ref(self, user_id: str):
        """Get Firestore reference for a user."""
        return self.db.collection('users').document(user_id)
    
    def load_user_data(self, user_id: str) -> Dict[str, Any]:
        """Load user data from Firestore."""
        user_doc = self._get_user_ref(user_id).get()
        if user_doc.exists:
            return user_doc.to_dict() or {}
        return {}
    
    def save_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Save user data to Firestore."""
        data['last_updated'] = firestore.SERVER_TIMESTAMP
        self._get_user_ref(user_id).set(data, merge=True)
        
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists in Firestore."""
        return self._get_user_ref(user_id).get().exists
```

#### 2.2 Extended Session State and Manager

```python
# src/app/game/session_manager.py (modifications)
from typing import Dict, Set, Any, Optional, List
from flask import session as flask_session
import uuid
from datetime import datetime
from .storage.storage_interface import UserStorageInterface
from .storage.flask_session_storage import FlaskSessionStorage

class SessionState:
    """
    Represents the user-specific session state that needs to be persisted.
    This contains only the data that varies per user and needs to be stored.
    """
    def __init__(self):
        self.solved_quizzes: Set[str] = set()
        self.variable_mappings: Dict[str, Dict[str, str]] = {}
        self.quiz_attempts: List[Dict[str, Any]] = []  # New field for quiz attempts
    
    def reset(self):
        """Reset the session state."""
        self.solved_quizzes.clear()
        self.variable_mappings.clear()
        self.quiz_attempts.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the session state to a dictionary for serialization."""
        return {
            'solved_quizzes': list(self.solved_quizzes),
            'variable_mappings': self.variable_mappings,
            'quiz_attempts': self.quiz_attempts
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Restore the session state from a dictionary."""
        self.solved_quizzes = set(data.get('solved_quizzes', []))
        self.variable_mappings = data.get('variable_mappings', {})
        self.quiz_attempts = data.get('quiz_attempts', [])

class SessionManager:
    """
    Manages quiz session persistence and state.
    Uses a storage implementation to persist data.
    """
    
    def __init__(self, storage: Optional[UserStorageInterface] = None, user_id: Optional[str] = None):
        """
        Initialize the session manager.
        
        Args:
            storage: Storage implementation. Defaults to FlaskSessionStorage.
            user_id: User ID. If not provided, will be loaded from Flask session
                    or a new one will be generated.
        """
        self.storage = storage or FlaskSessionStorage()
        self.user_id = user_id or self._get_or_create_user_id()
        self.state = SessionState()
        self._load_state()
    
    def _get_or_create_user_id(self) -> str:
        """Get existing user ID from Flask session or create a new one."""
        if 'user_id' not in flask_session:
            flask_session['user_id'] = str(uuid.uuid4())
        return flask_session['user_id']
    
    def _load_state(self):
        """Load state from storage."""
        data = self.storage.load_user_data(self.user_id)
        if 'session_state' in data:
            self.state.from_dict(data['session_state'])
    
    def _save_state(self):
        """Save state to storage."""
        self.storage.save_user_data(self.user_id, {
            'session_state': self.state.to_dict()
        })
    
    def reset(self):
        """Reset the session state."""
        self.state.reset()
        self._save_state()
    
    def mark_quiz_solved(self, quiz_id: str):
        """Mark a quiz as solved."""
        self.state.solved_quizzes.add(quiz_id)
        self._save_state()
    
    def is_quiz_solved(self, quiz_id: str) -> bool:
        """Check if a quiz is solved."""
        return quiz_id in self.state.solved_quizzes
    
    @property
    def solved_quizzes(self) -> Set[str]:
        """Get the set of solved quizzes."""
        return self.state.solved_quizzes
    
    def get_variable_mappings(self, quiz_id: str) -> Dict[str, str]:
        """
        Get existing variable mappings for a quiz.
        """
        return self.state.variable_mappings.get(quiz_id, {})
    
    def set_variable_mappings(self, quiz_id: str, mappings: Dict[str, str]):
        """
        Set variable mappings for a quiz.
        """
        self.state.variable_mappings[quiz_id] = mappings
        self._save_state()
    
    def has_variable_mappings(self, quiz_id: str) -> bool:
        """
        Check if variable mappings exist for a quiz.
        """
        return quiz_id in self.state.variable_mappings
    
    @classmethod
    def load_from_flask_session(cls, storage: Optional[UserStorageInterface] = None) -> 'SessionManager':
        """
        Load session manager using user_id from Flask session.
        If no user_id exists, a new one is created.
        """
        # Get user ID from session or create new one
        if 'user_id' not in flask_session:
            flask_session['user_id'] = str(uuid.uuid4())
        
        # Create session manager with specified storage
        return cls(storage=storage, user_id=flask_session['user_id'])
    
    def save_to_flask_session(self):
        """
        Save user_id to Flask session and state to storage.
        """
        flask_session['user_id'] = self.user_id
        self._save_state()
        
    # New methods for quiz attempts
    
    def add_quiz_attempt(self, quiz_id: str, quiz_data: Dict[str, Any], score: int, total: int, completed: bool):
        """
        Record a quiz attempt with full quiz data.
        
        Args:
            quiz_id: The ID of the quiz
            quiz_data: Complete quiz data including equations, variables, solutions
            score: Number of points earned
            total: Total number of possible points
            completed: Whether the quiz was fully completed
        """
        self.state.quiz_attempts.append({
            'quiz_id': quiz_id,
            'timestamp': datetime.now().isoformat(),
            'score': score,
            'total': total,
            'completed': completed,
            'quiz_data': quiz_data,  # Store complete quiz data for restoration
        })
        self._save_state()
    
    def get_quiz_attempts(self) -> List[Dict[str, Any]]:
        """Get all quiz attempts."""
        return self.state.quiz_attempts
    
    def remove_quiz_attempt(self, timestamp: str):
        """Remove a quiz attempt by timestamp."""
        self.state.quiz_attempts = [
            attempt for attempt in self.state.quiz_attempts 
            if attempt.get('timestamp') != timestamp
        ]
        self._save_state()
```

#### 2.3 Session Factory Function

```python
# src/app/game/session_factory.py
from typing import Optional
from .session_manager import SessionManager
from .storage.firestore_storage import FirestoreStorage

def create_session_manager(use_firestore: bool = True) -> SessionManager:
    """
    Factory function to create a SessionManager with the appropriate storage.
    
    Args:
        use_firestore: Whether to use Firestore storage (True) or Flask session storage (False)
        
    Returns:
        SessionManager instance with the specified storage
    """
    storage = FirestoreStorage() if use_firestore else None
    return SessionManager.load_from_flask_session(storage=storage)
```

### 3. Implementation Tasks

#### 3.1 Firebase/Firestore Configuration

1. Add Firebase Admin SDK to requirements.txt:
   ```
   firebase-admin>=6.0.0
   ```

2. Set up Firebase project and enable Firestore:
   - Create a Firebase project in the Firebase console
   - Enable Firestore Database
   - Set up security rules for Firestore
   - Generate service account credentials JSON file
   - Configure environment variables for deployment

3. Create the storage module structure:
   ```
   src/app/game/storage/
   ├── __init__.py
   ├── storage_interface.py
   ├── flask_session_storage.py
   └── firestore_storage.py
   ```

#### 3.2 Session Manager Updates

1. Modify SessionState to include quiz attempts data structure
2. Update SessionManager to use the storage interface
3. Add new methods for quiz attempt management

#### 3.3 Application Route Updates

1. Update quiz route to handle missing quizzes:

```python
# src/app/app.py (modifications to quiz route)
@app.route('/quiz/<quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    quiz_session = get_quiz_session()
    
    # Check if quiz exists in current GAME_CONFIG
    quiz_exists = False
    is_random = quiz_id.startswith('random_')
    stored_quiz_data = None
    
    if is_random:
        # For random quizzes, we need to check the session data
        for attempt in quiz_session.session_manager.get_quiz_attempts():
            if attempt['quiz_id'] == quiz_id and 'quiz_data' in attempt:
                quiz_exists = True
                stored_quiz_data = attempt['quiz_data']
                break
    else:
        # For regular quizzes, check the GAME_CONFIG
        quiz_exists = quiz_id in GAME_CONFIG.quizzes
    
    if not quiz_exists:
        # Quiz no longer exists, show an error page
        return render_template('quiz_not_found.html', quiz_id=quiz_id)
    
    # For random quizzes, use the stored data
    if is_random and stored_quiz_data:
        # Reconstruct quiz from stored data
        view_model = QuizViewModel.from_random_quiz(stored_quiz_data, 
                                                    stored_quiz_data.get('pokemon_vars', {}))
        # ... rest of route handling
    else:
        # Normal quiz handling
        # ... existing code ...
```

2. Add My Quizzes route:

```python
@app.route('/my-quizzes')
def my_quizzes():
    quiz_session = get_quiz_session()
    attempts = quiz_session.session_manager.get_quiz_attempts()
    
    # Format attempts for display
    formatted_attempts = []
    for attempt in attempts:
        quiz_id = attempt.get('quiz_id')
        quiz_exists = False
        quiz_title = 'Unknown Quiz'
        
        # Check if it's a random quiz with stored data
        if quiz_id.startswith('random_') and 'quiz_data' in attempt:
            quiz_exists = True
            quiz_title = 'Random Exercise'
            quiz_data = attempt.get('quiz_data', {})
            if 'title' in quiz_data:
                quiz_title = quiz_data['title']
        else:
            # Check if regular quiz still exists
            quiz = GAME_CONFIG.quizzes.get(quiz_id)
            if quiz:
                quiz_exists = True
                quiz_title = quiz.title
        
        formatted_attempts.append({
            'id': quiz_id,
            'title': quiz_title,
            'timestamp': attempt.get('timestamp'),
            'score': f"{attempt.get('score')}/{attempt.get('total')}",
            'completed': attempt.get('completed'),
            'solved': quiz_session.session_manager.is_quiz_solved(quiz_id),
            'exists': quiz_exists  # Flag to indicate if quiz still exists
        })
    
    # Sort by timestamp, most recent first
    formatted_attempts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Calculate total stats
    total_attempts = len(formatted_attempts)
    total_solved = sum(1 for attempt in formatted_attempts if attempt['solved'])
    
    return render_template(
        'my_quizzes.html',
        attempts=formatted_attempts,
        stats={
            'total_attempts': total_attempts,
            'total_solved': total_solved
        }
    )
```

3. Add Forget Quiz route:

```python
@app.route('/forget-quiz', methods=['POST'])
def forget_quiz():
    quiz_session = get_quiz_session()
    timestamp = request.form.get('timestamp')
    
    if timestamp:
        quiz_session.session_manager.remove_quiz_attempt(timestamp)
    
    return redirect(url_for('my_quizzes'))
```

4. Update random quiz generation to store complete data:

```python
# When generating random quizzes
complete_quiz_data = {
    'quiz_id': random_quiz_id,
    'title': 'Random Exercise',
    'equations': equations,
    'solution': equation_solution,
    'difficulty': selected_difficulty,
    'parameters': {
        'operation_types': selected_difficulty.get('operations', []),
        'min_value': selected_difficulty.get('min_value', 1),
        'max_value': selected_difficulty.get('max_value', 10),
        'num_equations': selected_difficulty.get('num_equations', 3),
    },
    'pokemon_vars': pokemon_var_map,  # Store Pokemon mappings
    'timestamp': datetime.now().isoformat(),
    'is_random': True
}
```

5. Rename "All Exercises" to "Community Exercises":

```python
@app.route('/exercises')
def all_exercises():
    """Display all available exercises."""
    quiz_session = get_quiz_session()
    
    # Get a list of all quizzes with their completion status
    quizzes = []
    for quiz_id, quiz in GAME_CONFIG.quizzes.items():
        quizzes.append({
            'id': quiz_id,
            'title': quiz.title,
            'description': quiz.description,
            'is_solved': quiz_session.session_manager.is_quiz_solved(quiz_id)
        })
    
    return render_template('all_exercises.html', quizzes=quizzes, title="Community Exercises")
```

#### 3.4 UI Templates

1. Create My Quizzes template:

```html
<!-- src/templates/my_quizzes.html -->
{% extends "layout.html" %}

{% block title %}My Quizzes{% endblock %}

{% block content %}
<div class="container">
    <h1>My Quizzes</h1>
    
    <div class="summary-box">
        <h2>Summary</h2>
        <p>Total quizzes attempted: {{ stats.total_attempts }}</p>
        <p>Quizzes solved: {{ stats.total_solved }}</p>
    </div>
    
    {% if attempts %}
    <div class="quiz-list">
        {% for attempt in attempts %}
        <div class="quiz-card">
            <div class="quiz-info">
                <h3>{{ attempt.title }}</h3>
                <p>Date: {{ attempt.timestamp | datetime }}</p>
                <p>Score: {{ attempt.score }}</p>
                <p class="status">
                    {% if attempt.solved %}
                    <span class="solved">Solved</span>
                    {% else %}
                    <span class="unsolved">Not Solved</span>
                    {% endif %}
                </p>
                {% if not attempt.exists %}
                <p class="warning">This quiz is no longer available in the community exercises.</p>
                {% endif %}
            </div>
            <div class="quiz-actions">
                {% if attempt.exists %}
                <a href="{{ url_for('quiz', quiz_id=attempt.id) }}" class="btn btn-primary">Open</a>
                {% else %}
                <button disabled class="btn btn-primary disabled">Not Available</button>
                {% endif %}
                <form action="{{ url_for('forget_quiz') }}" method="post">
                    <input type="hidden" name="timestamp" value="{{ attempt.timestamp }}">
                    <button type="submit" class="btn btn-danger">Forget</button>
                </form>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="empty-state">
        <p>You haven't attempted any quizzes yet.</p>
        <a href="{{ url_for('all_exercises') }}" class="btn btn-primary">Browse Community Exercises</a>
    </div>
    {% endif %}
</div>
{% endblock %}
```

2. Create Quiz Not Found template:

```html
<!-- src/templates/quiz_not_found.html -->
{% extends "layout.html" %}

{% block title %}Quiz Not Found{% endblock %}

{% block content %}
<div class="container">
    <div class="error-message">
        <h1>Quiz Not Available</h1>
        <p>Sorry, the quiz you're looking for ({{ quiz_id }}) is no longer available in our community exercises.</p>
        <p>It may have been removed or updated.</p>
        
        <div class="actions">
            <a href="{{ url_for('all_exercises') }}" class="btn btn-primary">Browse Community Exercises</a>
            <a href="{{ url_for('my_quizzes') }}" class="btn btn-secondary">My Quizzes</a>
        </div>
    </div>
</div>
{% endblock %}
```

3. Update navigation in layout template:

```html
<!-- src/templates/layout.html (modifications) -->
<nav>
    <ul>
        <li><a href="{{ url_for('index') }}">Home</a></li>
        <li><a href="{{ url_for('all_exercises') }}">Community Exercises</a></li>
        <li><a href="{{ url_for('my_quizzes') }}">My Quizzes</a></li>
        <!-- Other navigation items -->
    </ul>
</nav>
```

### 4. Data Model (Firestore)

```
users/
  {user_id}/
    session_state:
      solved_quizzes: [quizId1, quizId2, ...]
      variable_mappings: {
        quizId1: { var1: val1, var2: val2, ... },
        quizId2: { ... }
      }
      quiz_attempts: [
        {
          quiz_id: "quizId1",
          timestamp: "2023-05-20T14:30:00",
          score: 3,
          total: 5,
          completed: true,
          quiz_data: {
            // Complete data to restore the quiz
            quiz_id: "quizId1",
            title: "Quiz Title",
            equations: ["eq1", "eq2"],
            solution: { var1: val1, var2: val2 },
            // For random quizzes
            is_random: true,
            parameters: { ... },
            pokemon_vars: { ... }
          }
        },
        // More attempt objects
      ]
    last_updated: timestamp
```

### 5. Implementation Timeline

#### Week 1: Foundation
- Set up Firebase project and Firestore
- Add Firebase Admin SDK to requirements
- Implement storage interface and implementations
- Update SessionState and SessionManager

#### Week 2: Application Integration
- Update app.py to use the new SessionManager with Firestore
- Implement quiz attempt handling and storage
- Test with local Firestore emulator

#### Week 3: UI Development
- Create My Quizzes page and template
- Implement Forget Quiz functionality
- Add Quiz Not Found page
- Update navigation and rename sections

#### Week 4: Testing and Refinement
- Write unit tests for storage implementations
- Test with Firebase production environment
- Refine UI and UX based on testing
- Fix any bugs or issues
- Document the implementation

### 6. Considerations and Future Work

1. **Error Handling**: Implement robust error handling for Firestore operations with fallback to Flask session if Firestore is unavailable.

2. **Performance Optimization**: Consider caching strategies for frequently accessed data to reduce Firestore reads.

3. **User Authentication**: When adding user authentication in the future, implement logic to merge anonymous user data with authenticated user accounts.

4. **Data Cleanup**: Implement periodic cleanup of old/unused data to keep storage requirements manageable.

5. **Pagination**: For users with many quiz attempts, implement pagination in the My Quizzes view.

6. **Offline Support**: Consider implementing offline support using service workers and IndexedDB for a better user experience. 