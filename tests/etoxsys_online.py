import argparse
from knowledgehub.services import Services
from knowledgehub.api import KnowledgeHubAPI


def test():
    parser = argparse.ArgumentParser(description='test similarity service')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()
    #api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    status = api.login(args.username, args.password)
    print(status)

    findings = api.eToxSys().getAllFindings(10)

if __name__ == "__main__":
    test()