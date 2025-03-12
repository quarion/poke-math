#!/usr/bin/env python
"""
Progression Plotter Tool
------------------------
A tool for visualizing Pokémon tier distribution and XP curves in PokeMath.

This tool helps visualize:
1. The distribution of Pokémon tiers based on player level and difficulty
2. XP curves showing progression through levels

Usage:
    python progression_plotter.py tier --level 20 --difficulty 3
    python progression_plotter.py tier --level 20 --all-difficulties
    python progression_plotter.py xp --max-level 50
"""

import argparse
import sys
import os
import traceback
from typing import Dict, List, Tuple, Optional

# Add the project root to the Python path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Check for required packages
try:
    import numpy as np
    import matplotlib.pyplot as plt
except ImportError as e:
    print(f"Error: {e}")
    print("Please install the required packages with:")
    print("pip install matplotlib numpy")
    sys.exit(1)

# Import project modules
try:
    from src.app.game.progression_config import (
        TIER_BASE_WEIGHTS,
        DIFFICULTY_MULTIPLIER,
        TIER_UNLOCK_LEVELS,
        BASE_XP,
        XP_MULTIPLIER
    )
    from src.app.game.pokemon_selector import PokemonSelector
    from src.app.game.progression_manager import ProgressionManager
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)


def calculate_tier_distribution(player_level: int, difficulty: int) -> Dict[int, float]:
    """
    Calculate the probability distribution of Pokémon tiers for a given player level and difficulty.
    
    Args:
        player_level: Current player level
        difficulty: Adventure difficulty (1-7)
        
    Returns:
        Dictionary mapping tier to probability
    """
    # Get eligible tiers based on player level
    eligible_tiers = PokemonSelector.get_eligible_tiers(player_level)
    
    # Calculate weights for each eligible tier
    weights = {
        tier: PokemonSelector.calculate_adjusted_weight(tier, difficulty, player_level)
        for tier in eligible_tiers
    }
    
    # Calculate total weight
    total_weight = sum(weights.values())
    
    # Calculate probabilities
    probabilities = {
        tier: weight / total_weight
        for tier, weight in weights.items()
    }
    
    return probabilities


def calculate_xp_needed_per_level(max_level: int) -> List[int]:
    """
    Calculate XP needed for each level up to max_level.
    
    Args:
        max_level: Maximum level to calculate
        
    Returns:
        List of XP values needed for each level
    """
    return [ProgressionManager.calculate_xp_needed(level) for level in range(1, max_level + 1)]


def calculate_cumulative_xp(max_level: int) -> List[int]:
    """
    Calculate cumulative XP needed to reach each level.
    
    Args:
        max_level: Maximum level to calculate
        
    Returns:
        List of cumulative XP values
    """
    xp_per_level = calculate_xp_needed_per_level(max_level)
    cumulative_xp = []
    total = 0
    
    for xp in xp_per_level:
        total += xp
        cumulative_xp.append(total)
    
    return cumulative_xp


def plot_tier_distribution(player_level: int, difficulty: int = None, all_difficulties: bool = False) -> None:
    """
    Plot the distribution of Pokémon tiers for a given player level and difficulty.
    
    Args:
        player_level: Current player level
        difficulty: Adventure difficulty (1-7), or None if all_difficulties is True
        all_difficulties: Whether to plot for all difficulties
    """
    plt.figure(figsize=(10, 6))
    
    # Define colors for each difficulty
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    
    if all_difficulties:
        # Plot for all difficulties
        difficulties = range(1, 8)  # 1-7
        
        for i, diff in enumerate(difficulties):
            distribution = calculate_tier_distribution(player_level, diff)
            
            # Sort by tier
            tiers = sorted(distribution.keys())
            probabilities = [distribution[tier] for tier in tiers]
            
            plt.bar(
                [str(tier) for tier in tiers],
                probabilities,
                alpha=0.7,
                label=f'Difficulty {diff}',
                color=colors[i % len(colors)]
            )
            
        plt.title(f'Pokémon Tier Distribution at Level {player_level} (All Difficulties)')
        plt.legend()
        
    else:
        # Plot for a single difficulty
        if difficulty is None:
            difficulty = 4  # Default to middle difficulty
            
        distribution = calculate_tier_distribution(player_level, difficulty)
        
        # Sort by tier
        tiers = sorted(distribution.keys())
        probabilities = [distribution[tier] for tier in tiers]
        
        plt.bar(
            [str(tier) for tier in tiers],
            probabilities,
            color=colors[0]
        )
        
        plt.title(f'Pokémon Tier Distribution at Level {player_level}, Difficulty {difficulty}')
    
    # Add tier labels
    tier_labels = {
        1: "Common",
        2: "Uncommon",
        3: "Rare",
        4: "Very Rare",
        5: "Legendary"
    }
    
    plt.xlabel('Pokémon Tier')
    plt.ylabel('Probability')
    
    # Add tier names to x-axis
    plt.xticks(
        [str(tier) for tier in sorted(tier_labels.keys())],
        [f"{tier} - {tier_labels[tier]}" for tier in sorted(tier_labels.keys())]
    )
    
    plt.ylim(0, 1)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()


def plot_xp_curve(max_level: int) -> None:
    """
    Plot the XP curve showing XP needed for each level and cumulative XP.
    
    Args:
        max_level: Maximum level to plot
    """
    levels = list(range(1, max_level + 1))
    xp_per_level = calculate_xp_needed_per_level(max_level)
    cumulative_xp = calculate_cumulative_xp(max_level)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot XP needed per level
    ax1.plot(levels, xp_per_level, 'o-', color='#1f77b4', linewidth=2)
    ax1.set_title('XP Needed Per Level')
    ax1.set_xlabel('Level')
    ax1.set_ylabel('XP Needed')
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Plot cumulative XP
    ax2.plot(levels, cumulative_xp, 'o-', color='#ff7f0e', linewidth=2)
    ax2.set_title('Cumulative XP Needed')
    ax2.set_xlabel('Level')
    ax2.set_ylabel('Total XP')
    ax2.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()


def setup_tier_parser(subparsers):
    """Set up the parser for the tier distribution command."""
    tier_parser = subparsers.add_parser('tier', help='Plot Pokémon tier distribution')
    tier_parser.add_argument('--level', type=int, required=True,
                            help='Player level for tier distribution plot')
    tier_parser.add_argument('--difficulty', type=int, choices=range(1, 8),
                            help='Adventure difficulty (1-7) for tier distribution plot')
    tier_parser.add_argument('--all-difficulties', action='store_true',
                            help='Plot for all difficulties (1-7)')
    return tier_parser


def setup_xp_parser(subparsers):
    """Set up the parser for the XP curve command."""
    xp_parser = subparsers.add_parser('xp', help='Plot XP curves')
    xp_parser.add_argument('--max-level', type=int, default=50,
                          help='Maximum level for XP curve plot (default: 50)')
    return xp_parser


def main():
    """Main function to parse arguments and run the appropriate plotting function."""
    parser = argparse.ArgumentParser(
        description='Plot Pokémon tier distribution and XP curves.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('Usage:')[1]
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Set up subparsers for each command
    setup_tier_parser(subparsers)
    setup_xp_parser(subparsers)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'tier':
            if args.all_difficulties:
                plot_tier_distribution(args.level, all_difficulties=True)
            else:
                if args.difficulty is None:
                    print("Error: Either --difficulty or --all-difficulties is required for tier distribution plot")
                    print("Example: python progression_plotter.py tier --level 20 --difficulty 3")
                    print("Example: python progression_plotter.py tier --level 20 --all-difficulties")
                    return
                plot_tier_distribution(args.level, args.difficulty)
        
        elif args.command == 'xp':
            plot_xp_curve(args.max_level)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main()) 