Create v2 version of equations generator from scratch

# Functional description
Create a random equation generator for specific use cases

1. Output must be in format of existing _equations_Generator. But we should desing the configuration input from scratch.
2. Need to cover following scenarios:

A. Basic math ✅ (COMPLETED)
 - Only 1 unknown
 - Unknown is always on the left side of equation
 - Allowed operations are configurable (+, -, / *). Default to "+, -"
 - Range of values is configurable (eg up to 100). Default to 30
 - It is configurable if decimals are allowed or only integers
 - It is configurable how many elements we can have in equation (eg for 2 x = 10 + 5, for 3 x = 10 + 5 - 2)

B. Simple quiz
 - More than 1 unknown - configurable
 - Only use "+" and "-" operation.
 - Can repeat the same symbol in the same equation.
 - Solution is always integer

    Examples:
    - {x+x+x = 3; x + y + y = 10}
    - { x + x = 10; y - x = 10; x + y = z }

C. Grade school equations
 - Configurable number of unknows (can cap at 3)
 - Configurable allowed operations
 - Configurable range of values
 - Configurable if can use decimals or all constants and solution need to be integer (eg if allowed: 1.5*x = 10 is ok)

    Examples:
 - {x + 10 = 12; y + x = 20}
 - {x = y * 2; y + x = 1.5}
 - { x * 10 = y - 3; y + z = 2; 2*z = y - 3 }

3. Be sure to NEVER generate equations that has infinite number of solutions, for example {2x = y; 4x = 2y}

# Implementation plan
1. First create comprehensive set of tests. Create them in new V2 test file
   2. Create separate fuzzing test to make sure we will never generate set of equations without single solution
2. After test are accepted, create comprehensive description of algorithm you will implement and the configuration parameters
3. After plan is accepted, execute coding

# Detailed Implementation Plan

## 1. Core Architecture

The `EquationsGeneratorV2` class will be the main entry point with three specialized generation methods, plus a generic method that routes to the appropriate specialized method based on configuration:

- `generate_basic_math()` - For type A equations
- `generate_simple_quiz()` - For type B equations
- `generate_grade_school()` - For type C equations
- `generate_equations()` - Generic method that delegates to specific generators

## 2. Algorithm Approach

### Common Components

1. **Equation Building Process**:
   - Create SymPy symbol objects for variables (x, y, z, etc.)
   - Build symbolic expressions based on configuration
   - Ensure equations have single, unique solutions

2. **Solution Verification**:
   - Use SymPy's solve() to verify solvability
   - Check for infinite solutions by analyzing linear dependencies
   - Ensure solutions meet constraints (integers when required)

3. **Random Generation Strategy**:
   - Use seeded random number generation for reproducibility
   - Create a solution first, then generate equations that produce that solution
   - This "solution-first" approach guarantees solvability

### Type-Specific Algorithms

#### A. Basic Math Generator ✅ (IMPLEMENTED)

1. Generate a random value for the unknown variable (respecting constraints)
2. Build the right side of the equation using random operations and values:
   - Start with a random value
   - Apply random operations (from allowed set) with random values
   - Respect max_value constraints
   - Generate appropriate decimals if allowed
   - Ensure correct number of elements

3. Example algorithm pseudocode:
   ```
   x_value = random_in_range(1, max_value)
   right_side = random_in_range(1, max_value)
   
   for i in range(elements - 1):
       operation = random_choice(operations)
       operand = random_in_range(1, max_value)
       
       if operation == "+":
           right_side += operand
       elif operation == "-":
           right_side -= operand
       # Similar for * and /
   
   # Build equation: x = right_side
   ```

#### B. Simple Quiz Generator

1. **Start with variable repetition patterns**:
   - Begin with patterns like `x+x=10` or `y+y+y=12`
   - Ensure each equation has an integer solution
   - Always include variable repetition as it's a defining characteristic

2. **Build a complete system with integer solutions**:
   - Generate exactly as many equations as unknowns
   - Ensure the system has exactly one solution
   - Use only addition and subtraction operations
   - Always produce integer solutions

3. **Pseudocode**:
   ```
   # Step 1: Create solution set with integer values
   solution = {var: random_int(1, max_value) for var in variables[:num_unknowns]}
   
   # Step 2: Generate equations with variable repetition
   equations = []
   for i in range(num_unknowns):
     # Decide on a pattern with repeated variables
     var_to_repeat = random_choice(variables[:num_unknowns])
     repetitions = random_int(2, 3)  # Use 2-3 repetitions of the same variable
     
     # Create equation using this pattern
     left_side = var_to_repeat * repetitions  # symbolic multiplication = repetition
     right_side = solution[var_to_repeat] * repetitions
     
     # Sometimes mix in other variables
     if random.random() > 0.5 and i > 0:
       other_var = random_choice([v for v in variables[:num_unknowns] if v != var_to_repeat])
       operation = random_choice(['+', '-'])
       
       if operation == '+':
         left_side += other_var
         right_side += solution[other_var]
       else:
         left_side -= other_var
         right_side -= solution[other_var]
         
     equations.append(sympy.Eq(left_side, right_side))
   
   # Step 3: Verify system has exactly one solution
   matrix = system_to_matrix(equations, variables[:num_unknowns])
   if matrix.rank() < num_unknowns:
     # Try again with different equation patterns
     return generate_equations()
   ```

#### C. Grade School Generator

1. **Pre-determine all variable solutions**:
   - Assign random values to all variables within constraints
   - Ensure these values meet requirements (integers vs. decimals)

2. **Generate linearly independent equations**:
   - Create exactly as many equations as unknowns
   - Build a system with proper rank for unique solution
   - Use configured operations to create diverse equation types

3. **Pseudocode**:
   ```
   # Step 1: Assign solution values to all variables
   solutions = {}
   for var in variables[:num_unknowns]:
     if allow_decimals:
       solutions[var] = round(random.uniform(1, max_value), 1)  # One decimal place
     else:
       solutions[var] = random.randint(1, max_value)
   
   # Step 2: Generate equations with the allowed operations
   equations = []
   for i in range(num_unknowns):
     # Select variables to include in this equation
     used_vars = random.sample(variables[:num_unknowns], random.randint(1, min(3, num_unknowns)))
     
     # Build equation terms
     left_side = 0
     for var in used_vars:
       coef = random.randint(1, 5) if var != variables[0] else 1  # First var often has coef=1
       op = random.choice(operations) if left_side != 0 else '+'
       
       if op == '+':
         left_side += coef * var
       elif op == '-':
         left_side -= coef * var
       elif op == '*' and var != variables[0]:  # Only multiply secondary variables
         left_side *= coef
     
     # Calculate right side based on solution values
     right_side = left_side.subs(solutions)
     
     equations.append(sympy.Eq(left_side, right_side))
   
   # Step A3: Verify system has exactly one solution and is linearly independent
   if not verify_system_independence(equations, variables[:num_unknowns]):
     # Try again with different equations
     return generate_equations()
   ```

## 3. Linear Independence Verification

The core of ensuring all equation sets have exactly one solution:

```
def verify_system_independence(equations, variables):
    # Convert to matrix form
    A, b = sympy.linear_eq_to_matrix(equations, variables)
    
    # Check rank matches number of variables
    if A.rank() < len(variables):
        return False
    
    # Verify solution uniqueness
    solution = sympy.solve(equations, variables)
    if len(solution) != 1:
        return False
        
    return True
```

## 4. Output Formatting

Ensure compatibility with the original format:
1. Convert SymPy expressions to formatted strings
2. Create solution objects with both symbolic and human-readable forms
3. Structure DynamicQuizV2 objects consistent with the original format

## 5. Error Handling and Constraints

- Implement robust validation for all configuration options
- Add retry mechanisms when constraints can't be satisfied
- Cap the number of generation attempts to prevent infinite loops

## 6. Performance Considerations

- Use efficient algorithms for system generation
- Implement early detection of unsolvable systems
- Ensure all equations are solvable by construction using the solution-first approach

# Implementation Progress

## Basic Math (Type A) ✅
- Implemented and tested the basic math equation generator
- All tests are passing
- Features implemented:
  - Configurable operations (+, -, *, /)
  - Configurable max value for constants
  - Support for decimal values
  - Configurable number of elements in the equation
  - Random seed for reproducibility
  - Solution correctness verification

## Next Steps
- Implement Simple Quiz (Type B) equations
- Implement Grade School (Type C) equations