import random
import sympy as sp
import numpy as np
from fractions import Fraction


class MathEquationGenerator:
    def __init__(self):
        self.variables = list('xyzwvu')
        self.operations = ['+', '-', '*']

    def generate_quiz(self, num_unknowns=1, num_equations=1,
                      allow_fractions=False, allow_division=False,
                      complexity=1, num_helper_equations=0):
        """
        Generate a system of equations with guaranteed solutions.

        Parameters:
        - num_unknowns: Number of variables (1-3)
        - num_equations: Number of primary equations
        - allow_fractions: Whether to include fractional coefficients
        - allow_division: Whether to include division operations
        - complexity: Level of complexity (1-3)
        - num_helper_equations: Number of redundant helper equations

        Returns:
        - dictionary with equations, solution, and formatted output
        """
        # Constrain parameters to valid ranges
        num_unknowns = min(max(1, num_unknowns), 3)
        complexity = min(max(1, complexity), 3)

        # Create variable symbols
        variables = self.variables[:num_unknowns]
        var_symbols = sp.symbols(variables)

        # Generate a solution (values for each variable)
        if allow_fractions:
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
        for _ in range(num_equations + num_helper_equations):
            equation = self._generate_equation(var_symbols, solution_dict,
                                               complexity, allow_division)
            equations.append(equation)

        # Format the output
        quiz_text = "Solve the following system of equations:\n\n"
        for i, eq in enumerate(equations, 1):
            quiz_text += f"Equation {i}: {eq}\n"

        solution_text = "Solution:\n"
        for var, val in solution.items():
            solution_text += f"{var} = {val}\n"

        return {
            "equations": equations,
            "symbolic_solution": solution_dict,
            "solution": solution,
            "quiz_text": quiz_text,
            "solution_text": solution_text
        }

    def _generate_equation(self, var_symbols, solution_dict, complexity, allow_division):
        """Generate a single equation that is satisfied by the solution."""
        # Start with a simple linear combination
        expr = 0

        # Add terms with each variable
        for var_symbol in var_symbols:
            # Coefficient complexity increases with level
            if complexity == 1:
                coef = random.choice([-2, -1, 1, 2])
            elif complexity == 2:
                coef = random.choice([-5, -3, -2, -1, 1, 2, 3, 5])
            else:  # complexity == 3
                coef = random.choice([-10, -7, -5, -3, -2, -1, 1, 2, 3, 5, 7, 10])

            term = coef * var_symbol
            expr += term

        # Calculate the right side by substituting the solution
        right_side = expr.subs(solution_dict)

        # For higher complexity, we can make the equation more interesting
        if complexity > 1:
            # Maybe move a term to the right side
            if random.random() > 0.5 and len(var_symbols) > 1:
                move_var = random.choice(var_symbols)
                coef = expr.coeff(move_var)
                expr -= coef * move_var
                right_side -= coef * solution_dict[move_var]

            # Add some constant terms
            const_term = random.randint(-5 * complexity, 5 * complexity)
            expr += const_term
            right_side += const_term

        # Format as an equation string
        equation = f"{expr} = {right_side}"

        # For division, we could rewrite as fractions
        if allow_division and random.random() > 0.5:
            # Multiply both sides by a divisor
            divisor = random.randint(2, 3 + complexity)
            equation = f"{expr * divisor} = {right_side * divisor}"
            # Then represent one side as division
            if random.random() > 0.5:
                equation = f"{expr * divisor} / {divisor} = {right_side}"
            else:
                equation = f"{expr} = {right_side * divisor} / {divisor}"

        return equation

    def generate_quiz_worksheet(self, num_problems=5, **kwargs):
        """Generate a complete worksheet with multiple problems."""
        worksheet = "MATH EQUATIONS WORKSHEET\n\n"
        solutions = "SOLUTIONS\n\n"

        for i in range(1, num_problems + 1):
            quiz = self.generate_quiz(**kwargs)
            worksheet += f"Problem {i}:\n{quiz['quiz_text']}\n\n"
            solutions += f"Problem {i}:\n{quiz['solution_text']}\n\n"

        return {
            "worksheet": worksheet,
            "solutions": solutions
        }


# Example usage
if __name__ == "__main__":
    generator = MathEquationGenerator()

    # Generate a basic single-variable equation
    print("Basic equation:")
    quiz = generator.generate_quiz(num_unknowns=1, complexity=1)
    print(quiz["quiz_text"])
    print(quiz["solution_text"])
    print("-" * 40)

    # Generate a more complex system with 2 unknowns and fractions
    print("More complex system:")
    quiz = generator.generate_quiz(
        num_unknowns=2,
        num_equations=2,
        allow_fractions=True,
        complexity=2
    )
    print(quiz["quiz_text"])
    print(quiz["solution_text"])
    print("-" * 40)

    # Generate a worksheet with multiple problems
    worksheet = generator.generate_quiz_worksheet(
        num_problems=3,
        num_unknowns=2,
        num_equations=2,
        allow_fractions=True,
        complexity=2,
        num_helper_equations=1
    )

    print("Sample worksheet:")
    print(worksheet["worksheet"])
    print("Sample solutions:")
    print(worksheet["solutions"])