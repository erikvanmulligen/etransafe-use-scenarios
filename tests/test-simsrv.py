import pprint
from kh.api import KnowledgeHubAPI


def main():
    api = KnowledgeHubAPI()
    api.set_service('DEV')
    api.login('erik.mulligen', 'Crosby99!')
    status = api.SimilarityService().spaces()
    print(f'status={status}')
    omeprazole = 'CCC1=C(C)CN(C(=O)NCCC2=CC=C(C=C2)S(=O)(=O)NC(=O)NC2CCC(C)CC2)C1-Cl'
    similar_compounds = api.SimilarityService().get(omeprazole)
    pprint.pprint(similar_compounds)


if __name__ == "__main__":
    main()
