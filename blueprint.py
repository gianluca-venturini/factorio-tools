from itertools import count
import json
import zlib
import base64
from utils import visit_solution

# Blueprint representation of belt direction
BELT_DIRECTION_TO_BLUEPRINT_DIRECTION = {
    'N': 0,
    'S': 4,
    'E': 2,
    'W': 6,
}

UNDERGROUND_BELT_DIRECTION_TO_BLUEPRINT_DIRECTION = {
    'N': 0,
    'S': 4,
    'E': 2,
    'W': 6,
}

# Blueprint mixers coordinates are centered, so we need to apply an offset based on the direction
MIXER_FIRST_CELL_BLUEPRINT_OFFSET = {
    'N': (0.5, 0),
    'S': (-0.5, 0),
    'E': (0, -0.5),
    'W': (0, 0.5),
}

FACTORIO_BLUEPRINT_VERSION = 281479276344320 # Factorio version 1.1.0

def generate_entities_blueprint(solution, grid_size):
    W, H = grid_size
    unique_entity_number_generator = count(1)

    result = []
    def render_b(i, j, d):
        result.append({
            "entity_number": next(unique_entity_number_generator),
            "name": "transport-belt",
            "position": { "x": i, "y": H - 1 - j },
            "direction": BELT_DIRECTION_TO_BLUEPRINT_DIRECTION[d]
        })
    def render_m(i, j, d, c):
        if c == 0:
            # Render mixer on first cell to render it only once
            offset = MIXER_FIRST_CELL_BLUEPRINT_OFFSET[d]
            result.append({
                "entity_number": next(unique_entity_number_generator),
                "name": "splitter",
                "position": { "x": i + offset[0], "y": H - 1 - (j + offset[1]) },
                "direction": BELT_DIRECTION_TO_BLUEPRINT_DIRECTION[d]
            })
    def render_u(i, j, d, c):
        result.append({
            "entity_number": next(unique_entity_number_generator),
            "name": "underground-belt",
            "position": { "x": i, "y": H - 1 - j },
            "type": "input" if c == 0 else "output",
            "direction": UNDERGROUND_BELT_DIRECTION_TO_BLUEPRINT_DIRECTION[d],
        })
    def render_ua(i, j, d):
        render_u(i, j, d, 0)
    def render_ub(i, j, d):
        render_u(i, j, d, 1)
    def render_empty():
        pass
    def render_new_line():
        pass

    visit_solution(solution, grid_size, render_new_line, render_empty, render_b, render_m, render_ua, render_ub)

    return {
        "blueprint": {
            "item": "blueprint",
            "label": "Belt balancer ",
            "icons": [
                {
                    "signal": { "type": "item", "name": "transport-belt" },
                    "index": 1
                }
            ],
            "entities": result,
            "version": FACTORIO_BLUEPRINT_VERSION
        }
    }

def encode_components_blueprint_json(blueprint_json):
    # Use this tool to test this code online: https://factorioblueprints.tech/user/blueprint-create

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

if __name__ == '__main__':
    # Test the encoding of a blueprint
    blueprint_json = generate_entities_blueprint('▲', (1, 1))
    encoded_blueprint = encode_components_blueprint_json(blueprint_json)
    print(encoded_blueprint)