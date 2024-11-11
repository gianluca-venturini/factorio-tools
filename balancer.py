from ortools.linear_solver import pywraplp
from utils import DIRECTIONS, BELT_INPUT_DIRECTIONS, DIRECTIONS_SYMBOL, MIXER_SYMBOL, MAX_UNDERGROUND_DISTANCE, encode_components_blueprint_json, viz_flows, viz_belts, viz_occupied, viz_components, mixer_can_be_placed, mixer_second_cell, mixer_first_cell, mixer_input_direction, mixer_output_direction, mixer_zero_directions, inside_grid, mixer_input_direction_idx, mixer_output_direction_idx, underground_exit_coordinates, underground_entrance_coordinates

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
    # underground belt in a direction
    u = [[[[solver.BoolVar(f'u_{i}_{j}_{d}_{n}') for n in range(MAX_UNDERGROUND_DISTANCE)] for d in DIRECTIONS] for j in range(H)] for i in range(W)]
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
                # Mixer first cell i, j
                sum(m[i][j][d] for d in range(len(DIRECTIONS)) if mixer_can_be_placed(i, j, DIRECTIONS[d], grid_size)) +
                # Mixer first cell in ci, cj. Second cell in i, j
                sum(m[ci][cj][d] for d in range(len(DIRECTIONS)) for ci, cj in [mixer_first_cell(i, j, DIRECTIONS[d])] if inside_grid(ci, cj, grid_size)) +
                # Underground belt entrance in cell i, j
                sum(u[i][j][d][n] for n in range(MAX_UNDERGROUND_DISTANCE) for d in range(len(DIRECTIONS))) +
                # Underground belt exit in cell i, j. Entrance in ci, cj
                sum(u[ci][cj][d][n] for n in range(MAX_UNDERGROUND_DISTANCE) for d in range(len(DIRECTIONS)) for ci, cj in [underground_entrance_coordinates(i, j, DIRECTIONS[d], n)] if inside_grid(ci, cj, grid_size))
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
        print('Blueprint')
        print(encode_components_blueprint_json(b, m, grid_size))
        return viz_components(b, m, grid_size)
    else:
        print('No optimal solution found.')
        return None

# # Single belt balancer
# solve_factorio_belt_balancer((3, 3), 1, [
#     (0, 2, 'N', 0, -1),
#     (0, 0, 'S', 0, 1),
# ])

# # Single mixer balancer
# solve_factorio_belt_balancer((2, 3), 2, [
#     (0, 0, 'S', 0, 1),
#     (1, 0, 'S', 1, 1),
#     (0, 2, 'N', 0, -0.5),
#     (0, 2, 'N', 1, -0.5),
#     (1, 2, 'N', 0, -0.5),
#     (1, 2, 'N', 1, -0.5),
# ])

# Undergroun 2 belts
solve_factorio_belt_balancer((6, 6), 2, [
    (2, 0, 'S', 0, 1),
    (3, 0, 'S', 1, 1),
    (3, 5, 'N', 0, -1),
    (2, 5, 'N', 1, -1),
])