"""
Progression management module.
Handles XP calculations, level-up logic, and progression-related functionality.
"""

from typing import Dict, List, Any, Optional
from src.app.game.progression_config import BASE_XP, XP_MULTIPLIER, TIER_XP_REWARDS, DIFFICULTY_BONUS_XP


class ProgressionManager:
    """
    Manages player progression, XP calculations, and level-up logic.
    This class is responsible for all progression-related functionality.
    """

    @staticmethod
    def calculate_xp_reward(caught_pokemon: List[str], difficulty: int, game_config) -> int:
        """
        Calculate XP reward for catching Pokémon and completing an adventure.
        
        Args:
            caught_pokemon: List of caught Pokémon IDs
            difficulty: Adventure difficulty (1-7)
            game_config: GameConfig object containing Pokémon data
            
        Returns:
            Total XP reward
        """
        # Calculate XP for caught Pokémon
        pokemon_xp = 0
        for pokemon_id in caught_pokemon:
            if pokemon_id in game_config.pokemons:
                tier = game_config.pokemons[pokemon_id].tier
                pokemon_xp += TIER_XP_REWARDS.get(tier, TIER_XP_REWARDS[1])  # Default to tier 1 reward

        # Add bonus XP for adventure completion
        bonus_xp = DIFFICULTY_BONUS_XP * difficulty

        return pokemon_xp + bonus_xp

    @staticmethod
    def calculate_xp_needed(level: int) -> int:
        """
        Calculate XP needed for the next level.
        
        Args:
            level: Current player level
            
        Returns:
            XP needed for next level
        """
        return int(BASE_XP * (XP_MULTIPLIER ** (level - 1)))

    @classmethod
    def process_level_up(cls, current_level: int, current_xp: int) -> Dict[str, Any]:
        """
        Process level-up logic based on current level and XP.
        
        Args:
            current_level: Current player level
            current_xp: Current player XP
            
        Returns:
            Dictionary with updated level, XP, and whether player leveled up
        """
        level = current_level
        xp = current_xp
        leveled_up = False

        # Check for level up
        while xp >= cls.calculate_xp_needed(level):
            xp -= cls.calculate_xp_needed(level)
            level += 1
            leveled_up = True

        return {
            'level': level,
            'xp': xp,
            'leveled_up': leveled_up
        }

    @classmethod
    def get_level_info(cls, level: int, xp: int) -> Dict[str, Any]:
        """
        Get player level information.
        
        Args:
            level: Current player level
            xp: Current player XP
            
        Returns:
            Dictionary with level, current XP, and XP needed for next level
        """
        return {
            'level': level,
            'xp': xp,
            'xp_needed': cls.calculate_xp_needed(level)
        } 