import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import connect,init_database
from evaluate import load_cases,offline_evaluation


class EvaluationTests(unittest.TestCase):
    def test_fifty_curated_cases_pass_without_key_or_network(self):
        cases=load_cases()
        self.assertEqual(len(cases),50)
        self.assertEqual(len({case['id'] for case in cases}),50)
        with tempfile.TemporaryDirectory() as folder:
            connection=connect(Path(folder)/'test.sqlite')
            try:
                init_database(connection)
                with patch('ai.read_api_key',side_effect=AssertionError('No key needed offline')),patch('urllib.request.urlopen',side_effect=AssertionError('No network offline')):
                    results=offline_evaluation(connection)
                self.assertTrue(all(result['passed'] for result in results),[r for r in results if not r['passed']])
            finally:
                connection.close()
