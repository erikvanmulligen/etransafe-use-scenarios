import unittest
from knowledgehub.services import Services
from knowledgehub.api import KnowledgeHubAPI
import argparse


class ServiceTest(unittest.TestCase):
    services = None
    username = None
    password = None

    def setUp(self, username, password):
        super(ServiceTest, self).setUp()
        api = KnowledgeHubAPI()
        api.set_service('DEV')
        api.login(self.username, self.password)
        self.services = Services(api.get_token(), 'https://dev.toxhub.etransafe.eu/registry.kh.svc/api/v1')

    def test(self):
        databases = self.services.get('database')
        for database in databases:
            print(f'{database.get_title()}:{database.get_service_type()}:{database.get_address()}')
        self.assertEqual(len(databases), 5, 'failed')

    def tearDown(self):
        super(ServiceTest, self).tearDown()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process parameters for collecting information about services')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()
    print(args)
    ServiceTest.username = args.username
    ServiceTest.password = args.password
    unittest.main('tester' 'tester')