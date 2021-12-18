import pprint
import argparse
import sys

from src.knowledgehub.api import KnowledgeHubAPI


def main():
    api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
    #api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    api.login('erik.mulligen', 'Crosby99!')

    omeprazole = 'CCC1=C(C)CN(C(=O)NCCC2=CC=C(C=C2)S(=O)(=O)NC(=O)NC2CCC(C)CC2)C1-Cl'

    smiles = api.ChemistryService().getCompoundByName('Fingolimod')
    print(smiles)

    # recid = 0
    # while True:
    #     recid += 1
    #     compound = api.ChemicalService().getCompoundByRecNr(recid)
    #     if compound is None:
    #         continue
    #     if compound['name'] is not None:
    #         print(f'{recid}:{compound["name"]}')
    #         if compound['name'].lower() == 'omeprazole':
    #             break


if __name__ == "__main__":
    main()
