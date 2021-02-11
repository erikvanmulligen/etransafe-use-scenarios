import pprint
from kh.api import KnowledgeHubAPI


def main():
    api = KnowledgeHubAPI()
    api.login('e.vanmulligen@erasmusmc.nl', 'Crosby99')
    api.SimilarityService().spaces()
    omeprazole = 'CCC1=C(C)CN(C(=O)NCCC2=CC=C(C=C2)S(=O)(=O)NC(=O)NC2CCC(C)CC2)C1-Cl'
    similar_compounds = api.SimilarityService().get(omeprazole)
    pprint.pprint(similar_compounds)


if __name__ == "__main__":
    main()
