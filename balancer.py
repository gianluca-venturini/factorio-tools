from ortools.sat.python import cp_model
from utils import DIRECTIONS, BELT_INPUT_DIRECTIONS, DIRECTIONS_SYMBOL, MIXER_SYMBOL, MAX_UNDERGROUND_DISTANCE, OPPOSITE_DIRECTIONS, encode_components_blueprint_json, viz_flows, viz_belts, viz_occupied, viz_components, mixer_can_be_placed, mixer_second_cell, mixer_first_cell, mixer_input_direction, mixer_output_direction, mixer_zero_directions, inside_grid, mixer_input_direction_idx, mixer_output_direction_idx, underground_exit_coordinates, underground_entrance_coordinates, underground_entrance_zero_directions, underground_exit_zero_directions, underground_entrance_flow_direction

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
    # entrance
    ua = [[[solver.NewBoolVar(f'ua_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    # exit
    ub = [[[solver.NewBoolVar(f'ub_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    # flow of a source in a direction
    f = [[[[solver.NewIntVar(-max_flow, max_flow, f'f_{i}_{j}_{s}_{d}') for d in DIRECTIONS] for s in range(num_sources)] for j in range(H)] for i in range(W)]
    # underground flow of a source in a direction
    uf = [[[[solver.NewIntVar(-max_flow, max_flow, f'uf_{i}_{j}_{s}_{d}') for d in DIRECTIONS] for s in range(num_sources)] for j in range(H)] for i in range(W)]

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
                # Underground belt entrance
                sum(ua[i][j][d] for d in range(len(DIRECTIONS))) +
                # Underground belt exit
                sum(ub[i][j][d] for d in range(len(DIRECTIONS)))
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

    # 7. Sum of flows for all sources can never exceed max_flow or be below -max_flow
    # TODO: revisit this constraint if different components support different max flows in the future
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                solver.Add(sum(f[i][j][s][d] for s in range(num_sources)) <= max_flow)
                solver.Add(sum(f[i][j][s][d] for s in range(num_sources)) >= -max_flow)

    ###
    ### Underground flow
    ###

    # Underground flow on adjacent cells
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                # Flow into the cell must equal the flow out of the adjiacent cell
                if i > 0:
                    solver.Add(uf[i][j][s][DIRECTIONS.index('W')] == - uf[i-1][j][s][DIRECTIONS.index('E')])
                if i < W - 1:
                    solver.Add(uf[i][j][s][DIRECTIONS.index('E')] == - uf[i+1][j][s][DIRECTIONS.index('W')])
                if j > 0:
                    solver.Add(uf[i][j][s][DIRECTIONS.index('S')] == - uf[i][j-1][s][DIRECTIONS.index('N')])
                if j < H - 1:
                    solver.Add(uf[i][j][s][DIRECTIONS.index('N')] == - uf[i][j+1][s][DIRECTIONS.index('S')])

    # Zero underground flow on border cells
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                if i == 0:
                    solver.Add(uf[i][j][s][DIRECTIONS.index('W')] == 0)
                if i == W - 1:
                    solver.Add(uf[i][j][s][DIRECTIONS.index('E')] == 0)
                if j == 0:
                    solver.Add(uf[i][j][s][DIRECTIONS.index('S')] == 0)
                if j == H - 1:
                    solver.Add(uf[i][j][s][DIRECTIONS.index('N')] == 0)

    # Flows continues on non-underground belt cell
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Continues in the same direction
                    solver.Add(uf[i][j][s][d] == - uf[i][j][s][DIRECTIONS.index(OPPOSITE_DIRECTIONS[DIRECTIONS[d]])]).only_enforce_if(
                        [ua[i][j][di].Not() for di in range(len(DIRECTIONS))] +
                        [ub[i][j][di].Not() for di in range(len(DIRECTIONS))]
                    )
                # # Incorrect constraint -- debug only
                # solver.Add(sum(uf[i][j][s][d] for d in range(len(DIRECTIONS))) == 0).only_enforce_if([ua[i][j][d].Not(), ub[i][j][d].Not()])

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
                    solver.Add(ua[i][j][d] == 0)
                    solver.Add(ub[i][j][d] == 0)

    # Ensures that for every entrance there's at least an exit before max distance is reached
    # this is necessary to prevent un underground flow longer than MAX_UNDERGROUND_DISTANCE
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                solver.Add(
                    sum(
                        ub[ci][cj][d]
                        for n in range(MAX_UNDERGROUND_DISTANCE)
                        for ci, cj in [underground_exit_coordinates(i, j, DIRECTIONS[d], n)]
                        if inside_grid(ci, cj, grid_size))
                        >= 1
                    ).only_enforce_if(ua[i][j][d])

    # 13. Flow through underground belt
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Entrance sends the flow underground
                    solver.Add(
                        f[i][j][s][DIRECTIONS.index(OPPOSITE_DIRECTIONS[DIRECTIONS[d]])] + 
                        uf[i][j][s][d] == 0
                    ).only_enforce_if(ua[i][j][d])
                    # Entrance opposite flow must be zero to prevent the flow from summing up with entering flows
                    # lateral flows are allowed because underground belts are allowed to cross
                    solver.Add(
                        uf[i][j][s][DIRECTIONS.index(OPPOSITE_DIRECTIONS[DIRECTIONS[d]])] == 0
                    ).only_enforce_if(ua[i][j][d])

                    # Exit receives the flow from underground
                    solver.Add(
                        f[i][j][s][d] + 
                        uf[i][j][s][DIRECTIONS.index(OPPOSITE_DIRECTIONS[DIRECTIONS[d]])] == 0
                    ).only_enforce_if(ub[i][j][d])
                    # After consuming the flow, it sends it to zero in the opposite direction
                    solver.Add(uf[i][j][s][d] == 0).only_enforce_if(ub[i][j][d])

                    # Flow balance in underground belt is zero across underground and upper ground
                    # Entrance
                    solver.Add(
                        sum(f[i][j][s][d] for d in range(len(DIRECTIONS))) +
                        sum(uf[i][j][s][d] for d in range(len(DIRECTIONS)))
                        == 0
                    ).only_enforce_if(ua[i][j][d])

                    # Exit
                    solver.Add(
                        sum(f[i][j][s][d] for d in range(len(DIRECTIONS))) +
                        sum(uf[i][j][s][d] for d in range(len(DIRECTIONS)))
                        == 0
                    ).only_enforce_if(ub[i][j][d])

    # 14. Flow direction
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Entrance flow is gte zero
                    solver.Add(f[i][j][s][DIRECTIONS.index(underground_entrance_flow_direction(DIRECTIONS[d]))] >= 0).only_enforce_if(ua[i][j][d])
                    # Exit flow is lte zero
                    solver.Add(f[i][j][s][d] <= 0).only_enforce_if(ub[i][j][d])
                    # Entrance flows are zero in all the other directions
                    for dir in underground_entrance_zero_directions(DIRECTIONS[d]):
                        solver.Add(f[i][j][s][DIRECTIONS.index(dir)] == 0).only_enforce_if(ua[i][j][d])
                    # Exit flows are zero in all the other directions
                    for dir in underground_exit_zero_directions(DIRECTIONS[d]):
                        solver.Add(f[i][j][s][DIRECTIONS.index(dir)] == 0).only_enforce_if(ub[i][j][d])

    # Input constraints
    for input in input_flows:
        i, j, d, s, flow = input
        solver.Add(f[i][j][s][DIRECTIONS.index(d)] == flow)

    objective1 = sum(x[i][j] for i in range(W) for j in range(H))
    solver.Minimize(objective1)

    # Configure the solver to use all available threads
    if max_parallel:
        solver.SetSolverSpecificParametersAsString("parallel/maxnthreads=0")  # Use all threads

    solver_cp = cp_model.CpSolver()
    solver_cp.parameters.log_search_progress = True  # This enables solver output
    
    if feasible_ok:
        # Set 10 minute time limit
        solver_cp.parameters.max_time_in_seconds = 300

    status = solver_cp.Solve(solver)
    print(solver_cp.ResponseStats())

    # Output the results
    if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
        print('Solution is', 'optimal' if status == cp_model.OPTIMAL else 'feasible')
        print('components:')
        print(viz_components(solver_cp, (b, m, ua, ub), grid_size))
        print('occupied:')
        print(viz_occupied(solver_cp, x, grid_size))
        print('flows:')
        print(viz_flows(solver_cp, f, grid_size, num_sources))
        print('underground flows:')
        print(viz_flows(solver_cp, uf, grid_size, num_sources))
        # print(f'Minimum area: {solver.Objective().Value()}')
        # print('Blueprint')
        # print(encode_components_blueprint_json(solver_cp, b, m, u, grid_size))
        return viz_components(solver_cp, (b, m, ua, ub), grid_size)
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
    # ], 1)

    # Balancer 3 x 3
    # solve_factorio_belt_balancer((5, 6), 3, [
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
    # solve_factorio_belt_balancer((4, 7), 4, [
    #     (0, 0, 'S', 0, 16),
    #     (1, 0, 'S', 1, 16),
    #     (2, 0, 'S', 2, 16),
    #     (3, 0, 'S', 3, 16),

    #     (0, 6, 'N', 0, -4),
    #     (0, 6, 'N', 1, -4),
    #     (0, 6, 'N', 2, -4),
    #     (0, 6, 'N', 3, -4),

    #     (1, 6, 'N', 0, -4),
    #     (1, 6, 'N', 1, -4),
    #     (1, 6, 'N', 2, -4),
    #     (1, 6, 'N', 3, -4),

    #     (2, 6, 'N', 0, -4),
    #     (2, 6, 'N', 1, -4),
    #     (2, 6, 'N', 2, -4),
    #     (2, 6, 'N', 3, -4),

    #     (3, 6, 'N', 0, -4),
    #     (3, 6, 'N', 1, -4),
    #     (3, 6, 'N', 2, -4),
    #     (3, 6, 'N', 3, -4),
    # ], 16)

    # Balancer 6 x 6
    solve_factorio_belt_balancer((8, 9), 6, [
        (1, 0, 'S', 0, 48),
        (2, 0, 'S', 1, 48),
        (3, 0, 'S', 2, 48),
        (4, 0, 'S', 3, 48),
        (5, 0, 'S', 4, 48),
        (6, 0, 'S', 5, 48),

        (0, 8, 'N', 0, -8),
        (0, 8, 'N', 1, -8),
        (0, 8, 'N', 2, -8),
        (0, 8, 'N', 3, -8),
        (0, 8, 'N', 4, -8),
        (0, 8, 'N', 5, -8),

        (1, 8, 'N', 0, -8),
        (1, 8, 'N', 1, -8),
        (1, 8, 'N', 2, -8),
        (1, 8, 'N', 3, -8),
        (1, 8, 'N', 4, -8),
        (1, 8, 'N', 5, -8),

        (2, 8, 'N', 0, -8),
        (2, 8, 'N', 1, -8),
        (2, 8, 'N', 2, -8),
        (2, 8, 'N', 3, -8),
        (2, 8, 'N', 4, -8),
        (2, 8, 'N', 5, -8),

        (3, 8, 'N', 0, -8),
        (3, 8, 'N', 1, -8),
        (3, 8, 'N', 2, -8),
        (3, 8, 'N', 3, -8),
        (3, 8, 'N', 4, -8),
        (3, 8, 'N', 5, -8),

        (4, 8, 'N', 0, -8),
        (4, 8, 'N', 1, -8),
        (4, 8, 'N', 2, -8),
        (4, 8, 'N', 3, -8),
        (4, 8, 'N', 4, -8),
        (4, 8, 'N', 5, -8),

        (5, 8, 'N', 0, -8),
        (5, 8, 'N', 1, -8),
        (5, 8, 'N', 2, -8),
        (5, 8, 'N', 3, -8),
        (5, 8, 'N', 4, -8),
        (5, 8, 'N', 5, -8),
    ], 48)

    # Balancer 6 x 6
    # Larger -- not tested
    # solve_factorio_belt_balancer((9, 9), 6, [
    #     (0, 0, 'S', 0, 24),
    #     (1, 0, 'S', 1, 24),
    #     (2, 0, 'S', 2, 24),
    #     (3, 0, 'S', 3, 24),
    #     (4, 0, 'S', 4, 24),
    #     (5, 0, 'S', 5, 24),

    #     (0, 8, 'N', 0, -4),
    #     (0, 8, 'N', 1, -4),
    #     (0, 8, 'N', 2, -4),
    #     (0, 8, 'N', 3, -4),
    #     (0, 8, 'N', 4, -4),
    #     (0, 8, 'N', 5, -4),

    #     (1, 8, 'N', 0, -4),
    #     (1, 8, 'N', 1, -4),
    #     (1, 8, 'N', 2, -4),
    #     (1, 8, 'N', 3, -4),
    #     (1, 8, 'N', 4, -4),
    #     (1, 8, 'N', 5, -4),

    #     (2, 8, 'N', 0, -4),
    #     (2, 8, 'N', 1, -4),
    #     (2, 8, 'N', 2, -4),
    #     (2, 8, 'N', 3, -4),
    #     (2, 8, 'N', 4, -4),
    #     (2, 8, 'N', 5, -4),

    #     (3, 8, 'N', 0, -4),
    #     (3, 8, 'N', 1, -4),
    #     (3, 8, 'N', 2, -4),
    #     (3, 8, 'N', 3, -4),
    #     (3, 8, 'N', 4, -4),
    #     (3, 8, 'N', 5, -4),

    #     (4, 8, 'N', 0, -4),
    #     (4, 8, 'N', 1, -4),
    #     (4, 8, 'N', 2, -4),
    #     (4, 8, 'N', 3, -4),
    #     (4, 8, 'N', 4, -4),
    #     (4, 8, 'N', 5, -4),

    #     (5, 8, 'N', 0, -4),
    #     (5, 8, 'N', 1, -4),
    #     (5, 8, 'N', 2, -4),
    #     (5, 8, 'N', 3, -4),
    #     (5, 8, 'N', 4, -4),
    #     (5, 8, 'N', 5, -4),
    # ], 24, feasible_ok=True)

    # solve_factorio_belt_balancer((10, 11), 6, [
    #     (2, 0, 'S', 0, 24),
    #     (3, 0, 'S', 1, 24),
    #     (4, 0, 'S', 2, 24),
    #     (5, 0, 'S', 3, 24),
    #     (6, 0, 'S', 4, 24),
    #     (7, 0, 'S', 5, 24),

    #     (2, 10, 'N', 0, -4),
    #     (2, 10, 'N', 1, -4),
    #     (2, 10, 'N', 2, -4),
    #     (2, 10, 'N', 3, -4),
    #     (2, 10, 'N', 4, -4),
    #     (2, 10, 'N', 5, -4),

    #     (3, 10, 'N', 0, -4),
    #     (3, 10, 'N', 1, -4),
    #     (3, 10, 'N', 2, -4),
    #     (3, 10, 'N', 3, -4),
    #     (3, 10, 'N', 4, -4),
    #     (3, 10, 'N', 5, -4),

    #     (4, 10, 'N', 0, -4),
    #     (4, 10, 'N', 1, -4),
    #     (4, 10, 'N', 2, -4),
    #     (4, 10, 'N', 3, -4),
    #     (4, 10, 'N', 4, -4),
    #     (4, 10, 'N', 5, -4),

    #     (5, 10, 'N', 0, -4),
    #     (5, 10, 'N', 1, -4),
    #     (5, 10, 'N', 2, -4),
    #     (5, 10, 'N', 3, -4),
    #     (5, 10, 'N', 4, -4),
    #     (5, 10, 'N', 5, -4),

    #     (6, 10, 'N', 0, -4),
    #     (6, 10, 'N', 1, -4),
    #     (6, 10, 'N', 2, -4),
    #     (6, 10, 'N', 3, -4),
    #     (6, 10, 'N', 4, -4),
    #     (6, 10, 'N', 5, -4),

    #     (7, 10, 'N', 0, -4),
    #     (7, 10, 'N', 1, -4),
    #     (7, 10, 'N', 2, -4),
    #     (7, 10, 'N', 3, -4),
    #     (7, 10, 'N', 4, -4),
    #     (7, 10, 'N', 5, -4),
    # ], 24)

    # # Balancer 8 x 8
    # solve_factorio_belt_balancer((8, 10), 8, [
    #     (0, 0, 'S', 0, 8),
    #     (1, 0, 'S', 1, 8),
    #     (2, 0, 'S', 2, 8),
    #     (3, 0, 'S', 3, 8),
    #     (4, 0, 'S', 4, 8),
    #     (5, 0, 'S', 5, 8),
    #     (6, 0, 'S', 6, 8),
    #     (7, 0, 'S', 7, 8),

    #     (0, 9, 'N', 0, -1),
    #     (0, 9, 'N', 1, -1),
    #     (0, 9, 'N', 2, -1),
    #     (0, 9, 'N', 3, -1),
    #     (0, 9, 'N', 4, -1),
    #     (0, 9, 'N', 5, -1),
    #     (0, 9, 'N', 6, -1),
    #     (0, 9, 'N', 7, -1),

    #     (1, 9, 'N', 0, -1),
    #     (1, 9, 'N', 1, -1),
    #     (1, 9, 'N', 2, -1),
    #     (1, 9, 'N', 3, -1),
    #     (1, 9, 'N', 4, -1),
    #     (1, 9, 'N', 5, -1),
    #     (1, 9, 'N', 6, -1),
    #     (1, 9, 'N', 7, -1),

    #     (2, 9, 'N', 0, -1),
    #     (2, 9, 'N', 1, -1),
    #     (2, 9, 'N', 2, -1),
    #     (2, 9, 'N', 3, -1),
    #     (2, 9, 'N', 4, -1),
    #     (2, 9, 'N', 5, -1),
    #     (2, 9, 'N', 6, -1),
    #     (2, 9, 'N', 7, -1),

    #     (3, 9, 'N', 0, -1),
    #     (3, 9, 'N', 1, -1),
    #     (3, 9, 'N', 2, -1),
    #     (3, 9, 'N', 3, -1),
    #     (3, 9, 'N', 4, -1),
    #     (3, 9, 'N', 5, -1),
    #     (3, 9, 'N', 6, -1),
    #     (3, 9, 'N', 7, -1),

    #     (4, 9, 'N', 0, -1),
    #     (4, 9, 'N', 1, -1),
    #     (4, 9, 'N', 2, -1),
    #     (4, 9, 'N', 3, -1),
    #     (4, 9, 'N', 4, -1),
    #     (4, 9, 'N', 5, -1),
    #     (4, 9, 'N', 6, -1),
    #     (4, 9, 'N', 7, -1),

    #     (5, 9, 'N', 0, -1),
    #     (5, 9, 'N', 1, -1),
    #     (5, 9, 'N', 2, -1),
    #     (5, 9, 'N', 3, -1),
    #     (5, 9, 'N', 4, -1),
    #     (5, 9, 'N', 5, -1),
    #     (5, 9, 'N', 6, -1),
    #     (5, 9, 'N', 7, -1),

    #     (6, 9, 'N', 0, -1),
    #     (6, 9, 'N', 1, -1),
    #     (6, 9, 'N', 2, -1),
    #     (6, 9, 'N', 3, -1),
    #     (6, 9, 'N', 4, -1),
    #     (6, 9, 'N', 5, -1),
    #     (6, 9, 'N', 6, -1),
    #     (6, 9, 'N', 7, -1),

    #     (7, 9, 'N', 0, -1),
    #     (7, 9, 'N', 1, -1),
    #     (7, 9, 'N', 2, -1),
    #     (7, 9, 'N', 3, -1),
    #     (7, 9, 'N', 4, -1),
    #     (7, 9, 'N', 5, -1),
    #     (7, 9, 'N', 6, -1),
    #     (7, 9, 'N', 7, -1),
    # ], 8)

    # Balancer 16 x 16
    # solve_factorio_belt_balancer((16, 16), 16, [
    #     # 16 inputs at the top, each with flow 16
    #     (0, 0, 'S', 0, 16),
    #     (1, 0, 'S', 1, 16),
    #     (2, 0, 'S', 2, 16),
    #     (3, 0, 'S', 3, 16),
    #     (4, 0, 'S', 4, 16),
    #     (5, 0, 'S', 5, 16),
    #     (6, 0, 'S', 6, 16),
    #     (7, 0, 'S', 7, 16),
    #     (8, 0, 'S', 8, 16),
    #     (9, 0, 'S', 9, 16),
    #     (10, 0, 'S', 10, 16),
    #     (11, 0, 'S', 11, 16),
    #     (12, 0, 'S', 12, 16),
    #     (13, 0, 'S', 13, 16),
    #     (14, 0, 'S', 14, 16),
    #     (15, 0, 'S', 15, 16),

    #     # Output 0
    #     (0, 15, 'N', 0, -1), (0, 15, 'N', 1, -1), (0, 15, 'N', 2, -1), (0, 15, 'N', 3, -1),
    #     (0, 15, 'N', 4, -1), (0, 15, 'N', 5, -1), (0, 15, 'N', 6, -1), (0, 15, 'N', 7, -1),
    #     (0, 15, 'N', 8, -1), (0, 15, 'N', 9, -1), (0, 15, 'N', 10, -1), (0, 15, 'N', 11, -1),
    #     (0, 15, 'N', 12, -1), (0, 15, 'N', 13, -1), (0, 15, 'N', 14, -1), (0, 15, 'N', 15, -1),

    #     # Output 1
    #     (1, 15, 'N', 0, -1), (1, 15, 'N', 1, -1), (1, 15, 'N', 2, -1), (1, 15, 'N', 3, -1),
    #     (1, 15, 'N', 4, -1), (1, 15, 'N', 5, -1), (1, 15, 'N', 6, -1), (1, 15, 'N', 7, -1),
    #     (1, 15, 'N', 8, -1), (1, 15, 'N', 9, -1), (1, 15, 'N', 10, -1), (1, 15, 'N', 11, -1),
    #     (1, 15, 'N', 12, -1), (1, 15, 'N', 13, -1), (1, 15, 'N', 14, -1), (1, 15, 'N', 15, -1),

    #     # Output 2
    #     (2, 15, 'N', 0, -1), (2, 15, 'N', 1, -1), (2, 15, 'N', 2, -1), (2, 15, 'N', 3, -1),
    #     (2, 15, 'N', 4, -1), (2, 15, 'N', 5, -1), (2, 15, 'N', 6, -1), (2, 15, 'N', 7, -1),
    #     (2, 15, 'N', 8, -1), (2, 15, 'N', 9, -1), (2, 15, 'N', 10, -1), (2, 15, 'N', 11, -1),
    #     (2, 15, 'N', 12, -1), (2, 15, 'N', 13, -1), (2, 15, 'N', 14, -1), (2, 15, 'N', 15, -1),

    #     # Output 3
    #     (3, 15, 'N', 0, -1), (3, 15, 'N', 1, -1), (3, 15, 'N', 2, -1), (3, 15, 'N', 3, -1),
    #     (3, 15, 'N', 4, -1), (3, 15, 'N', 5, -1), (3, 15, 'N', 6, -1), (3, 15, 'N', 7, -1),
    #     (3, 15, 'N', 8, -1), (3, 15, 'N', 9, -1), (3, 15, 'N', 10, -1), (3, 15, 'N', 11, -1),
    #     (3, 15, 'N', 12, -1), (3, 15, 'N', 13, -1), (3, 15, 'N', 14, -1), (3, 15, 'N', 15, -1),

    #     # Output 4
    #     (4, 15, 'N', 0, -1), (4, 15, 'N', 1, -1), (4, 15, 'N', 2, -1), (4, 15, 'N', 3, -1),
    #     (4, 15, 'N', 4, -1), (4, 15, 'N', 5, -1), (4, 15, 'N', 6, -1), (4, 15, 'N', 7, -1),
    #     (4, 15, 'N', 8, -1), (4, 15, 'N', 9, -1), (4, 15, 'N', 10, -1), (4, 15, 'N', 11, -1),
    #     (4, 15, 'N', 12, -1), (4, 15, 'N', 13, -1), (4, 15, 'N', 14, -1), (4, 15, 'N', 15, -1),

    #     # Output 5
    #     (5, 15, 'N', 0, -1), (5, 15, 'N', 1, -1), (5, 15, 'N', 2, -1), (5, 15, 'N', 3, -1),
    #     (5, 15, 'N', 4, -1), (5, 15, 'N', 5, -1), (5, 15, 'N', 6, -1), (5, 15, 'N', 7, -1),
    #     (5, 15, 'N', 8, -1), (5, 15, 'N', 9, -1), (5, 15, 'N', 10, -1), (5, 15, 'N', 11, -1),
    #     (5, 15, 'N', 12, -1), (5, 15, 'N', 13, -1), (5, 15, 'N', 14, -1), (5, 15, 'N', 15, -1),

    #     # Output 6
    #     (6, 15, 'N', 0, -1), (6, 15, 'N', 1, -1), (6, 15, 'N', 2, -1), (6, 15, 'N', 3, -1),
    #     (6, 15, 'N', 4, -1), (6, 15, 'N', 5, -1), (6, 15, 'N', 6, -1), (6, 15, 'N', 7, -1),
    #     (6, 15, 'N', 8, -1), (6, 15, 'N', 9, -1), (6, 15, 'N', 10, -1), (6, 15, 'N', 11, -1),
    #     (6, 15, 'N', 12, -1), (6, 15, 'N', 13, -1), (6, 15, 'N', 14, -1), (6, 15, 'N', 15, -1),

    #     # Output 7
    #     (7, 15, 'N', 0, -1), (7, 15, 'N', 1, -1), (7, 15, 'N', 2, -1), (7, 15, 'N', 3, -1),
    #     (7, 15, 'N', 4, -1), (7, 15, 'N', 5, -1), (7, 15, 'N', 6, -1), (7, 15, 'N', 7, -1),
    #     (7, 15, 'N', 8, -1), (7, 15, 'N', 9, -1), (7, 15, 'N', 10, -1), (7, 15, 'N', 11, -1),
    #     (7, 15, 'N', 12, -1), (7, 15, 'N', 13, -1), (7, 15, 'N', 14, -1), (7, 15, 'N', 15, -1),

    #     # Output 8
    #     (8, 15, 'N', 0, -1), (8, 15, 'N', 1, -1), (8, 15, 'N', 2, -1), (8, 15, 'N', 3, -1),
    #     (8, 15, 'N', 4, -1), (8, 15, 'N', 5, -1), (8, 15, 'N', 6, -1), (8, 15, 'N', 7, -1),
    #     (8, 15, 'N', 8, -1), (8, 15, 'N', 9, -1), (8, 15, 'N', 10, -1), (8, 15, 'N', 11, -1),
    #     (8, 15, 'N', 12, -1), (8, 15, 'N', 13, -1), (8, 15, 'N', 14, -1), (8, 15, 'N', 15, -1),

    #     # Output 9
    #     (9, 15, 'N', 0, -1), (9, 15, 'N', 1, -1), (9, 15, 'N', 2, -1), (9, 15, 'N', 3, -1),
    #     (9, 15, 'N', 4, -1), (9, 15, 'N', 5, -1), (9, 15, 'N', 6, -1), (9, 15, 'N', 7, -1),
    #     (9, 15, 'N', 8, -1), (9, 15, 'N', 9, -1), (9, 15, 'N', 10, -1), (9, 15, 'N', 11, -1),
    #     (9, 15, 'N', 12, -1), (9, 15, 'N', 13, -1), (9, 15, 'N', 14, -1), (9, 15, 'N', 15, -1),

    #     # Output 10
    #     (10, 15, 'N', 0, -1), (10, 15, 'N', 1, -1), (10, 15, 'N', 2, -1), (10, 15, 'N', 3, -1),
    #     (10, 15, 'N', 4, -1), (10, 15, 'N', 5, -1), (10, 15, 'N', 6, -1), (10, 15, 'N', 7, -1),
    #     (10, 15, 'N', 8, -1), (10, 15, 'N', 9, -1), (10, 15, 'N', 10, -1), (10, 15, 'N', 11, -1),
    #     (10, 15, 'N', 12, -1), (10, 15, 'N', 13, -1), (10, 15, 'N', 14, -1), (10, 15, 'N', 15, -1),

    #     # Output 11
    #     (11, 15, 'N', 0, -1), (11, 15, 'N', 1, -1), (11, 15, 'N', 2, -1), (11, 15, 'N', 3, -1),
    #     (11, 15, 'N', 4, -1), (11, 15, 'N', 5, -1), (11, 15, 'N', 6, -1), (11, 15, 'N', 7, -1),
    #     (11, 15, 'N', 8, -1), (11, 15, 'N', 9, -1), (11, 15, 'N', 10, -1), (11, 15, 'N', 11, -1),
    #     (11, 15, 'N', 12, -1), (11, 15, 'N', 13, -1), (11, 15, 'N', 14, -1), (11, 15, 'N', 15, -1),

    #     # Output 12
    #     (12, 15, 'N', 0, -1), (12, 15, 'N', 1, -1), (12, 15, 'N', 2, -1), (12, 15, 'N', 3, -1),
    #     (12, 15, 'N', 4, -1), (12, 15, 'N', 5, -1), (12, 15, 'N', 6, -1), (12, 15, 'N', 7, -1),
    #     (12, 15, 'N', 8, -1), (12, 15, 'N', 9, -1), (12, 15, 'N', 10, -1), (12, 15, 'N', 11, -1),
    #     (12, 15, 'N', 12, -1), (12, 15, 'N', 13, -1), (12, 15, 'N', 14, -1), (12, 15, 'N', 15, -1),

    #     # Output 13
    #     (13, 15, 'N', 0, -1), (13, 15, 'N', 1, -1), (13, 15, 'N', 2, -1), (13, 15, 'N', 3, -1),
    #     (13, 15, 'N', 4, -1), (13, 15, 'N', 5, -1), (13, 15, 'N', 6, -1), (13, 15, 'N', 7, -1),
    #     (13, 15, 'N', 8, -1), (13, 15, 'N', 9, -1), (13, 15, 'N', 10, -1), (13, 15, 'N', 11, -1),
    #     (13, 15, 'N', 12, -1), (13, 15, 'N', 13, -1), (13, 15, 'N', 14, -1), (13, 15, 'N', 15, -1),

    #     # Output 14
    #     (14, 15, 'N', 0, -1), (14, 15, 'N', 1, -1), (14, 15, 'N', 2, -1), (14, 15, 'N', 3, -1),
    #     (14, 15, 'N', 4, -1), (14, 15, 'N', 5, -1), (14, 15, 'N', 6, -1), (14, 15, 'N', 7, -1),
    #     (14, 15, 'N', 8, -1), (14, 15, 'N', 9, -1), (14, 15, 'N', 10, -1), (14, 15, 'N', 11, -1),
    #     (14, 15, 'N', 12, -1), (14, 15, 'N', 13, -1), (14, 15, 'N', 14, -1), (14, 15, 'N', 15, -1),

    #     # Output 15
    #     (15, 15, 'N', 0, -1), (15, 15, 'N', 1, -1), (15, 15, 'N', 2, -1), (15, 15, 'N', 3, -1),
    #     (15, 15, 'N', 4, -1), (15, 15, 'N', 5, -1), (15, 15, 'N', 6, -1), (15, 15, 'N', 7, -1),
    #     (15, 15, 'N', 8, -1), (15, 15, 'N', 9, -1), (15, 15, 'N', 10, -1), (15, 15, 'N', 11, -1),
    #     (15, 15, 'N', 12, -1), (15, 15, 'N', 13, -1), (15, 15, 'N', 14, -1), (15, 15, 'N', 15, -1),
    # ], 16)