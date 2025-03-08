# Implementation Plan for Pokémon Adventure Game Progression System

## Overview
This plan outlines a progression system for our Pokémon-themed math adventure game, including Pokémon tiers, player XP/level mechanics, Pokémon appearance logic, catching mechanics, and UI feedback. Each checkpoint includes detailed instructions for data model extensions, UI changes, and formulas to implement the progression system within our existing codebase.

## Checkpoint 1: Pokémon Tier Assignment ✅
**Objective**: Extend the Pokémon data model to include tiers for rarity and power.

### Data Model Changes

1. **Update `Pokemon` class in `src/app/game/game_config.py`**:
   ```python
   @dataclass
   class Pokemon:
       name: str
       image_path: str
       tier: int = 1  # Default to tier 1 (common)
   ```

2. **Update `quizzes.json` in `src/data/`**:
   - Extend the Pokémon entries to include tier information:
   ```json
   "pokemons": {
     "pikachu": {
       "image_path": "pikachu.png",
       "tier": 2
     },
     "bulbasaur": {
       "image_path": "bulbasaur.png",
       "tier": 2
     },
     "charmander": {
       "image_path": "charmander.png",
       "tier": 2
     },
     "mew": {
       "image_path": "mew.png",
       "tier": 5
     },
     "squirtle": {
       "image_path": "squirtle.png",
       "tier": 2
     }
     // Add more Pokémon with tiers
   }
   ```

3. **Update `load_game_config()` in `src/app/game/game_config.py`**:
   ```python
   # Prepare Pokemon data
   pokemons = {}
   for name, pokemon_data in raw_data['pokemons'].items():
       # Handle both old and new format
       if isinstance(pokemon_data, str):
           # Old format: just image path
           pokemons[name] = Pokemon(name=name, image_path=pokemon_data)
       else:
           # New format: dictionary with image_path and tier
           pokemons[name] = Pokemon(
               name=name,
               image_path=pokemon_data.get('image_path', ''),
               tier=pokemon_data.get('tier', 1)
           )
   ```

### Testing
- ✅ Verify that every Pokémon in the database has a tier (1–5)
- ✅ Retrieve a few Pokémon programmatically to ensure the tier field is stored and accessible

## Checkpoint 2: Player Level and XP System
**Objective**: Add level and XP tracking for players with level-up mechanics.

### Data Model Changes

1. **Update `SessionState` class in `src/app/game/models.py`**:
   ```python
   @dataclass
   class SessionState:
       """Strongly typed model for session state."""
       solved_quizzes: Set[str] = field(default_factory=set)
       quiz_attempts: List[QuizAttempt] = field(default_factory=list)
       user_name: Optional[str] = None
       level: int = 1
       xp: int = 0
       caught_pokemon: Dict[str, int] = field(default_factory=dict)  # Pokemon ID -> count

       def to_dict(self) -> Dict[str, Any]:
           """Convert to dictionary for serialization."""
           return {
               'solved_quizzes': list(self.solved_quizzes),
               'quiz_attempts': [attempt.to_dict() for attempt in self.quiz_attempts],
               'user_name': self.user_name,
               'level': self.level,
               'xp': self.xp,
               'caught_pokemon': self.caught_pokemon
           }

       @classmethod
       def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
           """Create a SessionState instance from a dictionary."""
           quiz_attempts = [
               QuizAttempt.from_dict(attempt_data)
               for attempt_data in data.get('quiz_attempts', [])
           ]
           return cls(
               solved_quizzes=set(data.get('solved_quizzes', [])),
               quiz_attempts=quiz_attempts,
               user_name=data.get('user_name'),
               level=data.get('level', 1),
               xp=data.get('xp', 0),
               caught_pokemon=data.get('caught_pokemon', {})
           )
   ```

2. **Add XP and Level Management to `SessionManager` in `src/app/game/session_manager.py`**:
   ```python
   def calculate_xp_needed(self, level: int) -> int:
       """
       Calculate XP needed for the next level.
       
       Args:
           level: Current player level
           
       Returns:
           XP needed for next level
       """
       return int(100 * (1.2 ** (level - 1)))
   
   def add_xp(self, xp_amount: int) -> bool:
       """
       Add XP to the player and handle level-ups.
       
       Args:
           xp_amount: Amount of XP to add
           
       Returns:
           True if player leveled up, False otherwise
       """
       self.state.xp += xp_amount
       leveled_up = False
       
       # Check for level up
       while self.state.xp >= self.calculate_xp_needed(self.state.level):
           self.state.xp -= self.calculate_xp_needed(self.state.level)
           self.state.level += 1
           leveled_up = True
           
       self._save_state()
       return leveled_up
   
   def get_level_info(self) -> Dict[str, Any]:
       """
       Get player level information.
       
       Returns:
           Dictionary with level, current XP, and XP needed for next level
       """
       return {
           'level': self.state.level,
           'xp': self.state.xp,
           'xp_needed': self.calculate_xp_needed(self.state.level)
       }
   ```

### UI Changes

1. **Update `profile.html` in `src/templates/`**:
   - Add a section to display player level and XP progress
   ```html
   <div class="card mb-4">
     <div class="card-header">
       <h5 class="mb-0">Player Level</h5>
     </div>
     <div class="card-body">
       <div class="d-flex align-items-center mb-3">
         <h2 class="mb-0 me-2">Level {{ level_info.level }}</h2>
         <span class="text-muted">{{ level_info.xp }}/{{ level_info.xp_needed }} XP</span>
       </div>
       <div class="progress">
         <div class="progress-bar bg-success" role="progressbar" 
              style="width: {{ (level_info.xp / level_info.xp_needed * 100) | int }}%" 
              aria-valuenow="{{ level_info.xp }}" aria-valuemin="0" aria-valuemax="{{ level_info.xp_needed }}">
         </div>
       </div>
     </div>
   </div>
   ```

2. **Update the route handler for profile in `src/app/app.py`**:
   ```python
   @app.route('/profile')
   def profile():
       session_manager = SessionManager.load_from_storage()
       level_info = session_manager.get_level_info()
       
       return render_template(
           'profile.html',
           user_name=session_manager.get_user_name(),
           level_info=level_info
       )
   ```

### Testing
- Simulate XP gains and check if level increments correctly
- Verify UI updates reflect the current level and XP accurately

## Checkpoint 3: Pokémon Appearance Algorithm
**Objective**: Implement logic to select Pokémon based on player level and adventure difficulty.

### Logic Implementation

1. **Create a new file `src/app/game/pokemon_selector.py`**:
   ```python
   """
   Module for selecting Pokémon based on player level and adventure difficulty.
   """
   import random
   from typing import List, Dict, Any
   
   class PokemonSelector:
       """
       Handles the selection of Pokémon based on player level and adventure difficulty.
       """
       
       @staticmethod
       def get_eligible_tiers(player_level: int) -> List[int]:
           """
           Determine which Pokémon tiers are unlocked based on player level.
           
           Args:
               player_level: Current player level
               
           Returns:
               List of unlocked tier numbers
           """
           if player_level >= 41:
               return [1, 2, 3, 4, 5]
           elif player_level >= 31:
               return [1, 2, 3, 4]
           elif player_level >= 21:
               return [1, 2, 3]
           elif player_level >= 11:
               return [1, 2]
           else:
               return [1]
       
       @staticmethod
       def calculate_adjusted_weight(tier: int, difficulty: int) -> float:
           """
           Calculate the adjusted weight for a Pokémon based on its tier and adventure difficulty.
           
           Args:
               tier: Pokémon tier (1-5)
               difficulty: Adventure difficulty (1-7)
               
           Returns:
               Adjusted weight for random selection
           """
           # Base weights by tier
           base_weights = {1: 100, 2: 50, 3: 20, 4: 10, 5: 5}
           
           # Apply the formula: W_T × (1 + (D-1)/6 × (T-1))
           return base_weights[tier] * (1 + (difficulty - 1) / 6 * (tier - 1))
       
       @classmethod
       def select_pokemon(cls, pokemons: Dict[str, Any], player_level: int, difficulty: int, count: int = 1) -> List[str]:
           """
           Select Pokémon based on player level and adventure difficulty.
           
           Args:
               pokemons: Dictionary of all available Pokémon
               player_level: Current player level
               difficulty: Adventure difficulty (1-7)
               count: Number of Pokémon to select (default: 1)
               
           Returns:
               List of selected Pokémon IDs
           """
           eligible_tiers = cls.get_eligible_tiers(player_level)
           
           # Filter Pokémon by eligible tiers
           eligible_pokemon = {
               name: pokemon for name, pokemon in pokemons.items()
               if pokemon.tier in eligible_tiers
           }
           
           if not eligible_pokemon:
               return []
           
           # Calculate weights for each eligible Pokémon
           weights = {
               name: cls.calculate_adjusted_weight(pokemon.tier, difficulty)
               for name, pokemon in eligible_pokemon.items()
           }
           
           # Select Pokémon based on weights
           pokemon_names = list(weights.keys())
           pokemon_weights = [weights[name] for name in pokemon_names]
           
           # Ensure we don't try to select more than available
           count = min(count, len(pokemon_names))
           
           if count == 0:
               return []
           
           # Select Pokémon
           selected = random.choices(
               population=pokemon_names,
               weights=pokemon_weights,
               k=count
           )
           
           return selected
   ```

2. **Update `__init__.py` in `src/app/game/` to expose the new module**:
   ```python
   from src.app.game.game_config import load_game_config, load_equation_difficulties
   from src.app.game.game_manager import GameManager
   from src.app.game.session_manager import SessionManager
   from src.app.game.quiz_engine import QuizEngine
   from src.app.game.pokemon_selector import PokemonSelector
   ```

### Testing
- Create a test script to simulate adventures at various levels and difficulties
- Confirm only unlocked tiers appear and higher difficulties favor higher tiers

## Checkpoint 4: Catching Pokémon and Earning XP
**Objective**: Enable catching Pokémon and awarding XP with adventure completion bonuses.

### Logic Implementation

1. **Add Pokémon catching methods to `SessionManager` in `src/app/game/session_manager.py`**:
   ```python
   def catch_pokemon(self, pokemon_id: str) -> int:
       """
       Add a Pokémon to the player's caught list or increment its count.
       
       Args:
           pokemon_id: ID of the Pokémon to catch
           
       Returns:
           The new count for this Pokémon
       """
       current_count = self.state.caught_pokemon.get(pokemon_id, 0)
       new_count = current_count + 1
       self.state.caught_pokemon[pokemon_id] = new_count
       self._save_state()
       
       return new_count
   
   def get_caught_pokemon(self) -> Dict[str, int]:
       """
       Get the dictionary of caught Pokémon IDs and their counts.
       
       Returns:
           Dictionary mapping Pokémon IDs to catch counts
       """
       return self.state.caught_pokemon
   
   def calculate_xp_reward(self, caught_pokemon: List[str], difficulty: int, game_config) -> int:
       """
       Calculate XP reward for catching Pokémon and completing an adventure.
       
       Args:
           caught_pokemon: List of caught Pokémon IDs
           difficulty: Adventure difficulty (1-7)
           game_config: GameConfig object containing Pokémon data
           
       Returns:
           Total XP reward
       """
       # XP per Pokémon tier
       tier_xp = {1: 50, 2: 100, 3: 200, 4: 400, 5: 800}
       
       # Calculate XP for caught Pokémon
       pokemon_xp = 0
       for pokemon_id in caught_pokemon:
           if pokemon_id in game_config.pokemons:
               tier = game_config.pokemons[pokemon_id].tier
               pokemon_xp += tier_xp.get(tier, 50)
       
       # Add bonus XP for adventure completion
       bonus_xp = 50 * difficulty
       
       return pokemon_xp + bonus_xp
   ```

2. **Create a new route for adventure completion in `src/app/app.py`**:
   ```python
   @app.route('/adventure/complete', methods=['POST'])
   def complete_adventure():
       data = request.json
       difficulty = data.get('difficulty', 1)
       caught_pokemon = data.get('caught_pokemon', [])
       
       session_manager = SessionManager.load_from_storage()
       game_config = load_game_config(Path('src/data/quizzes.json'))
       
       # Record caught Pokémon and their new counts
       pokemon_counts = {}
       for pokemon_id in caught_pokemon:
           pokemon_counts[pokemon_id] = session_manager.catch_pokemon(pokemon_id)
       
       # Calculate and award XP
       xp_reward = session_manager.calculate_xp_reward(caught_pokemon, difficulty, game_config)
       leveled_up = session_manager.add_xp(xp_reward)
       
       # Get updated level info
       level_info = session_manager.get_level_info()
       
       return jsonify({
           'success': True,
           'xp_gained': xp_reward,
           'pokemon_counts': pokemon_counts,
           'leveled_up': leveled_up,
           'level_info': level_info
       })
   ```

3. **Create a new template `src/templates/adventure_results.html`**:
   ```html
   {% extends "base.html" %}
   
   {% block content %}
   <div class="container mt-4">
       <div class="card">
           <div class="card-header bg-success text-white">
               <h2 class="mb-0">Adventure Complete!</h2>
           </div>
           <div class="card-body">
               <h3 class="mb-4">Pokémon Caught</h3>
               
               <div class="row">
                   {% for pokemon in caught_pokemon %}
                   <div class="col-md-4 mb-4">
                       <div class="card">
                           <img src="{{ url_for('static', filename='images/' + pokemon.image_path) }}" 
                                class="card-img-top" alt="{{ pokemon.name }}">
                           <div class="card-body text-center">
                               <h5 class="card-title">{{ pokemon.name }}</h5>
                               <p class="card-text">Caught: {{ pokemon_counts[pokemon.id] }} times</p>
                               {% if pokemon_counts[pokemon.id] == 1 %}
                               <span class="badge bg-primary">First Catch!</span>
                               {% endif %}
                           </div>
                       </div>
                   </div>
                   {% endfor %}
               </div>
               
               <div class="alert alert-info mt-4">
                   <h4>XP Gained: {{ xp_gained }}</h4>
                   {% if leveled_up %}
                   <div class="alert alert-success mt-2">
                       <h5>Level Up! You are now Level {{ level_info.level }}</h5>
                   </div>
                   {% endif %}
                   
                   <div class="progress mt-3">
                       <div class="progress-bar bg-success" role="progressbar" 
                            style="width: {{ (level_info.xp / level_info.xp_needed * 100) | int }}%" 
                            aria-valuenow="{{ level_info.xp }}" aria-valuemin="0" aria-valuemax="{{ level_info.xp_needed }}">
                            {{ level_info.xp }}/{{ level_info.xp_needed }}
                       </div>
                   </div>
               </div>
               
               <div class="text-center mt-4">
                   <a href="{{ url_for('index') }}" class="btn btn-primary">Back to Home</a>
               </div>
           </div>
       </div>
   </div>
   {% endblock %}
   ```

### Testing
- Simulate catching Pokémon and verify XP totals
- Check UI for correct Pokémon listing and catch counts

## Checkpoint 5: UI Enhancements and Collection Display
**Objective**: Improve UI with collection stats and Pokémon collection display.

### UI Changes

1. **Update `profile.html` in `src/templates/` to show collection stats**:
   ```html
   <div class="card mb-4">
     <div class="card-header">
       <h5 class="mb-0">Pokémon Collection</h5>
     </div>
     <div class="card-body">
       <p>You have caught {{ total_unique_pokemon }} unique Pokémon out of {{ total_available_pokemon }} available.</p>
       <div class="progress mb-4">
         <div class="progress-bar bg-info" role="progressbar" 
              style="width: {{ (total_unique_pokemon / total_available_pokemon * 100) | int if total_available_pokemon > 0 else 0 }}%" 
              aria-valuenow="{{ total_unique_pokemon }}" aria-valuemin="0" aria-valuemax="{{ total_available_pokemon }}">
         </div>
       </div>
       
       <div class="row">
         {% for pokemon in collection %}
         <div class="col-md-3 mb-3">
           <div class="card">
             <img src="{{ url_for('static', filename='images/' + pokemon.image_path) }}" 
                  class="card-img-top" alt="{{ pokemon.name }}">
             <div class="card-body text-center">
               <h6 class="card-title">{{ pokemon.name }}</h6>
               <p class="card-text">Caught: {{ pokemon.count }} times</p>
             </div>
           </div>
         </div>
         {% endfor %}
       </div>
     </div>
   </div>
   ```

2. **Add collection stats to the profile route in `src/app/app.py`**:
   ```python
   @app.route('/profile')
   def profile():
       session_manager = SessionManager.load_from_storage()
       level_info = session_manager.get_level_info()
       
       # Get game config for Pokémon data
       game_config = load_game_config(Path('src/data/quizzes.json'))
       
       # Get caught Pokémon
       caught_pokemon = session_manager.get_caught_pokemon()
       
       # Prepare collection data for the template
       collection = []
       for pokemon_id, count in caught_pokemon.items():
           if pokemon_id in game_config.pokemons:
               pokemon = game_config.pokemons[pokemon_id]
               collection.append({
                   'id': pokemon_id,
                   'name': pokemon.name,
                   'image_path': pokemon.image_path,
                   'count': count
               })
       
       # Sort by name
       collection.sort(key=lambda p: p['name'])
       
       # Calculate totals
       total_unique_pokemon = len(caught_pokemon)
       total_available_pokemon = len(game_config.pokemons)
       
       return render_template(
           'profile.html',
           user_name=session_manager.get_user_name(),
           level_info=level_info,
           collection=collection,
           total_unique_pokemon=total_unique_pokemon,
           total_available_pokemon=total_available_pokemon
       )
   ```

### Testing
- Catch Pokémon and verify the collection display updates correctly
- Check that catch counts are displayed properly

## Checkpoint 6: Final Testing and Balancing
**Objective**: Test the full system and adjust for balance.

### Configuration Implementation

1. **Create a new file `src/app/game/progression_config.py`**:
   ```python
   """
   Configuration for the progression system.
   Contains adjustable parameters for XP, leveling, and Pokémon selection.
   """
   
   # XP formula multiplier (higher = more XP needed per level)
   XP_MULTIPLIER = 1.2
   
   # Base XP needed for level 1
   BASE_XP = 100
   
   # XP rewards per Pokémon tier
   TIER_XP_REWARDS = {
       1: 50,   # Common
       2: 100,  # Uncommon
       3: 200,  # Rare
       4: 400,  # Very Rare
       5: 800   # Legendary
   }
   
   # Base weights for Pokémon selection by tier
   TIER_BASE_WEIGHTS = {
       1: 100,  # Common
       2: 50,   # Uncommon
       3: 20,   # Rare
       4: 10,   # Very Rare
       5: 5     # Legendary
   }
   
   # Difficulty multiplier for tier weights
   DIFFICULTY_MULTIPLIER = 1/6
   
   # Tier unlock levels
   TIER_UNLOCK_LEVELS = {
       1: 1,    # Available from start
       2: 11,   # Unlock at level 11
       3: 21,   # Unlock at level 21
       4: 31,   # Unlock at level 31
       5: 41    # Unlock at level 41
   }
   
   # Bonus XP per difficulty level
   DIFFICULTY_BONUS_XP = 50
   ```

2. **Update the relevant methods to use these configuration values**:
   - Update `calculate_xp_needed` in `SessionManager`
   - Update `calculate_xp_reward` in `SessionManager`
   - Update `calculate_adjusted_weight` in `PokemonSelector`
   - Update `get_eligible_tiers` in `PokemonSelector`

### Testing
- Create a test script to simulate progression from Level 1 to 50
- Assess pacing (too fast/slow) and tier distribution (too common/rare)
- Adjust configuration values as needed based on testing results

## Implementation Notes

1. **Database Considerations**:
   - The current implementation uses the existing storage system (FlaskSessionStorage or FirestoreStorage)
   - No database schema changes are required beyond the SessionState model updates

2. **Performance Considerations**:
   - The Pokémon selection algorithm uses weighted random selection, which is efficient
   - XP calculations are simple and should not impact performance

3. **Security Considerations**:
   - All progression data is stored in the user's session, which is already secured
   - No additional security measures are needed

4. **Tier System Notes**:
   - Tiers are kept internal to the system and not exposed to users in the UI
   - They affect Pokémon appearance rates and XP rewards but are not directly shown

5. **Future Extensions**:
   - The tier system could be extended to include more properties (e.g., special abilities)
   - The progression system could be extended to include achievements or badges
``` 