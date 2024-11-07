from ortools.linear_solver import pywraplp

DIRECTIONS = ('N', 'S', 'E', 'W')

BELT_INPUT_DIRECTIONS = {
    'N': ['S', 'E', 'W'],
    'S': ['N', 'E', 'W'],
    'E': ['N', 'S', 'W'],
    'W': ['N', 'S', 'E'],
}

# Synbols used for visualizing the belt based on direction
DIRECTIONS_SYMBOL = {
    'N': '^',
    'S': 'v',
    'E': '>',
    'W': '<',
}
# Symbols used for visualizing the mixer based on direction
# since the mixer has two cells we have two different symbols (cell1, cell2)
MIXER_SYMBOL = {
    'N': ('W', 'w'),
    'S': ('S', 's'),
    'E': ('A', 'a'),
    'W': ('D', 'd'),
}

'''
Finds the minimum area of a belt balancer for a given grid size and input flows

grid_size: tuple (W, H) where W is the width and H is the height of the grid
num_sources: int number of flow sources
input_flows: list of tuples (i, j, d, flow) where i, j are the coordinates of the flow source, d is the direction of the flow, s the source number, and flow is the flow value
'''
def solve_factorio_belt_balancer(grid_size, num_sources, input_flows):
    # Grid size
    W, H = grid_size


    # Create the solver
    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Decision variables
    # wheter a cell is occupied by a component
    x = [[solver.BoolVar(f'x_{i}_{j}') for j in range(H)] for i in range(W)]
    # belt in a direction
    b = [[[solver.BoolVar(f'b_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    # mixer in a direction. note that i, j are the left cell of the mixer
    m = [[[solver.BoolVar(f'm_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    # flow of a source in a direction
    f = [[[[solver.NumVar(-1, 1, f'f_{i}_{j}_{s}_{d}') for d in DIRECTIONS] for s in range(num_sources)] for j in range(H)] for i in range(W)]

    # Constraints

    # Large constant M for big-M constraints
    large_M = 1000
    
    # 1. Occupied Cells Constraint
    for i in range(W):
        for j in range(H):
            # A cell is occupied if there's a belt or mixer
            solver.Add(x[i][j] == 
                # Belt in cell
                sum(b[i][j][d] for d in range(len(DIRECTIONS))) +
                # First cell of mixer in cell i, j
                sum(m[i][j][d] for d in range(len(DIRECTIONS)) if mixer_can_be_placed(i, j, DIRECTIONS[d], grid_size)) +
                # Second cell of mixer in ci, cj in cell i, j
                sum(m[ci][cj][d] for d in range(len(DIRECTIONS)) for ci, cj in [mixer_first_cell(i, j, DIRECTIONS[d])] if inside_grid(ci, cj, grid_size))
            )

    # 2. Empty Flow Constraints
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # No flow on empty cell
                    solver.Add(f[i][j][s][d] <= large_M *  x[i][j])
                    solver.Add(f[i][j][s][d] >= -large_M * x[i][j])

    ##
    ## Belt constraints
    ##

    # 3. Flow Conservation for Belts
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Flow into the belt must equal the flow out of the belt
                    solver.Add(sum(f[i][j][s][di] for di in range(len(DIRECTIONS))) <= large_M * (1 - b[i][j][d]))
                    solver.Add(sum(f[i][j][s][di] for di in range(len(DIRECTIONS))) >= -large_M * (1 - b[i][j][d]))

    # 4. Flow through belt
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Output flow always lower or equal zero
                    solver.Add(f[i][j][s][d] <= large_M * (1 - b[i][j][d]))
                    for di in [DIRECTIONS.index(dir) for dir in BELT_INPUT_DIRECTIONS[DIRECTIONS[d]]]:
                        # Input flow always greater or equal zero
                        solver.Add(f[i][j][s][di] >= -large_M * (1 - b[i][j][d]))

    ##
    ## Flow constraints
    ##

    # 5. Flow on adjacent cells
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                # Flow into the cell must equal the flow out of the adjiacent cell
                if i > 0:
                    solver.Add(f[i][j][s][DIRECTIONS.index('W')] == - f[i-1][j][s][DIRECTIONS.index('E')])
                if i < W - 1:
                    solver.Add(f[i][j][s][DIRECTIONS.index('E')] == - f[i+1][j][s][DIRECTIONS.index('W')])
                if j > 0:
                    solver.Add(f[i][j][s][DIRECTIONS.index('S')] == - f[i][j-1][s][DIRECTIONS.index('N')])
                if j < H - 1:
                    solver.Add(f[i][j][s][DIRECTIONS.index('N')] == - f[i][j+1][s][DIRECTIONS.index('S')])

    # 6. Zero flow on border cells
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                if i == 0 and not any([input[0] == i and input[1] == j and input[3] == s and input[2] == 'E' for input in input_flows]):
                    solver.Add(f[i][j][s][DIRECTIONS.index('W')] == 0)
                if i == W - 1 and not any([input[0] == i and input[1] == j and input[3] == s and input[2] == 'W' for input in input_flows]):
                    solver.Add(f[i][j][s][DIRECTIONS.index('E')] == 0)
                if j == 0 and not any([input[0] == i and input[1] == j and input[3] == s and input[2] == 'S' for input in input_flows]):
                    solver.Add(f[i][j][s][DIRECTIONS.index('S')] == 0)
                if j == H - 1 and not any([input[0] == i and input[1] == j and input[3] == s and input[2] == 'N' for input in input_flows]):
                    solver.Add(f[i][j][s][DIRECTIONS.index('N')] == 0)

    # 7. Sum of flows for all sources can never exceed 1 or be below -1
    # TODO: revisit this constraint if different components support different max flows in the future
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                solver.Add(sum(f[i][j][s][d] for s in range(num_sources)) <= 1)
                solver.Add(sum(f[i][j][s][d] for s in range(num_sources)) >= -1)

    ##
    ## Mixer constraints
    ##

    # 8. Mixer can't have a cell outside of the grid
    # this is needed in order to avoid hald placed mixers with nonsensical flows
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                if not mixer_can_be_placed(i, j, DIRECTIONS[d], grid_size):
                    solver.Add(m[i][j][d] == 0)

    # 9. Flow through mixer
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    ci, cj = mixer_second_cell(i, j, DIRECTIONS[d])
                    if inside_grid(ci, cj, grid_size):
                        # Input and output flows sum to zero
                        solver.Add(
                            f[i][j][s][mixer_input_direction_idx(d)] + f[ci][cj][s][mixer_input_direction_idx(d)] + 
                            f[i][j][s][mixer_output_direction_idx(d)] + f[ci][cj][s][mixer_output_direction_idx(d)] <= 
                            large_M * (1 - m[i][j][d])
                        )
                        solver.Add(
                            f[i][j][s][mixer_input_direction_idx(d)] + f[ci][cj][s][mixer_input_direction_idx(d)] + 
                            f[i][j][s][mixer_output_direction_idx(d)] + f[ci][cj][s][mixer_output_direction_idx(d)] >= 
                            -large_M * (1 - m[i][j][d])
                        )
                        # Output flow is evenly distributed in the two cell outputs: the two outputs are identical
                        solver.Add(f[i][j][s][mixer_output_direction_idx(d)] - f[ci][cj][s][mixer_output_direction_idx(d)] <= large_M * (1 - m[i][j][d]))
                        solver.Add(f[i][j][s][mixer_output_direction_idx(d)] - f[ci][cj][s][mixer_output_direction_idx(d)] >= -large_M * (1 - m[i][j][d]))
                        # Input flows are gte zero
                        solver.Add(f[i][j][s][mixer_input_direction_idx(d)] >= -large_M * (1 - m[i][j][d]))
                        solver.Add(f[ci][cj][s][mixer_input_direction_idx(d)] >= -large_M * (1 - m[i][j][d]))
                        # Output flows are lte zero
                        solver.Add(f[i][j][s][mixer_output_direction_idx(d)] <= large_M * (1 - m[i][j][d]))
                        solver.Add(f[ci][cj][s][mixer_output_direction_idx(d)] <= large_M * (1 - m[i][j][d]))
                        # Zero flow from all the other directions that are not input or output
                        directions = mixer_zero_directions(DIRECTIONS[d])
                        for dir in directions:
                            # cell 1
                            solver.Add(f[i][j][s][DIRECTIONS.index(dir)] <= large_M * (1 - m[i][j][d]))
                            solver.Add(f[i][j][s][DIRECTIONS.index(dir)] >= -large_M * (1 - m[i][j][d]))
                            # cell 2
                            solver.Add(f[ci][cj][s][DIRECTIONS.index(dir)] <= large_M * (1 - m[i][j][d]))
                            solver.Add(f[ci][cj][s][DIRECTIONS.index(dir)] >= -large_M * (1 - m[i][j][d]))

    # Input constraints
    for input in input_flows:
        i, j, d, s, flow = input
        solver.Add(f[i][j][s][DIRECTIONS.index(d)] == flow)

    objective1 = solver.Sum(x[i][j] for i in range(W) for j in range(H))
    solver.Minimize(objective1)

    # Solve the problem
    status = solver.Solve()

    # Output the results
    if status == pywraplp.Solver.OPTIMAL:
        print('Solution')
        print('components:')
        print(viz_components(b, m, grid_size))
        print('occupied:')
        print(viz_occupied(x, grid_size))
        print('flows:')
        print(viz_flows(f, grid_size, num_sources))
        print(f'Minimum area: {solver.Objective().Value()}')
        return viz_components(b, m, grid_size)
    else:
        print('No optimal solution found.')
        return None

def viz_occupied(x, grid_size):
    W, H = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        # Iterate backward since Y axis is inverted
        for i in range(W):
            result += 'X' if x[i][j].solution_value() > 0 else 'O'
        result += '\n'
    return result

def viz_belts(b, grid_size):
    W, H = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        for i in range(W):
            result += ''.join([f"{DIRECTIONS_SYMBOL[DIRECTIONS[d]]}" if b[i][j][d].solution_value() > 0 else '' for d in range(len(DIRECTIONS))]) if sum(b[i][j][d].solution_value() for d in range(len(DIRECTIONS))) > 0 else 'O'
        result += '\n'
    return result

'''
Visualizes all the components of the belt balancer
'''
def viz_components(b, m, grid_size):
    W, H = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        for i in range(W):
            found = False
            # Visualize the belt
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                if b[i][j][d].solution_value() > 0:
                    result += f"{DIRECTIONS_SYMBOL[DIRECTIONS[d]]}"
                    found = True
            # Visualize the mixer first cell
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                if m[i][j][d].solution_value() > 0:
                    result += f"{MIXER_SYMBOL[DIRECTIONS[d]][0]}"
                    found = True
            # Visualize the mixer second cell
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                ci, cj = mixer_first_cell(i, j, DIRECTIONS[d])
                if inside_grid(ci, cj, grid_size) and m[ci][cj][d].solution_value() > 0:
                    result += f"{MIXER_SYMBOL[DIRECTIONS[d]][1]}"
                    found = True
            if not found:
                result += 'O'
        result += '\n'
    return result

def viz_flows(f, grid_size, num_flows):
    W, H = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        for i in range(W):
            for d in range(len(DIRECTIONS)):
                for s in range(num_flows):
                    if f[i][j][s][d].solution_value() != 0:
                        result += f"{DIRECTIONS_SYMBOL[DIRECTIONS[d]]}({s}){f[i][j][s][d].solution_value()} "
                result += ' '
            result += '| '
        result += '\n'
    return result

'''
Returns true if the mixer can be placed given the coordinates and direction of the first cell.
Note that the mixer i, j are the left cell of the mixer, so we need to keep into
account where the right cell is going to be based on the direction.
'''
def mixer_can_be_placed(i, j, d, grid_size):
    W, H = grid_size
    ci, cj = mixer_second_cell(i, j, d)
    result = inside_grid(i, j, grid_size) and inside_grid(ci, cj, grid_size)
    return result

def inside_grid(i, j, grid_size):
    W, H = grid_size
    return i >= 0 and i < W and j >= 0 and j < H

'''
Returns the coordinates of the second cell of the mixer given the coordinates of the first cell and the direction
'''
def mixer_second_cell(i, j, d):
    if d == 'N':
        return (i + 1, j)
    if d == 'S':
        return (i - 1, j)
    if d == 'E':
        return (i, j - 1)
    if d == 'W':
        return (i, j + 1)
    raise Exception('Invalid direction')

'''
Returns the coordinates of the first cell of the mixer given the coordinates of the second cell and the direction
'''
def mixer_first_cell(i, j, d):
    if d == 'N':
        return (i - 1, j)
    if d == 'S':
        return (i + 1, j)
    if d == 'E':
        return (i, j + 1)
    if d == 'W':
        return (i, j - 1)
    raise Exception('Invalid direction')

'''
Returns the input direction of the mixer
'''
def mixer_input_direction(d):
    if d == 'N':
        return 'S'
    if d == 'S':
        return 'N'
    if d == 'E':
        return 'W'
    if d == 'W':
        return 'E'
    raise Exception('Invalid direction')

'''
Like mixer_input_direction but takes the index of the direction and output index
'''
def mixer_input_direction_idx(d):
    return DIRECTIONS.index(mixer_input_direction(DIRECTIONS[d]))

'''
Returns the input direction of the mixer
identity function since the mixer direction is defined as the output one
'''
def mixer_output_direction(d):
    if d == 'N':
        return 'N'
    if d == 'S':
        return 'S'
    if d == 'E':
        return 'E'
    if d == 'W':
        return 'W'
    raise Exception('Invalid direction')

'''
Like mixer_output_direction but takes the index of the direction and output index
'''
def mixer_output_direction_idx(d):
    return DIRECTIONS.index(mixer_output_direction(DIRECTIONS[d]))

'''
Return the directions that have a flow of zero
'''
def mixer_zero_directions(d):
    if d == 'N':
        return ['E', 'W']
    if d == 'S':
        return ['E', 'W']
    if d == 'E':
        return ['N', 'S']
    if d == 'W':
        return ['N', 'S']
    raise Exception('Invalid direction')

# # Single belt balancer
# solve_factorio_belt_balancer((3, 3), 1, [
#     (0, 2, 'N', 0, -1),
#     (0, 0, 'S', 0, 1),
# ])

# Single mixer balancer
solve_factorio_belt_balancer((2, 3), 2, [
    (0, 0, 'S', 0, 1),
    (1, 0, 'S', 1, 1),
    (0, 2, 'N', 0, -0.5),
    (0, 2, 'N', 1, -0.5),
    (1, 2, 'N', 0, -0.5),
    (1, 2, 'N', 1, -0.5),
])