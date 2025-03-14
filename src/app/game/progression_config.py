"""
Configuration for the progression system.
Contains adjustable parameters for XP, leveling, and Pokémon selection.
"""

# XP formula multiplier (higher = more XP needed per level)
XP_MULTIPLIER = 1.2

# Base XP needed for level 1
BASE_XP = 150

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
    1: 1,  # Common
    2: 2,   # Uncommon
    3: 3,   # Rare
    4: 5,   # Very Rare
    5: 8     # Legendary
}

# Difficulty multiplier for tier weights
DIFFICULTY_MULTIPLIER = 1/5

# Level multiplier for tier weights
LEVEL_MULTIPLIER = 1/4

# Tier unlock levels
TIER_UNLOCK_LEVELS = {
    1: 1,    # Available from start
    2: 11,   # Unlock at level 11
    3: 21,   # Unlock at level 21
    4: 31,   # Unlock at level 31
    5: 41    # Unlock at level 41
}

# Bonus XP per difficulty level
DIFFICULTY_BONUS_XP = 100