from ortools.sat.python import cp_model
from utils import (
    DIRECTIONS,
    BELT_INPUT_DIRECTIONS,
    MAX_UNDERGROUND_DISTANCE,
    OPPOSITE_DIRECTIONS,
    underground_exit_coordinates,
    viz_flows,
    viz_components,
    mixer_can_be_placed,
    mixer_second_cell,
    mixer_first_cell, 
    mixer_zero_directions, 
    inside_grid, 
    mixer_input_direction_idx, 
    mixer_output_direction_idx, 
    underground_entrance_zero_directions, 
    underground_exit_zero_directions, 
    underground_entrance_flow_direction, 
    load_solution,
    viz_variables_verbose
)
from blueprint import encode_components_blueprint_json, generate_entities_blueprint

'''
Finds the minimum area of a belt balancer for a given grid size and input flows

grid_size: tuple (W, H) where W is the width and H is the height of the grid
num_sources: int number of flow sources
input_flows: list of tuples (i, j, d, flow) where i, j are the coordinates of the flow source, d is the direction of the flow, s the source number, and flow is the flow value
'''
def solve_factorio_belt_balancer(
        grid_size,
        num_sources,
        input_flows,
        max_flow,
        disable_belt=False,
        disable_underground=False,
        max_parallel=False,
        feasible_ok=False,
        time_limit=False,
        solution=None,
        hint_solutions=None,
        disable_solve=False,
        deterministic_time=False,
        network_solution=None,
    ):
    # Grid size
    W, H = grid_size

    num_mixers = len(network_solution) if network_solution is not None else 1

    # Create the CP-SAT solver
    solver = cp_model.CpModel()

    # Decision variables
    # belt in a direction
    b = [[solver.NewBoolVar(f'b_{i}_{j}') for j in range(H)] for i in range(W)]
    # mixer in a direction. note that i, j are the left cell of the mixer
    m = [[solver.NewBoolVar(f'm_{i}_{j}') for j in range(H)] for i in range(W)]
    # underground belt in a direction
    # entrance
    ua = [[solver.NewBoolVar(f'ua_{i}_{j}') for j in range(H)] for i in range(W)]
    # exit
    ub = [[solver.NewBoolVar(f'ub_{i}_{j}') for j in range(H)] for i in range(W)]
    # flow of a source in a direction
    f = [[[[solver.NewIntVar(-max_flow, max_flow, f'f_{i}_{j}_{s}_{d}') for d in DIRECTIONS] for s in range(num_sources)] for j in range(H)] for i in range(W)]
    # underground flow of a source in a direction
    uf = [[[[solver.NewIntVar(-max_flow, max_flow, f'uf_{i}_{j}_{s}_{d}') for d in DIRECTIONS] for s in range(num_sources)] for j in range(H)] for i in range(W)]
    # Direction of the component
    dc = [[[solver.NewBoolVar(f'd_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]
    # Direction of mixer
    dm = [[[solver.NewBoolVar(f'dm_{i}_{j}_{d}') for d in DIRECTIONS] for j in range(H)] for i in range(W)]

    variables = (b, m, ua, ub, dc, dm)

    # Mixer direction is the same as the mixer component
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                solver.AddMultiplicationEquality(dm[i][j][d], [m[i][j], dc[i][j][d]])

    # Constraints

    # Only one direction active at a time
    for i in range(W):
        for j in range(H):
            solver.AddExactlyOne([dc[i][j][d] for d in range(len(DIRECTIONS))])

    def components_in_cell(i, j):
        return (
            [b[i][j]] +
            [m[i][j]] +
            [dm[ci][cj][d] for d in range(len(DIRECTIONS)) for ci, cj in [mixer_first_cell(i, j, DIRECTIONS[d])] if inside_grid(ci, cj, grid_size)] +
            [ua[i][j]] +
            [ub[i][j]]
        )
    
    # 1. Occupied Cells Constraint
    for i in range(W):
        for j in range(H):
            solver.AddAtMostOne(components_in_cell(i, j))

    # 2. Empty Flow Constraints
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # No flow on empty cell
                    solver.Add(f[i][j][s][d] == 0).only_enforce_if([x.Not() for x in components_in_cell(i, j)])

    ##
    ## Belt constraints
    ##

    if disable_belt:
        for i in range(W):
            for j in range(H):
                solver.Add(b[i][j] == 0)

    # 3. Flow Conservation for Belts
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Flow into the belt must equal the flow out of the belt
                    solver.Add(sum(f[i][j][s][di] for di in range(len(DIRECTIONS))) == 0).only_enforce_if([b[i][j], dc[i][j][d]])

    # 4. Flow through belt
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Output flow always lower or equal zero
                    solver.Add(f[i][j][s][d] <= 0).only_enforce_if([b[i][j], dc[i][j][d]])
                    for di in [DIRECTIONS.index(dir) for dir in BELT_INPUT_DIRECTIONS[DIRECTIONS[d]]]:
                        # Input flow always greater or equal zero
                        solver.Add(f[i][j][s][di] >= 0).only_enforce_if([b[i][j], dc[i][j][d]])

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
                        [ua[i][j].Not(), ub[i][j].Not()]
                    )

    ##
    ## Mixer constraints
    ##

    # 8. Mixer can't have a cell outside of the grid
    # this is needed in order to avoid hald placed mixers with nonsensical flows
    for i in range(W):
        for j in range(H):
            for d in range(len(DIRECTIONS)):
                if not mixer_can_be_placed(i, j, DIRECTIONS[d], grid_size):
                    solver.Add(dc[i][j][d] == 0).only_enforce_if(m[i][j])


    # Source flow constraints on every mixer
    if network_solution is not None:
        # Create boolean variables to represent mixer type conditions
        mixer_network = [[[solver.NewBoolVar(f"mixer_network_{i}_{j}_{n}") for n in range(num_mixers)] for j in range(H)] for i in range(W)]
    
        # Enforce that exactly one mixer is placed for each element in network_solution
        for n in range(num_mixers):
            solver.Add(sum(mixer_network[i][j][n] for i in range(W) for j in range(H)) == 1)

        for i in range(W):
            for j in range(H):
                for d in range(len(DIRECTIONS)):
                    solver.Add(sum(mixer_network[i][j][n] for n in range(num_mixers)) == 1).only_enforce_if([m[i][j], dc[i][j][d]])

        for n in range(num_mixers):
            inputs, outputs = network_solution[n]
            for i in range(W):
                for j in range(H):
                    for d in range(len(DIRECTIONS)):
                        ci, cj = mixer_second_cell(i, j, DIRECTIONS[d])
                        if inside_grid(ci, cj, grid_size):
                            # Input flow and output flows are the same
                            solver.Add(
                                sum(
                                    (
                                        f[i][j][s][mixer_input_direction_idx(d)] +
                                        f[ci][cj][s][mixer_input_direction_idx(d)] + 
                                        f[i][j][s][mixer_output_direction_idx(d)] + 
                                        f[ci][cj][s][mixer_output_direction_idx(d)]
                                    )
                                    for s in range(num_sources)
                                ) == 
                                0
                            ).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                            # Output flow is evenly distributed in the two cell outputs: the two outputs are identical
                            solver.Add(sum(f[i][j][s][mixer_output_direction_idx(d)] - f[ci][cj][s][mixer_output_direction_idx(d)] for s in range(num_sources)) == 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                            zero_directions = mixer_zero_directions(DIRECTIONS[d])
                            for s in range(num_sources):
                                for dir in zero_directions:
                                    solver.Add(f[i][j][s][DIRECTIONS.index(dir)] == 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                                    solver.Add(f[ci][cj][s][DIRECTIONS.index(dir)] == 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])

                                if s in inputs:
                                    # Input sources flow is gte zero
                                    solver.Add(f[i][j][s][mixer_input_direction_idx(d)] >= 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                                    solver.Add(f[ci][cj][s][mixer_input_direction_idx(d)] >= 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                                    # Force the source to enter from one of the two cells
                                    solver.Add(f[i][j][s][mixer_input_direction_idx(d)] + f[ci][cj][s][mixer_input_direction_idx(d)] > 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                                else:
                                    solver.Add(f[i][j][s][mixer_input_direction_idx(d)] == 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                                    solver.Add(f[ci][cj][s][mixer_input_direction_idx(d)] == 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])

                                if s in outputs:
                                    # Output sources flow is lte zero
                                    solver.Add(f[i][j][s][mixer_output_direction_idx(d)] <= 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                                    solver.Add(f[ci][cj][s][mixer_output_direction_idx(d)] <= 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                                    # Force the source to exit from one of the two cells
                                    solver.Add(f[i][j][s][mixer_output_direction_idx(d)] + f[ci][cj][s][mixer_output_direction_idx(d)] < 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                                else:
                                    solver.Add(f[i][j][s][mixer_output_direction_idx(d)] == 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
                                    solver.Add(f[ci][cj][s][mixer_output_direction_idx(d)] == 0).only_enforce_if([m[i][j], mixer_network[i][j][n], dc[i][j][d]])
    else:
        # Regular flow through mixer
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
                            ).only_enforce_if([m[i][j], dc[i][j][d]])
                            # Output flow is evenly distributed in the two cell outputs: the two outputs are identical
                            solver.Add(f[i][j][s][mixer_output_direction_idx(d)] - f[ci][cj][s][mixer_output_direction_idx(d)] == 0).only_enforce_if([m[i][j], dc[i][j][d]])
                            # Input flows are gte zero
                            solver.Add(f[i][j][s][mixer_input_direction_idx(d)] >= 0).only_enforce_if([m[i][j], dc[i][j][d]])
                            solver.Add(f[ci][cj][s][mixer_input_direction_idx(d)] >= 0).only_enforce_if([m[i][j], dc[i][j][d]])
                            # Output flows are lte zero
                            solver.Add(f[i][j][s][mixer_output_direction_idx(d)] <= 0).only_enforce_if([m[i][j], dc[i][j][d]])
                            solver.Add(f[ci][cj][s][mixer_output_direction_idx(d)] <= 0).only_enforce_if([m[i][j], dc[i][j][d]])
                            # Zero flow from all the other directions that are not input or output
                            directions = mixer_zero_directions(DIRECTIONS[d])
                            for dir in directions:
                                # cell 1
                                solver.Add(f[i][j][s][DIRECTIONS.index(dir)] == 0).only_enforce_if([m[i][j], dc[i][j][d]])
                                # cell 2
                                solver.Add(f[ci][cj][s][DIRECTIONS.index(dir)] == 0).only_enforce_if([m[i][j], dc[i][j][d]])

    ##
    ## Underground belt constraints
    ##

    if disable_underground:
        for i in range(W):
            for j in range(H):
                solver.Add(ua[i][j] == 0)
                solver.Add(ub[i][j] == 0)

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
                    ).only_enforce_if([ua[i][j], dc[i][j][d]])

    # 13. Flow through underground belt
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Entrance sends the flow underground
                    solver.Add(
                        f[i][j][s][DIRECTIONS.index(OPPOSITE_DIRECTIONS[DIRECTIONS[d]])] + 
                        uf[i][j][s][d] == 0
                    ).only_enforce_if([ua[i][j], dc[i][j][d]])
                    # Entrance opposite flow must be zero to prevent the flow from summing up with entering flows
                    # lateral flows are allowed because underground belts are allowed to cross
                    solver.Add(
                        uf[i][j][s][DIRECTIONS.index(OPPOSITE_DIRECTIONS[DIRECTIONS[d]])] == 0
                    ).only_enforce_if([ua[i][j], dc[i][j][d]])

                    # Exit receives the flow from underground
                    solver.Add(
                        f[i][j][s][d] + 
                        uf[i][j][s][DIRECTIONS.index(OPPOSITE_DIRECTIONS[DIRECTIONS[d]])] == 0
                    ).only_enforce_if([ub[i][j], dc[i][j][d]])
                    # After consuming the flow, it sends it to zero in the opposite direction
                    solver.Add(uf[i][j][s][d] == 0).only_enforce_if([ub[i][j], dc[i][j][d]])

                    # Flow balance in underground belt is zero across underground and upper ground
                    # Entrance
                    solver.Add(
                        sum(f[i][j][s][d] for d in range(len(DIRECTIONS))) +
                        sum(uf[i][j][s][d] for d in range(len(DIRECTIONS)))
                        == 0
                    ).only_enforce_if([ua[i][j], dc[i][j][d]])

                    # Exit
                    solver.Add(
                        sum(f[i][j][s][d] for d in range(len(DIRECTIONS))) +
                        sum(uf[i][j][s][d] for d in range(len(DIRECTIONS)))
                        == 0
                    ).only_enforce_if([ub[i][j], dc[i][j][d]])

    # 14. Flow direction
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    # Entrance flow is gte zero
                    solver.Add(f[i][j][s][DIRECTIONS.index(underground_entrance_flow_direction(DIRECTIONS[d]))] >= 0).only_enforce_if([ua[i][j], dc[i][j][d]])
                    # Exit flow is lte zero
                    solver.Add(f[i][j][s][d] <= 0).only_enforce_if([ub[i][j], dc[i][j][d]])
                    # Entrance flows are zero in all the other directions
                    for dir in underground_entrance_zero_directions(DIRECTIONS[d]):
                        solver.Add(f[i][j][s][DIRECTIONS.index(dir)] == 0).only_enforce_if([ua[i][j], dc[i][j][d]])
                    # Exit flows are zero in all the other directions
                    for dir in underground_exit_zero_directions(DIRECTIONS[d]):
                        solver.Add(f[i][j][s][DIRECTIONS.index(dir)] == 0).only_enforce_if([ub[i][j], dc[i][j][d]])

    # Input constraints
    for input in input_flows:
        i, j, d, s, flow = input
        solver.Add(f[i][j][s][DIRECTIONS.index(d)] == flow)

    # Hints
    for i in range(W):
        for j in range(H):
            for s in range(num_sources):
                for d in range(len(DIRECTIONS)):
                    solver.AddHint(uf[i][j][s][d], 0)

    if hint_solutions is not None:
        for hint_solution in hint_solutions:
            load_solution(solver, variables, hint_solution, grid_size, num_mixers, is_hint=True)

    if solution is not None:
        load_solution(solver, variables, solution, grid_size, num_mixers)

    if not feasible_ok:
        objective1 = sum(
            [b[i][j] for i in range(W) for j in range(H)] +
            [5 * m[i][j] for i in range(W) for j in range(H)] +
            [2 * ua[i][j] for i in range(W) for j in range(H)] +
            [2 * ub[i][j] for i in range(W) for j in range(H)]
        )
        solver.Minimize(objective1)

    # Configure the solver to use all available threads
    if max_parallel:
        solver.SetSolverSpecificParametersAsString("parallel/maxnthreads=0")  # Use all threads

    solver_cp = cp_model.CpSolver()
    solver_cp.parameters.log_search_progress = True  # This enables solver output
    solver_cp.parameters.symmetry_level = 4
    # solver_cp.parameters.search_branching = cp_model.sat_parameters_pb2.SatParameters.PORTFOLIO_SEARCH

    if deterministic_time:
        solver_cp.parameters.random_seed = 42
        solver_cp.parameters.num_search_workers = 1
    
    if time_limit:
        # Set 10 minute time limit
        solver_cp.parameters.max_time_in_seconds = 300

    if disable_solve:
        # Do not solve
        status = cp_model.UNKNOWN
    else:
        status = solver_cp.Solve(solver)

    # Output the results
    if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
        print('Solution is', 'optimal' if status == cp_model.OPTIMAL else 'feasible')
        print('components:')
        print(viz_components(solver_cp, variables, grid_size))
        print('flows:')
        print(viz_flows(solver_cp, f, grid_size, num_sources))
        print('underground flows:')
        print(viz_flows(solver_cp, uf, grid_size, num_sources))
        # print(f'Minimum area: {solver.Objective().Value()}')
        # print('Blueprint')
        solution = viz_components(solver_cp, variables, grid_size)
        print(encode_components_blueprint_json(generate_entities_blueprint(solution, grid_size)))
        # viz_variables_verbose(solver, variables)

        return solution
    elif status == cp_model.INFEASIBLE:
        print('No optimal solution found.')
        return None
    elif status == cp_model.UNKNOWN:
        print('Not known if solution exists or its optimal.')
        return None
    else:
        raise Exception(f'Unexpected solver status: {status}.')


BALANCERS = {
    '1_b': lambda:
        solve_factorio_belt_balancer((3, 3), 1, [
            (0, 2, 'N', 0, -1),
            (0, 0, 'S', 0, 1),
        ], 1, disable_underground=True),
    # 1 belt with solution
    '1_b_s': lambda:
        solve_factorio_belt_balancer((3, 3), 1, [
            (0, 2, 'N', 0, -1),
            (0, 0, 'S', 0, 1),
        ], 1, solution=
            '▲‧‧\n' +
            '▲‧‧\n' +
            '▲‧‧\n'
        ),
    # 1 mixer with
    '1_m': lambda:
        solve_factorio_belt_balancer((2, 1), 2, [
            (0, 0, 'S', 0, 2),
            (1, 0, 'S', 1, 2),
            (0, 0, 'N', 0, -1),
            (0, 0, 'N', 1, -1),
            (1, 0, 'N', 0, -1),
            (1, 0, 'N', 1, -1),
        ], 2),
    # 1 mixer with network solution
    '1_m_n': lambda:
        solve_factorio_belt_balancer((2, 1), 2, [
            (0, 0, 'S', 0, 1),
            (1, 0, 'S', 0, 1),
            (0, 0, 'N', 1, -1),
            (1, 0, 'N', 1, -1),
        ], 1, network_solution=(
            ((0, 0), (1, 1)),
        )),
    # Swap two belts
    's_2': lambda:
        solve_factorio_belt_balancer((5, 6), 2, [
            (2, 0, 'S', 0, 1),
            (3, 0, 'S', 1, 1),
            (3, 5, 'N', 0, -1),
            (2, 5, 'N', 1, -1),
        ], 1),
    '2x2': lambda:
        solve_factorio_belt_balancer((2, 3), 2, [
            (0, 0, 'S', 0, 2),
            (1, 0, 'S', 1, 2),
            (0, 2, 'N', 0, -1),
            (0, 2, 'N', 1, -1),
            (1, 2, 'N', 0, -1),
            (1, 2, 'N', 1, -1),
        ], 2),
    '3x3': lambda:
        solve_factorio_belt_balancer((5, 6), 3, [
            (0, 0, 'S', 0, 24),
            (1, 0, 'S', 1, 24),
            (2, 0, 'S', 2, 24),

            (1, 5, 'N', 0, -8),
            (1, 5, 'N', 1, -8),
            (1, 5, 'N', 2, -8),

            (2, 5, 'N', 0, -8),
            (2, 5, 'N', 1, -8),
            (2, 5, 'N', 2, -8),

            (3, 5, 'N', 0, -8),
            (3, 5, 'N', 1, -8),
            (3, 5, 'N', 2, -8),
        ], 24),
    # Balancer 3 x 3 - with network solutions
    '3x3_n': lambda:
        solve_factorio_belt_balancer((5, 6), 4, [
            (0, 0, 'S', 0, 1),
            (1, 0, 'S', 0, 1),
            (2, 0, 'S', 0, 1),

            (1, 5, 'N', 3, -1),
            (2, 5, 'N', 3, -1),
            (3, 5, 'N', 3, -1),
        ], 1, network_solution=(
            ((0, 0), (1, 1)),
            ((0, 3), (2, 2)),
            ((1, 2), (3, 3)),
            ((1, 2), (3, 3))
        )),
    '4x4': lambda:
        solve_factorio_belt_balancer((4, 7), 4, [
            (0, 0, 'S', 0, 16),
            (1, 0, 'S', 1, 16),
            (2, 0, 'S', 2, 16),
            (3, 0, 'S', 3, 16),

            (0, 6, 'N', 0, -4),
            (0, 6, 'N', 1, -4),
            (0, 6, 'N', 2, -4),
            (0, 6, 'N', 3, -4),

            (1, 6, 'N', 0, -4),
            (1, 6, 'N', 1, -4),
            (1, 6, 'N', 2, -4),
            (1, 6, 'N', 3, -4),

            (2, 6, 'N', 0, -4),
            (2, 6, 'N', 1, -4),
            (2, 6, 'N', 2, -4),
            (2, 6, 'N', 3, -4),

            (3, 6, 'N', 0, -4),
            (3, 6, 'N', 1, -4),
            (3, 6, 'N', 2, -4),
            (3, 6, 'N', 3, -4),
        ], 16),
    # Balancer 4 x 4 - with precomputed solution
    '4x4_s': lambda:
        solve_factorio_belt_balancer((4, 7), 4, [
            (0, 0, 'S', 0, 16),
            (1, 0, 'S', 1, 16),
            (2, 0, 'S', 2, 16),
            (3, 0, 'S', 3, 16),

            (0, 6, 'N', 0, -4),
            (0, 6, 'N', 1, -4),
            (0, 6, 'N', 2, -4),
            (0, 6, 'N', 3, -4),

            (1, 6, 'N', 0, -4),
            (1, 6, 'N', 1, -4),
            (1, 6, 'N', 2, -4),
            (1, 6, 'N', 3, -4),

            (2, 6, 'N', 0, -4),
            (2, 6, 'N', 1, -4),
            (2, 6, 'N', 2, -4),
            (2, 6, 'N', 3, -4),

            (3, 6, 'N', 0, -4),
            (3, 6, 'N', 1, -4),
            (3, 6, 'N', 2, -4),
            (3, 6, 'N', 3, -4),
        ], 16, solution=
            '↥↿↾↥\n' +
            '‧↥↥△\n' +
            '△▶▶▲\n' +
            '↿↾‧‧\n' +
            '↥▲◀◀\n' +
            '△△△▲\n' +
            '↿↾↿↾\n'
        ),
    '4x4_n': lambda:
        solve_factorio_belt_balancer((4, 7), 4, [
            (0, 0, 'S', 0, 1),
            (1, 0, 'S', 0, 1),
            (2, 0, 'S', 0, 1),
            (3, 0, 'S', 0, 1),

            (0, 6, 'N', 3, -1),
            (1, 6, 'N', 3, -1),
            (2, 6, 'N', 3, -1),
            (3, 6, 'N', 3, -1),
        ], 1, network_solution=(
            ((0, 0), (1, 1)),
            ((0, 0), (2, 2)),
            ((1, 2), (3, 3)),
            ((1, 2), (3, 3)),
        )),
    # Balancer 8 x 8 - with precomputed partial solution
    '8x8_ps': lambda:
        solve_factorio_belt_balancer((8, 10), 8, [
            (0, 0, 'S', 0, 8),
            (1, 0, 'S', 1, 8),
            (2, 0, 'S', 2, 8),
            (3, 0, 'S', 3, 8),
            (4, 0, 'S', 4, 8),
            (5, 0, 'S', 5, 8),
            (6, 0, 'S', 6, 8),
            (7, 0, 'S', 7, 8),

            (0, 9, 'N', 0, -1),
            (0, 9, 'N', 1, -1),
            (0, 9, 'N', 2, -1),
            (0, 9, 'N', 3, -1),
            (0, 9, 'N', 4, -1),
            (0, 9, 'N', 5, -1),
            (0, 9, 'N', 6, -1),
            (0, 9, 'N', 7, -1),

            (1, 9, 'N', 0, -1),
            (1, 9, 'N', 1, -1),
            (1, 9, 'N', 2, -1),
            (1, 9, 'N', 3, -1),
            (1, 9, 'N', 4, -1),
            (1, 9, 'N', 5, -1),
            (1, 9, 'N', 6, -1),
            (1, 9, 'N', 7, -1),

            (2, 9, 'N', 0, -1),
            (2, 9, 'N', 1, -1),
            (2, 9, 'N', 2, -1),
            (2, 9, 'N', 3, -1),
            (2, 9, 'N', 4, -1),
            (2, 9, 'N', 5, -1),
            (2, 9, 'N', 6, -1),
            (2, 9, 'N', 7, -1),

            (3, 9, 'N', 0, -1),
            (3, 9, 'N', 1, -1),
            (3, 9, 'N', 2, -1),
            (3, 9, 'N', 3, -1),
            (3, 9, 'N', 4, -1),
            (3, 9, 'N', 5, -1),
            (3, 9, 'N', 6, -1),
            (3, 9, 'N', 7, -1),

            (4, 9, 'N', 0, -1),
            (4, 9, 'N', 1, -1),
            (4, 9, 'N', 2, -1),
            (4, 9, 'N', 3, -1),
            (4, 9, 'N', 4, -1),
            (4, 9, 'N', 5, -1),
            (4, 9, 'N', 6, -1),
            (4, 9, 'N', 7, -1),

            (5, 9, 'N', 0, -1),
            (5, 9, 'N', 1, -1),
            (5, 9, 'N', 2, -1),
            (5, 9, 'N', 3, -1),
            (5, 9, 'N', 4, -1),
            (5, 9, 'N', 5, -1),
            (5, 9, 'N', 6, -1),
            (5, 9, 'N', 7, -1),

            (6, 9, 'N', 0, -1),
            (6, 9, 'N', 1, -1),
            (6, 9, 'N', 2, -1),
            (6, 9, 'N', 3, -1),
            (6, 9, 'N', 4, -1),
            (6, 9, 'N', 5, -1),
            (6, 9, 'N', 6, -1),
            (6, 9, 'N', 7, -1),

            (7, 9, 'N', 0, -1),
            (7, 9, 'N', 1, -1),
            (7, 9, 'N', 2, -1),
            (7, 9, 'N', 3, -1),
            (7, 9, 'N', 4, -1),
            (7, 9, 'N', 5, -1),
            (7, 9, 'N', 6, -1),
            (7, 9, 'N', 7, -1),
        ], 8,
            # solution=
            #     '↿↾↿↾↿↾↿↾' +
            #     '↥↥↥▲↥↥↥▲' +
            #     '‧▶▷▲◀◀↦▲' +
            #     '△▲◀‧△▲◀◀' +
            #     '▲↤▲▶▲◁◀▲' +
            #     '‧‧↿↾‧‧↿↾' +
            #     '▶▶▲↥▶▶▲↥' +
            #     '↥△△‧↥△△‧' +
            #     '△↿↾△△↿↾△' +
            #     '↿↾↿↾↿↾↿↾',
            solution=
                '↿↾↿↾↿↾↿↾' +
                '‧‧‧‧‧‧‧▲' +
                '‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧△' +
                '↿↾↿↾↿↾↿↾',
            deterministic_time=True,
            feasible_ok=True,
        ),
        '16x16_n': lambda:
            solve_factorio_belt_balancer((16, 16), 16, [
            # Inputs
            (0, 0, 'S', 0, 1),
            (1, 0, 'S', 0, 1),
            (2, 0, 'S', 0, 1),
            (3, 0, 'S', 0, 1),
            (4, 0, 'S', 0, 1),
            (5, 0, 'S', 0, 1),
            (6, 0, 'S', 0, 1),
            (7, 0, 'S', 0, 1),
            (8, 0, 'S', 0, 1),
            (9, 0, 'S', 0, 1),
            (10, 0, 'S', 0, 1),
            (11, 0, 'S', 0, 1),
            (12, 0, 'S', 0, 1),
            (13, 0, 'S', 0, 1),
            (14, 0, 'S', 0, 1),
            (15, 0, 'S', 0, 1),

            # Outputs
            (0, 15, 'N', 15, -1),
            (1, 15, 'N', 15, -1),
            (2, 15, 'N', 15, -1),
            (3, 15, 'N', 15, -1),
            (4, 15, 'N', 15, -1),
            (5, 15, 'N', 15, -1),
            (6, 15, 'N', 15, -1),
            (7, 15, 'N', 15, -1),
            (8, 15, 'N', 15, -1),
            (9, 15, 'N', 15, -1),
            (10, 15, 'N', 15, -1),
            (11, 15, 'N', 15, -1),
            (12, 15, 'N', 15, -1),
            (13, 15, 'N', 15, -1),
            (14, 15, 'N', 15, -1),
            (15, 15, 'N', 15, -1),
        ], 1,
            network_solution=(
                ((0, 0), (1, 1)),
                ((0, 0), (2, 2)),
                ((0, 0), (3, 3)),
                ((0, 0), (4, 4)),
                ((0, 0), (5, 5)),
                ((0, 0), (6, 6)),
                ((0, 0), (7, 7)),
                ((0, 0), (8, 8)),
                ((1, 2), (9, 9)),
                ((1, 2), (9, 9)),
                ((3, 4), (10, 10)),
                ((3, 4), (10, 10)),
                ((5, 6), (11, 11)),
                ((5, 6), (11, 11)),
                ((7, 8), (12, 12)),
                ((7, 8), (12, 12)),
                ((9, 10), (13, 13)),
                ((9, 10), (13, 13)),
                ((9, 10), (13, 13)),
                ((9, 10), (13, 13)),
                ((11, 12), (14, 14)),
                ((11, 12), (14, 14)),
                ((11, 12), (14, 14)),
                ((11, 12), (14, 14)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
            ),
            solution=
                '↿↾↿↾↿↾↿↾↿↾↿↾↿↾↿↾' +
                '▲▲▲▲▲▲▲▲▲▲▲↥↥▲▲▲' +
                '▲▲▲↥↥▲↥↥↥▲▲◀◀▲↥↥' +
                '▲▲▲◀↤▲◁↼↤▲◀‧↿↾◁◀' +
                '‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧' +
                '‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧‧' +
                '‧‧↿↾↿↾‧‧‧‧↿↾↿↾‧‧' +
                '▶▶▲▲▲▲◀◀▶▶▲▲▲▲◀◀' +
                '▲△△▲▲△△▲▲△△▲▲△△▲' +
                '▲↿↾▲▲↿↾▲▲↿↾▲▲↿↾▲' +
                '↿↾↿↾↿↾↿↾↿↾↿↾↿↾↿↾',
            feasible_ok=True,
        ),
        '16x16_n_s': lambda:
            solve_factorio_belt_balancer((16, 16), 16, [
            # Inputs
            (0, 0, 'S', 0, 1),
            (1, 0, 'S', 0, 1),
            (2, 0, 'S', 0, 1),
            (3, 0, 'S', 0, 1),
            (4, 0, 'S', 0, 1),
            (5, 0, 'S', 0, 1),
            (6, 0, 'S', 0, 1),
            (7, 0, 'S', 0, 1),
            (8, 0, 'S', 0, 1),
            (9, 0, 'S', 0, 1),
            (10, 0, 'S', 0, 1),
            (11, 0, 'S', 0, 1),
            (12, 0, 'S', 0, 1),
            (13, 0, 'S', 0, 1),
            (14, 0, 'S', 0, 1),
            (15, 0, 'S', 0, 1),

            # Outputs
            (0, 15, 'N', 15, -1),
            (1, 15, 'N', 15, -1),
            (2, 15, 'N', 15, -1),
            (3, 15, 'N', 15, -1),
            (4, 15, 'N', 15, -1),
            (5, 15, 'N', 15, -1),
            (6, 15, 'N', 15, -1),
            (7, 15, 'N', 15, -1),
            (8, 15, 'N', 15, -1),
            (9, 15, 'N', 15, -1),
            (10, 15, 'N', 15, -1),
            (11, 15, 'N', 15, -1),
            (12, 15, 'N', 15, -1),
            (13, 15, 'N', 15, -1),
            (14, 15, 'N', 15, -1),
            (15, 15, 'N', 15, -1),
        ], 1,
            solution=
                '↿↾↿↾↿↾↿↾↿↾↿↾↿↾↿↾' +
                '▲▲▲▲▲▲▲▲▲▲▲↥↥▲▲▲' +
                '▲▲▲↥↥▲↥↥↥▲▲◀◀▲↥↥' +
                '▲▲▲◀↤▲◁↼↤▲◀‧↿↾◁◀' +
                '▲▲▶▶▷▲◀↽◀◀▲↦▲▲△▲' +
                '▲▲↥‧‧▶▶▷△↥▲↦▶▲▲▲' +
                '↥▲◀▶▼↥△‧▲◀▲◀◀▶▲▲' +
                '▶▷↿↾▶▶▲↦⇀▲▶▼↿↾▶▲' +
                '▲◀▲▲◀◀▶▶⇁▼↥▶▲↥↥△' +
                '△▲▲△△▲▲△‧▶▷△△↦▶▲' +
                '▲↥▲↿↾▲▲▲↼◀◀↿↾▶▶▼' +
                '▲↤↿↾↿↾↥◁↽↤↿↾↿↾◁◀' +
                '▶▶▲▲▲▲◀◀▶▶▲▲▲▲◀◀' +
                '▲△△▲▲△△▲▲△△▲▲△△▲' +
                '▲↿↾▲▲↿↾▲▲↿↾▲▲↿↾▲' +
                '↿↾↿↾↿↾↿↾↿↾↿↾↿↾↿↾',
            network_solution=(
                ((0, 0), (1, 1)),
                ((0, 0), (2, 2)),
                ((0, 0), (3, 3)),
                ((0, 0), (4, 4)),
                ((0, 0), (5, 5)),
                ((0, 0), (6, 6)),
                ((0, 0), (7, 7)),
                ((0, 0), (8, 8)),
                ((1, 2), (9, 9)),
                ((1, 2), (9, 9)),
                ((3, 4), (10, 10)),
                ((3, 4), (10, 10)),
                ((5, 6), (11, 11)),
                ((5, 6), (11, 11)),
                ((7, 8), (12, 12)),
                ((7, 8), (12, 12)),
                ((9, 10), (13, 13)),
                ((9, 10), (13, 13)),
                ((9, 10), (13, 13)),
                ((9, 10), (13, 13)),
                ((11, 12), (14, 14)),
                ((11, 12), (14, 14)),
                ((11, 12), (14, 14)),
                ((11, 12), (14, 14)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
                ((13, 14), (15, 15)),
            ),
            feasible_ok=True,
        )
}

    # Balancer 6 x 6
    # solve_factorio_belt_balancer((8, 9), 6, [
    #     (1, 0, 'S', 0, 48),
    #     (2, 0, 'S', 1, 48),
    #     (3, 0, 'S', 2, 48),
    #     (4, 0, 'S', 3, 48),
    #     (5, 0, 'S', 4, 48),
    #     (6, 0, 'S', 5, 48),

    #     (0, 8, 'N', 0, -8),
    #     (0, 8, 'N', 1, -8),
    #     (0, 8, 'N', 2, -8),
    #     (0, 8, 'N', 3, -8),
    #     (0, 8, 'N', 4, -8),
    #     (0, 8, 'N', 5, -8),

    #     (1, 8, 'N', 0, -8),
    #     (1, 8, 'N', 1, -8),
    #     (1, 8, 'N', 2, -8),
    #     (1, 8, 'N', 3, -8),
    #     (1, 8, 'N', 4, -8),
    #     (1, 8, 'N', 5, -8),

    #     (2, 8, 'N', 0, -8),
    #     (2, 8, 'N', 1, -8),
    #     (2, 8, 'N', 2, -8),
    #     (2, 8, 'N', 3, -8),
    #     (2, 8, 'N', 4, -8),
    #     (2, 8, 'N', 5, -8),

    #     (3, 8, 'N', 0, -8),
    #     (3, 8, 'N', 1, -8),
    #     (3, 8, 'N', 2, -8),
    #     (3, 8, 'N', 3, -8),
    #     (3, 8, 'N', 4, -8),
    #     (3, 8, 'N', 5, -8),

    #     (4, 8, 'N', 0, -8),
    #     (4, 8, 'N', 1, -8),
    #     (4, 8, 'N', 2, -8),
    #     (4, 8, 'N', 3, -8),
    #     (4, 8, 'N', 4, -8),
    #     (4, 8, 'N', 5, -8),

    #     (5, 8, 'N', 0, -8),
    #     (5, 8, 'N', 1, -8),
    #     (5, 8, 'N', 2, -8),
    #     (5, 8, 'N', 3, -8),
    #     (5, 8, 'N', 4, -8),
    #     (5, 8, 'N', 5, -8),
    # ], 48)

    # # Balancer 6 x 6
    # # Larger
    # solve_factorio_belt_balancer((10, 10), 6, [
    #     (2, 0, 'S', 0, 24),
    #     (3, 0, 'S', 1, 24),
    #     (4, 0, 'S', 2, 24),
    #     (5, 0, 'S', 3, 24),
    #     (6, 0, 'S', 4, 24),
    #     (7, 0, 'S', 5, 24),

    #     (2, 9, 'N', 0, -4),
    #     (2, 9, 'N', 1, -4),
    #     (2, 9, 'N', 2, -4),
    #     (2, 9, 'N', 3, -4),
    #     (2, 9, 'N', 4, -4),
    #     (2, 9, 'N', 5, -4),

    #     (3, 9, 'N', 0, -4),
    #     (3, 9, 'N', 1, -4),
    #     (3, 9, 'N', 2, -4),
    #     (3, 9, 'N', 3, -4),
    #     (3, 9, 'N', 4, -4),
    #     (3, 9, 'N', 5, -4),

    #     (4, 9, 'N', 0, -4),
    #     (4, 9, 'N', 1, -4),
    #     (4, 9, 'N', 2, -4),
    #     (4, 9, 'N', 3, -4),
    #     (4, 9, 'N', 4, -4),
    #     (4, 9, 'N', 5, -4),

    #     (5, 9, 'N', 0, -4),
    #     (5, 9, 'N', 1, -4),
    #     (5, 9, 'N', 2, -4),
    #     (5, 9, 'N', 3, -4),
    #     (5, 9, 'N', 4, -4),
    #     (5, 9, 'N', 5, -4),
        
    #     (6, 9, 'N', 0, -4),
    #     (6, 9, 'N', 1, -4),
    #     (6, 9, 'N', 2, -4),
    #     (6, 9, 'N', 3, -4),
    #     (6, 9, 'N', 4, -4),
    #     (6, 9, 'N', 5, -4),

    #     (7, 9, 'N', 0, -4),
    #     (7, 9, 'N', 1, -4),
    #     (7, 9, 'N', 2, -4),
    #     (7, 9, 'N', 3, -4),
    #     (7, 9, 'N', 4, -4),
    #     (7, 9, 'N', 5, -4),
    # ], 24,
    #     # solution=
    #     # '▼◀▲▲▲▲▲▲▶▼' +
    #     # '▼↿↾↿↾↿↾↿↾▼' +
    #     # '▼↥↿↾▲▲↿↾↥▼' +
    #     # '▶▶▲▲↥↥↥▲◀◀' +
    #     # '‧‧‧▲◀◀◀◀‧‧' +
    #     # '‧△▶▼‧‧△↥△‧' +
    #     # '‧▲↥▶▶▶▲‧▲‧' +
    #     # '‧▲◀◀△△▶▶▲‧' +
    #     # '‧‧△↿↾↿↾△‧‧' +
    #     # '‧‧↿↾↿↾↿↾‧‧',
    #     feasible_ok=True,
    #     num_mixers=11,
    #     # deterministic_time=True
    # )