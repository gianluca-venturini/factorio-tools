import json
import zlib
import base64
from itertools import count

DIRECTIONS = ('N', 'S', 'E', 'W')

# Maximum distance between entrance and exit of the underground belt
# it's just the cells between the entrance and exit cell, without counting them
# e.g. distance 0 means that entrance and exit are adjacent
MAX_UNDERGROUND_DISTANCE = 3

BELT_INPUT_DIRECTIONS = {
    'N': ['S', 'E', 'W'],
    'S': ['N', 'E', 'W'],
    'E': ['N', 'S', 'W'],
    'W': ['N', 'S', 'E'],
}

# Synbols used for visualizing the belt based on direction
DIRECTIONS_SYMBOL = {
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

# Blueprint representation of belt direction
BELT_DIRECTION_TO_BLUEPRINT_DIRECTION = {
    'N': 6,
    'S': 2,
    'E': 0,
    'W': 4,
}

UNDERGROUND_BELT_DIRECTION_TO_BLUEPRINT_DIRECTION = {
    # Note: these mappings may be incorrect, need to double check them
    'N': 6,
    'S': 2,
    'E': 0,
    'W': 4,
}

# Blueprint mixers coordinates are centered, so we need to apply an offset based on the direction
MIXER_FIRST_CELL_BLUEPRINT_OFFSET = {
    'N': (0.5, 0),
    'S': (-0.5, 0),
    'E': (0, -0.5),
    'W': (0, 0.5),
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

def viz_occupied(solver, x, grid_size):
    W, H = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        # Iterate backward since Y axis is inverted
        for i in range(W):
            result += '■' if solver.Value(x[i][j]) > 0 else '‧'
        result += '\n'
    return result

def viz_belts(solver, b, grid_size):
    W, H = grid_size
    result = ''
    # Iterate backward since Y axis is inverted
    for j in range(H-1, -1, -1):
        for i in range(W):
            result += ''.join([f"{DIRECTIONS_SYMBOL[DIRECTIONS[d]]}" if solver.Value(b[i][j][d]) > 0 else '' for d in range(len(DIRECTIONS))]) if sum(solver.Value(b[i][j][d]) for d in range(len(DIRECTIONS))) > 0 else 'O'
        result += '\n'
    return result

'''
Visualizes all the components of the belt balancer
'''
def viz_components(solver, b, m, u, grid_size):
    result = ''
    def render_b(i, j, d):
        nonlocal result
        result += f"{DIRECTIONS_SYMBOL[d]}"
    def render_m(i, j, d, c):
        nonlocal result
        result += f"{MIXER_SYMBOL[d][c]}"
    def render_u(i, j, d, c):
        nonlocal result
        result += f"{UNDERGROUND_BELT_SYMBOL[d][c]}"
    def render_empty():
        nonlocal result
        result += '‧'
    def render_new_line():
        nonlocal result
        result += '\n'

    visitor_components(solver, b, m, u, grid_size, render_new_line, render_empty, render_b, render_m, render_u)
    return result

'''
Visit all the cells and call the render_*() functions to render all the elements.
It's guaranteed to complete the entire row before proceeding to the next one.
Starts from coordinate 0, 0.
'''
def visitor_components(solver, b, m, u, grid_size, render_new_line, render_empty, render_b, render_m, render_u):
    W, H = grid_size
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
                if solver.Value(m[i][j][d]) > 0:
                    render_m(i, j, DIRECTIONS[d], 0)
                    found = True
            # Visualize the mixer second cell
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                ci, cj = mixer_first_cell(i, j, DIRECTIONS[d])
                if inside_grid(ci, cj, grid_size) and solver.Value(m[ci][cj][d]) > 0:
                    render_m(i, j, DIRECTIONS[d], 1)
                    found = True
            # Visualize the underground belt entrance
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                for n in range(MAX_UNDERGROUND_DISTANCE):
                    if solver.Value(u[i][j][d][n]) > 0:
                        render_u(i, j, DIRECTIONS[d], 0)
                        found = True
            # Visualize the underground belt exit
            for d in range(len(DIRECTIONS)):
                if found:
                    break
                for n in range(MAX_UNDERGROUND_DISTANCE):
                    ci, cj = underground_entrance_coordinates(i, j, DIRECTIONS[d], n)
                    if inside_grid(ci, cj, grid_size) and solver.Value(u[ci][cj][d][n]) > 0:
                        render_u(i, j, DIRECTIONS[d], 1)
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
            for d in range(len(DIRECTIONS)):
                for s in range(num_flows):
                    if solver.Value(f[i][j][s][d]) < -EPSILON or solver.Value(f[i][j][s][d]) > EPSILON:
                        result += f"{DIRECTIONS_SYMBOL[DIRECTIONS[d]]}({s}){solver.Value(f[i][j][s][d])} "
                result += ' '
            result += '| '
        result += '\n'
    return result

def generate_entities_blueprint(solver, b, m, u, grid_size):
    unique_entity_number_generator = count(1)

    result = []
    def render_b(i, j, d):
        result.append({
            "entity_number": next(unique_entity_number_generator),
            "name": "transport-belt",
            "position": { "x": i, "y": j },
            "direction": BELT_DIRECTION_TO_BLUEPRINT_DIRECTION[d]
        })
    def render_m(i, j, d, c):
        if c == 0:
            # Render mixer on first cell to render it only once
            offset = MIXER_FIRST_CELL_BLUEPRINT_OFFSET[d]
            result.append({
                "entity_number": next(unique_entity_number_generator),
                "name": "splitter",
                "position": { "x": i + offset[0], "y": j + offset[1] },
                "direction": BELT_DIRECTION_TO_BLUEPRINT_DIRECTION[d]
            })
    def render_u(i, j, d, c):
        result.append({
            "entity_number": next(unique_entity_number_generator),
            "name": "underground-belt",
            "position": { "x": i, "y": j },
            "type": "input" if c == 0 else "output",
            "direction": UNDERGROUND_BELT_DIRECTION_TO_BLUEPRINT_DIRECTION[d],
        })
        pass
    def render_empty():
        pass
    def render_new_line():
        pass

    visitor_components(solver, b, m, u, grid_size, render_new_line, render_empty, render_b, render_m, render_u)
    return result

def encode_components_blueprint_json(solver, b, m, u, grid_size):
    # Use this tool to test this code online: https://factorioblueprints.tech/user/blueprint-create

    blueprint_json = {
        "blueprint": {
            "item": "blueprint",
            "label": "Belt balancer ",
            "icons": [
                {
                    "signal": { "type": "item", "name": "transport-belt" },
                    "index": 1
                }
            ],
            "entities": generate_entities_blueprint(solver, b, m, u, grid_size),
            "version": 281479276344320 # Factorio version 1.1.0
        }
    }

    # Serialize the JSON object to a compact string
    json_str = json.dumps(blueprint_json, separators=(',', ':'))
    print(json_str)

    # Compress the JSON string using zlib's DEFLATE algorithm
    compressed_data = zlib.compress(json_str.encode('utf-8'))

    # Encode the compressed data in base64
    base64_encoded = base64.b64encode(compressed_data).decode('utf-8')

    # Prepend the version byte (0) to the base64 string
    blueprint_string = '0' + base64_encoded

    return blueprint_string
