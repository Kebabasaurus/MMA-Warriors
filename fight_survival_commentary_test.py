"""Named composed-survival commentary has broad authored variety."""
import ast
import inspect
import textwrap
import unittest

from fight_engine import FightEngineMixin


class SurvivalCommentaryTests(unittest.TestCase):
    def test_at_least_fifty_survived_templates_are_authored(self):
        tree = ast.parse(textwrap.dedent(inspect.getsource(FightEngineMixin.evidence_driven_exchange_pool)))
        counts = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == 'survived' and isinstance(value, ast.Tuple):
                    strings = [item.value for item in value.elts if isinstance(item, ast.Constant) and isinstance(item.value, str)]
                    if any('{move}' in item for item in strings):
                        counts.append(len(strings))
        self.assertGreaterEqual(sum(counts), 50)
        self.assertGreaterEqual(min(counts), 25)

    def test_survival_template_placeholders_are_supported(self):
        tree = ast.parse(textwrap.dedent(inspect.getsource(FightEngineMixin.evidence_driven_exchange_pool)))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == 'survived' and isinstance(value, ast.Tuple):
                    for item in value.elts:
                        if isinstance(item, ast.Constant) and isinstance(item.value, str):
                            self.assertNotIn('{target_copy}', item.value)
                            self.assertIn('{actor}', item.value)
                            self.assertIn('{move}', item.value)


if __name__ == '__main__':
    unittest.main()
