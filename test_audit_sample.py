import copy
import unittest
from audit_sample import select


class SampleTests(unittest.TestCase):
    def setUp(self):
        self.population = [{'id': str(i), 'stratum': 'high' if i < 3 else 'normal'} for i in range(10)]
        self.plan = {'high': 3, 'normal': 2}

    def test_order_independent_reproducibility(self):
        self.assertEqual(select(self.population, self.plan, 'fixed'), select(list(reversed(self.population)), self.plan, 'fixed'))

    def test_exact_counts_no_replacement(self):
        report = select(self.population, self.plan, 'fixed')
        chosen = [row['id'] for group in report['selections'] for row in group['selected']]
        self.assertEqual(len(chosen), 5)
        self.assertEqual(len(set(chosen)), 5)
        self.assertTrue({'0', '1', '2'} <= set(chosen))

    def test_population_change_changes_digest(self):
        altered = copy.deepcopy(self.population)
        altered[0]['context'] = 'changed'
        self.assertNotEqual(select(self.population, self.plan, 'fixed')['population_sha256'], select(altered, self.plan, 'fixed')['population_sha256'])

    def test_duplicate_ids_and_incomplete_plan_fail(self):
        with self.assertRaises(ValueError):
            select(self.population + [self.population[0]], self.plan, 'fixed')
        with self.assertRaises(ValueError):
            select(self.population, {'high': 1}, 'fixed')

    def test_invalid_counts_fail(self):
        for count in (-1, True, 99, 1.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                select(self.population, {'high': count, 'normal': 2}, 'fixed')


if __name__ == '__main__':
    unittest.main()
