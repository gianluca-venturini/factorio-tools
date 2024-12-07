import unittest
from blueprint import generate_entities_blueprint

class TestFactorioBlueprint(unittest.TestCase):

    def test_solve_factorio_belt_balancer_single_cell_no_flow(self):
        generate_entities_blueprint()