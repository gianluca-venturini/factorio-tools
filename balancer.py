from ortools.sat.python import cp_model
from utils import DIRECTIONS, BELT_INPUT_DIRECTIONS, DIRECTIONS_SYMBOL, MIXER_SYMBOL, MAX_UNDERGROUND_DISTANCE, encode_components_blueprint_json, viz_flows, viz_belts, viz_occupied, viz_components, mixer_can_be_placed, mixer_second_cell, mixer_first_cell, mixer_input_direction, mixer_output_direction, mixer_zero_directions, inside_grid, mixer_input_direction_idx, mixer_output_direction_idx, underground_exit_coordinates, underground_entrance_coordinates, underground_entrance_zero_directions, underground_exit_zero_directions, underground_entrance_flow_direction

'''
Finds the minimum area of a belt balancer for a given grid size and input flows

grid_size: tuple (W, H) where W is the width and H is the height of the grid
num_sources: int number of flow sources
input_flows: list of tuples (i, j, d, flow) where i, j are the coordinates of the flow source, d is the direction of the flow, s the source number, and flow is the flow value
'''
def solve_factorio_belt_balancer(grid_size, num_sources, input_flows, max_flow, disable_belt=False, disable_underground=False, max_parallel=False, feasible_ok=False):
    # Grid size
    W, H = grid_size

    # Create the CP-SAT solver
    solver = cp_model.CpModel()

    # Decision variables
    # wheter a cell is occupied by a component
    x = [[solver.NewBoolVar(f'x_{i}_{j}') for j in range(H)] for i in range(W)]
    # belt in a direction
    b = [[[solver.NewBoolVar(f'b_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    # mixer in a direction. note that i, j are the left cell of the mixer
    m = [[[solver.NewBoolVar(f'm_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    # underground belt in a direction
    u = [[[[solver.NewBoolVar(f'u_{i}_{j}_{d}_{n}') for n in range(MAX_UNDERGROUND_DISTANCE)] for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    # flow of a source in a direction
    f = [[[[solver.NewIntVar(-max_flow, max_flow, f'f_{i}_{j}_{s}_{d}') for d in DIRECTIONS] for s in range(num_sources)] for j in range(H)] for i in range(W)]

    # Constraints
    
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
                    solver.Add(f[i][j][s][d] == 0).only_enforce_if(x[i][j].Not())

    ##
    ## Belt constraints
    ##

    if disable_belt:
        for i in range(W):
            for j in range(H):
                for d in range(len(DIRECTIONS)):
                    solver.Add(b[i][j][d] == 0)

    # 3. Flow Conservation for Belts
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Flow into the belt must equal the flow out of the belt
                    solver.Add(sum(f[i][j][s][di] for di in range(len(DIRECTIONS))) == 0).only_enforce_if(b[i][j][d])

    # 4. Flow through belt
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Output flow always lower or equal zero
                    solver.Add(f[i][j][s][d] <= 0).only_enforce_if(b[i][j][d])
                    for di in [DIRECTIONS.index(dir) for dir in BELT_INPUT_DIRECTIONS[DIRECTIONS[d]]]:
                        # Input flow always greater or equal zero
                        solver.Add(f[i][j][s][di] >= 0).only_enforce_if(b[i][j][d])

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
                solver.Add(sum(f[i][j][s][d] for s in range(num_sources)) <= max_flow)
                solver.Add(sum(f[i][j][s][d] for s in range(num_sources)) >= -max_flow)

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
                            f[i][j][s][mixer_output_direction_idx(d)] + f[ci][cj][s][mixer_output_direction_idx(d)] == 
                            0
                        ).only_enforce_if(m[i][j][d])
                        # Output flow is evenly distributed in the two cell outputs: the two outputs are identical
                        solver.Add(f[i][j][s][mixer_output_direction_idx(d)] - f[ci][cj][s][mixer_output_direction_idx(d)] == 0).only_enforce_if(m[i][j][d])
                        # Input flows are gte zero
                        solver.Add(f[i][j][s][mixer_input_direction_idx(d)] >= 0).only_enforce_if(m[i][j][d])
                        solver.Add(f[ci][cj][s][mixer_input_direction_idx(d)] >= 0).only_enforce_if(m[i][j][d])
                        # Output flows are lte zero
                        solver.Add(f[i][j][s][mixer_output_direction_idx(d)] <= 0).only_enforce_if(m[i][j][d])
                        solver.Add(f[ci][cj][s][mixer_output_direction_idx(d)] <= 0).only_enforce_if(m[i][j][d])
                        # Zero flow from all the other directions that are not input or output
                        directions = mixer_zero_directions(DIRECTIONS[d])
                        for dir in directions:
                            # cell 1
                            solver.Add(f[i][j][s][DIRECTIONS.index(dir)] == 0).only_enforce_if(m[i][j][d])
                            # cell 2
                            solver.Add(f[ci][cj][s][DIRECTIONS.index(dir)] == 0).only_enforce_if(m[i][j][d])

    ##
    ## Underground belt constraints
    ##

    if disable_underground:
        for i in range(W):
            for j in range(H):
                for d in range(len(DIRECTIONS)):
                    for n in range(MAX_UNDERGROUND_DISTANCE):
                        solver.Add(u[i][j][d][n] == 0)

    # 10. Underground belt can't have a cell outside of the grid
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                for n in range(MAX_UNDERGROUND_DISTANCE):
                    ci, cj = underground_exit_coordinates(i, j, DIRECTIONS[d], n)
                    if not inside_grid(ci, cj, grid_size):
                        solver.Add(u[i][j][d][n] == 0)

    # 11. Flow through underground belt
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    for n in range(MAX_UNDERGROUND_DISTANCE):
                        ci, cj = underground_exit_coordinates(i, j, DIRECTIONS[d], n)
                        if inside_grid(ci, cj, grid_size):
                            # Entrance and exit flows sum to zero
                            solver.Add(
                                f[i][j][s][DIRECTIONS.index(underground_entrance_flow_direction(DIRECTIONS[d]))] + f[ci][cj][s][d] == 0
                            ).only_enforce_if(u[i][j][d][n])
                            # Input flow is gte zero
                            solver.Add(f[i][j][s][DIRECTIONS.index(underground_entrance_flow_direction(DIRECTIONS[d]))] >= 0).only_enforce_if(u[i][j][d][n])
                            # Output flow is lte zero
                            solver.Add(f[ci][cj][s][d] <= 0).only_enforce_if(u[i][j][d][n])

                            # Zero flow from all the other directions in entrance
                            for dir in underground_entrance_zero_directions(DIRECTIONS[d]):
                                solver.Add(f[i][j][s][DIRECTIONS.index(dir)] == 0).only_enforce_if(u[i][j][d][n])

                            # Zero flow from all the other directions in exit
                            for dir in underground_exit_zero_directions(DIRECTIONS[d]):
                                solver.Add(f[ci][cj][s][DIRECTIONS.index(dir)] == 0).only_enforce_if(u[i][j][d][n])

    # 12. No entrance between entrance and exit
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                for n in range(MAX_UNDERGROUND_DISTANCE):
                    for d2 in range(len(DIRECTIONS)):
                        for n2 in range(n):
                            ci, cj = underground_exit_coordinates(i, j, DIRECTIONS[d], n2)
                            if not inside_grid(ci, cj, grid_size):
                                continue
                            for n3 in range(MAX_UNDERGROUND_DISTANCE):
                                solver.Add(u[ci][cj][d2][n3] == 0).only_enforce_if(u[i][j][d][n])
                                
                            

    # Input constraints
    for input in input_flows:
        i, j, d, s, flow = input
        solver.Add(f[i][j][s][DIRECTIONS.index(d)] == flow)

    objective1 = sum(x[i][j] for i in range(W) for j in range(H))
    # solver.Minimize(objective1)
    solver.Minimize(objective1)

    # Configure the solver to use all available threads
    if max_parallel:
        solver.SetSolverSpecificParametersAsString("parallel/maxnthreads=0")  # Use all threads

    if feasible_ok:
        solver.SetSolverSpecificParametersAsString("""
            limits/time = 10
            limits/solutions = 1
        """)

    # solver.EnableOutput()

    # Solve the problem
    # status = solver.Solve()

    solver_cp = cp_model.CpSolver()
    status = solver_cp.Solve(solver)

    # Output the results
    if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
        print('Solution is', 'optimal' if status == cp_model.OPTIMAL else 'feasible')
        print('components:')
        print(viz_components(solver_cp, b, m, u, grid_size))
        print('occupied:')
        print(viz_occupied(solver_cp, x, grid_size))
        print('flows:')
        print(viz_flows(solver_cp, f, grid_size, num_sources))
        # print(f'Minimum area: {solver.Objective().Value()}')
        # print('Blueprint')
        # print(encode_components_blueprint_json(solver_cp, b, m, u, grid_size))
        return viz_components(solver_cp, b, m, u, grid_size)
    elif status == cp_model.INFEASIBLE:
        print('No optimal solution found.')
        return None
    else:
        raise Exception(f'Unexpected solver status: {status}')

# if main
if __name__ == '__main__':

    # Single belt balancer
    # solve_factorio_belt_balancer((3, 3), 1, [
    #     (0, 2, 'N', 0, -1),
    #     (0, 0, 'S', 0, 1),
    # ], 1, disable_underground=True)

    # Mixer 2 x 1
    # solve_factorio_belt_balancer((2, 1), 2, [
    #     (0, 0, 'S', 0, 2),
    #     (1, 0, 'S', 1, 2),
    #     (0, 0, 'N', 0, -1),
    #     (0, 0, 'N', 1, -1),
    #     (1, 0, 'N', 0, -1),
    #     (1, 0, 'N', 1, -1),
    # ], 2)

    # # Single mixer balancer
    # solve_factorio_belt_balancer((2, 3), 2, [
    #     (0, 0, 'S', 0, 2),
    #     (1, 0, 'S', 1, 2),
    #     (0, 2, 'N', 0, -1),
    #     (0, 2, 'N', 1, -1),
    #     (1, 2, 'N', 0, -1),
    #     (1, 2, 'N', 1, -1),
    # ], 2)

    # Undergroun 2 belts
    # solve_factorio_belt_balancer((5, 6), 2, [
    #     (2, 0, 'S', 0, 1),
    #     (3, 0, 'S', 1, 1),
    #     (3, 5, 'N', 0, -1),
    #     (2, 5, 'N', 1, -1),
    # ])

    # Balancer 3 x 3
    # solve_factorio_belt_balancer((6, 6), 3, [
    #     (0, 0, 'S', 0, 24),
    #     (1, 0, 'S', 1, 24),
    #     (2, 0, 'S', 2, 24),

    #     (1, 5, 'N', 0, -8),
    #     (1, 5, 'N', 1, -8),
    #     (1, 5, 'N', 2, -8),

    #     (2, 5, 'N', 0, -8),
    #     (2, 5, 'N', 1, -8),
    #     (2, 5, 'N', 2, -8),

    #     (3, 5, 'N', 0, -8),
    #     (3, 5, 'N', 1, -8),
    #     (3, 5, 'N', 2, -8),
    # ], 24)

    # Balancer 4 x 4
    solve_factorio_belt_balancer((4, 8), 4, [
        (0, 0, 'S', 0, 16),
        (1, 0, 'S', 1, 16),
        (2, 0, 'S', 2, 16),
        (3, 0, 'S', 3, 16),

        (0, 7, 'N', 0, -4),
        (0, 7, 'N', 1, -4),
        (0, 7, 'N', 2, -4),
        (0, 7, 'N', 3, -4),

        (1, 7, 'N', 0, -4),
        (1, 7, 'N', 1, -4),
        (1, 7, 'N', 2, -4),
        (1, 7, 'N', 3, -4),

        (2, 7, 'N', 0, -4),
        (2, 7, 'N', 1, -4),
        (2, 7, 'N', 2, -4),
        (2, 7, 'N', 3, -4),

        (3, 7, 'N', 0, -4),
        (3, 7, 'N', 1, -4),
        (3, 7, 'N', 2, -4),
        (3, 7, 'N', 3, -4),
    ], 16)