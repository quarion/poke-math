"""
Module for selecting Pokémon based on player level and adventure difficulty.
"""
import random
from typing import Any, Dict, List

from src.app.game.progression_config import (
    DIFFICULTY_MULTIPLIER,
    LEVEL_MULTIPLIER,
    TIER_BASE_WEIGHTS,
    TIER_UNLOCK_LEVELS,
)


class PokemonSelector:
    """
    Handles the selection of Pokémon based on player level and adventure difficulty.
    """
    
    @staticmethod
    def get_eligible_tiers(player_level: int) -> List[int]:
        """
        Determine which Pokémon tiers are unlocked based on player level.
        """
        eligible_tiers = []
        for tier, unlock_level in TIER_UNLOCK_LEVELS.items():
            if player_level >= unlock_level:
                eligible_tiers.append(tier)
        return sorted(eligible_tiers)
    
    @staticmethod
    def calculate_adjusted_weight(tier: int, difficulty: int, player_level: int = 1) -> float:
        """
        Calculate the adjusted weight for a Pokémon based on its tier, adventure difficulty, and player level.
        
        Args:
            tier: Pokémon tier (1-5)
            difficulty: Adventure difficulty (1-7)
            player_level: Player level (default: 1)
            
        Returns:
            Adjusted weight for random selection
        """
        # Apply the formula: W_T × (1 + (D-1)/6 × (T-1) + L/50 × (T-1))
        # Where:
        # - W_T is the base weight for tier T
        # - D is the difficulty level (1-7)
        # - L is the player level
        # - T is the Pokémon tier (1-5)
        
        # For tier 1, always return the base weight regardless of difficulty or level
        if tier == 1:
            return TIER_BASE_WEIGHTS[tier]
            
        # For other tiers, apply the formula
        return TIER_BASE_WEIGHTS[tier] * (1 + (difficulty - 1) * DIFFICULTY_MULTIPLIER * (tier - 1) +
                                          (player_level - 10) * LEVEL_MULTIPLIER * (tier - 1))
    
    @classmethod
    def select_pokemon(cls, pokemons: Dict[str, Any], player_level: int, difficulty: int, count: int = 1) -> List[str]:
        """
        Select Pokémon based on player level and adventure difficulty.
        Pokemon will be only select from eligible tiers, based on level
        From all eligible pokemon they will be selected based on their weight - on lower level and with lower difficulty
        common pokemon are more likely, with higher level and higher difficulty more rare pokemon start to appear
        
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
            name: cls.calculate_adjusted_weight(pokemon.tier, difficulty, player_level)
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