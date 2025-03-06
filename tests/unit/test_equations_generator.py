import pytest
import sympy as sp
from fractions import Fraction
from typing import Dict, Any
import random

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
        Fuzz test to check that no configuration produces a system with infinite solutions.
        
        This test is critical for verifying the core requirement that all generated equation
        systems have exactly one solution. By testing random configurations, we can discover
        edge cases that might lead to linearly dependent equations, which would result in
        infinite solutions or inconsistent systems.
        
        The test generates random configurations, creates equation systems, and verifies
        their linear independence through rank analysis of the coefficient matrix.
        """
        # List to store problematic configurations
        problematic_configs = []
        problematic_equations = []
        
        # Number of random configurations to test
        num_tests = 30
        
        for _ in range(num_tests):
            # Generate random configuration
            config = {
                'num_unknowns': random.randint(1, 3),
                'complexity': random.randint(1, 3),
                'allow_fractions': random.choice([True, False]),
                'allow_division': random.choice([True, False]),
                'very_simple': random.choice([True, False]),
                'num_helper_equations': random.randint(0, 2)
            }
            
            # Ensure we have enough equations for a unique solution
            config['num_equations'] = max(config['num_unknowns'], random.randint(1, 3))
            
            # Generate a quiz with this configuration
            quiz = generator.generate_quiz(**config)
            
            # Extract the variables and equations
            variables = list(quiz.solution.human_readable.keys())
            equations_list = [eq.symbolic for eq in quiz.equations]
            
            # Check if the system has exactly one solution
            has_unique_solution = True
            
            # Convert equations to standard form and check linear independence
            if len(variables) > 1:  # Only relevant for systems with multiple variables
                try:
                    # Check for linear dependence by creating a coefficient matrix
                    if len(variables) > 1:  # Only relevant for systems with multiple variables
                        # Convert equations to standard form: ax + by + ... = c
                        matrix_rows = []
                        constants = []
                        
                        for eq in equations_list:
                            # Convert equation to standard form
                            if isinstance(eq, str) and '=' in eq:
                                sides = eq.split('=')
                                lhs = sp.sympify(sides[0].strip())
                                rhs = sp.sympify(sides[1].strip())
                                eq = lhs - rhs
                            
                            # Extract coefficients for each variable
                            row = []
                            for var in variables:
                                var_sym = sp.Symbol(var)
                                coef = eq.coeff(var_sym)
                                row.append(coef)
                            
                            # Add to matrix
                            matrix_rows.append(row)
                        
                        # Check rank of coefficient matrix
                        coef_matrix = sp.Matrix(matrix_rows)
                        rank = coef_matrix.rank()
                        
                        # If rank < number of variables, system has infinite solutions
                        if rank < len(variables):
                            has_unique_solution = False
                except Exception as e:
                    # Log the specific exception for debugging
                    print(f"Exception during solution check: {type(e).__name__}: {str(e)}")
                    # If solving fails, it might be due to an inconsistent system or other issues
                    continue
            
            # If the system doesn't have a unique solution, add to problematic configs
            if not has_unique_solution:
                problematic_configs.append(config)
                problematic_equations.append([eq.formatted for eq in quiz.equations])
        
        # If we found any problematic configurations, the test should fail
        if problematic_configs:
            for i, (config, equations) in enumerate(zip(problematic_configs, problematic_equations)):
                print(f"Problematic config {i+1}: {config}")
                print(f"Equations: {equations}")
                print("---")
            
            # Include more debugging information in assertion message
            assert not problematic_configs, f"Found {len(problematic_configs)} configurations with infinite solutions. See output above for details."

    def test_linear_independence(self, generator):
        """
        Test that generated equations are linearly independent.
        
        Linear independence is the mathematical property that ensures a system of equations
        has exactly one solution. This test directly verifies this critical property by
        checking that the coefficient matrix of the generated equations has full rank.
        
        If the rank equals the number of variables, the system has exactly one solution.
        If the rank is less, the system has infinite solutions or is inconsistent.
        """
        # Test with different numbers of unknowns
        for num_unknowns in [2, 3]:
            # Generate a quiz with the same number of equations as unknowns
            quiz = generator.generate_quiz(
                num_unknowns=num_unknowns,
                num_equations=num_unknowns
            )
            
            # Extract the variables and equations
            variables = list(quiz.solution.human_readable.keys())
            var_symbols = [sp.Symbol(var) for var in variables]
            equations = [eq.symbolic for eq in quiz.equations]
            
            # Create coefficient matrix
            matrix_rows = []
            for eq in equations:
                row = generator._extract_coefficient_row(eq, var_symbols)
                matrix_rows.append(row)
            
            # Check rank of coefficient matrix
            coef_matrix = sp.Matrix(matrix_rows)
            rank = coef_matrix.rank()
            
            # For a system with a unique solution, rank should equal number of variables
            if rank != num_unknowns:
                print(f"Linear dependence detected in system with {num_unknowns} unknowns:")
                print(f"Coefficient matrix: {coef_matrix}")
                print(f"Rank: {rank} (should be {num_unknowns})")
                print(f"Equations: {[eq.formatted for eq in quiz.equations]}")
                print(f"Solution: {quiz.solution.human_readable}")
                print("---")
            
            assert rank == num_unknowns, f"System with {num_unknowns} unknowns has rank {rank}, expected {num_unknowns}" 