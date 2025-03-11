# PokeMath Architecture Documentation

## Project Overview

PokeMath is an educational web application that gamifies math equation solving using Pokémon characters as variables in equations.

## Directory Structure

```
poke-math/
├── src/                     # Source code for the application
│   ├── app/                 # Main application code
│   │   ├── auth/            # Authentication module
│   │   ├── equations/       # Equation generation module
│   │   ├── firebase/        # Firebase configuration and utilities
│   │   ├── game/            # Game logic and state management
│   │   ├── storage/         # Storage implementations
│   │   ├── view_models.py   # Strongly typed view models for templates
│   │   └── app.py           # Flask application and routes
│   ├── data/                # Application data files
│   ├── static/              # Static assets
│   └── templates/           # HTML templates
├── tests/                   # Test files
├── infrastructure/          # Terraform infrastructure as code
└── docs/                    # Documentation files
```

## Core Modules

### Flask Web Application (`src/app/app.py`)
Entry point for the web application that handles HTTP requests, routes, and coordinates between modules.

### View Models (`src/app/view_models.py`)
Strongly typed view model classes used to pass data to templates, providing a type-safe interface between the application and views.

### Authentication Module (`src/app/auth/`)

#### Authentication Manager (`auth.py`)
Handles user authentication, registration, and session management.

### Firebase Module (`src/app/firebase/`)

#### Firebase Initialization (`firebase_init.py`)
Initializes and configures Firebase services for the application.

### Game Module (`src/app/game/`)

#### Game Manager (`game_manager.py`)
Manages game session state and coordinates user progress through quizzes.

#### Quiz Engine (`quiz_engine.py`)
Handles validation of user answers and quiz completion logic.

#### Game Configuration (`game_config.py`)
Loads quiz definitions and Pokémon data from JSON files.

#### Session Manager (`session_manager.py`)
Manages user session data and progress persistence.

#### Progression Manager (`progression_manager.py`)
Handles XP calculations, level-up logic, and progression-related functionality.

#### Models (`models.py`)
Data models and structures used throughout the game module.

### Storage Module (`src/app/storage/`)

- **Storage Interface** (`storage_interface.py`): Abstract base class for storage implementations.
- **Flask Session Storage** (`flask_session_storage.py`): Stores data in Flask session.
- **Firestore Storage** (`firestore_storage.py`): Stores data in Google Cloud Firestore.
- **Session Factory** (`session_factory.py`): Creates appropriate storage implementation.

### Equations Module (`src/app/equations/`)

#### Equations Generator V2 (`equations_generator_v2.py`)
Generates random mathematical equations based on difficulty settings

#### Equations Tests (`equations_tests.py`)
Contains internal tests for validating equation generation.

### Data Files (`src/data/`)

- **equation_difficulties_v2.json**: Configuration for equation difficulty levels using the V2 generator.
- **quizzes.json**: Predefined quiz structures and progression paths.

## Infrastructure (`infrastructure/`)
Terraform configuration files for GCP deployment.

## Testing (`tests/`)
Unit tests and test fixtures for application components.

## Data Flow

1. User accesses Flask route → loads game config → generates equations → manages game state → validates answers → persists session → returns results

## Key Abstractions

- **Quiz**: Set of equations with metadata
- **Equation**: Mathematical expression with Pokémon variables
- **Session**: User progress and history
- **Storage**: Session data persistence mechanism
- **Authentication**: User registration and login functionality
- **View Models**: Strongly typed data containers for template rendering

## Extension Points

1. **New Equation Types**: Add patterns to equation generator
2. **Additional Storage Backends**: Implement new storage interfaces
3. **New Quiz Types**: Extend quiz engine
4. **Difficulty Adjustments**: Modify JSON configurations 
5. **Authentication Methods**: Extend auth module with additional providers

## Documentation Maintenance Guidelines

When updating this documentation:

1. **Keep descriptions concise** - Aim for one-sentence descriptions per component
2. **Avoid listing functions** - Focus on purpose, not detailed functionality
3. **Use file paths** - Always include file paths for easy reference
4. **Maintain structure** - Preserve the hierarchical organization
5. **Document new modules** - Add new modules as they're created
6. **Remove obsolete entries** - Delete references to removed components
7. **Remember the purpose** - This document is a quick reference map, not comprehensive documentation
8. **Use arrows in workflows** - Use → in data flow descriptions for brevity
9. **Consider context limits** - Keep content minimal to avoid polluting AI context windows
10. **Only detail key abstractions** - Focus on core concepts, not implementation details 
11. **Note on planning documents** - Historical planning documents in the docs/plans/completed directory may contain outdated implementation details and file paths that don't reflect the current architecture 