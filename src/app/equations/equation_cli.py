#!/usr/bin/env python
import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List

from src.app.equations.equations_generator_v2 import (
    DynamicQuizV2,
    EquationsGeneratorV2,
)


def load_difficulty_configs(json_path: str) -> List[Dict[str, Any]]:
    """
    Load difficulty configurations from a JSON file.
    
    Args:
        json_path: Path to the JSON file containing difficulty configurations
        
    Returns:
        List of difficulty configurations
    """
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find difficulty configuration file at {json_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_path}")
        sys.exit(1)


def format_value(value: Any) -> str:
    if isinstance(value, float):
        # Format float to 2 decimal places if it has decimal part
        if value.is_integer():
            return str(int(value))
        else:
            return f"{value:.2f}"
    return str(value)


def print_equation(quiz: DynamicQuizV2, index: int = 1, config_type: str = None) -> None:
    """
    Print a formatted equation and its solution.
    
    Args:
        quiz: The generated quiz containing equations and solutions
        index: The equation number (for display purposes)
        config_type: The type of configuration used to generate the equations
    """
    print(f"\nEquation {index}:")
    for _i, eq in enumerate(quiz.equations):
        # Clean up the equation formatting for better display
        formatted_eq = eq.formatted
        
        # Replace decimal values with cleaner format
        if '.' in formatted_eq:
            # Find all decimal numbers and format them
            decimal_pattern = r'(\d+\.\d+)'
            formatted_eq = re.sub(decimal_pattern, lambda m: format_value(float(m.group(1))), formatted_eq)
        
        print(f"  {formatted_eq}")
    
    print("\nSolution:")
    for var, value in quiz.solution.human_readable.items():
        print(f"  {var} = {format_value(value)}")
    print()


def generate_equations(difficulty_configs: List[Dict[str, Any]], 
                      difficulty_id: str = None, 
                      count: int = 4) -> None:
    """
    Generate equations based on difficulty configurations.
    
    Args:
        difficulty_configs: List of difficulty configurations
        difficulty_id: ID of the specific difficulty to generate (None for all)
        count: Number of equations to generate for each difficulty
    """
    generator = EquationsGeneratorV2()
    
    # Filter configurations based on difficulty_id if provided
    if difficulty_id:
        configs = [config for config in difficulty_configs if config["id"] == difficulty_id]
        if not configs:
            print(f"Error: No difficulty found with ID '{difficulty_id}'")
            print("Available difficulty IDs:")
            for config in difficulty_configs:
                print(f"  - {config['id']} ({config['name']})")
            sys.exit(1)
    else:
        configs = difficulty_configs
    
    # Generate equations for each selected difficulty
    for config in configs:
        print(f"\n=== {config['name']} (Difficulty Level: {config['difficulty']}) ===")
        
        # Get the configuration type
        config_type = config["params"].get("type", "")
        
        for i in range(count):
            # Use the v2 generator's generate_equations method with the params
            quiz = generator.generate_equations(config["params"])
            print_equation(quiz, i + 1, config_type)
        
        print("-" * 60)


def main():
    """Main entry point for the CLI application."""
    # Define the path to the difficulty configurations
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                            "data", "equation_difficulties_v2.json")
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate math equations based on difficulty levels")
    parser.add_argument("-d", "--difficulty", 
                        help="Generate equations for a specific difficulty ID")
    parser.add_argument("-c", "--count", type=int, default=4,
                        help="Number of equations to generate for each difficulty (default: 4)")
    parser.add_argument("-l", "--list", action="store_true",
                        help="List all available difficulty levels")
    
    args = parser.parse_args()
    
    # Load difficulty configurations
    difficulty_configs = load_difficulty_configs(json_path)
    
    # List available difficulties if requested
    if args.list:
        print("Available difficulty levels:")
        for config in difficulty_configs:
            print(f"  - {config['id']}: {config['name']} (Level {config['difficulty']})")
        sys.exit(0)
    
    # Generate equations
    generate_equations(difficulty_configs, args.difficulty, args.count)


if __name__ == "__main__":
    main() 