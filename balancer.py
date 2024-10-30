from ortools.linear_solver import pywraplp

DIRECTIONS = ('N', 'S', 'E', 'W')
DIRECTIONS_SYMBOL = ('^', 'v', '>', '<')
BELT_INPUT_DIRECTIONS = {
    'N': ['S', 'E', 'W'],
    'S': ['N', 'E', 'W'],
    'E': ['N', 'S', 'W'],
    'W': ['N', 'S', 'E'],
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
    x = [[solver.BoolVar(f'x_{i}_{j}') for j in range(H)] for i in range(W)]
    b = [[[solver.BoolVar(f'b_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    f = [[[[solver.NumVar(-1, 1, f'f_{i}_{j}_{s}_{d}') for d in DIRECTIONS] for s in range(num_sources)] for j in range(H)] for i in range(W)]

    # Constraints

    # Large constant M for big-M constraints
    large_M = 1000
    
    # 1. Occupied Cells Constraint
    for i in range(W):
        for j in range(H):
            # A cell is occupied if there's a belt
            solver.Add(x[i][j] == sum(b[i][j][d] for d in range(len(DIRECTIONS))))

    # 2. Empty Flow Constraints
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # No flow on empty cell
                    solver.Add(f[i][j][s][d] <= large_M *  x[i][j])
                    solver.Add(f[i][j][s][d] >= -large_M * x[i][j])

    # 3. Flow Conservation for Belts
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Flow into the belt must equal the flow out of the belt
                    solver.Add(sum(f[i][j][s][di] for di in range(len(DIRECTIONS))) <= large_M * (1 - b[i][j][d]))
                    solver.Add(sum(f[i][j][s][di] for di in range(len(DIRECTIONS))) >= -large_M * (1 - b[i][j][d]))

    # 4. Flow In/Out for Belts
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Output flow always lower or equal zero
                    solver.Add(f[i][j][s][d] <= large_M * (1 - b[i][j][d]))
                    for di in [DIRECTIONS.index(dir) for dir in BELT_INPUT_DIRECTIONS[DIRECTIONS[d]]]:
                        # Input flow always greater or equal zero
                        solver.Add(f[i][j][s][di] >= -large_M * (1 - b[i][j][d]))

    # 5. Flow constraints on adjacent cells
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

    # 6. Zero flow constraints on border cells
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                if i == 0 and not any([input[0] == i and input[1] == j and input[3] == s and input[2] == 'E' for input in input_flows]):
                    print('HERE', i, j, s)
                    solver.Add(f[i][j][s][DIRECTIONS.index('W')] == 0)
                if i == W - 1 and not any([input[0] == i and input[1] == j and input[3] == s and input[2] == 'W' for input in input_flows]):
                    solver.Add(f[i][j][s][DIRECTIONS.index('E')] == 0)
                if j == 0 and not any([input[0] == i and input[1] == j and input[3] == s and input[2] == 'S' for input in input_flows]):
                    solver.Add(f[i][j][s][DIRECTIONS.index('S')] == 0)
                if j == H - 1 and not any([input[0] == i and input[1] == j and input[3] == s and input[2] == 'N' for input in input_flows]):
                    solver.Add(f[i][j][s][DIRECTIONS.index('N')] == 0)

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
        print('belts:')
        print(viz_belts(b, grid_size))
        print('occupied:')
        print(viz_occupied(x, grid_size))
        # print('flows:')
        # print(viz_flows(f, grid_size, num_sources))
        print(f'Minimum area: {solver.Objective().Value()}')
    else:
        print('No optimal solution found.')
    return viz_belts(b, grid_size)

def viz_occupied(x, grid_size):
    H, W = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        # Iterate backward since Y axis is inverted
        for i in range(W):
            result += 'X' if x[i][j].solution_value() > 0 else 'O'
        result += '\n'
    return result

def viz_belts(b, grid_size):
    H, W = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        for i in range(W):
            result += ''.join([f"{DIRECTIONS_SYMBOL[d]}" if b[i][j][d].solution_value() > 0 else '' for d in range(len(DIRECTIONS))]) if sum(b[i][j][d].solution_value() for d in range(len(DIRECTIONS))) > 0 else 'O'
        result += '\n'
    return result

def viz_flows(f, grid_size, num_flows):
    H, W = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        for i in range(W):
            for d in range(len(DIRECTIONS)):
                for s in range(num_flows):
                    result += f"{i} {j} {s} {DIRECTIONS[d]} {f[i][j][s][d].solution_value()} "
                result += ' '
            result += '| '
        result += '\n'
    return result

solve_factorio_belt_balancer((3, 3), 1, [
    (0, 2, 'N', 0, -1),
    (0, 0, 'S', 0, 1),
])