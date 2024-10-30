from ortools.linear_solver import pywraplp

DIRECTIONS = ('N', 'S', 'E', 'W')
DIRECTIONS_SYMBOL = ('^', 'v', '>', '<')
BELT_INPUT_DIRECTIONS = {
    'N': ['S', 'E', 'W'],
    'S': ['N', 'E', 'W'],
    'E': ['N', 'S', 'W'],
    'W': ['N', 'S', 'E'],
}

def solve_factorio_belt_balancer(grid_size, input_flows):
    # Grid size
    W, H = grid_size


    # Create the solver
    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Decision variables
    x = [[solver.BoolVar(f'x_{i}_{j}') for j in range(H)] for i in range(W)]
    b = [[[solver.BoolVar(f'b_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    f = [[[solver.NumVar(-1, 1, f'f_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]

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
            for d in range(len(DIRECTIONS)):
                # No flow on empty cell
                solver.Add(f[i][j][d] <= large_M *  x[i][j])
                solver.Add(f[i][j][d] >= -large_M * x[i][j])

    # 3. Flow Conservation for Belts
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                # Flow into the belt must equal the flow out of the belt
                solver.Add(sum(f[i][j][di] for di in range(len(DIRECTIONS))) <= large_M * (1 - b[i][j][d]))
                solver.Add(sum(f[i][j][di] for di in range(len(DIRECTIONS))) >= -large_M * (1 - b[i][j][d]))

    # 4. Flow In/Out for Belts
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                # Output flow always lower than zero
                solver.Add(f[i][j][d] <= large_M * (1 - b[i][j][d]))
                for di in [DIRECTIONS.index(dir) for dir in BELT_INPUT_DIRECTIONS[DIRECTIONS[d]]]:
                    # Input flow always greater than zero
                    solver.Add(f[i][j][di] >= -large_M * (1 - b[i][j][d]))

    # 5. Flow constraints on adjacent cells
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                # Flow into the cell must equal the flow out of the cell
                if i > 0:
                    solver.Add(f[i][j][DIRECTIONS.index('W')] == - f[i-1][j][DIRECTIONS.index('E')])
                if i < W - 1:
                    solver.Add(f[i][j][DIRECTIONS.index('E')] == - f[i+1][j][DIRECTIONS.index('W')])
                if j > 0:
                    solver.Add(f[i][j][DIRECTIONS.index('S')] == - f[i][j-1][DIRECTIONS.index('N')])
                if j < H - 1:
                    solver.Add(f[i][j][DIRECTIONS.index('N')] == - f[i][j+1][DIRECTIONS.index('S')])

    # Input constraints
    for input in input_flows:
        i, j, d, flow = input
        solver.Add(f[i][j][DIRECTIONS.index(d)] == flow)

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

solve_factorio_belt_balancer((2, 2), [
    (0, 0, 'N', -1),
    (0, 0, 'S', 1),
])