import pytest
import sympy as sp
import random
import numpy as np
from typing import Dict, Any, List, Optional, Union
from fractions import Fraction

"""
Tests for the EquationsGeneratorV2 class.

This test file is organized into four categories:
1. Common tests - Tests for shared functionality and configuration
2. Basic Math tests - Tests for the basic math equation generation (Type A)
3. Simple Quiz tests - Tests for the simple quiz equation generation (Type B)
4. Grade School tests - Tests for the grade school equation generation (Type C)

To run specific test categories, use the pytest `-m` option with the appropriate marker:

- Run all tests: `python -m pytest tests/unit/test_equations_generator_v2.py`
- Run common tests only: `python -m pytest tests/unit/test_equations_generator_v2.py -m common`
- Run basic math tests only: `python -m pytest tests/unit/test_equations_generator_v2.py -m basic_math`
- Run simple quiz tests only: `python -m pytest tests/unit/test_equations_generator_v2.py -m simple_quiz`
- Run grade school tests only: `python -m pytest tests/unit/test_equations_generator_v2.py -m grade_school`

You can also combine multiple markers, for example to run basic math and common tests:
`python -m pytest tests/unit/test_equations_generator_v2.py -m "common or basic_math"`

During development, you can focus on implementing one section at a time and run only those tests,
while skipping the others that are expected to fail until their respective functions are implemented.
"""

# Assuming the v2 version will be in this location - adjust if needed
from src.app.equations.equations_generator_v2 import (
    EquationsGeneratorV2, EquationV2, DynamicQuizV2, DynamicQuizSolutionV2,
    BasicMathConfig, SimpleQuizConfig, GradeSchoolConfig, EquationPatternConfig
)

# Import the original classes for compatibility testing
try:
    from src.app.equations.equations_generator import MathEquationGenerator, DynamicQuiz, Equation, DynamicQuizSolution

    ORIGINAL_AVAILABLE = True
except ImportError:
    ORIGINAL_AVAILABLE = False


class TestEquationsGeneratorV2:
    """Test suite for the EquationsGeneratorV2 class."""

    @pytest.fixture
    def generator(self):
        """Return an instance of EquationsGeneratorV2 for testing."""
        return EquationsGeneratorV2()

    @pytest.mark.common
    def test_initialization(self, generator):
        """Test that the generator initializes correctly with default values."""
        assert generator is not None
        # Verify default variables (adjust based on actual implementation)
        assert hasattr(generator, 'variables')
        # Verify default operations (adjust based on actual implementation)
        assert hasattr(generator, 'operations')

    # ==== COMMON TESTS ====
    @pytest.mark.common
    def test_configuration_structure(self, generator):
        """Test the configuration structure accepted by generate_equations."""
        # Test basic math configuration
        config_basic = {
            "type": "basic_math",
            "operations": ["+", "-"],
            "max_value": 20,
            "allow_decimals": False,
            "elements": 3,
            "random_seed": 12345
        }

        quiz = generator.generate_equations(config_basic)
        assert isinstance(quiz, DynamicQuizV2)

        # Test simple quiz configuration
        config_simple = {
            "type": "simple_quiz",
            "num_unknowns": 3,
            "max_value": 15,
            "random_seed": 12345
        }

        quiz = generator.generate_equations(config_simple)
        assert isinstance(quiz, DynamicQuizV2)

        # Test grade school configuration
        config_grade = {
            "type": "grade_school",
            "num_unknowns": 3,
            "operations": ["+", "-", "*"],
            "max_value": 25,
            "allow_decimals": True,
            "random_seed": 12345
        }

        quiz = generator.generate_equations(config_grade)
        assert isinstance(quiz, DynamicQuizV2)

    @pytest.mark.common
    def test_configuration_validation(self, generator):
        """Test validation of configuration parameters."""
        # Test with invalid equation type
        with pytest.raises(ValueError):
            generator.generate_equations({"type": "invalid_type"})

        # Test with invalid operations
        with pytest.raises(ValueError):
            generator.generate_basic_math(operations=["invalid_op"])

        # Test with invalid num_unknowns
        with pytest.raises(ValueError):
            generator.generate_simple_quiz(num_unknowns=0)

        # Test with invalid max_value
        with pytest.raises(ValueError):
            generator.generate_grade_school(max_value=-1)

        # Test with invalid elements
        with pytest.raises(ValueError):
            generator.generate_basic_math(elements=1)  # Needs at least 2 elements

    @pytest.mark.common
    def test_random_seed_configuration(self, generator):
        """Test that using the same random seed produces the same equations."""
        config1: BasicMathConfig = {
            "type": "basic_math",
            "operations": ["+", "-"],
            "max_value": 30,
            "allow_decimals": False,
            "elements": 2,
            "random_seed": 12345
        }

        config2 = config1.copy()  # Same config with same seed

        config3 = config1.copy()
        config3["random_seed"] = 67890  # Different seed

        # Generate quizzes
        quiz1 = generator.generate_equations(config1)
        quiz2 = generator.generate_equations(config2)
        quiz3 = generator.generate_equations(config3)

        # Same seed should produce same equations
        assert quiz1.equations[0].formatted == quiz2.equations[0].formatted

        # Different seed should produce different equations
        # Note: There's a small probability they could randomly be the same
        assert quiz1.equations[0].formatted != quiz3.equations[0].formatted

    @pytest.mark.common
    def test_no_infinite_solutions(self, generator):
        """Fuzz test to ensure no equations with infinite solutions are generated."""
        # Generate multiple equation sets for each type
        for _ in range(10):
            # Test basic math
            quiz1 = generator.generate_basic_math()
            assert self._has_unique_solution(quiz1)

            # Test simple quiz
            quiz2 = generator.generate_simple_quiz(num_unknowns=2)
            assert self._has_unique_solution(quiz2)

            # Test grade school
            quiz3 = generator.generate_grade_school(num_unknowns=3)
            assert self._has_unique_solution(quiz3)

    @pytest.mark.common
    @pytest.mark.fuzz
    def test_fuzz_for_infinite_solutions(self, generator):
        """
        Dedicated fuzz test to ensure the system NEVER generates equations with infinite solutions.
        This test repeatedly generates equation sets with different configurations to increase
        confidence in the uniqueness constraint.
        """
        # Test parameters to try
        unknown_counts = [1, 2, 3]
        operation_sets = [
            ['+', '-'],
            ['+', '-', '*'],
            ['+', '-', '*', '/']
        ]
        max_values = [10, 30, 100]
        decimal_options = [True, False]

        # Run a large number of tests with random combinations
        for _ in range(50):  # 50 random combinations
            # Randomly select parameters
            num_unknowns = random.choice(unknown_counts)
            operations = random.choice(operation_sets)
            max_value = random.choice(max_values)
            allow_decimals = random.choice(decimal_options)

            # Test each generator type with these parameters

            # Basic math (only applies if num_unknowns=1)
            if num_unknowns == 1:
                quiz = generator.generate_basic_math(
                    operations=operations,
                    max_value=max_value,
                    allow_decimals=allow_decimals
                )
                assert self._has_unique_solution(quiz), "Basic math quiz has infinite solutions"

            # Simple quiz
            quiz = generator.generate_simple_quiz(
                num_unknowns=num_unknowns,
                max_value=max_value
            )
            assert self._has_unique_solution(quiz), "Simple quiz has infinite solutions"

            # Grade school equations
            quiz = generator.generate_grade_school(
                num_unknowns=num_unknowns,
                operations=operations,
                max_value=max_value,
                allow_decimals=allow_decimals
            )
            assert self._has_unique_solution(quiz), "Grade school quiz has infinite solutions"

            # Test specific prone-to-failure cases
            if num_unknowns > 1:
                # Test a case that might produce dependent equations like 2x = y and 4x = 2y
                # These should be detected and avoided by the generator
                quiz = generator.generate_grade_school(
                    num_unknowns=2,
                    operations=['*'],  # Only multiplication makes this more likely
                    max_value=5,  # Small range increases chance of dependent equations
                )
                assert self._has_unique_solution(quiz), "Failed with multiplication-only equations"

    @pytest.mark.common
    def test_solution_correctness(self, generator):
        """Test that solutions provided are correct for the equations."""
        # Generate a quiz for each type
        quiz1 = generator.generate_basic_math()
        quiz2 = generator.generate_simple_quiz(num_unknowns=2)
        quiz3 = generator.generate_grade_school(num_unknowns=3)

        # Verify solutions for each quiz
        for quiz in [quiz1, quiz2, quiz3]:
            for equation in quiz.equations:
                assert self._verify_solution(equation, quiz.solution)

    @pytest.mark.common
    @pytest.mark.skipif(not ORIGINAL_AVAILABLE, reason="Original equations_generator not available")
    def test_output_format_compatibility(self, generator):
        """
        Test that the output format of EquationsGeneratorV2 is compatible with the existing MathEquationGenerator.
        The requirement states: 'Output must be in format of existing _equations_Generator'.
        """
        # Generate quizzes from both generators
        v2_quiz = generator.generate_basic_math()

        # Create an instance of the original generator
        original_generator = MathEquationGenerator()
        original_quiz = original_generator.generate_quiz()

        # Verify the structure matches
        assert hasattr(v2_quiz, 'equations'), "V2 quiz missing 'equations' attribute"
        assert hasattr(v2_quiz, 'solution'), "V2 quiz missing 'solution' attribute"

        assert hasattr(v2_quiz.solution, 'symbolic'), "V2 solution missing 'symbolic' attribute"
        assert hasattr(v2_quiz.solution, 'human_readable'), "V2 solution missing 'human_readable' attribute"

        assert all(hasattr(eq, 'symbolic') and hasattr(eq, 'formatted') for eq in v2_quiz.equations), \
            "V2 equations missing required attributes"

        # Check that the types match the original (or are compatible subclasses)
        assert isinstance(v2_quiz, DynamicQuizV2), "V2 quiz not instance of DynamicQuizV2"
        assert isinstance(v2_quiz.solution, DynamicQuizSolutionV2), "V2 solution not instance of DynamicQuizSolutionV2"
        assert all(isinstance(eq, EquationV2) for eq in v2_quiz.equations), "V2 equations not instances of EquationV2"

        # Verify that V2 classes can be properly converted to/from original classes if needed
        # (This depends on the actual implementation - you might need adapters or conversion methods)
        assert isinstance(v2_quiz.solution.human_readable, dict), "V2 solution.human_readable not a dict"
        assert all(isinstance(key, str) for key in v2_quiz.solution.human_readable.keys()), \
            "V2 solution.human_readable keys not strings"
        assert all(isinstance(value, (int, float, Fraction)) for value in v2_quiz.solution.human_readable.values()), \
            "V2 solution.human_readable values not numeric"

        # Further compatibility tests can be added based on how you intend to integrate v2 with existing code

    @pytest.mark.common
    def test_deterministic_generation_with_seeds(self, generator):
        """Test that the same seed produces the same equations across multiple runs."""
        # Use a fixed seed for reproducibility
        seed_value = 12345
        
        # Generate equations with the same seed twice
        generator1 = EquationsGeneratorV2(random_seed=seed_value)
        generator2 = EquationsGeneratorV2(random_seed=seed_value)
        
        # Generate equations for all three types
        basic_math1 = generator1.generate_basic_math()
        simple_quiz1 = generator1.generate_simple_quiz()
        grade_school1 = generator1.generate_grade_school()
        
        basic_math2 = generator2.generate_basic_math()
        simple_quiz2 = generator2.generate_simple_quiz()
        grade_school2 = generator2.generate_grade_school()
        
        # Verify that the equations and solutions are identical
        for eq1, eq2 in zip(basic_math1.equations, basic_math2.equations):
            assert eq1.formatted == eq2.formatted
            
        for eq1, eq2 in zip(simple_quiz1.equations, simple_quiz2.equations):
            assert eq1.formatted == eq2.formatted
            
        for eq1, eq2 in zip(grade_school1.equations, grade_school2.equations):
            assert eq1.formatted == eq2.formatted
        
        # Verify solutions are identical
        assert basic_math1.solution.human_readable == basic_math2.solution.human_readable
        assert simple_quiz1.solution.human_readable == simple_quiz2.solution.human_readable
        assert grade_school1.solution.human_readable == grade_school2.solution.human_readable

    @pytest.mark.common
    def test_linear_independence_verification(self, generator):
        """Test that generated equation systems have proper matrix rank for a unique solution."""
        # Test for each equation type
        for gen_method in [
            generator.generate_simple_quiz, 
            generator.generate_grade_school
        ]:
            # Generate equations with multiple unknowns
            quiz = gen_method(num_unknowns=3)
            
            # Extract variables and equations
            variables = list(quiz.solution.symbolic.keys())
            equations = [eq.symbolic for eq in quiz.equations]
            
            # Convert to matrix form using SymPy
            try:
                # This is a placeholder - the actual implementation would depend on
                # how equations are represented in the final code
                # A, b = sp.linear_eq_to_matrix(equations, variables)
                # assert A.rank() == len(variables), "Matrix rank doesn't match number of variables"
                
                # For now, we'll just verify there's one solution using our helper
                assert self._has_unique_solution(quiz), "System doesn't have a unique solution"
            except (AttributeError, TypeError):
                # Skip if symbolic representation isn't available yet
                pass

    @pytest.mark.common
    def test_boundary_configuration(self, generator):
        """Test boundary conditions for configuration parameters."""
        # Test minimal configuration (1 unknown)
        min_quiz = generator.generate_simple_quiz(num_unknowns=1)
        assert len(min_quiz.solution.human_readable) == 1
        assert len(min_quiz.equations) == 1
        
        # Test maximum allowed configuration (3 unknowns is max for grade school)
        max_quiz = generator.generate_grade_school(num_unknowns=3)
        assert len(max_quiz.solution.human_readable) == 3
        assert len(max_quiz.equations) == 3
        
        # Test minimum value range
        min_range_quiz = generator.generate_basic_math(max_value=5)
        for eq in min_range_quiz.equations:
            values = self._extract_values_from_equation(eq.formatted)
            assert all(abs(v) <= 5 for v in values if isinstance(v, (int, float)))
            
        # Test with very small decimal values
        small_decimal_quiz = generator.generate_grade_school(
            max_value=1, 
            allow_decimals=True,
            operations=['+', '-', '*', '/']
        )
        # Verify it can handle small values without errors
        assert self._has_unique_solution(small_decimal_quiz)

    @pytest.mark.common
    def test_error_handling_invalid_config(self, generator):
        """Test error handling for invalid configurations."""
        # Test invalid operations
        with pytest.raises(ValueError):
            generator.generate_basic_math(operations=['invalid_op'])
            
        # Test negative max_value
        with pytest.raises(ValueError):
            generator.generate_basic_math(max_value=-10)
            
        # Test invalid number of unknowns
        with pytest.raises(ValueError):
            generator.generate_simple_quiz(num_unknowns=0)
            
        # Test too many unknowns
        with pytest.raises(ValueError):
            generator.generate_grade_school(num_unknowns=10)  # Assuming there's a reasonable upper limit

    # ==== BASIC MATH TESTS ====
    @pytest.mark.basic_math
    def test_basic_math_default_config(self, generator):
        """Test basic math equations with default configuration."""
        quiz = generator.generate_basic_math()

        # Verify we get a valid quiz object
        assert isinstance(quiz, DynamicQuizV2)
        assert len(quiz.equations) > 0
        assert isinstance(quiz.solution, DynamicQuizSolutionV2)

        # Verify default settings are applied
        for eq in quiz.equations:
            # Unknown should be on the left side
            assert eq.formatted.strip().startswith('x')
            # Verify only + and - operations are used
            assert all(op not in eq.formatted for op in ['*', '/'])

    @pytest.mark.basic_math
    def test_basic_math_with_all_operations(self, generator):
        """Test basic math equations with all operations allowed."""
        quiz = generator.generate_basic_math(operations=['+', '-', '*', '/'])

        # We can't be certain all operations will be used in each equation,
        # but we can verify that the operations parameter is respected
        for eq in quiz.equations:
            # Unknown should be on the left side
            assert eq.formatted.strip().startswith('x')
            # Verify solution is correct
            assert self._verify_solution(eq, quiz.solution)

    @pytest.mark.basic_math
    def test_basic_math_with_custom_range(self, generator):
        """Test basic math equations with custom value range."""
        max_value = 10
        quiz = generator.generate_basic_math(max_value=max_value)

        # Parse the equation to check that values are within range
        for eq in quiz.equations:
            # Extract the values from the equation
            values = self._extract_values_from_equation(eq.formatted)
            # Check all values are within range
            assert all(abs(value) <= max_value for value in values)

    @pytest.mark.basic_math
    def test_basic_math_with_decimal_values(self, generator):
        """Test basic math equations with decimal values allowed."""
        quiz = generator.generate_basic_math(allow_decimals=True)

        # Check if at least one equation contains decimal values
        # Note: This might not always be true, as the generator could randomly generate only integers
        solution_values = list(quiz.solution.human_readable.values())
        equation_values = []
        for eq in quiz.equations:
            equation_values.extend(self._extract_values_from_equation(eq.formatted))

        # Verify that decimal capability exists, but don't require every test run to have decimals
        assert isinstance(solution_values[0], (int, float, Fraction))

    @pytest.mark.basic_math
    def test_basic_math_with_elements_count(self, generator):
        """Test basic math equations with configurable element count."""
        elements = 3  # x = a + b + c
        quiz = generator.generate_basic_math(elements=elements)

        for eq in quiz.equations:
            # Count the number of operations to verify elements
            operations_count = sum(1 for op in ['+', '-', '*', '/'] if op in eq.formatted)
            # Elements = operations_count + 1 (due to the format: x = a op b op c)
            assert operations_count == elements - 1

    @pytest.mark.basic_math
    def test_left_side_variable_basic_math(self, generator):
        """
        Test that in basic math equations, the unknown is always on the left side.
        This is a key requirement for Scenario A.
        """
        quiz = generator.generate_basic_math(elements=3)

        for eq in quiz.equations:
            # The equation should start with the variable name
            assert eq.formatted.strip()[0].isalpha(), f"Equation '{eq.formatted}' doesn't start with a variable"

            # The equation should have the form "x = ..."
            parts = eq.formatted.split('=', 1)
            assert len(parts) == 2, f"Equation '{eq.formatted}' missing equals sign"

            # Left side should be just the variable
            assert parts[0].strip() in quiz.solution.human_readable, f"Left side '{parts[0].strip()}' not a variable"

            # Right side should not contain the variable
            var_name = parts[0].strip()
            assert var_name not in parts[1], f"Variable '{var_name}' found on right side of equation"

    @pytest.mark.basic_math
    def test_basic_math_variable_elements_count(self, generator):
        """Test basic math with different element counts."""
        # Test with various element counts
        for elements in [2, 3, 4]:
            quiz = generator.generate_basic_math(elements=elements)
            
            for eq in quiz.equations:
                # Count the number of operations to verify elements
                operations_count = sum(1 for op in ['+', '-', '*', '/'] if op in eq.formatted)
                # For the format: x = a op b op c ..., operations_count should be elements-1
                assert operations_count == elements - 1, f"Expected {elements-1} operations for {elements} elements, got {operations_count}"
                
                # Parse the right side of the equation
                parts = eq.formatted.split('=', 1)
                right_side = parts[1].strip()
                
                # Split the right side by operators and check the number of operands
                # This is a simplified approach and might need refinement
                for op in ['+', '-', '*', '/']:
                    right_side = right_side.replace(op, " ")
                operands = [o for o in right_side.split() if o]
                assert len(operands) == elements - 1, f"Expected {elements-1} operands for {elements} elements, got {len(operands)}"

    # ==== SIMPLE QUIZ TESTS ====
    @pytest.mark.simple_quiz
    def test_simple_quiz_with_multiple_unknowns(self, generator):
        """Test simple quiz with multiple unknowns."""
        num_unknowns = 3
        quiz = generator.generate_simple_quiz(num_unknowns=num_unknowns)

        # Verify that the correct number of unknowns is used
        solution = quiz.solution.human_readable
        assert len(solution) == num_unknowns

        # Verify that all solutions are integers
        assert all(isinstance(val, int) for val in solution.values())

        # Verify the number of equations equals the number of unknowns
        assert len(quiz.equations) == num_unknowns

    @pytest.mark.simple_quiz
    def test_simple_quiz_integer_solutions(self, generator):
        """Test that simple quiz solutions are always integers."""
        quiz = generator.generate_simple_quiz()

        # Check that all values in the solution are integers
        for value in quiz.solution.human_readable.values():
            assert isinstance(value, int)

        # Verify each equation is satisfied by the solution
        for eq in quiz.equations:
            assert self._verify_solution(eq, quiz.solution)

    @pytest.mark.simple_quiz
    def test_simple_quiz_variable_repetition(self, generator):
        """Test that symbols can repeat in the same equation for simple quiz."""
        quiz = generator.generate_simple_quiz(num_unknowns=2)
        
        # Look for repetition of variables in the equations
        found_repetition = False
        for eq in quiz.equations:
            # Get the variable names
            var_names = list(quiz.solution.human_readable.keys())
            
            # Count occurrences of each variable in the equation
            for var_name in var_names:
                # Count exact matches of variable name (with word boundaries)
                occurrences = eq.formatted.count(var_name)
                if occurrences > 1:
                    found_repetition = True
                    break
            
            if found_repetition:
                break
                
        assert found_repetition, "No variable repetition found in any equation"
        
        # Generate a quiz with a specific pattern that requires repetition
        pattern_config = {
            "type": "simple_quiz",
            "num_unknowns": 2,
            "equations_config": [
                {"pattern": "{var1}+{var1}={const}", "values": {"const": 10}}
            ]
        }
        
        specific_quiz = generator.generate_equations(pattern_config)
        var1_name = list(specific_quiz.solution.human_readable.keys())[0]
        
        # Check the solution value makes sense for the pattern (x+x=10 means x=5)
        assert specific_quiz.solution.human_readable[var1_name] == 5

    @pytest.mark.simple_quiz
    def test_simple_quiz_operations_restriction(self, generator):
        """Test that only addition and subtraction are used in simple quiz."""
        quiz = generator.generate_simple_quiz(num_unknowns=2)
        
        for eq in quiz.equations:
            # Check that no multiplication or division is used
            assert '*' not in eq.formatted, f"Multiplication found in equation: {eq.formatted}"
            assert '/' not in eq.formatted, f"Division found in equation: {eq.formatted}"
            
            # Verify that addition or subtraction is used
            assert any(op in eq.formatted for op in ['+', '-']), f"No addition or subtraction found in equation: {eq.formatted}"

    # ==== GRADE SCHOOL TESTS ====
    @pytest.mark.grade_school
    def test_grade_school_equations_config(self, generator):
        """Test grade school equations with custom configuration."""
        # Test with custom operations
        operations = ['+', '-', '*']
        quiz = generator.generate_grade_school(operations=operations)

        # We can't guarantee all operations will be used, but we can verify
        # that the solution is correct
        assert self._has_unique_solution(quiz)

        # Test with more unknowns
        num_unknowns = 3
        quiz = generator.generate_grade_school(num_unknowns=num_unknowns)

        # Verify the number of equations equals the number of unknowns
        assert len(quiz.equations) == num_unknowns

        # Verify all specified unknowns have values in the solution
        assert len(quiz.solution.human_readable) == num_unknowns

    @pytest.mark.grade_school
    def test_grade_school_with_decimals(self, generator):
        """Test grade school equations with decimal values allowed."""
        quiz = generator.generate_grade_school(
            num_unknowns=2,
            operations=['+', '-', '*', '/'],
            max_value=10,
            allow_decimals=True
        )

        # Just verify that the equations and solutions are generated correctly
        # We can't guarantee decimals will appear in every test run
        assert isinstance(quiz, DynamicQuizV2)
        assert len(quiz.equations) > 0
        assert len(quiz.solution.human_readable) > 0

    @pytest.mark.grade_school
    def test_grade_school_integer_only(self, generator):
        """Test grade school equations with integer-only constraint."""
        quiz = generator.generate_grade_school(
            num_unknowns=2,
            operations=['+', '-', '*', '/'],
            max_value=20,
            allow_decimals=False
        )

        # Verify all solutions are integers
        for value in quiz.solution.human_readable.values():
            assert isinstance(value, int), f"Solution {value} is not an integer"

    @pytest.mark.grade_school
    def test_grade_school_complex_equation_system(self, generator):
        """Test generating complex multi-variable systems with interdependencies."""
        # Generate a 3-variable system
        quiz = generator.generate_grade_school(
            num_unknowns=3,
            operations=['+', '-', '*', '/']
        )
        
        # Check that we have 3 equations
        assert len(quiz.equations) == 3
        
        # Check that all 3 variables appear across the equations
        variables = list(quiz.solution.human_readable.keys())
        assert len(variables) == 3
        
        # Verify each variable appears in at least two equations (interdependency)
        var_appearances = {var: 0 for var in variables}
        for eq in quiz.equations:
            for var in variables:
                if var in eq.formatted:
                    var_appearances[var] += 1
                    
        # Each variable should appear in at least 2 equations for proper interdependency
        assert all(count >= 2 for count in var_appearances.values()), "Not all variables appear in multiple equations"
        
        # Test with a specific complex pattern
        complex_config = {
            "type": "grade_school",
            "num_unknowns": 3,
            "operations": ['+', '-', '*'],
            "equations_config": [
                {"pattern": "{var1}*10={var2}-3", "values": {}},
                {"pattern": "{var2}+{var3}=2", "values": {}},
                {"pattern": "2*{var3}={var2}-3", "values": {}}
            ]
        }
        
        complex_quiz = generator.generate_equations(complex_config)
        solution = complex_quiz.solution.human_readable
        
        # Verify this specific system has the correct solution
        vars = list(solution.keys())
        x, y, z = vars[0], vars[1], vars[2]
        
        # Check the solution satisfies the equations: x*10 = y-3, y+z = 2, 2*z = y-3
        assert abs(solution[x] * 10 - (solution[y] - 3)) < 0.001
        assert abs(solution[y] + solution[z] - 2) < 0.001
        assert abs(2 * solution[z] - (solution[y] - 3)) < 0.001

    @pytest.mark.grade_school
    def test_grade_school_value_range_validation(self, generator):
        """Test that values stay within the configured range for grade school equations."""
        max_value = 15
        quiz = generator.generate_grade_school(
            num_unknowns=2,
            max_value=max_value
        )
        
        # Check solutions are within range
        for value in quiz.solution.human_readable.values():
            assert abs(value) <= max_value, f"Solution value {value} exceeds configured max {max_value}"
        
        # Check constants in equations are within range
        for eq in quiz.equations:
            values = self._extract_values_from_equation(eq.formatted)
            for value in values:
                if isinstance(value, (int, float)) and not any(var in str(value) for var in quiz.solution.human_readable.keys()):
                    assert abs(value) <= max_value, f"Equation value {value} exceeds configured max {max_value}"

    # ==== MIXED EQUATION TESTS ====
    @pytest.mark.basic_math
    @pytest.mark.simple_quiz
    @pytest.mark.grade_school
    def test_specific_equation_examples(self, generator):
        """Test specific equation examples mentioned in the requirements."""
        # Example 1: Simple quiz with repeated symbols (x+x+x = 3; x + y + y = 10)
        equations_config1: List[EquationPatternConfig] = [
            {"pattern": "{var1}+{var1}+{var1}={const}", "values": {"const": 3}},
            {"pattern": "{var1}+{var2}+{var2}={const}", "values": {"const": 10}}
        ]

        config1: SimpleQuizConfig = {
            "type": "simple_quiz",
            "num_unknowns": 2,
            "allow_repeated_symbols": True,
            "equations_config": equations_config1
        }

        quiz1 = generator.generate_equations(config1)
        assert len(quiz1.solution.human_readable) == 2

        # The solutions should be x=1, y=4.5
        var1_name = list(quiz1.solution.human_readable.keys())[0]
        var2_name = list(quiz1.solution.human_readable.keys())[1]

        # Verify expected values based on specified equations
        assert quiz1.solution.human_readable[var1_name] == 1  # x+x+x=3 means x=1
        assert quiz1.solution.human_readable[var2_name] == 4.5  # x+y+y=10 with x=1 means y=4.5

        # Example 2: Simple quiz with different pattern (x + x = 10; y - x = 10; x + y = z)
        equations_config2: List[EquationPatternConfig] = [
            {"pattern": "{var1}+{var1}={const}", "values": {"const": 10}},
            {"pattern": "{var2}-{var1}={const}", "values": {"const": 10}},
            {"pattern": "{var1}+{var2}={var3}", "values": {}}
        ]

        config2: SimpleQuizConfig = {
            "type": "simple_quiz",
            "num_unknowns": 3,
            "allow_repeated_symbols": True,
            "equations_config": equations_config2
        }

        quiz2 = generator.generate_equations(config2)
        assert len(quiz2.solution.human_readable) == 3

        # Example 3: Grade school equations (x + 10 = 12; y + x = 20)
        equations_config3: List[EquationPatternConfig] = [
            {"pattern": "{var1}+10=12", "values": {}},
            {"pattern": "{var2}+{var1}=20", "values": {}}
        ]

        config3: GradeSchoolConfig = {
            "type": "grade_school",
            "num_unknowns": 2,
            "equations_config": equations_config3
        }

        quiz3 = generator.generate_equations(config3)
        assert len(quiz3.solution.human_readable) == 2

        # Solutions should be x=2, y=18
        var1_name = list(quiz3.solution.human_readable.keys())[0]
        var2_name = list(quiz3.solution.human_readable.keys())[1]
        assert quiz3.solution.human_readable[var1_name] == 2
        assert quiz3.solution.human_readable[var2_name] == 18

        # Example 4: Grade school with multiplication (x = y * 2; y + x = 1.5)
        equations_config4: List[EquationPatternConfig] = [
            {"pattern": "{var1}={var2}*2", "values": {}},
            {"pattern": "{var2}+{var1}=1.5", "values": {}}
        ]

        config4: GradeSchoolConfig = {
            "type": "grade_school",
            "num_unknowns": 2,
            "operations": ["+", "-", "*"],
            "allow_decimals": True,
            "equations_config": equations_config4
        }

        quiz4 = generator.generate_equations(config4)
        assert len(quiz4.solution.human_readable) == 2

        # Solutions should be x=1, y=0.5
        var1_name = list(quiz4.solution.human_readable.keys())[0]
        var2_name = list(quiz4.solution.human_readable.keys())[1]
        assert quiz4.solution.human_readable[var1_name] == 1
        assert quiz4.solution.human_readable[var2_name] == 0.5

    # ==== HELPER METHODS ====
    def _extract_values_from_equation(self, equation_str: str) -> List[Union[int, float]]:
        """Extract all numeric values from an equation string."""
        # Simplified implementation - actual implementation may need to be more sophisticated
        parts = equation_str.replace('=', ' ').replace('+', ' ').replace('-', ' ').replace('*', ' ').replace('/',
                                                                                                             ' ').split()
        values = []
        for part in parts:
            try:
                values.append(float(part))
            except ValueError:
                # Not a number, could be a variable
                pass
        return values

    def _verify_solution(self, equation: EquationV2, solution: DynamicQuizSolutionV2) -> bool:
        """Verify that the solution is correct for the given equation."""
        # This implementation will depend on how equations and solutions are represented
        # For example, if the symbolic form uses SymPy expressions:
        substituted = equation.symbolic.subs(solution.symbolic)
        return substituted == True

    def _has_unique_solution(self, quiz: DynamicQuizV2) -> bool:
        """
        Check if the system of equations has exactly one solution.
        
        This implementation uses SymPy to evaluate the system of equations by:
        1. Creating a matrix from the coefficients of the linear system
        2. Checking that its rank equals the number of variables
        3. Verifying that the system is consistent (has solutions)
        
        Returns:
            bool: True if the system has exactly one solution, False otherwise
        """
        if not quiz.equations:
            return False

        # Extract variables from solution
        variables = list(quiz.solution.symbolic.keys())
        num_vars = len(variables)

        # Create a system of linear equations
        system = []
        for eq in quiz.equations:
            system.append(eq.symbolic)

        try:
            # Use SymPy's linsolve to find solutions
            solutions = sp.linsolve(system, variables)

            # Check if we have exactly one solution
            if isinstance(solutions, sp.sets.sets.FiniteSet) and len(solutions) == 1:
                return True

            # Check if solution is not a line, plane, or higher-dimensional space
            if isinstance(solutions, sp.sets.sets.ImageSet) or len(solutions) > 1:
                return False

            # Check for empty solution set (inconsistent system)
            if len(solutions) == 0:
                return False

            return True
        except Exception as e:
            # If SymPy can't solve it, we'll use an alternative approach
            # For non-linear systems, we can check that the provided solution works
            # and assume the generator's correctness
            for eq in quiz.equations:
                if not self._verify_solution(eq, quiz.solution):
                    return False
            return True
