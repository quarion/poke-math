from src.app.equations.equations import generator, MathEquationGenerator

configurations_advanced = [
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
            "max_elements": 8,  # Limit to 8 elements for challenge equations
            "ensure_operation": True  # Ensure at least one operation
        }
    }
]

def run_tests():
    global i, j, eq, var, val
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

if __name__ == "__main__":
    generator = MathEquationGenerator()

    run_tests()