import json
import unittest
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
                "entities": [{"entity_number": 1, "name": "transport-belt", "position": {"x": 0, "y": 0}, "direction": 0}],
                "version": FACTORIO_BLUEPRINT_VERSION
            }
        })

class TestFactorioBlueprintEncodeJson(unittest.TestCase):

    def test_encoded_blueprint_1_b(self):
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('▲', (1, 1))),
            '0eJx1jUsKwjAQhq9SZh2hL6x26TVEJGkHCaSTkkzFUnJ3J+3GjZuB//XNBsYtOAdLDP0GlnGC/sdT4LRBJ94NHRdGO00DhkICO3iK0N83iPZF2uU9rzNKd8coID1lxUFTnH3gk5AYkkxpxA/0VXooQGLLFg/SLtYnLZPBIIV/DAWzjzLzlL8KqlSwyhX2aAMOR1Jm/htD3FV9qdruWnfnpm2bukzpC063U4M='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('▼', (1, 1))),
            '0eJx1jUsKwjAQhq9SZh2hL6xm6TVEJG0HCaTTkEzFUnJ3J+3GjZuB//XNBr1b0AdLDHoDyziB/vEUONOjE++GjoveOEMDhkICO8wUQd83iPZFxuU9rx6lu2MUkJmy4mAo+jnwSUgMSaY04gd0lR4KkNiyxYO0i/VJy9RjkMI/hgI/R5nNlL8KqlSwyhX2aAMOR9Jm/htD3FV9qdruWnfnpm2bukzpC08zU4c='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('▶', (1, 1))),
            '0eJx1jUsKwjAQhq9SZh2hL6xm6TVEJG0HCaTTkEzFUnJ3J+3GjZuB//XNBr1b0AdLDHoDyziB/vEUONOjE++GjoveOEMDhkICO8wUQd83iPZFxuU9rx6lu2MUkJmy4mAo+jnwSUgMSaY04gd0lR4KkNiyxYO0i/VJy9RjkMI/hgI/R5nNlL8KqlSwyhX2aAMOR1Jn/htDPNSlartr3Z2btm3qMqUvTvVThQ=='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('◀', (1, 1))),
            '0eJx1jUsKwjAQhq9SZh2hL1rN0muISFIHCaTTkkzFUnJ3J+3GjZuB//XNBtYvOAdHDHoDxziC/vEUeGPRi3dFz4U13tCAoZDADRNF0LcNonuR8XnP64zS3TEKyIxZcTAU5ynwSUgMSab0xA/oKt0VILFjhwdpF+uDltFikMI/hoJ5ijKbKH8VVKlglSvspws4HEmX+W8McVf1uWr7S913Tds2dZnSF09xU4k='
        )

    def test_encoded_blueprint_1_u_a(self):
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('△', (1, 1))),
            '0eJxNjtEKwjAMRX9F8lxhzuF0j/6GiHQzjEKXljQTx9i/m24oviTc5N6TzND6ESM7EmhmcIIDNH8zA9626HV2RS+71npLHfJOF64LlKC5zZBcT9bnvEwR1btiDJAdshK2lGJg2StJYNEoPfENzWG5G0ASJw430iqmB41Di6yGH2PUBPcctG8UAzEkDQbKdxVWGJi0Kv37BMUx+56OsduMRT74Qk6rKs+Hqr6U9elYVceyWJYPJ/FZIw=='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('▽', (1, 1))),
            '0eJxNjt0KgzAMhV9l5LoDp7IfL/caY4yqYRRqWtI4JuK7L1U2dpNwknO+ZIbWjxjZkUAzgxMcoPmbGfC2Ra+zK3rZtdZb6pB3unBdoATNbYbknmR9zssUUb0rxgDZISthSykGlr2SBBaNUo9vaA7L3QCSOHG4kVYxPWgcWmQ1/BijJvjJQftGMRBD0mCgfFdhhYFJq9K/T1Acs693jN1mrPPBF3JaVXk+1KdLeTpWdV2VxbJ8AChtWSc='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('▷', (1, 1))),
            '0eJxNjt0KwjAMhV9l5LqC+8GfXfoaItLNIIUuLWkmjrF3N91QvEk4yTlfMkPnR4zsSKCdwQkO0P7NDHjbodfZBb0UnfWWeuRCF64PlKC9zpDck6zPeZkiqnfFGCA7ZCVsKcXAslOSwKJReuAb2nK5GUASJw430iqmO41Dh6yGH2PUBD85aN8oBmJIGgyU7ypsb2DSqvTvExTH7Hs4xn4zVvngCzlt6lQ2x3N1PNRNU1f7ZfkAKC9ZJQ=='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('◁', (1, 1))),
            '0eJxNjtEKwjAMRX9F8lxBtzF1j/6GiHRbkEKXljQTx9i/m24oviTc5N6TzND6ESM7EmhmcIIDNH8zA9626HV2RS+71npLHfJOF64LlKC5zZDck6zPeZkiqnfFGCA7ZCVsKcXAsleSwKJR6vENzXG5G0ASJw430iqmB41Di6yGH2PUBD85aN8oBmJIGgyU7yrsYGDSqvTvExTH7OsdY7cZ63zwhZxWVZyP1elSnOqyqsrisCwfKKtZKQ=='
        )

    def test_encoded_blueprint_1_u_b(self):
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('↥', (1, 1))),
            '0eJxNjt0KwjAMhV9Fcl1hzuHPLn0NEelmkEKXljQVx9i7m24i3iSc5JwvmaDzGSM7EmgncIIDtH8zA9526HV2QS+bznpLPfJGF64PlKC9TpDck6wveRkjqnfBGCA7FCVsKcXAslWSwKxReuAb2t18M4AkThyupEWMd8pDh6yGHyNrgp8ctK8UAzEkDQYqdxVWGRi1Kv37RMgSczE+HGO/Oqty8YWcFlWfds3xXB8P+6bZ19U8fwCLMFmk'
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('↧', (1, 1))),
            '0eJxNjt0KwjAMhV9Fcl1Bt+HPLn0NEelmkEKXljQVx9i7m24i3iSc5JwvmaDzGSM7EmgncIIDtH8zA9526HV2QS+bznpLPfJGF64PlKC9TpDck6wveRkjqnfBGCA7FCVsKcXAslWSwKxReuAb2v18M4AkThyupEWMd8pDh6yGHyNrgp8ctK8UAzEkDQYqdxW2MzBqVfr3iZAl5mJ8OMZ+dTbl4gs5Lao67ZvjuToe6qapq908fwCLrFmo'
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('↦', (1, 1))),
            '0eJxNjt0KwjAMhV9Fcl1hzuHPLn0NEem2IIUuLWkqjrF3N3Ui3iSc5JwvmaHzGSM7EmhncIIjtH8zA9526HV2QS+bznpLPfJGF64PlKC9zpDcg6wveZkiqveDMUB2LErYUoqBZaskgUWjNOAL2t1yM4AkThyupI+Y7pTHDlkNP0bWBD84aF8pBmJIGgxU7iqsMjBpVfr3iZAl5mIcHGO/Outy8YmcVnXaNcdzfTzsm2ZfV8vyBotuWaY='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('↤', (1, 1))),
            '0eJxNjt0KwjAMhV9Fcl1Bt+HPLn0NEelmkEKXljQVx9i7m24i3iSc5JwvmaDzGSM7EmgncIIDtH8zA9526HV2QS+bznpLPfJGF64PlKC9TpDck6wveRkjqnfBGCA7FCVsKcXAslWSwKxReuAb2v18M4AkThyupEWMd8pDh6yGHyNrgp8ctK8UAzEkDQYqdxW2MzBqVfr3iZAl5mJ8OMZ+dR7KxRdyWlR12jfHc3U81E1TV7t5/gCL6lmq'
        )

    def test_encoded_blueprint_1_m(self):
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('↿↾', (2, 1))),
            '0eJxNjdsKwjAMhl9l5LrKTjrdpa8hIu0WpNBlpc3EMfruZhuIV+E/fVnAuAl9sMTQLmAZB2j/PAVOG3Ti3dBxZrTT1GHIJLDdSBHa+wLRvki7dc+zR+luGAWkh1Vx0BT9GPggJIYkU+rxA22RHgqQ2LLFnbSJ+UnTYDBI4ceI3llm8RT4McpgpPWfQPLjScEsV7i9DdjtWb6y3xjipspLUTfXsjlXdV2VeUpf1WpRnA=='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('⇃⇂', (2, 1))),
            '0eJxNjdsKwjAMhl9l5LrKDtXpLn0NEem2IIUuK20mjtF3N9tAvAr/6csCrZvQB0sMzQKWcYDmz1PgTItOvBs6zlrjDHUYMglsN1KE5r5AtC8ybt3z7FG6G0YBmWFVHAxFPwY+CIkhyZR6/EBTpIcCJLZscSdtYn7SNLQYpPBjRO8ss3gK/BhlMNL6TyD58aRglivc3gbs9kyv7DeGuKnyUuj6WtbnSuuqzFP6AtXmUaA='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('⇀\n⇁', (1, 2))),
            '0eJxNjdsKwjAMhl9l5LrKTjrdpa8hIu0WpNBlpc3EMfruZhuIN4H/9GUB4yb0wRJDu4BlHKD98xQ4bdCJd0PHmdFOU4chk8B2I0Vo7wtE+yLt1j3PHqW7YRSQHlbFQVP0Y+CDkBiSTKnHD7RFeihAYssWd9Im5idNg8EghR8jemeZxVPgxyiDkdZ/AskVzHKPJ+H2NmC3Z+XKfmOIu7oUdXMtm3NV11WZp/QF1fxRng=='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('↼\n↽', (1, 2))),
            '0eJxNjdsKwjAMhl9Fcl1lJzfdpa8hIu0WpNClpc3EMfbuZhuIN4H/9GUG40YM0RJDO4NlHKD98xQ4bdCJd0PHB6Odpg7jQQLbeUrQ3mdI9kXarXueAkp3wyggPayKo6YUfOSjkBgWmVKPH2jz5aEAiS1b3EmbmJ40DgajFH6MFJxlFk9B8EkGntZ/AskUTHJPZ+H2NmK3Z/XKfmNMmyouedVci6Yuq6ossmX5AtZ4UaI='
        )

    def test_encoded_blueprint_position_on_grid_2_b(self):
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('▲\n▲\n', (1, 2))),
            '0eJyVjs0KwkAMhF9Fcl6hf1jdo68hIrttkIVtWnZTsZR9d9P2IooHL4HJzHzJDNaPOARHDHoGx9iBftsp8Mail90ZPe+s8YYaDDsxXNNTBH2ZIbo7Gb/0eRpQsitGAZluURwMxaEPvBcSQ5IqtfgEnaerAiR27HAjrWK60dhZDBL4xVAw9FFqPS1XBZUpmGQKu3UBm80R+YUs/kTmn0h5+YEhrqo45lV9KupDWVVlkaX0AptWb1g='
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('▲▲', (2, 1))),
            '0eJyNjt0KwjAMhV9Fcl1hfzjtpa8hIu0WpNBlo83EMfruZtuNoII3gZNzzpfMYP2IQ3DEoGdwjB3ot50Cbyx62Z3R884ab6jBsBPDNT1F0JcZoruT8UufpwElu2IUkOkWxcFQHPrAeyExJKlSi0/QeboqQGLHDjfSKqYbjZ3FIIFfDAVDH6XW03JVUJmCSaawWxew2RyRH8jib2T+HSkvPzDEVRXHvKpPRX0oq6osspRem1xvWA=='
        )

    def test_encoded_blueprint_position_on_grid_2_b_1_m(self):
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('↿↾\n▲▲', (2, 2))),
            '0eJyN0MkKwjAQBuBXkTlH6eaWo68hImkdJJBOQzIVS+m7O60gQhU9hX+WLyE9lK5FHywx6B4sYw36rabAmRKd1A7oeFEaZ6jCsJCGrRqKoI89RHsl48Z97jzK7MQoIFOPiYOh6JvAS5EYBlmlC95Bp8NJARJbtviUptCdqa1LDDLwMqJ3lllqCnwTZaGh8T5BktVaQSenuBcbsHr2JM647NuT5uhEpr/J/G8y/UzKD9wwxCllu7TY7rPtJi+KPEuG4QE6BolI'
        )
        self.assertEqual(
            encode_components_blueprint_json(generate_entities_blueprint('▲▲\n↿↾', (2, 2))),
            '0eJyN0EsKwjAQBuCrlFlH6UurXXoNEUnbQQLpNCSjWErv7rSCiEXoJvDP40vIAJW9o/OGGMoBDGML5VdNgdUVWqmd0HJUaaupRh9Jw9QdBSjPAwRzI22nfe4dyuzMKCDdTom9puA6zxuRGEZZpQafUCbjRQESGzb4lubQX+neVuhl4J+hwHVB1jqabhUqVtDLKXZjPNbvjsQFma4mk7Vk9iGDs4ZZasv3bXczl/xy8gMP9GFO6SHJi2Na7LM8z9J4HF+W+olH'
        )
