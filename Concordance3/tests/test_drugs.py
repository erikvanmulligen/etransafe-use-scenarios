import unittest

import mysql.connector

from Concordance3.classes.table import Table
from Concordance3.settings import settings

class MyTestCase(unittest.TestCase):
    def connect(self):
        print(settings)
        self.db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'],
                                          username=settings['db']['user'], password=settings['db']['password'])

    def test_something(self):
        self.connect()
        drugs = Table(self.db)
        records = drugs.select('select * from drugs')
        for record in records:
            print(f'inchi_key:{record.get("inchi_key")}')
        self.assertEqual(len(records), 298)  # add assertion here


if __name__ == '__main__':
    unittest.main()
