#!/usr/bin/env python
"""
Progression Plotter GUI
-----------------------
A graphical interface for visualizing Pokémon tier distribution and XP curves in PokeMath.

This tool provides a GUI for:
1. Visualizing the distribution of Pokémon tiers based on player level and difficulty
2. Visualizing XP curves showing progression through levels

Usage:
    python progression_plotter_gui.py
"""

import sys
import os
import traceback
from typing import Dict, List

# Add the project root to the Python path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Check for required packages
try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError as e:
    print(f"Error: {e}")
    print("Please install the required packages with:")
    print("pip install matplotlib numpy")
    print("Note: tkinter should be included with your Python installation.")
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
    """Calculate the probability distribution of Pokémon tiers."""
    eligible_tiers = PokemonSelector.get_eligible_tiers(player_level)
    
    weights = {
        tier: PokemonSelector.calculate_adjusted_weight(tier, difficulty, player_level)
        for tier in eligible_tiers
    }
    
    total_weight = sum(weights.values())
    
    probabilities = {
        tier: weight / total_weight
        for tier, weight in weights.items()
    }
    
    return probabilities


def calculate_xp_needed_per_level(max_level: int) -> List[int]:
    """Calculate XP needed for each level up to max_level."""
    return [ProgressionManager.calculate_xp_needed(level) for level in range(1, max_level + 1)]


def calculate_cumulative_xp(max_level: int) -> List[int]:
    """Calculate cumulative XP needed to reach each level."""
    xp_per_level = calculate_xp_needed_per_level(max_level)
    cumulative_xp = []
    total = 0
    
    for xp in xp_per_level:
        total += xp
        cumulative_xp.append(total)
    
    return cumulative_xp


class ProgressionPlotterApp:
    """Main application class for the Progression Plotter GUI."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PokeMath Progression Plotter")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set up the main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_control = ttk.Notebook(self.main_frame)
        
        self.tier_tab = ttk.Frame(self.tab_control)
        self.xp_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tier_tab, text="Tier Distribution")
        self.tab_control.add(self.xp_tab, text="XP Curves")
        
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Set up the tier distribution tab
        self.setup_tier_tab()
        
        # Set up the XP curves tab
        self.setup_xp_tab()
        
        # Add help menu
        self.create_menu()
    
    def create_menu(self):
        """Create the application menu."""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            "About PokeMath Progression Plotter",
            "PokeMath Progression Plotter\n\n"
            "A tool for visualizing Pokémon tier distribution and XP curves in PokeMath.\n\n"
            "This tool helps understand:\n"
            "1. The distribution of Pokémon tiers based on player level and difficulty\n"
            "2. XP curves showing progression through levels"
        )
    
    def setup_tier_tab(self):
        """Set up the tier distribution tab."""
        # Control frame
        control_frame = ttk.LabelFrame(self.tier_tab, text="Controls", padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Level selection
        ttk.Label(control_frame, text="Player Level:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.level_var = tk.IntVar(value=20)
        level_spinner = ttk.Spinbox(control_frame, from_=1, to=100, textvariable=self.level_var, width=5)
        level_spinner.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Difficulty selection
        ttk.Label(control_frame, text="Difficulty:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.difficulty_var = tk.IntVar(value=4)
        difficulty_spinner = ttk.Spinbox(control_frame, from_=1, to=7, textvariable=self.difficulty_var, width=5)
        difficulty_spinner.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # All difficulties checkbox
        self.all_difficulties_var = tk.BooleanVar(value=False)
        all_difficulties_check = ttk.Checkbutton(
            control_frame, 
            text="Show All Difficulties", 
            variable=self.all_difficulties_var
        )
        all_difficulties_check.grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        
        # Plot button
        plot_button = ttk.Button(control_frame, text="Plot", command=self.plot_tier_distribution)
        plot_button.grid(row=0, column=5, sticky=tk.E, padx=5, pady=5)
        
        # Figure frame
        self.tier_figure_frame = ttk.Frame(self.tier_tab)
        self.tier_figure_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create initial plot
        self.plot_tier_distribution()
    
    def setup_xp_tab(self):
        """Set up the XP curves tab."""
        # Control frame
        control_frame = ttk.LabelFrame(self.xp_tab, text="Controls", padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Max level selection
        ttk.Label(control_frame, text="Max Level:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_level_var = tk.IntVar(value=50)
        max_level_spinner = ttk.Spinbox(control_frame, from_=1, to=100, textvariable=self.max_level_var, width=5)
        max_level_spinner.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Plot button
        plot_button = ttk.Button(control_frame, text="Plot", command=self.plot_xp_curves)
        plot_button.grid(row=0, column=2, sticky=tk.E, padx=5, pady=5)
        
        # Figure frame
        self.xp_figure_frame = ttk.Frame(self.xp_tab)
        self.xp_figure_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create initial plot
        self.plot_xp_curves()
    
    def plot_tier_distribution(self):
        """Plot the tier distribution based on current settings."""
        try:
            # Clear previous plot
            for widget in self.tier_figure_frame.winfo_children():
                widget.destroy()
            
            # Get values from controls
            player_level = self.level_var.get()
            difficulty = self.difficulty_var.get()
            all_difficulties = self.all_difficulties_var.get()
            
            # Create figure
            fig = plt.Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
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
                    
                    ax.bar(
                        [str(tier) for tier in tiers],
                        probabilities,
                        alpha=0.7,
                        label=f'Difficulty {diff}',
                        color=colors[i % len(colors)]
                    )
                    
                ax.set_title(f'Pokémon Tier Distribution at Level {player_level} (All Difficulties)')
                ax.legend()
                
            else:
                # Plot for a single difficulty
                distribution = calculate_tier_distribution(player_level, difficulty)
                
                # Sort by tier
                tiers = sorted(distribution.keys())
                probabilities = [distribution[tier] for tier in tiers]
                
                ax.bar(
                    [str(tier) for tier in tiers],
                    probabilities,
                    color=colors[0]
                )
                
                ax.set_title(f'Pokémon Tier Distribution at Level {player_level}, Difficulty {difficulty}')
            
            # Add tier labels
            tier_labels = {
                1: "Common",
                2: "Uncommon",
                3: "Rare",
                4: "Very Rare",
                5: "Legendary"
            }
            
            ax.set_xlabel('Pokémon Tier')
            ax.set_ylabel('Probability')
            
            # Add tier names to x-axis
            ax.set_xticks([str(tier) for tier in sorted(tier_labels.keys())])
            ax.set_xticklabels([f"{tier} - {tier_labels[tier]}" for tier in sorted(tier_labels.keys())])
            
            ax.set_ylim(0, 1)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            fig.tight_layout()
            
            # Add the plot to the frame
            canvas = FigureCanvasTkAgg(fig, master=self.tier_figure_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while plotting tier distribution: {str(e)}")
            traceback.print_exc()
    
    def plot_xp_curves(self):
        """Plot the XP curves based on current settings."""
        try:
            # Clear previous plot
            for widget in self.xp_figure_frame.winfo_children():
                widget.destroy()
            
            # Get values from controls
            max_level = self.max_level_var.get()
            
            # Create figure
            fig = plt.Figure(figsize=(10, 6), dpi=100)
            
            # Plot XP needed per level
            ax1 = fig.add_subplot(121)
            levels = list(range(1, max_level + 1))
            xp_per_level = calculate_xp_needed_per_level(max_level)
            
            ax1.plot(levels, xp_per_level, 'o-', color='#1f77b4', linewidth=2)
            ax1.set_title('XP Needed Per Level')
            ax1.set_xlabel('Level')
            ax1.set_ylabel('XP Needed')
            ax1.grid(True, linestyle='--', alpha=0.7)
            
            # Plot cumulative XP
            ax2 = fig.add_subplot(122)
            cumulative_xp = calculate_cumulative_xp(max_level)
            
            ax2.plot(levels, cumulative_xp, 'o-', color='#ff7f0e', linewidth=2)
            ax2.set_title('Cumulative XP Needed')
            ax2.set_xlabel('Level')
            ax2.set_ylabel('Total XP')
            ax2.grid(True, linestyle='--', alpha=0.7)
            
            fig.tight_layout()
            
            # Add the plot to the frame
            canvas = FigureCanvasTkAgg(fig, master=self.xp_figure_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while plotting XP curves: {str(e)}")
            traceback.print_exc()


def main():
    """Main function to run the application."""
    try:
        root = tk.Tk()
        app = ProgressionPlotterApp(root)
        root.mainloop()
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main()) 