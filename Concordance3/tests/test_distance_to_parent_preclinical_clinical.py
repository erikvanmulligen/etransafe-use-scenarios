import unittest
import mysql.connector
from Concordance3.settings import settings
from Concordance3.classes.table import Table

class MyTestCase(unittest.TestCase):
    def test_distance(self):
        self.db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'],
                                          username=settings['db']['user'], password=settings['db']['password'])
        self.meddra = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'],
                                              username=settings['db']['user'], password=settings['db']['password'])
        preclininical_distance = Table(self.db)
        records = preclininical_distance.select('select findingCode from findings where db in ("Medline")')
        for record in records:
            print(record.get('findingCode'))
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
