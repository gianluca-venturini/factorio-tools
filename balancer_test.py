import unittest
from balancer import solve_factorio_belt_balancer

class TestFactorioBalancer(unittest.TestCase):

    def test_solve_factorio_belt_balancer_single_cell_no_flow(self):
        result = solve_factorio_belt_balancer((1, 1), 1, [])
        # No components
        self.assertEqual(result, 'O\n')

    ###
    ### Belts
    ###

    def test_solve_factorio_belt_balancer_single_cell_flow_up(self):
        result = solve_factorio_belt_balancer((1, 1), 1, [
            (0, 0, 'N', 0, -1),
            (0, 0, 'S', 0, 1),
        ])
        # One belt that goes up
        self.assertEqual(result, '^\n')

    def test_solve_factorio_belt_balancer_single_cell_flow_down(self):
        result = solve_factorio_belt_balancer((1, 1), 1, [
            (0, 0, 'N', 0, 1),
            (0, 0, 'S', 0, -1),
        ])
        # One belt that goes down
        self.assertEqual(result, 'v\n')

    def test_solve_factorio_belt_balancer_2_2_flow_up(self):
        result = solve_factorio_belt_balancer((2, 2), 1, [
            (0, 0, 'S', 0, 1),
            (0, 1, 'N', 0, -1),
        ])
        # One belt that goes down
        self.assertEqual(result,
            '^O\n' +
            '^O\n'
        )

    def test_solve_factorio_belt_balancer_2_2_1_flow_down(self):
        result = solve_factorio_belt_balancer((2, 2), 1, [
            (0, 1, 'N', 0, 1),
            (0, 0, 'S', 0, -1),
        ])
        # One belt that goes down
        self.assertEqual(result,
            'vO\n' +
            'vO\n'
        )
    def test_solve_factorio_belt_balancer_3_3_1_flow_down(self):
        result = solve_factorio_belt_balancer((3, 3), 1, [
            (0, 2, 'N', 0, 1),
            (0, 0, 'S', 0, -1),
        ])
        # One belt that goes down
        self.assertEqual(result,
            'vOO\n' +
            'vOO\n' +
            'vOO\n'
        )

    def test_solve_factorio_belt_balancer_3_3_1_flow_up(self):
        result = solve_factorio_belt_balancer((3, 3), 1, [
            (0, 2, 'N', 0, -1),
            (0, 0, 'S', 0, 1),
        ])
        # One belt that goes down
        self.assertEqual(result,
            '^OO\n' +
            '^OO\n' +
            '^OO\n'
        )

    def test_solve_factorio_belt_balancer_2_2_2(self):
        # Two flows in parallel
        result = solve_factorio_belt_balancer((2, 2), 2, [
            (0, 1, 'N', 0, 1),
            (0, 0, 'S', 0, -1),
            (1, 1, 'N', 1, 1),
            (1, 0, 'S', 1, -1),
        ])
        # Two parallel belts that go down
        self.assertEqual(result,
            'vv\n' +
            'vv\n'
        )

    ###
    ### Mixers
    ###

    def test_solve_factorio_belt_balancer_mixer_2_1(self):
        # Two flows in parallel that need to be mixed
        result = solve_factorio_belt_balancer((2, 1), 2, [
            (0, 0, 'S', 0, 1),
            (1, 0, 'S', 1, 1),
            (0, 0, 'N', 0, -0.5),
            (0, 0, 'N', 1, -0.5),
            (1, 0, 'N', 0, -0.5),
            (1, 0, 'N', 1, -0.5),
        ])
        # Single mixer that gos up
        self.assertEqual(result,
            'Ww\n'
        )

    def test_solve_factorio_belt_balancer_mixer_belt_2_2(self):
        # Two flows in parallel, requires two belts
        result = solve_factorio_belt_balancer((2, 2), 2, [
            (0, 0, 'S', 0, 1),
            (1, 0, 'S', 1, 1),
            (0, 1, 'N', 0, -0.5),
            (0, 1, 'N', 1, -0.5),
            (1, 1, 'N', 0, -0.5),
            (1, 1, 'N', 1, -0.5),
        ])
        # Single mixer that goes up
        self.assertEqual(result,
            '^^\n'
            'Ww\n'
        )

    def test_solve_factorio_belt_balancer_mixer_belt_2_3(self):
        # Two flows in parallel, requires two belts
        result = solve_factorio_belt_balancer((2, 3), 2, [
            (0, 0, 'S', 0, 1),
            (1, 0, 'S', 1, 1),
            (0, 2, 'N', 0, -0.5),
            (0, 2, 'N', 1, -0.5),
            (1, 2, 'N', 0, -0.5),
            (1, 2, 'N', 1, -0.5),
        ])
        # Single mixer that goes up
        self.assertEqual(result,
            'Ww\n'
            '^^\n'
            '^^\n'
        )

if __name__ == '__main__':
    unittest.main()