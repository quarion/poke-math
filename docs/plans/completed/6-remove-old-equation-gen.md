# Implementation Plan: Replacing Equation Generator with V2

Based on the codebase search, here is a specific plan for replacing the old equation generator with the V2 version:

## Phase 1: Update the Equation Generator Class and Imports

1. **Update imports in src/app/app.py (line 27)**
   - Replace:
     ```python
     from src.app.equations.equations_generator import MathEquationGenerator
     ```
     with:
     ```python
     from src.app.equations.equations_generator_v2 import EquationsGeneratorV2
     ```

2. **Update generator instantiation in src/app/app.py (line 145)**
   - Replace:
     ```python
     EQUATION_GENERATOR = MathEquationGenerator()
     ```
     with:
     ```python
     EQUATION_GENERATOR = EquationsGeneratorV2()
     ```

## Phase 2: Update Configuration Path and Loading

3. **Update configuration path in src/app/app.py (line 141)**
   - Replace:
     ```python
     DIFFICULTY_CONFIG_PATH = Path(__file__).parent.parent / 'data' / 'equation_difficulties.json'
     ```
     with:
     ```python
     DIFFICULTY_CONFIG_PATH = Path(__file__).parent.parent / 'data' / 'equation_difficulties_v2.json'
     ```

4. **Ensure game_config.py can load the new format**
   - The `load_equation_difficulties` function in src/app/game/game_config.py (line 104-107) should work with the new format without changes, as it just loads the JSON

## Phase 3: Update Generator Usage in Quiz Engine

5. **Update quiz generation in src/app/game/quiz_engine.py (line 85-86)**
   - Replace:
     ```python
     # Generate a random equation using the MathEquationGenerator
     quiz = equation_generator.generate_quiz(**difficulty['params'])
     ```
     with:
     ```python
     # Generate a random equation using the EquationsGeneratorV2
     quiz = equation_generator.generate_equations(difficulty['params'])
     ```

6. **Update variable access in src/app/game/quiz_engine.py (line 102-120)**
   - Update to use the V2 quiz format:
     ```python
     # Assign a unique Pokemon to each variable
     for i, var in enumerate(quiz.solution.human_readable.keys()):
         # ... existing code ...
     
     # Format equations to ensure consistent variable format
     formatted_equations = []
     for eq in quiz.equations:
         formatted_eq = eq.formatted
         formatted_equations.append(formatted_eq)
     
     # Create quiz data structure
     quiz_data = {
         # ... existing code ...
         'solution': {var: str(val) for var, val in quiz.solution.human_readable.items()},
         # ... existing code ...
     }
     ```
   - No changes needed here if the structure of `DynamicQuizV2` matches `DynamicQuiz`

## Phase 4: Delete Old Files and Code

7. **Delete src/app/equations/equations_generator.py**
   - This file is no longer needed after the migration

8. **Delete src/data/equation_difficulties.json**
   - Replace with equation_difficulties_v2.json as the primary configuration file

9. **Delete tests/unit/test_equations_generator.py**
   - Remove the old test file as we don't want to maintain the old functionality

## Phase 5: Testing (Requires User Interaction)

10. **CHECKPOINT: Test generating random equations** (USER INTERACTION REQUIRED)
    - Navigate to the application's random equation generation feature
    - Test each difficulty level in equation_difficulties_v2.json
    - Verify that equations display correctly and have appropriate difficulty

11. **CHECKPOINT: Test equation solutions** (USER INTERACTION REQUIRED)
    - Solve generated equations to verify the solution checking works correctly
    - Test both correct and incorrect answers to verify feedback

12. **CHECKPOINT: Test UI integration** (USER INTERACTION REQUIRED)
    - Verify that the Pokemon images are correctly mapped to variables
    - Check that the equation formatting is correct and readable 