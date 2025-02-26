import random
from fractions import Fraction
from typing import List, Dict, Tuple, Set, Union, Optional, Any, NamedTuple

import sympy as sp


class Equation(NamedTuple):
    """Strongly typed representation of a generated equation."""
    symbolic: Any  # SymPy equation
    formatted: str  # Human-readable format


class DynamicQuizSolution(NamedTuple):
    """Strongly typed representation of variable solutions."""
    symbolic: Dict[Any, Union[int, Fraction]]  # SymPy symbols to values
    human_readable: Dict[str, Union[int, Fraction]]  # Variable names to values


class DynamicQuiz(NamedTuple):
    """Strongly typed representation of a complete quiz with equations and solutions."""
    equations: List[Equation]
    solution: DynamicQuizSolution


class MathEquationGenerator:
    def __init__(self):
        self.variables = list('xyzwvu')
        self.operations = ['+', '-', '*']

    def generate_quiz(self, num_unknowns: int = 1, num_equations: int = 1,
                      allow_fractions: bool = False, allow_division: bool = False,
                      complexity: int = 1, num_helper_equations: int = 0,
                      very_simple: bool = False, max_elements: Optional[int] = None,
                      ensure_operation: bool = True) -> DynamicQuiz:
        """
        Generate a system of equations with guaranteed solutions.

        Parameters:
        - num_unknowns: Number of variables (1-3)
        - num_equations: Number of primary equations
        - allow_fractions: Whether to include fractional coefficients
        - allow_division: Whether to include division operations
        - complexity: Level of complexity (1-3)
        - num_helper_equations: Number of redundant helper equations
        - very_simple: If True, uses repeated addition instead of multiplication
                      and avoids negative numbers and negative variable terms
        - max_elements: Maximum number of total elements (terms) in an equation.
                       This limits the sum of all variable terms and constants.
        - ensure_operation: If True, ensures each equation has at least one operation
                           (not just "x = 2")

        Returns:
        - Quiz object containing equations and solution
        """
        # Constrain parameters to valid ranges
        num_unknowns = min(max(1, num_unknowns), 3)
        complexity = min(max(1, complexity), 3)

        # Ensure we have enough equations for a unique solution
        if num_equations < num_unknowns:
            num_equations = num_unknowns

        # Create variable symbols
        variables = self.variables[:num_unknowns]
        var_symbols = sp.symbols(variables)

        # Generate a solution (values for each variable)
        if very_simple:
            # For very simple mode, only positive integers as solutions
            solution = {var: random.randint(1, 5) for var in variables}
        elif allow_fractions:
            # Create fractions with denominators based on complexity
            denominators = list(range(2, 2 + complexity))
            solution = {var: Fraction(random.randint(1, 5), random.choice(denominators))
                        for var in variables}
        else:
            # Integer solutions with range based on complexity
            max_val = 5 * complexity
            solution = {var: random.randint(-max_val, max_val) for var in variables}

        # Convert solution to SymPy symbols dictionary
        solution_dict = {sp.Symbol(var): val for var, val in solution.items()}

        # Generate the required number of equations
        equations = []
        formatted_equations = []
        coefficient_sets: Set[Tuple] = set()  # Track the coefficient sets to avoid duplicates

        attempt_count = 0
        max_attempts = 50  # Maximum attempts to generate unique equations

        while len(equations) < (num_equations + num_helper_equations) and attempt_count < max_attempts:
            attempt_count += 1

            equation, formatted_eq, coefficients, has_operation = self._generate_equation(
                var_symbols, solution_dict, complexity,
                allow_division, very_simple, max_elements
            )

            # If we need to ensure operations and this equation doesn't have any, skip it
            if ensure_operation and not has_operation:
                continue

            # Check if this is a unique equation (not linearly dependent on existing ones)
            if coefficients not in coefficient_sets:
                coefficient_sets.add(coefficients)
                equations.append(equation)
                formatted_equations.append(formatted_eq)

        # Create list of Equation objects
        equation_objects = [
            Equation(symbolic=eq, formatted=fmt)
            for eq, fmt in zip(equations, formatted_equations)
        ]

        # Create solution object
        quiz_solution = DynamicQuizSolution(
            symbolic=solution_dict,
            human_readable=solution
        )

        # Create and return Quiz object
        return DynamicQuiz(
            equations=equation_objects,
            solution=quiz_solution
        )

    def _generate_equation(self, var_symbols, solution_dict, complexity, allow_division, very_simple,
                           max_elements=None) -> Tuple[Any, str, Tuple, bool]:
        """
        Generate a single equation that is satisfied by the solution.
        Returns the equation, formatted equation, a coefficient tuple for uniqueness checking,
        and a boolean indicating if the equation contains at least one operation.
        """
        # Start with an empty expression
        expr = 0
        formatted_expr_parts = []
        coefficients = []  # Track coefficients for uniqueness checking
        element_count = 0  # Count total elements in the equation
        operations_count = 0  # Count operations in the equation

        # For very simple mode, we'll ensure we have at least one positive term
        # to avoid equations that start with negative terms
        if very_simple:
            # Determine how many elements we can use per variable
            if max_elements is not None:
                # Reserve at least one element for each variable and possibly one for a constant
                max_per_var = max(1, (max_elements - 1) // len(var_symbols))
            else:
                max_per_var = 3  # Default if no max_elements specified

            # Start with a positive term for the first variable
            first_var = var_symbols[0]

            # Ensure at least two terms for the first variable to guarantee an operation
            if len(var_symbols) == 1:
                # If only one variable, make sure to have at least 2 terms
                coef = random.randint(2, max_per_var)
            else:
                coef = random.randint(1, max_per_var)

            # Add repeated addition
            term = coef * first_var
            formatted_term = " + ".join([str(first_var)] * coef)
            formatted_expr_parts.append(formatted_term)
            expr += term
            coefficients.append((str(first_var), coef))
            element_count += coef

            # Each repetition after the first is an operation
            operations_count += (coef - 1)

            # Then process the rest of the variables
            for var_symbol in var_symbols[1:]:
                # Check if we're approaching the element limit
                remaining_elements = max_elements - element_count if max_elements else None

                # Skip if we've reached the element limit
                if remaining_elements is not None and remaining_elements <= 0:
                    break

                var_name = str(var_symbol)

                # For simplicity, let's just randomly choose between addition and subtraction
                operation = random.choice(['+', '-'])
                operations_count += 1  # Adding/subtracting a new variable is an operation

                # Limit coefficient based on remaining elements
                if remaining_elements is not None:
                    max_coef = min(max_per_var, remaining_elements)
                else:
                    max_coef = max_per_var

                # Use at least 1 element for each variable
                coef = random.randint(1, max(1, max_coef))

                if operation == '+':
                    # Addition - positive coefficient
                    term = coef * var_symbol
                    formatted_term = " + ".join([var_name] * coef)
                    formatted_expr_parts.append("+ " + formatted_term)
                    coefficients.append((var_name, coef))
                else:
                    # Subtraction - keep the variable positive but subtract it
                    term = -coef * var_symbol
                    formatted_term = " - ".join([""] + [var_name] * coef)
                    formatted_expr_parts.append(formatted_term)
                    coefficients.append((var_name, -coef))

                expr += term
                element_count += coef

                # Each repetition after the first is an additional operation
                operations_count += (coef - 1)
        else:
            # Regular mode - use standard algebraic notation
            # Determine how many variables we can include based on max_elements
            usable_vars = var_symbols
            if max_elements is not None:
                # Ensure we don't try to use more variables than max_elements
                usable_vars = var_symbols[:min(len(var_symbols), max_elements)]

            # Ensure we use at least two variables or add a constant term to guarantee an operation
            need_operation = True
            variable_count = 0

            for var_symbol in usable_vars:
                # Skip if we've reached the element limit
                if max_elements is not None and element_count >= max_elements:
                    break

                var_name = str(var_symbol)
                variable_count += 1

                # If this is the second or later variable, we've ensured an operation
                if variable_count >= 2:
                    need_operation = False
                    operations_count += 1  # Adding a second variable is an operation

                # Coefficient complexity increases with level
                if complexity == 1:
                    coef = random.choice([-2, -1, 1, 2])
                elif complexity == 2:
                    coef = random.choice([-5, -3, -2, -1, 1, 2, 3, 5])
                else:  # complexity == 3
                    coef = random.choice([-10, -7, -5, -3, -2, -1, 1, 2, 3, 5, 7, 10])

                # To ensure uniqueness, avoid zero coefficients
                if coef == 0:
                    coef = 1

                term = coef * var_symbol
                coefficients.append((var_name, coef))
                element_count += 1  # Each algebraic term counts as 1 element

                # Format the term
                if coef == 1:
                    formatted_term = var_name
                elif coef == -1:
                    formatted_term = f"-{var_name}"
                else:
                    formatted_term = f"{coef}*{var_name}"

                # Add to the list of terms
                if coef > 0 and formatted_expr_parts:  # Positive and not the first term
                    formatted_expr_parts.append(f"+ {formatted_term}")
                elif coef < 0 and formatted_expr_parts:  # Negative and not the first term
                    formatted_expr_parts.append(f"- {abs(coef)}*{var_name}")
                else:  # First term
                    formatted_expr_parts.append(formatted_term)

                expr += term

        # Calculate the right side by substituting the solution
        right_side = expr.subs(solution_dict)
        formatted_right_side = str(right_side)

        # For higher complexity, we can make the equation more interesting
        # only if we haven't reached max_elements
        if complexity > 1 and not very_simple and (max_elements is None or element_count < max_elements):
            # Maybe move a term to the right side
            if random.random() > 0.5 and len(var_symbols) > 1:
                move_var = random.choice(var_symbols)
                coef = expr.coeff(move_var)
                expr -= coef * move_var
                right_side -= coef * solution_dict[move_var]
                operations_count += 1  # Moving a term is an operation

                # Update coefficients for uniqueness checking
                coefficients = [(v, (c if v != str(move_var) else 0)) for v, c in coefficients]

                # Update the formatted expression (this is simplified for brevity)
                formatted_expr_parts = [str(expr)]
                formatted_right_side = str(right_side)

            # Add constant term only if element count allows
            if max_elements is None or element_count < max_elements:
                const_term = random.randint(-5 * complexity, 5 * complexity)
                if const_term != 0:  # Avoid adding 0
                    expr += const_term
                    right_side += const_term
                    coefficients.append(('const', const_term))
                    element_count += 1  # Constants count as 1 element
                    operations_count += 1  # Adding a constant is an operation

                    # Update formatted parts
                    if const_term > 0:
                        formatted_expr_parts.append(f"+ {const_term}")
                    elif const_term < 0:
                        formatted_expr_parts.append(f"- {abs(const_term)}")

                    formatted_right_side = str(right_side)
        elif very_simple and (max_elements is None or element_count < max_elements):
            # For very simple, we only add positive constants to keep things simple
            if operations_count == 0 or random.random() > 0.5:
                const_term = random.randint(1, 10)
                expr += const_term
                right_side += const_term
                formatted_expr_parts.append(f"+ {const_term}")
                formatted_right_side = str(right_side)
                coefficients.append(('const', const_term))
                element_count += 1  # Constants count as 1 element
                operations_count += 1  # Adding a constant is an operation

        # If there are still no operations and we have only one variable,
        # force a constant term to be added
        if operations_count == 0 and element_count < (max_elements or float('inf')):
            const_term = random.randint(1, 10)
            expr += const_term
            right_side += const_term
            if formatted_expr_parts:
                formatted_expr_parts.append(f"+ {const_term}")
            else:
                formatted_expr_parts.append(f"{const_term}")
            formatted_right_side = str(right_side)
            coefficients.append(('const', const_term))
            operations_count += 1

        # Clean up the formatted expression
        formatted_expr = " ".join(formatted_expr_parts).replace("+ -", "- ")
        if not formatted_expr:
            formatted_expr = "0"

        # Format as equation strings
        equation = f"{expr} = {right_side}"
        formatted_equation = f"{formatted_expr} = {formatted_right_side}"

        # For division, we could rewrite as fractions
        if allow_division and random.random() > 0.5 and not very_simple:
            # Multiply both sides by a divisor
            divisor = random.randint(2, 3 + complexity)
            equation = f"{expr * divisor} = {right_side * divisor}"
            # Then represent one side as division
            if random.random() > 0.5:
                equation = f"{expr * divisor} / {divisor} = {right_side}"
                formatted_equation = f"({expr * divisor}) / {divisor} = {formatted_right_side}"
            else:
                equation = f"{expr} = {right_side * divisor} / {divisor}"
                formatted_equation = f"{formatted_expr} = ({right_side * divisor}) / {divisor}"

            # Add divisor to coefficients for uniqueness checking
            coefficients.append(('divisor', divisor))
            operations_count += 1  # Division is an operation

        # Convert coefficients to a hashable form for uniqueness checking
        coefficient_tuple = tuple(sorted(coefficients))

        # Return whether this equation has at least one operation
        has_operation = operations_count > 0

        return equation, formatted_equation, coefficient_tuple, has_operation

    def generate_quiz_worksheet(self, num_problems: int = 5, **kwargs) -> List[DynamicQuiz]:
        """Generate a complete worksheet with multiple problems."""
        quizzes = []

        for _ in range(num_problems):
            quiz = self.generate_quiz(**kwargs)
            quizzes.append(quiz)

        return quizzes


# Example usage
if __name__ == "__main__":
    generator = MathEquationGenerator()

    # Define different difficulty configurations
    configrations_simple = [
        {
            "name": "Very Simple (Grade 1-2)",
            "params": {
                "num_unknowns": 1,
                "complexity": 1,
                "num_equations": 1,
                "max_elements": 3,
                "allow_fractions": False,
                "allow_division": False,
                "very_simple": True,
                "ensure_operation": False
            }
        },
        {
            "name": "Very Simple 2 (Grade 1-2)",
            "params": {
                "num_unknowns": 1,
                "num_equations": 1,
                "max_elements": 3,
                "complexity": 1,
                "allow_fractions": False,
                "allow_division": False,
                "very_simple": True,
                "ensure_operation": True
            }
        },
        {
            "name": "Very Simple 3 (Grade 1-2)",
            "params": {
                "num_unknowns": 1,
                "num_equations": 2,
                "max_elements": 3,
                "complexity": 1,
                "allow_fractions": False,
                "allow_division": False,
                "very_simple": True,
                "ensure_operation": True
            }
        },
        {
            "name": "Very Simple 4 (Grade 1-2)",
            "params": {
                "num_unknowns": 1,
                "num_equations": 2,
                "complexity": 1,
                "allow_fractions": False,
                "allow_division": False,
                "very_simple": True,
                "max_elements": 3,
                "ensure_operation": True
            }
        },
        {
            "name": "Basic (Grade 3-4)",
            "params": {
                "num_unknowns": 2,
                "num_equations": 2,
                "complexity": 1,
                "allow_fractions": False,
                "allow_division": False,
                "very_simple": False,
                "max_elements": 3,
                "ensure_operation": True
            }
        }
    ]

    configrations_advanced = [
        {
            "name": "Intermediate (Grade 5-6)",
            "params": {
                "num_unknowns": 1,
                "num_equations": 2,
                "complexity": 2,
                "allow_fractions": True,
                "allow_division": False,
                "very_simple": False,
                "max_elements": 5,  # Limit to 5 elements for intermediate equations
                "ensure_operation": True  # Ensure at least one operation
            }
        },
        {
            "name": "Advanced (Grade 7-8)",
            "params": {
                "num_unknowns": 2,
                "num_equations": 2,
                "complexity": 2,
                "allow_fractions": True,
                "allow_division": True,
                "very_simple": False,
                "max_elements": 6,  # Limit to 6 elements for advanced equations
                "ensure_operation": True  # Ensure at least one operation
            }
        },
        {
            "name": "Challenge (Grade 9+)",
            "params": {
                "num_unknowns": 3,
                "num_equations": 3,
                "complexity": 3,
                "allow_fractions": True,
                "allow_division": True,
                "very_simple": False,
                "num_helper_equations": 1,
                "max_elements": 8, # Limit to 8 elements for challenge equations
                "ensure_operation": True  # Ensure at least one operation
            }
        }
    ]

    # Generate and print examples for each difficulty level
    for config in configrations_simple:
        print(f"\n{'=' * 60}")
        print(f"DIFFICULTY LEVEL: {config['name']}")
        print(f"Settings: {config['params']}")
        print(f"{'-' * 60}")

        # Generate 4 examples for each difficulty
        for i in range(1, 5):
            quiz = generator.generate_quiz(**config['params'])
            print(f"\nExample {i}:")
            print(f"Equations:")
            for j, eq in enumerate(quiz.equations, 1):
                print(f"Equation {j}: {eq.formatted}")
            print("\nSolution:")
            for var, val in quiz.solution.human_readable.items():
                print(f"{var} = {val}")
            print(f"{'-' * 40}")

    # Test for single-variable equations to ensure they have operations
    print("\nTESTING SINGLE VARIABLE EQUATIONS WITH OPERATION REQUIREMENT:")
    for i in range(5):
        test_simple = generator.generate_quiz(
            num_unknowns=1,
            complexity=1,
            ensure_operation=True
        )
        print(f"Test {i + 1}:")
        for j, eq in enumerate(test_simple.equations, 1):
            print(f"Equation {j}: {eq.formatted}")
    print("-" * 40)

    # Test for a specific issue with duplicate equations
    print("\nTESTING SYSTEM OF EQUATIONS FOR UNIQUENESS:")
    test_system = generator.generate_quiz(
        num_unknowns=2,
        num_equations=2,
        complexity=2,
        max_elements=5  # Test with element limit
    )
    print("Equations:")
    for j, eq in enumerate(test_system.equations, 1):
        print(f"Equation {j}: {eq.formatted}")
    print("\nSolution:")
    for var, val in test_system.solution.human_readable.items():
        print(f"{var} = {val}")
    print("-" * 40)

    # Test with very simple equations and element limit
    print("\nTESTING VERY SIMPLE EQUATIONS WITH ELEMENT LIMIT:")
    test_simple = generator.generate_quiz(
        num_unknowns=2,
        complexity=1,
        very_simple=True,
        max_elements=3  # Limit to 3 elements total
    )
    print("Equations:")
    for j, eq in enumerate(test_simple.equations, 1):
        print(f"Equation {j}: {eq.formatted}")
    print("\nSolution:")
    for var, val in test_simple.solution.human_readable.items():
        print(f"{var} = {val}")
    print("-" * 40)