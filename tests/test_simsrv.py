import pprint
import argparse

from src.knowledgehub.api import KnowledgeHubAPI


def main():
    #api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    #api.set_service('DEV')
    print('before login')
    api.login('tester', 'tester')
    print('after login')
    status = api.SimilarityService().spaces()
    print(f'status={status}')
    omeprazole = 'CCC1=C(C)CN(C(=O)NCCC2=CC=C(C=C2)S(=O)(=O)NC(=O)NC2CCC(C)CC2)C1-Cl'
    similar_compounds = api.SimilarityService().get(omeprazole, cutoff=0.3)

    if similar_compounds != None:
        names = []
        smiles = []
        similarities = []

        if ('search_results' in similar_compounds) and (len(similar_compounds['search_results']) == 1):
            search_result = similar_compounds['search_results'][0]
            if 'obj_nam' in search_result:
                for i in range(len(search_result['obj_nam'])):
                    names.append(search_result['obj_nam'][i])
                    smiles.append(search_result['SMILES'][i])
                    similarities.append("{:.4f}".format(search_result['distances'][i]))

                for cmp in search_result['obj_nam']:
                    concept = api.ChemistryService().getCompoundByName(cmp)
                    print(concept)
                    # concept = api.SemanticService().normalize(cmp, ['RxNorm'])
                    # if 'concepts' in concept and len(concept['concepts']) == 1:
                    #     compoundIds.append(concept['concepts'][0]['conceptCode'])
                    #     compoundNames.append(concept['concepts'][0]['conceptName'])
            else:
                print('something wrong in the result object from the similarity service')


if __name__ == "__main__":
    main()
