import pprint
import argparse
import sys

from src.knowledgehub.api import KnowledgeHubAPI


def main():
    api = KnowledgeHubAPI()
    api.set_service('DEV')
    api.login('tester', 'tester')

    omeprazole = 'CCC1=C(C)CN(C(=O)NCCC2=CC=C(C=C2)S(=O)(=O)NC(=O)NC2CCC(C)CC2)C1-Cl'

    count = api.ChemistryService().getCompoundCount()
    print(count)

    smiles = api.ChemistryService().getSMILESbyNames(['Fingolimod'])
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
