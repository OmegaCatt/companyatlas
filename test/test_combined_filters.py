import tempfile,unittest
from pathlib import Path
from contextlib import closing
from core import connect,init_database,answer_question
class CombinedFilters(unittest.TestCase):
    def test_customer_before_multi_year_scope_and_status(self):
        with tempfile.TemporaryDirectory() as folder,closing(connect(Path(folder)/'test.sqlite')) as db:
            init_database(db)
            question='Kolik dokončených objednávek pro Studio Javor v letech 2024 až 2025?'
            result=answer_question(db,'operations',question)
            count=db.execute("SELECT COUNT(*) FROM orders WHERE customer='Studio Javor' AND status='dokoncena' AND substr(placed_date,1,4) IN ('2024','2025')").fetchone()[0]
            self.assertEqual(result['kind'],'metric');self.assertEqual(result['count'],count);self.assertEqual(result['scope']['years'],['2024','2025']);self.assertEqual(result['scope']['customer'],'Studio Javor');self.assertEqual(result['scope']['status'],'dokoncena')
    def test_all_ranges_and_additional_years_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder,closing(connect(Path(folder)/'test.sqlite')) as db:
            init_database(db)
            for question,years in [('Kolik objednávek v letech 2021 až 2023 a 2025 až 2027?',list(map(str,[2021,2022,2023,2025,2026,2027]))),('Kolik objednávek od roku 2022 do roku 2025?',['2022','2023','2024','2025']),('Kolik objednávek 2024-2025 a 2027?',['2024','2025','2027'])]:
                result=answer_question(db,'operations',question);self.assertEqual(result['kind'],'metric');self.assertEqual(result['scope']['years'],years)
            self.assertEqual(answer_question(db,'operations','Kolik objednávek nad 2024 Kč?')['kind'],'clarification')
            self.assertEqual(answer_question(db,'operations','Kolik objednávek 2020-2040 a 2050?')['kind'],'clarification')
