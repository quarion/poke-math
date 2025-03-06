Create v2 version of equations generator from scratch

# Functional description
Create a random equation generator for specific use cases

1. Output must be in format of existing _equations_Generator. But we should desing the configuration input from scratch.
2. Need to cover following scenarios:

A. Basic math
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

#### A. Basic Math Generator

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

1. **Start with a pattern-based first equation**:
   - Begin with a simple repetition pattern like `x+x=10` or `y+y+y=12`
   - Ensure this equation has an integer solution
   - This first equation provides a clear, structured entry point for learners

2. **Add subsequent equations with controlled complexity**:
   - Each additional equation will relate unknown variables in simple ways
   - Maintain only addition and subtraction operations
   - Ensure the system remains solvable with integer solutions

3. **Pseudocode**:
   ```
   # Step 1: Create first equation with variable repetition
   var1 = random_choice(variables)
   repetitions = random_int(2, 4)  # 2 to 4 repetitions of the same variable
   total = random_int(repetitions, max_value)
   # Ensure the total is divisible by repetitions to get integer value
   total = (total // repetitions) * repetitions
   
   first_equation = {left: [var1] * repetitions, right: total}
   
   # Step 2: Extract the solution for var1
   solution[var1] = total // repetitions
   
   # Step 3: Generate additional equations
   for i in range(1, num_equations):
       # Create equations with defined integer solutions
       equation = generate_equation_with_known_solution(solution, available_vars)
       equations.append(equation)
       
       # If needed, define a new variable in terms of known ones
       if i < num_unknowns - 1:
           new_var = get_unused_variable(variables, solution)
           solution[new_var] = random_int(1, max_value)
   ```

#### C. Grade School Generator (Deterministic Approach)

1. **Pre-determine all variable solutions**:
   - Assign random values to all variables within constraints
   - Ensure these values satisfy all configuration requirements (integers vs. decimals)

2. **Build a system guarantee matrix**:
   - Create an equation coefficient matrix with proper rank
   - Use elementary row operations to ensure linear independence

3. **Generate equations from this matrix**:
   - Convert matrix rows to equations with appropriate operations
   - Ensure operation diversity according to configuration

4. **Pseudocode for deterministic approach**:
   ```
   # Step 1: Assign solution values to all variables
   solutions = {var: generate_value(max_value, allow_decimals) for var in variables}
   
   # Step 2: Create coefficient matrix with guaranteed full rank
   # For n variables, start with identity matrix (guarantees full rank)
   coefficient_matrix = identity_matrix(num_unknowns)
   
   # Step 3: Apply random transformations while preserving rank
   for i in range(desired_complexity):
       transform_type = random_choice(["scale", "add_row", "swap"])
       apply_transformation(coefficient_matrix, transform_type)
   
   # Step 4: Generate right-hand sides based on solutions
   right_sides = []
   for row in coefficient_matrix:
       right_side = sum(coef * solutions[var] for coef, var in zip(row, variables))
       right_sides.append(right_side)
   
   # Step 5: Convert matrix rows to equations with diverse operations
   equations = []
   for i, row in enumerate(coefficient_matrix):
       if random.random() < 0.3 and "*" in operations:  # Probability for multiplicative equation
           # Create equation with multiplication, e.g., 2*x = y + 3
           equations.append(create_multiplicative_equation(row, right_sides[i], solutions))
       else:
           # Create standard linear equation, e.g., x + 2y = 5
           equations.append(create_linear_equation(row, right_sides[i]))
   ```

## 3. Linear Independence Verification

To prevent infinite solutions, we'll implement:

1. **Rank check**: Ensure the coefficient matrix has full rank
2. **Symbolic dependency check**: Use SymPy's linear dependency checking
3. **Solution uniqueness verification**: Verify that solve() returns exactly one solution per variable

Pseudocode:
```
def verify_system(equations, variables, solutions):
    # Verify each equation evaluates correctly with our solutions
    for eq in equations:
        if not equation_is_satisfied(eq, solutions):
            return False
    
    # Verify the system has exactly one solution
    matrix, vector = system_to_matrix_form(equations, variables)
    if matrix.rank() < len(variables):
        return False
        
    # Additional check: solve the system symbolically
    symbolic_solution = sympy.solve(equations, variables)
    if len(symbolic_solution) != 1:
        return False
        
    return True
```

## 4. Configuration and Pattern Support

For custom equation patterns:
1. Parse pattern strings with variable placeholders
2. Generate specific values that satisfy pattern constraints
3. Convert patterns to SymPy expressions

## 5. Output Formatting

Ensure compatibility with the original format:
1. Convert SymPy expressions to formatted strings
2. Create solution objects with both symbolic and human-readable forms
3. Structure DynamicQuizV2 objects consistent with the original format

## 6. Error Handling and Constraints

- Implement robust validation for all configuration options
- Add retry mechanisms when constraints can't be satisfied
- Cap the number of generation attempts to prevent infinite loops

## 7. Performance Considerations

- Use efficient algorithms for system generation
- Implement early detection of unsolvable or infinitely solvable systems
- Cache intermediate results when appropriate