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
    api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
    api.login('e.vanmulligen@erasmusmc.nl', 'Crosby99!')
    status = api.SimilarityService().spaces()
    print(f'status={status}')
    omeprazole = 'COc1ccc2[nH]c([S+]([O-])Cc3ncc(C)c(OC)c3C)nc2c1'
    # omeprazole = 'CCC1=C(C)CN(C(=O)NCCC2=CC=C(C=C2)S(=O)(=O)NC(=O)NC2CCC(C)CC2)C1-Cl'
    similar_compounds = api.SimilarityService().get(omeprazole)

    pprint.pprint(similar_compounds)


if __name__ == "__main__":
    main()
