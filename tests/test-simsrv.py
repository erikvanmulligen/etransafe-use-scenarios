import pprint
import argparse
from knowledgehub.api import KnowledgeHubAPI


def main():
    parser = argparse.ArgumentParser(description='test similarity service')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI()
    api.set_server('DEV')
    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    print('before login')
    api.login('tester', 'tester')
    print('after login')
    status = api.SimilarityService().spaces()
    print(f'status={status}')
    omeprazole = 'CCC1=C(C)CN(C(=O)NCCC2=CC=C(C=C2)S(=O)(=O)NC(=O)NC2CCC(C)CC2)C1-Cl'
    similar_compounds = api.SimilarityService().get(omeprazole)
    pprint.pprint(similar_compounds)


if __name__ == "__main__":
    main()
