# Equation Generator CLI

A command-line interface for generating math equations of various difficulty levels.

## Overview

This CLI app reads difficulty configurations from the `equation_difficulties.json` file and generates math equations based on the specified options. It provides a simple way to generate practice equations for different grade levels and difficulty settings.

## Usage

```bash
# Generate 4 equations for each difficulty level
python -m src.app.equations.equation_cli

# Generate 10 equations for each difficulty level
python -m src.app.equations.equation_cli -c 10

# Generate equations for a specific difficulty level
python -m src.app.equations.equation_cli -d grade_3_4_medium

# List all available difficulty levels
python -m src.app.equations.equation_cli -l
```

## Command-line Options

- `-d, --difficulty`: Generate equations for a specific difficulty ID
- `-c, --count`: Number of equations to generate for each difficulty (default: 4)
- `-l, --list`: List all available difficulty levels

## Example Output

```
=== Basic 2 (Grade 3-4) (Difficulty Level: 6) ===

Equation 1:
  x + 2*y = 8
  3*x - y = 7

Solution:
  x = 3
  y = 2.5

Equation 2:
  ...
```

## Difficulty Levels

The app reads difficulty configurations from `src/data/equation_difficulties.json`. Each difficulty level has parameters that control the complexity of the generated equations, such as:

- Number of unknowns
- Number of equations
- Maximum number of elements
- Whether to use very simple equations
- Whether to ensure operations are included

To see all available difficulty levels, use the `-l` or `--list` option. 