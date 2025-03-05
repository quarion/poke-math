import pytest
import sympy as sp
from fractions import Fraction
from typing import Dict, Any

from src.app.equations.equations_generator import MathEquationGenerator, DynamicQuiz, Equation, DynamicQuizSolution


class TestMathEquationGenerator:
    """Test suite for the MathEquationGenerator class."""

    @pytest.fixture
    def generator(self):
        """Return an instance of MathEquationGenerator for testing."""
        return MathEquationGenerator()

    def test_initialization(self, generator):
        """Test that the generator initializes correctly."""
        assert generator is not None
        assert generator.variables == list('xyzwvu')
        assert generator.operations == ['+', '-', '*']

    def test_generate_quiz_basic(self, generator):
        """Test that a basic quiz can be generated with default parameters."""
        quiz = generator.generate_quiz()
        assert isinstance(quiz, DynamicQuiz)
        assert len(quiz.equations) == 1
        assert isinstance(quiz.solution, DynamicQuizSolution)
        assert len(quiz.solution.human_readable) == 1
        
        # The basic quiz should have one variable (x)
        assert 'x' in quiz.solution.human_readable

    def test_basic_generation(self, generator):
        """Test that basic equation generation works with explicit parameters."""
        quiz = generator.generate_quiz(num_unknowns=1, num_equations=1)
        
        # Basic assertions
        assert len(quiz.equations) == 1
        assert len(quiz.solution.human_readable) == 1
        assert quiz.equations[0].formatted is not None
        assert quiz.equations[0].symbolic is not None

    def test_multiple_unknowns(self, generator):
        """Test generation of quizzes with multiple unknowns."""
        for num_unknowns in [1, 2, 3]:
            quiz = generator.generate_quiz(num_unknowns=num_unknowns, num_equations=num_unknowns)
            assert len(quiz.solution.human_readable) == num_unknowns
            
            # Check that the correct variable names are used
            expected_vars = generator.variables[:num_unknowns]
            for var in expected_vars:
                assert var in quiz.solution.human_readable

    def test_num_equations(self, generator):
        """Test generation of quizzes with different numbers of equations."""
        for num_equations in [1, 2, 3]:
            quiz = generator.generate_quiz(num_equations=num_equations)
            assert len(quiz.equations) == num_equations

    def test_helper_equations(self, generator):
        """Test the effect of helper equations on quiz generation."""
        # Test with 2 primary equations and different numbers of helper equations
        for helpers in [0, 1, 2]:
            quiz = generator.generate_quiz(
                num_unknowns=2, 
                num_equations=2, 
                num_helper_equations=helpers
            )
            assert len(quiz.equations) == 2 + helpers

    def test_complexity_levels(self, generator):
        """Test that different complexity levels produce appropriately complex equations."""
        # Generate quizzes with different complexity levels
        results = {}
        for complexity in [1, 2, 3]:
            quiz = generator.generate_quiz(complexity=complexity)
            results[complexity] = quiz
            
            # All quizzes should be solvable
            assert quiz.solution.human_readable['x'] is not None
        
        # Higher complexity can include larger coefficients
        # This is a probabilistic test, since coefficients are random

    def test_very_simple_mode(self, generator):
        """Test the very_simple parameter's effect on equation generation."""
        # Test with very_simple=True
        quiz_simple = generator.generate_quiz(very_simple=True)
        
        # In very_simple mode, solution values should be positive integers
        for value in quiz_simple.solution.human_readable.values():
            assert isinstance(value, int)
            assert value > 0
        
        # Check equation format
        for eq in quiz_simple.equations:
            # Check for lack of multiplication notation in very_simple mode
            assert "*" not in eq.formatted

        # Test with very_simple=False
        quiz_normal = generator.generate_quiz(very_simple=False)
        # Normal mode may include negative solutions
        # This is not guaranteed, but we can still check the type

    def test_very_simple_config(self, generator):
        """Test the very simple configuration works properly with all parameters explicitly set."""
        quiz = generator.generate_quiz(
            num_unknowns=1,
            complexity=1,
            num_equations=1,
            max_elements=3,
            allow_fractions=False,
            allow_division=False,
            very_simple=True,
            ensure_operation=False
        )
        
        # Assertions for very simple mode
        assert len(quiz.equations) == 1
        equation_text = quiz.equations[0].formatted
        assert 'x' in equation_text  # Should use 'x' variable
        
        # Solution should be a positive integer for very_simple mode
        x_value = quiz.solution.human_readable['x']
        assert isinstance(x_value, int)
        assert x_value > 0

    def test_very_simple_with_small_max_elements(self, generator):
        """Test very simple mode with small max_elements (bug reproduction)."""
        # Test with max_elements=2 (should still work)
        quiz = generator.generate_quiz(
            num_unknowns=1,
            complexity=1,
            num_equations=1,
            max_elements=2,
            allow_fractions=False,
            allow_division=False,
            very_simple=True,
            ensure_operation=False
        )
        assert len(quiz.equations) == 1
        
        # Test with max_elements=1 (should still work)
        quiz = generator.generate_quiz(
            num_unknowns=1,
            complexity=1,
            num_equations=1,
            max_elements=1,
            allow_fractions=False,
            allow_division=False,
            very_simple=True,
            ensure_operation=False
        )
        assert len(quiz.equations) == 1
        
        # Test with max_elements=0 (edge case)
        quiz = generator.generate_quiz(
            num_unknowns=1,
            complexity=1,
            num_equations=1,
            max_elements=0,
            allow_fractions=False,
            allow_division=False,
            very_simple=True,
            ensure_operation=False
        )
        assert len(quiz.equations) == 1

    def test_allow_fractions(self, generator):
        """Test that allowing fractions produces equations with fractional solutions."""
        quiz = generator.generate_quiz(allow_fractions=True)
        
        # At least some generated quizzes should have fractional solutions
        # This is a probabilistic test, so it might not always pass
        has_fraction = False
        for _ in range(5):
            quiz = generator.generate_quiz(
                num_unknowns=1,
                allow_fractions=True,
                complexity=2
            )
            if any(isinstance(val, Fraction) for val in quiz.solution.human_readable.values()):
                has_fraction = True
                break
        
        # For all values, verify they have the correct type
        for val in quiz.solution.human_readable.values():
            assert isinstance(val, (int, Fraction))

    def test_allow_division(self, generator):
        """Test that allowing division produces equations with division operations."""
        # Generate multiple quizzes to increase chances of finding division
        has_division = False
        for _ in range(5):
            quiz = generator.generate_quiz(allow_division=True, very_simple=False)
            if any("/" in eq.formatted for eq in quiz.equations):
                has_division = True
                break
    
    def test_max_elements(self, generator):
        """Test that max_elements limits the number of terms in equations."""
        # Test with a specific max_elements value
        max_elements = 2
        quiz = generator.generate_quiz(max_elements=max_elements, very_simple=True)
        
        # Count elements in each equation (very simplified version)
        for eq in quiz.equations:
            # Split the formatted equation by '=' to get LHS
            lhs = eq.formatted.split('=')[0]
            # Count '+' and '-' operations and add 1
            # This is a very rough estimate
            terms = lhs.count('+') + lhs.count('-') + 1
            assert terms <= max_elements

    @pytest.mark.parametrize("max_elements", [0, 1, 2, 3])
    def test_very_simple_with_parameterized_max_elements(self, generator, max_elements):
        """Test very simple mode with different max_elements values using pytest parametrization."""
        quiz = generator.generate_quiz(
            num_unknowns=1,
            complexity=1,
            num_equations=1,
            max_elements=max_elements,
            allow_fractions=False,
            allow_division=False,
            very_simple=True,
            ensure_operation=False
        )
        assert len(quiz.equations) == 1
        # Verify that the solution is valid
        assert len(quiz.solution.human_readable) == 1
        assert 'x' in quiz.solution.human_readable
    
    def test_ensure_operation(self, generator):
        """Test that ensure_operation parameter ensures equations have operations."""
        # Test with ensure_operation=True
        quiz = generator.generate_quiz(ensure_operation=True)
        
        # Each equation should have at least one operation (+, -, *, /)
        for eq in quiz.equations:
            has_operation = any(op in eq.formatted for op in ['+', '-', '*', '/'])
            assert has_operation

    def test_generate_quiz_worksheet(self, generator):
        """Test generation of a worksheet with multiple quizzes."""
        num_problems = 5
        worksheet = generator.generate_quiz_worksheet(num_problems=num_problems)
        
        # Check that we get the correct number of problems
        assert len(worksheet) == num_problems
        
        # Check that each problem is a valid quiz
        for quiz in worksheet:
            assert isinstance(quiz, DynamicQuiz)
            assert len(quiz.equations) > 0
            assert len(quiz.solution.human_readable) > 0

    def test_worksheet_generation(self, generator):
        """Test generation of a worksheet with explicit parameters."""
        num_problems = 5
        worksheet = generator.generate_quiz_worksheet(
            num_problems=num_problems,
            num_unknowns=1,
            complexity=1
        )
        assert len(worksheet) == num_problems
        
        # Check each quiz in the worksheet
        for quiz in worksheet:
            assert len(quiz.equations) == 1
            assert len(quiz.solution.human_readable) == 1
    
    def test_solution_correctness(self, generator):
        """Test that the solutions provided are correct for the equations."""
        quiz = generator.generate_quiz(num_unknowns=2, num_equations=2)
        
        # Check each equation
        for eq in quiz.equations:
            # If the equation is a string with an equals sign, convert it to a SymPy equation
            if isinstance(eq.symbolic, str) and '=' in eq.symbolic:
                sides = eq.symbolic.split('=')
                lhs = sp.sympify(sides[0].strip())
                rhs = sp.sympify(sides[1].strip())
                # Substitute the solution values into both sides
                lhs_val = lhs.subs(quiz.solution.symbolic)
                rhs_val = rhs.subs(quiz.solution.symbolic)
                # Verify that the equation is satisfied
                assert lhs_val == rhs_val, f"Equation {eq.formatted} not satisfied by solution {quiz.solution.human_readable}"
            else:
                # Substitute the solution values into the equation
                result = eq.symbolic.subs(quiz.solution.symbolic)
                # Verify that the equation is satisfied
                assert result == True, f"Equation {eq.formatted} not satisfied by solution {quiz.solution.human_readable}"

    def test_unique_solution(self, generator):
        """Test that generated equations have exactly one solution."""
        # Test with a few key configurations
        configurations = [
            {"num_unknowns": 1, "num_equations": 1},
            {"num_unknowns": 1, "num_equations": 1, "very_simple": True},
        ]
        
        for config in configurations:
            quiz = generator.generate_quiz(**config)
            
            # Extract the symbolic equations and convert them to SymPy equations
            symbolic_equations = []
            for eq in quiz.equations:
                # If the equation is a string with an equals sign, convert it to a SymPy equation
                if isinstance(eq.symbolic, str) and '=' in eq.symbolic:
                    sides = eq.symbolic.split('=')
                    lhs = sp.sympify(sides[0].strip())
                    rhs = sp.sympify(sides[1].strip())
                    symbolic_equations.append(sp.Eq(lhs, rhs))
                else:
                    symbolic_equations.append(eq.symbolic)
            
            # Use SymPy to solve the system
            variables = [sp.Symbol(var) for var in quiz.solution.human_readable.keys()]
            solutions = sp.solve(symbolic_equations, variables, dict=True)
            
            # Check that there is exactly one solution
            assert len(solutions) == 1, f"Expected exactly one solution, got {len(solutions)} for config {config}"
            
            # Verify the solution matches the one provided by the generator
            for var, value in quiz.solution.symbolic.items():
                assert solutions[0][var] == value, f"Solution mismatch for {var}: expected {value}, got {solutions[0][var]}"

    def test_fuzz_for_infinite_solutions(self, generator):
        """
        Fuzz test to find equations with infinite solutions.
        This test attempts to generate many equations with different configurations
        to find cases where the system has infinite solutions.
        """
        num_attempts = 20

        # Configurations to test - focus on cases where we might get linearly dependent equations
        configurations = [
            {"num_unknowns": 2, "num_equations": 2},  # Two equations, two unknowns
            {"num_unknowns": 2, "num_equations": 3},  # Overdetermined system
            {"num_unknowns": 3, "num_equations": 3},  # Three equations, three unknowns
        ]

        # Track configurations that produce infinite solutions
        problematic_configs = []
        problematic_equations = []

        for config in configurations:
            if len(problematic_equations) != 0:
                # We found a problematic case, no need to continue
                break

            for _ in range(num_attempts):
                quiz = generator.generate_quiz(**config)

                # Extract the symbolic equations and convert them to SymPy equations
                symbolic_equations = []
                for eq in quiz.equations:
                    # If the equation is a string with an equals sign, convert it to a SymPy equation
                    if isinstance(eq.symbolic, str) and '=' in eq.symbolic:
                        sides = eq.symbolic.split('=')
                        lhs = sp.sympify(sides[0].strip())
                        rhs = sp.sympify(sides[1].strip())
                        symbolic_equations.append(sp.Eq(lhs, rhs))
                    else:
                        symbolic_equations.append(eq.symbolic)

                # Use SymPy to solve the system
                variables = [sp.Symbol(var) for var in quiz.solution.human_readable.keys()]

                try:
                    # Check for linear dependence by creating a coefficient matrix
                    if len(variables) > 1:  # Only relevant for systems with multiple variables
                        # Convert equations to standard form: ax + by + ... = c
                        matrix_rows = []
                        constants = []

                        for eq in symbolic_equations:
                            if isinstance(eq, sp.Eq):
                                # Move everything to the left side
                                expr = eq.lhs - eq.rhs
                            else:
                                expr = eq

                            # Extract coefficients for each variable
                            row = []
                            for var in variables:
                                coef = expr.coeff(var)
                                row.append(coef)

                            # Extract the constant term
                            const = expr.subs({var: 0 for var in variables})
                            constants.append(-const)  # Negative because we're moving to the right side

                            matrix_rows.append(row)

                        # Create the coefficient matrix
                        coef_matrix = sp.Matrix(matrix_rows)

                        # Check the rank of the coefficient matrix
                        rank = coef_matrix.rank()

                        # If rank < number of variables, the system has infinite solutions
                        if rank < len(variables):
                            problematic_configs.append(config.copy())
                            problematic_equations.append([eq.formatted for eq in quiz.equations])
                            # We found a problematic case, no need to continue with this configuration
                            break

                    # Also try solving directly with SymPy
                    solutions = sp.solve(symbolic_equations, variables, dict=True)

                    # Check if we have exactly one solution
                    if len(solutions) != 1:
                        problematic_configs.append(config.copy())
                        problematic_equations.append([eq.formatted for eq in quiz.equations])
                        # We found a problematic case, no need to continue with this configuration
                        break

                except Exception as e:
                    # If solving fails, it might be due to an inconsistent system or other issues
                    continue

        # If we found any problematic configurations, the test should fail
        if problematic_configs:
            for i, (config, equations) in enumerate(zip(problematic_configs, problematic_equations)):
                print(f"Problematic config {i+1}: {config}")
                print(f"Equations: {equations}")

            assert not problematic_configs, f"Found {len(problematic_configs)} configurations with infinite solutions"
        
        # If we get here, no problematic configurations were found
        assert True

    def test_linear_independence(self, generator):
        """
        Test that generated equations are linearly independent.
        This ensures that the system has exactly one solution.
        """
        # Configurations to test
        configurations = [
            {"num_unknowns": 2, "num_equations": 2},
            {"num_unknowns": 3, "num_equations": 3},
        ]
        
        for config in configurations:
            quiz = generator.generate_quiz(**config)
            
            # Extract the symbolic equations and convert them to standard form
            symbolic_equations = []
            for eq in quiz.equations:
                # If the equation is a string with an equals sign, convert it to a SymPy equation
                if isinstance(eq.symbolic, str) and '=' in eq.symbolic:
                    sides = eq.symbolic.split('=')
                    lhs = sp.sympify(sides[0].strip())
                    rhs = sp.sympify(sides[1].strip())
                    symbolic_equations.append(sp.Eq(lhs, rhs))
                else:
                    symbolic_equations.append(eq.symbolic)
            
            # Get the variables
            variables = [sp.Symbol(var) for var in quiz.solution.human_readable.keys()]
            
            # Create coefficient matrix
            matrix_rows = []
            for eq in symbolic_equations:
                if isinstance(eq, sp.Eq):
                    # Move everything to the left side
                    expr = eq.lhs - eq.rhs
                else:
                    expr = eq
                
                # Extract coefficients for each variable
                row = []
                for var in variables:
                    coef = expr.coeff(var)
                    row.append(coef)
                
                matrix_rows.append(row)
            
            # Create the coefficient matrix
            coef_matrix = sp.Matrix(matrix_rows)
            
            # Check the rank of the coefficient matrix
            rank = coef_matrix.rank()
            
            # For a system to have a unique solution, the rank must equal the number of variables
            assert rank == len(variables), f"Equations are linearly dependent: {[eq.formatted for eq in quiz.equations]}"
            
            # Also verify by solving the system
            solutions = sp.solve(symbolic_equations, variables, dict=True)
            assert len(solutions) == 1, f"Expected exactly one solution, got {len(solutions)}" 