import unittest
from kh.services import Services
from kh.api import KnowledgeHubAPI


class ServiceTest(unittest.TestCase):
    services = None

    def setUp(self):
        super(ServiceTest, self).setUp()
        api = KnowledgeHubAPI()
        api.login('erik.mulligen', 'Crosby99!')
        self.services = Services(api.get_token(), 'https://aead2da1a152644f797ca358c0975f8e-1350926270.eu-west-1.elb.amazonaws.com/registry.kh.svc/api/v1')

    def test(self):
        databases = self.services.get('database')
        for database in databases:
            print(f'{database.get_title()}:{database.get_service_type()}:{database.get_address()}')
        self.assertEqual(len(databases), 5, 'failed')

    def tearDown(self):
        super(ServiceTest, self).tearDown()
        #self.mock_data = []


if __name__ == '__main__':
    unittest.main()