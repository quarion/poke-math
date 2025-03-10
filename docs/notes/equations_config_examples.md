# `equations_config` Parameter Usage Examples

The `equations_config` parameter allows educators to specify exact equation patterns rather than relying solely on random generation. This provides precise control over the education experience. Below are concrete examples for both equation types.

## Example 1: Simple Quiz with Specific Patterns

```python
# Create a Simple Quiz with specific equation patterns
quiz = generator.generate_simple_quiz(
    num_unknowns=3,  # We'll use x, y, and z
    max_value=20,
    equations_config=[
        {
            "pattern": "{x} + {x} = {const1}"  # Forces x+x=some_value pattern
        },
        {
            "pattern": "{y} - {x} = {const2}"  # Forces y-x=some_value pattern
        },
        {
            "pattern": "{x} + {y} = {z}"  # Forces x+y=z pattern
        }
    ]
)
```

This would generate exactly the example mentioned in the spec: `{ x + x = 10; y - x = 10; x + y = z }` but with random values that ensure one unique solution.

## Example 2: Grade School with Fixed Values

```python
# Create a Grade School equation set with some fixed values
quiz = generator.generate_grade_school(
    num_unknowns=3,  # We'll use x, y, and z
    operations=["+", "-", "*"],
    max_value=30,
    equations_config=[
        {
            "pattern": "{x} * 10 = {y} - {const1}",
            "values": {"const1": 3}  # Fix the constant to exactly 3
        },
        {
            "pattern": "{y} + {z} = {const2}"
        },
        {
            "pattern": "2 * {z} = {y} - {const1}",
            "values": {"const1": 3}  # Same constant as first equation
        }
    ]
)
```

This would generate exactly the example from the spec: `{ x * 10 = y - 3; y + z = 2; 2*z = y - 3 }` but potentially with different values for the variables and the second constant.

## Example 3: Curriculum Progression

```python
# For early lessons - focused addition only
day1_quiz = generator.generate_grade_school(
    num_unknowns=2,
    operations=["+"],
    equations_config=[
        {"pattern": "{x} + {const1} = {const2}"},
        {"pattern": "{y} + {x} = {const3}"}
    ]
)

# For later lessons - introduction to multiplication
day5_quiz = generator.generate_grade_school(
    num_unknowns=2,
    operations=["+", "*"],
    equations_config=[
        {"pattern": "{x} * {const1} = {const2}"},
        {"pattern": "{y} + {x} = {const3}"}
    ]
)
```

## Benefits of `equations_config`

1. **Pedagogical Control**: Teachers can target specific algebraic concepts
2. **Consistent Difficulty**: Ensures questions follow a specific structure
3. **Assessment Alignment**: Can create questions that match teaching progression
4. **Example Recreation**: Can recreate textbook examples exactly
5. **Custom Series**: Can generate series of equations that build on each other

The parameter provides significant flexibility while still ensuring mathematical validity and correct solution generation. It's an advanced feature that makes the generator much more valuable for educational purposes, especially when specific equation patterns need to be practiced. 