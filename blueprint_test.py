import unittest
import snapshottest


from blueprint import FACTORIO_BLUEPRINT_VERSION, encode_components_blueprint_json, generate_entities_blueprint

class TestFactorioBlueprintGenerateJson(unittest.TestCase):

    def test_json_blueprint_1_belt(self):
        result = generate_entities_blueprint('▲', (1, 1))
        self.assertEqual(result, {
            "blueprint": {
                "item": "blueprint",
                "label": "Belt balancer ",
                "icons": [
                    {"signal": {"type": "item", "name": "transport-belt"}, "index": 1}
                ], 
                "entities": [{"entity_number": 1, "name": "express-transport-belt", "position": {"x": 0, "y": 0}, "direction": 0}],
                "version": FACTORIO_BLUEPRINT_VERSION
            }
        })

class TestFactorioBlueprintEncodeJson(snapshottest.TestCase):

    def test_encoded_blueprint_1_b(self):
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('▲', (1, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('▼', (1, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('▶', (1, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('◀', (1, 1)))
        )

    def test_encoded_blueprint_1_u_a(self):
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('△', (1, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('▽', (1, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('▷', (1, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('◁', (1, 1)))
        )

    def test_encoded_blueprint_1_u_b(self):
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('↥', (1, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('↧', (1, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('↦', (1, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('↤', (1, 1)))
        )

    def test_encoded_blueprint_1_m(self):
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('↿↾', (2, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('⇃⇂', (2, 1)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('⇀\n⇁', (1, 2)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('↼\n↽', (1, 2)))
        )

    def test_encoded_blueprint_position_on_grid_2_b(self):
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('▲\n▲\n', (1, 2)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('▲▲', (2, 1)))
        )

    def test_encoded_blueprint_position_on_grid_2_b_1_m(self):
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('↿↾\n▲▲', (2, 2)))
        )
        self.assertMatchSnapshot(
            encode_components_blueprint_json(generate_entities_blueprint('▲▲\n↿↾', (2, 2)))
        )
