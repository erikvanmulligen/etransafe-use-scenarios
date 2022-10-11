import unittest
from knowledgehub.api import KnowledgeHubAPI
from Concordance3.settings import settings


class MyTestCase(unittest.TestCase):
    def test_something(self):
        api = KnowledgeHubAPI(server=settings['kh']['server'], client_secret=settings['kh']['client_secret'])

        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
