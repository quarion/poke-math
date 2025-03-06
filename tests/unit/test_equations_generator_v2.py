import pytest
import sympy as sp
import random
import numpy as np
from typing import Dict, Any, List, Optional, Union
from fractions import Fraction

from src.app.equations.equations_generator_v2 import EquationsGeneratorV2, DynamicQuizV2

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

class TestEquationsGeneratorV2:
    """Test suite for the EquationsGeneratorV2 class."""

    @pytest.fixture
    def generator(self):
        """Return an instance of EquationsGeneratorV2 for testing."""
        return EquationsGeneratorV2()
    
    # Common tests for all equation types
    @pytest.mark.common
    def test_initialization(self, generator):
        """Test that the generator initializes correctly."""
        assert isinstance(generator, EquationsGeneratorV2)
        assert generator.variables == list('xyzwvu')
        assert generator.operations == ['+', '-', '*', '/']
    
    @pytest.mark.common
    def test_generate_equations_invalid_type(self, generator):
        """Test that generate_equations raises an error for invalid equation types."""
        with pytest.raises(ValueError):
            generator.generate_equations({"type": "invalid_type"})
    
    @pytest.mark.common
    def test_generate_equations_missing_type(self, generator):
        """Test that generate_equations raises an error when type is missing."""
        with pytest.raises(ValueError):
            generator.generate_equations({})
    
    # Basic Math tests
    @pytest.mark.basic_math
    def test_basic_math_default_params(self, generator):
        """Test basic math generation with default parameters."""
        quiz = generator.generate_basic_math()
        
        # Check that we have one equation
        assert len(quiz.equations) == 1
        
        # Check that the equation has the expected format (x = ...)
        eq_str = quiz.equations[0].formatted
        assert eq_str.startswith("x =")
        
        # Check that the solution exists and is correct
        assert "x" in quiz.solution.human_readable
        
        # Verify the solution is correct by evaluating the equation
        x_value = quiz.solution.human_readable["x"]
        right_side = eq_str.split("=")[1].strip()
        assert x_value == eval(right_side)  # Safe to use eval here for testing
    
    @pytest.mark.basic_math
    def test_basic_math_operations(self, generator):
        """Test basic math generation with different operations."""
        operations = ["+", "-"]
        quiz = generator.generate_basic_math(operations=operations)
        
        # Check that only the specified operations are used
        eq_str = quiz.equations[0].formatted
        right_side = eq_str.split("=")[1].strip()
        
        # The right side should only contain the specified operations
        for op in ["+", "-"]:
            if op in operations:
                pass  # Operation is allowed
            else:
                assert op not in right_side, f"Operation {op} should not be in equation"
    
    @pytest.mark.basic_math
    def test_basic_math_max_value(self, generator):
        """Test basic math generation with different max values."""
        max_value = 10
        quiz = generator.generate_basic_math(max_value=max_value)
        
        # Check that all values in the equation are within the max value
        eq_str = quiz.equations[0].formatted
        right_side = eq_str.split("=")[1].strip()
        
        # Extract all numbers from the right side
        import re
        numbers = re.findall(r'\d+', right_side)
        for num in numbers:
            assert int(num) <= max_value, f"Value {num} exceeds max value {max_value}"
    
    @pytest.mark.basic_math
    def test_basic_math_allow_decimals(self, generator):
        """Test basic math generation with decimal values."""
        # Test with decimals allowed
        quiz_with_decimals = generator.generate_basic_math(allow_decimals=True)
        
        # Test with decimals not allowed
        quiz_without_decimals = generator.generate_basic_math(allow_decimals=False)
        
        # For quiz_without_decimals, check that all values are integers
        eq_str = quiz_without_decimals.equations[0].formatted
        right_side = eq_str.split("=")[1].strip()
        
        # Check if the solution is an integer
        assert isinstance(quiz_without_decimals.solution.human_readable["x"], int)
        
        # For quiz_with_decimals, we can't guarantee decimals will be used,
        # but we can check that the solution is correct
        x_value = quiz_with_decimals.solution.human_readable["x"]
        right_side = quiz_with_decimals.equations[0].formatted.split("=")[1].strip()
        assert abs(x_value - eval(right_side)) < 1e-10  # Use approximate equality for floats
    
    @pytest.mark.basic_math
    def test_basic_math_elements(self, generator):
        """Test basic math generation with different numbers of elements."""
        for elements in range(2, 5):
            quiz = generator.generate_basic_math(elements=elements)
            
            # Check that the equation has the expected number of elements
            eq_str = quiz.equations[0].formatted
            right_side = eq_str.split("=")[1].strip()
            
            # Count the number of operations (which is elements - 1)
            import re
            operations_count = len(re.findall(r'[\+\-\*\/]', right_side))
            assert operations_count == elements - 1, f"Expected {elements-1} operations for {elements} elements, got {operations_count}"
    
    @pytest.mark.basic_math
    def test_basic_math_solution_correctness(self, generator):
        """Test that the solutions provided are correct for basic math equations."""
        # Test with various configurations
        configurations = [
            {"operations": ["+", "-"], "max_value": 20, "allow_decimals": False, "elements": 2},
            {"operations": ["+", "-", "*"], "max_value": 10, "allow_decimals": False, "elements": 3},
            {"operations": ["+", "-", "*", "/"], "max_value": 30, "allow_decimals": True, "elements": 4},
        ]
        
        for config in configurations:
            quiz = generator.generate_basic_math(**config)
            
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
                    assert abs(float(lhs_val) - float(rhs_val)) < 1e-10, f"Equation {eq.formatted} not satisfied by solution {quiz.solution.human_readable}"
                else:
                    # If the equation is a SymPy equation, substitute the solution values
                    if eq.symbolic is not None:
                        result = eq.symbolic.subs(quiz.solution.symbolic)
                        # Verify that the equation is satisfied
                        assert result == True, f"Equation {eq.formatted} not satisfied by solution {quiz.solution.human_readable}"
    
    @pytest.mark.basic_math
    def test_basic_math_unique_solution(self, generator):
        """Test that basic math equations have exactly one solution."""
        quiz = generator.generate_basic_math()
        
        # Extract the symbolic equation
        eq = quiz.equations[0]
        
        # If the equation is a string with an equals sign, convert it to a SymPy equation
        if isinstance(eq.symbolic, str) and '=' in eq.symbolic:
            sides = eq.symbolic.split('=')
            lhs = sp.sympify(sides[0].strip())
            rhs = sp.sympify(sides[1].strip())
            symbolic_equation = sp.Eq(lhs, rhs)
        else:
            symbolic_equation = eq.symbolic
        
        # Use SymPy to solve the equation
        if symbolic_equation is not None:
            variable = sp.Symbol('x')
            solutions = sp.solve(symbolic_equation, variable)
            
            # Check that there is exactly one solution
            assert len(solutions) == 1, f"Expected exactly one solution, got {len(solutions)}"
            
            # Verify the solution matches the one provided by the generator
            assert abs(float(solutions[0]) - float(quiz.solution.human_readable['x'])) < 1e-10, f"Solution mismatch: expected {quiz.solution.human_readable['x']}, got {solutions[0]}"
    
    @pytest.mark.basic_math
    def test_basic_math_via_generate_equations(self, generator):
        """Test basic math generation via the generate_equations method."""
        config = {
            "type": "basic_math",
            "operations": ["+", "-"],
            "max_value": 20,
            "allow_decimals": False,
            "elements": 3
        }
        
        quiz = generator.generate_equations(config)
        
        # Check that we have one equation
        assert len(quiz.equations) == 1
        
        # Check that the equation has the expected format (x = ...)
        eq_str = quiz.equations[0].formatted
        assert eq_str.startswith("x =")
        
        # Check that the solution exists and is correct
        assert "x" in quiz.solution.human_readable
        
        # Verify the solution is correct by evaluating the equation
        x_value = quiz.solution.human_readable["x"]
        right_side = eq_str.split("=")[1].strip()
        assert x_value == eval(right_side)  # Safe to use eval here for testing
    
    @pytest.mark.basic_math
    def test_basic_math_random_seed(self, generator):
        """Test that using the same random seed produces the same equations."""
        # This test is for the generate_equations method which accepts a random_seed parameter
        config1 = {
            "type": "basic_math",
            "operations": ["+", "-"],
            "max_value": 20,
            "allow_decimals": False,
            "elements": 3,
            "random_seed": 12345
        }
        
        config2 = config1.copy()  # Same config with same seed
        
        quiz1 = generator.generate_equations(config1)
        quiz2 = generator.generate_equations(config2)
        
        # Check that the equations and solutions are identical
        assert quiz1.equations[0].formatted == quiz2.equations[0].formatted
        assert quiz1.solution.human_readable == quiz2.solution.human_readable
        
        # Now change the seed and verify we get different equations
        config3 = config1.copy()
        config3["random_seed"] = 54321
        
        quiz3 = generator.generate_equations(config3)
        
        # The equations should be different with a different seed
        # Note: There's a small chance they could be the same by coincidence
        assert quiz1.equations[0].formatted != quiz3.equations[0].formatted or \
               quiz1.solution.human_readable != quiz3.solution.human_readable