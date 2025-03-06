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