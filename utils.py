DIRECTIONS = ('N', 'S', 'E', 'W')

OPPOSITE_DIRECTIONS = {
    'N': 'S',
    'S': 'N',
    'E': 'W',
    'W': 'E',
}

# Maximum distance between entrance and exit of the underground belt
# it's just the cells between the entrance and exit cell, without counting them
# e.g. distance 0 means that entrance and exit are adjacent
MAX_UNDERGROUND_DISTANCE = 9

BELT_INPUT_DIRECTIONS = {
    'N': ['S', 'E', 'W'],
    'S': ['N', 'E', 'W'],
    'E': ['N', 'S', 'W'],
    'W': ['N', 'S', 'E'],
}

EMPTY_SYMBOL = '‧'
OCCUPIED_SYMBOL = '■'

# Synbols used for visualizing the belt based on direction
BELT_SYMBOL = {
    'N': '▲',
    'S': '▼',
    'E': '▶',
    'W': '◀',
}

# Symbols used for visualizing the mixer based on direction
# since the mixer has two cells we have two different symbols (cell1, cell2)
MIXER_SYMBOL = {
    'N': ('↿', '↾'),
    'S': ('⇂', '⇃'),
    'E': ('⇀', '⇁'),
    'W': ('↽', '↼'),
}

# Symbols used for visualizing the underground belt based on direction
# it's a tuple in the shape (entrance, exit)
UNDERGROUND_BELT_SYMBOL = {
    'N': ('△', '↥'),
    'S': ('▽', '↧'),
    'E': ('▷', '↦'),
    'W': ('◁', '↤'),
}

EPSILON = 1e-5

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

'''
Returns the coordinates of the exit of the underground belt given the coordinates of the entrance and the direction
'''
def underground_exit_coordinates(i, j, d, n):
    if n > MAX_UNDERGROUND_DISTANCE:
        raise Exception('Underground belt distance is unexpected')
    # Adding one to the offset is necessary since the exit is one cell after
    # the distance of the underground belt
    # e.g. distance 0 means that entrance and exit are adjacent, but not on the cell.
    offset = n + 1
    if d == 'N':
        return (i, j + offset)
    if d == 'S':
        return (i, j - offset)
    if d == 'E':
        return (i + offset, j)
    if d == 'W':
        return (i - offset, j)
    raise Exception('Invalid direction')

'''
Returns the coordinates of the entrance of the underground belt given the coordinates of the exit and the direction
'''
def underground_entrance_coordinates(i, j, d, n):
    if n > MAX_UNDERGROUND_DISTANCE:
        raise Exception('Underground belt distance is unexpected')
    # Adding one to the offset is necessary since the entrance is one cell before
    # the distance of the underground belt
    # e.g. distance 0 means that entrance and exit are adjacent, but not on the cell.
    offset = n + 1
    if d == 'N':
        return (i, j - offset)
    if d == 'S':
        return (i, j + offset)
    if d == 'E':
        return (i - offset, j)
    if d == 'W':
        return (i + offset, j)
    raise Exception('Invalid direction')

'''
Returns all the directions where the flow must be zero.
For underground belt entrance, the flow is zero everywhere except the entrance direction that is the opposite of d.
'''
def underground_entrance_zero_directions(d):
    if d == 'N':
        return ('N', 'E', 'W')
    if d == 'S':
        return ('S', 'E', 'W')
    if d == 'E':
        return ('E', 'N', 'S')
    if d == 'W':
        return ('W', 'N', 'S')
    raise Exception('Invalid direction')

'''
Returns all the directions where the flow must be zero.
For underground belt exit, the flow is zero everywhere except the exit direction that is d.
'''
def underground_exit_zero_directions(d):
    if d == 'N':
        return ('S', 'E', 'W')
    if d == 'S':
        return ('N', 'E', 'W')
    if d == 'E':
        return ('W', 'N', 'S')
    if d == 'W':
        return ('E', 'N', 'S')
    raise Exception('Invalid direction')

'''
The only non-zero flow direction in the entrance.
'''
def underground_entrance_flow_direction(d):
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
Given a cell and a direction, returns the next cell in that direction.
'''
def next_cell(i, j, d):
    if d == 'N':
        return (i, j + 1)
    if d == 'S':
        return (i, j - 1)
    if d == 'E':
        return (i + 1, j)
    if d == 'W':
        return (i - 1, j)
    raise Exception('Invalid direction')

def viz_occupied(solver, x, grid_size):
    W, H = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        # Iterate backward since Y axis is inverted
        for i in range(W):
            result += OCCUPIED_SYMBOL if solver.Value(x[i][j]) > 0 else EMPTY_SYMBOL
        result += '\n'
    return result

def viz_belts(solver, b, grid_size):
    W, H = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        for i in range(W):
            result += ''.join([f"{BELT_SYMBOL[DIRECTIONS[d]]}" if solver.Value(b[i][j][d]) > 0 else '' for d in range(len(DIRECTIONS))]) if sum(solver.Value(b[i][j][d]) for d in range(len(DIRECTIONS))) > 0 else 'O'
        result += '\n'
    return result

'''
Visualizes all the components of the belt balancer
'''
def viz_components(solver, variables, grid_size):
    result = ''
    def render_b(i, j, d):
        nonlocal result
        result += f"{BELT_SYMBOL[d]}"
    def render_m(i, j, d, c):
        nonlocal result
        result += f"{MIXER_SYMBOL[d][c]}"
    def render_ua(i, j, d):
        nonlocal result
        result += f"{UNDERGROUND_BELT_SYMBOL[d][0]}"
    def render_ub(i, j, d):
        nonlocal result
        result += f"{UNDERGROUND_BELT_SYMBOL[d][1]}"
    def render_empty():
        nonlocal result
        result += EMPTY_SYMBOL
    def render_new_line():
        nonlocal result
        result += '\n'

    visit_solver_variables(solver, variables, grid_size, render_new_line, render_empty, render_b, render_m, render_ua, render_ub)
    return result

'''
Visit all the cells and call the render_*() functions to render all the elements.
It's guaranteed to complete the entire row before proceeding to the next one.
Starts from coordinate 0, 0.
'''
def visit_solver_variables(solver, variables, grid_size, render_new_line, render_empty, render_b, render_m, render_ua, render_ub):
    W, H = grid_size
    b, m, ua, ub = variables
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        for i in range(W):
            found = False
            # Visualize the belt
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                if solver.Value(b[i][j][d]) > 0:
                    render_b(i, j, DIRECTIONS[d])
                    found = True
            # Visualize the mixer first cell
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                if any([solver.Value(m[i][j][d][n]) > 0 for n in range(len(m[i][j][d]))]):
                    render_m(i, j, DIRECTIONS[d], 0)
                    found = True
            # Visualize the mixer second cell
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                ci, cj = mixer_first_cell(i, j, DIRECTIONS[d])
                if inside_grid(ci, cj, grid_size) and any([solver.Value(m[ci][cj][d][n]) > 0 for n in range(len(m[ci][cj][d]))]):
                    render_m(i, j, DIRECTIONS[d], 1)
                    found = True
            # Visualize the underground belt
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                if solver.Value(ua[i][j][d]) > 0:
                    render_ua(i, j, DIRECTIONS[d])
                    found = True
                    break
                if solver.Value(ub[i][j][d]) > 0:
                    render_ub(i, j, DIRECTIONS[d])
                    found = True
            if not found:
                render_empty()
        render_new_line()

def viz_flows(solver, f, grid_size, num_flows):
    W, H = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        for i in range(W):
            for s in range(num_flows):
                for d in range(len(DIRECTIONS)):
                    if solver.Value(f[i][j][s][d]) < -EPSILON or solver.Value(f[i][j][s][d]) > EPSILON:
                        result += f" {BELT_SYMBOL[DIRECTIONS[d]]}({s}){solver.Value(f[i][j][s][d]):>2}"
                    else :
                        result += f' {EMPTY_SYMBOL * 6}'
            result += '|'
        result += '\n'
    return result



provided_solution = set()
def load_solution(solver, variables, solution, grid_size, num_mixers, is_hint=False):
    b, m, ua, ub = variables

    def add_solution(variable, value):
        if variable.name in provided_solution:
            # Skip variables that have already been set
            return
        provided_solution.add(variable.name)
        if is_hint:
            solver.AddHint(variable, value)
        else:
            solver.Add(variable == value)

    def add_mixer_solution(i, j, d, value):
        if is_hint:
            for n in range(num_mixers):
                add_solution(m[i][j][DIRECTIONS.index(d)][n], value)
        else:
            solver.Add(sum(m[i][j][DIRECTIONS.index(d)][n] for n in range(num_mixers)) == value)
    
    def render_new_line():
        pass
    def render_empty():
        pass
    def render_b(i, j, d):
        add_solution(b[i][j][DIRECTIONS.index(d)], 1)
    def render_m(i, j, d, c):
        add_mixer_solution(i, j, d, 1)
    def render_ua(i, j, d):
        add_solution(ua[i][j][DIRECTIONS.index(d)], 1)
    def render_ub(i, j, d):
        add_solution(ub[i][j][DIRECTIONS.index(d)], 1)
    
    visit_solution(solution, grid_size, render_new_line, render_empty, render_b, render_m, render_ua, render_ub)

def visit_solution(solution, grid_size, render_new_line, render_empty, render_b, render_m, render_ua, render_ub):
    W, H = grid_size
    normalize_solution = solution.replace('\n', '')
    if len(normalize_solution) != grid_size[0] * grid_size[1]:
        raise Exception(f'Invalid solution size: {len(normalize_solution)} != {grid_size[0] * grid_size[1]}')
    solution_iterator = iter(normalize_solution)
    for j in range(H - 1, -1, -1):
        for i in range(W):
            char = next(solution_iterator)
            if char == EMPTY_SYMBOL:
                render_empty()
                continue
            if char in BELT_SYMBOL.values():
                d = next(key for key, value in BELT_SYMBOL.items() if value == char)
                render_b(i, j, d)
            elif char in [v[0] for v in MIXER_SYMBOL.values()]:
                d = next(key for key, value in MIXER_SYMBOL.items() if value[0] == char)
                render_m(i, j, d, 0)
            elif any(char in v for v in UNDERGROUND_BELT_SYMBOL.values()):
                d = next(key for key, value in UNDERGROUND_BELT_SYMBOL.items() if value[0] == char or value[1] == char)
                if char == UNDERGROUND_BELT_SYMBOL[d][0]:
                    render_ua(i, j, d)
                elif char == UNDERGROUND_BELT_SYMBOL[d][1]:
                    render_ub(i, j, d)
        render_new_line()

