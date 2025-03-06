"""
Equations Generator V2 - A Complete Rewrite

This module implements a flexible equation generator for various educational scenarios:
1. Basic Math - Simple equations with one unknown on the left side
2. Simple Quiz - Multiple unknowns with simple operations, integer solutions
3. Grade School - Configurable equations with multiple unknowns and operations

Design goals:
- Cleaner, more modular architecture
- Better configuration options
- No infinite solution equations
- Output format compatible with the original generator
"""

import random
from fractions import Fraction
from typing import List, Dict, Tuple, Set, Union, Optional, Any, NamedTuple, TypedDict, Literal
import sympy as sp


# TypedDict definitions for configuration parameters
class EquationPatternConfig(TypedDict, total=False):
    """Configuration for a specific equation pattern."""
    pattern: str  # Pattern with placeholders like {var1}, {var2}, {const}
    values: Dict[str, Union[int, float]]  # Optional fixed values for variables or constants


class BasicMathConfig(TypedDict, total=False):
    """Configuration for basic math equations."""
    type: Literal["basic_math"]  # Must be "basic_math"
    operations: List[str]  # Allowed operations ["+", "-", "*", "/"]
    max_value: int  # Maximum value for constants
    allow_decimals: bool  # Whether to allow decimal values
    elements: int  # Number of elements in the equation (e.g., 2 for x = a + b)
    random_seed: Optional[int]  # Optional random seed for reproducibility


class SimpleQuizConfig(TypedDict, total=False):
    """Configuration for simple quiz equations."""
    type: Literal["simple_quiz"]  # Must be "simple_quiz"
    num_unknowns: int  # Number of unknown variables
    max_value: int  # Maximum value for constants
    random_seed: Optional[int]  # Optional random seed for reproducibility


class GradeSchoolConfig(TypedDict, total=False):
    """Configuration for grade school equations."""
    type: Literal["grade_school"]  # Must be "grade_school"
    num_unknowns: int  # Number of unknown variables
    operations: List[str]  # Allowed operations ["+", "-", "*", "/"] 
    max_value: int  # Maximum value for constants
    allow_decimals: bool  # Whether to allow decimal values
    random_seed: Optional[int]  # Optional random seed for reproducibility


# Union type for all configuration types
EquationConfig = Union[BasicMathConfig, SimpleQuizConfig, GradeSchoolConfig]


class EquationV2(NamedTuple):
    """Representation of a generated equation for V2."""
    symbolic: Any  # SymPy equation
    formatted: str  # Human-readable format


class DynamicQuizSolutionV2(NamedTuple):
    """Representation of variable solutions for V2."""
    symbolic: Dict[Any, Union[int, float, Fraction]]  # SymPy symbols to values
    human_readable: Dict[str, Union[int, float, Fraction]]  # Variable names to values


class DynamicQuizV2(NamedTuple):
    """Complete quiz with equations and solutions for V2."""
    equations: List[EquationV2]
    solution: DynamicQuizSolutionV2


class EquationsGeneratorV2:
    """
    The V2 implementation of the equation generator.
    
    This class provides methods to generate different types of equation sets:
    - Basic math equations (one unknown, left side only)
    - Simple quiz equations (multiple unknowns, integer solutions)
    - Grade school equations (configurable unknowns and operations)
    
    All generation methods ensure that the resulting equations have exactly one solution.
    """
    
    def __init__(self):
        """Initialize the equation generator with default values."""
        self.variables = list('xyzwvu')
        self.operations = ['+', '-', '*', '/']
    
    def generate_basic_math(self, operations: Optional[List[str]] = None, 
                           max_value: int = 30, 
                           allow_decimals: bool = False, 
                           elements: int = 2,
                           random_seed: Optional[int] = None) -> DynamicQuizV2:
        """
        Generate a basic math equation with one unknown on the left side.
        
        Args:
            operations: List of allowed operations, defaults to ['+', '-']
            max_value: Maximum value for constants, defaults to 30
            allow_decimals: Whether to allow decimal values, defaults to False
            elements: Number of elements in the equation, defaults to 2 (x = a + b)
            random_seed: Optional random seed for reproducibility
            
        Returns:
            DynamicQuizV2: The generated quiz with equations and solution
        """
        # Set default operations if not provided
        if operations is None:
            operations = ['+', '-']
        
        # Set random seed if provided
        if random_seed is not None:
            random.seed(random_seed)
        
        # Create the variable symbol
        x = sp.Symbol('x')
        
        # Build the right side of the equation
        right_side_expr = None
        right_side_formatted = ""
        
        # Start with a random value for the first element
        if allow_decimals:
            first_value = round(random.uniform(1, max_value), 1)
        else:
            first_value = random.randint(1, max_value)
        
        right_side_expr = first_value
        right_side_formatted = str(first_value)
        
        # Add additional elements based on the specified number
        for i in range(elements - 1):
            # Choose a random operation from the allowed operations
            operation = random.choice(operations)
            
            # Generate a random value for the operand
            if allow_decimals:
                operand_value = round(random.uniform(1, max_value), 1)
            else:
                operand_value = random.randint(1, max_value)
            
            # Apply the operation to the right side expression
            if operation == '+':
                right_side_expr += operand_value
                right_side_formatted += f" + {operand_value}"
            elif operation == '-':
                right_side_expr -= operand_value
                right_side_formatted += f" - {operand_value}"
            elif operation == '*':
                right_side_expr *= operand_value
                right_side_formatted += f" * {operand_value}"
            elif operation == '/':
                # Ensure we don't divide by zero and result is clean
                if operand_value == 0:
                    operand_value = 1
                
                # If decimals are not allowed, ensure division results in an integer
                if not allow_decimals:
                    # Find a divisor that divides the current expression evenly
                    divisors = [i for i in range(1, min(11, max_value + 1)) if right_side_expr % i == 0]
                    if not divisors:
                        # If no clean divisors, switch to multiplication
                        right_side_expr *= operand_value
                        right_side_formatted += f" * {operand_value}"
                        continue
                    
                    operand_value = random.choice(divisors)
                
                right_side_expr /= operand_value
                right_side_formatted += f" / {operand_value}"
        
        # The solution for x is the value of the right side expression
        x_value = right_side_expr
        
        # Create the equation
        equation = sp.Eq(x, right_side_expr)
        formatted_equation = f"x = {right_side_formatted}"
        
        # Create the solution
        symbolic_solution = {x: x_value}
        human_readable_solution = {"x": x_value}
        
        # Create the quiz
        return DynamicQuizV2(
            equations=[EquationV2(equation, formatted_equation)],
            solution=DynamicQuizSolutionV2(
                symbolic=symbolic_solution,
                human_readable=human_readable_solution
            )
        )
    
    def generate_simple_quiz(self, 
                            num_unknowns: int = 2, 
                            max_value: int = 20,
                            random_seed: Optional[int] = None) -> DynamicQuizV2:
        """
        Generate a simple quiz with multiple unknowns and integer solutions.
        
        Simple quiz equations always use + and - operations only.
        Same symbol can be repeated in the same equation.
        Solution is always an integer.
        Number of equations equals number of unknowns.
        
        Args:
            num_unknowns: Number of unknown variables, defaults to 2
            max_value: Maximum value for constants, defaults to 20
            random_seed: Optional random seed for reproducibility
            
        Returns:
            DynamicQuizV2: The generated quiz with equations and solution
        """
        # Set random seed if provided
        if random_seed is not None:
            random.seed(random_seed)
        
        # Create the variable symbols
        var_symbols = [sp.Symbol(var) for var in self.variables[:num_unknowns]]
        
        # Generate random integer solutions for each variable
        solution_values = {}
        for i, var in enumerate(var_symbols):
            solution_values[var] = random.randint(1, max_value)
        
        # Create human-readable solution dictionary
        human_readable_solution = {str(var): value for var, value in solution_values.items()}
        
        # Generate equations with variable repetition
        equations = []
        formatted_equations = []
        
        for i in range(num_unknowns):
            # Choose a variable to repeat in this equation
            var_to_repeat = random.choice(var_symbols)
            var_name = str(var_to_repeat)
            
            # Decide how many times to repeat the variable (2-3 times)
            repetitions = random.randint(2, 3)
            
            # Create the left side of the equation with repeated variable
            left_side = repetitions * var_to_repeat
            
            # Create a formatted left side with explicit repetition
            formatted_left = " + ".join([var_name] * repetitions)
            
            # Calculate the right side value based on the solution
            right_side_value = repetitions * solution_values[var_to_repeat]
            
            # Sometimes mix in other variables (for equations after the first one)
            if i > 0 and random.random() > 0.3 and num_unknowns > 1:
                # Choose another variable different from the repeated one
                other_vars = [v for v in var_symbols if v != var_to_repeat]
                other_var = random.choice(other_vars)
                other_var_name = str(other_var)
                
                # Choose an operation (+ or -)
                operation = random.choice(['+', '-'])
                
                if operation == '+':
                    left_side += other_var
                    formatted_left += f" + {other_var_name}"
                    right_side_value += solution_values[other_var]
                else:
                    left_side -= other_var
                    formatted_left += f" - {other_var_name}"
                    right_side_value -= solution_values[other_var]
            
            # Create the equation
            equation = sp.Eq(left_side, right_side_value)
            equations.append(equation)
            
            # Format the equation for human readability
            formatted_equation = f"{formatted_left} = {right_side_value}"
            formatted_equations.append(formatted_equation)
        
        # Verify that the system has exactly one solution
        if num_unknowns > 1:
            # Convert equations to a matrix form to check linear independence
            A, b = sp.linear_eq_to_matrix(equations, var_symbols)
            
            # Check if the matrix has full rank (linearly independent equations)
            if A.rank() < len(var_symbols):
                # If not linearly independent, try again with a different set of equations
                return self.generate_simple_quiz(num_unknowns, max_value, random_seed)
            
            # Double-check by solving the system
            solutions = sp.solve(equations, var_symbols, dict=True)
            if len(solutions) != 1:
                # If not exactly one solution, try again
                return self.generate_simple_quiz(num_unknowns, max_value, random_seed)
        
        # Create equation objects
        equation_objects = [EquationV2(eq, fmt) for eq, fmt in zip(equations, formatted_equations)]
        
        # Create the quiz
        return DynamicQuizV2(
            equations=equation_objects,
            solution=DynamicQuizSolutionV2(
                symbolic=solution_values,
                human_readable=human_readable_solution
            )
        )
    
    def generate_grade_school(self, 
                             num_unknowns: int = 2, 
                             operations: Optional[List[str]] = None, 
                             max_value: int = 30, 
                             allow_decimals: bool = False) -> DynamicQuizV2:
        """
        Generate grade school equations with multiple unknowns.
        
        Grade school equations can use multiple unknowns and various operations.
        Number of equations equals number of unknowns.
        
        Args:
            num_unknowns: Number of unknown variables, defaults to 2
            operations: List of allowed operations, defaults to ['+', '-']
            max_value: Maximum value for constants, defaults to 30
            allow_decimals: Whether to allow decimal values, defaults to False
            
        Returns:
            DynamicQuizV2: The generated quiz with equations and solution
        """
        # Placeholder for actual implementation
        # This will be replaced with the real implementation later
        return DynamicQuizV2(
            equations=[
                EquationV2(None, "2*x = y + 3"),
                EquationV2(None, "y - x = 5"),
            ],
            solution=DynamicQuizSolutionV2(
                symbolic={},
                human_readable={"x": 2, "y": 7}
            )
        )
    
    def generate_equations(self, config: EquationConfig) -> DynamicQuizV2:
        """
        Generate equations based on a configuration dictionary.
        
        This is the main entry point for the V2 generator, allowing for a unified
        configuration-based approach to generating all types of equations.
        
        Args:
            config: A strongly-typed configuration dictionary with the following structure:
                For BasicMathConfig:
                {
                    "type": "basic_math",
                    "operations": ["+", "-", ...],  # Optional
                    "max_value": 30,  # Optional
                    "allow_decimals": False,  # Optional
                    "elements": 2,  # Optional
                    "random_seed": 12345  # Optional
                }
                
                For SimpleQuizConfig:
                {
                    "type": "simple_quiz",
                    "num_unknowns": 2,  # Optional
                    "max_value": 20,  # Optional
                    "random_seed": 12345  # Optional
                }
                
                For GradeSchoolConfig:
                {
                    "type": "grade_school",
                    "num_unknowns": 2,  # Optional
                    "operations": ["+", "-", ...],  # Optional
                    "max_value": 30,  # Optional
                    "allow_decimals": False,  # Optional
                    "random_seed": 12345  # Optional
                }
                
        Returns:
            DynamicQuizV2: The generated quiz with equations and solution
            
        Raises:
            ValueError: If the configuration is invalid
        """
        # Validate the configuration
        if "type" not in config:
            raise ValueError("Configuration must specify a 'type'")
            
        equation_type = config.get("type")
        
        # Set random seed if provided
        if "random_seed" in config and config["random_seed"] is not None:
            random_seed = config["random_seed"]
        else:
            random_seed = None
        
        if equation_type == "basic_math":
            return self.generate_basic_math(
                operations=config.get("operations", ["+", "-"]),
                max_value=config.get("max_value", 30),
                allow_decimals=config.get("allow_decimals", False),
                elements=config.get("elements", 2),
                random_seed=random_seed
            )
        elif equation_type == "simple_quiz":
            return self.generate_simple_quiz(
                num_unknowns=config.get("num_unknowns", 2),
                max_value=config.get("max_value", 20),
                random_seed=random_seed
            )
        elif equation_type == "grade_school":
            return self.generate_grade_school(
                num_unknowns=config.get("num_unknowns", 2),
                operations=config.get("operations", ["+", "-"]),
                max_value=config.get("max_value", 30),
                allow_decimals=config.get("allow_decimals", False)
            )
        else:
            raise ValueError(f"Unknown equation type: {equation_type}") 