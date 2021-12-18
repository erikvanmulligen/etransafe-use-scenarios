from knowledgehub.api import KnowledgeHubAPI
from ipypublish import nb_setup
import numpy as np

def main():
    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    authenticate(api, 'tester', 'tester')
    compound_name = 'omeprazole'
    smiles = translate_compound_to_smiles(api, compound_name)
    retrieve_similar_compounds(api, smiles, compound_name)

def authenticate(api, username, password):
    if api.login(username, password) == False:
        print("Failed to login")
    else:
        print("successfully logged in")

def translate_compound_to_smiles(api, compound_name):
    compound_smile = api.ChemicalService().getSMILESByName(compound_name)
    print(f'Found SMILES {compound_smile} for {compound_name}')
    return compound_smile

def retrieve_similar_compounds(api, compound_smile, compound_name):
    similar_compounds = api.SimilarityService().get(compound_smile, nr_results=20)
    print(f'similar_compounds:{similar_compounds}')

    similar_compounds.append({'name': compound_name, 'smiles': compound_smile, 'distance': 1.0})

    for similar_compound in similar_compounds:
        print(f'retrieving studies for {similar_compound["name"]}')
        studies = api.Medline().getStudiesBySMILES(similar_compound['smiles']) + \
                  api.Faers().getStudiesBySMILES(similar_compound['smiles']) + \
                  api.ClinicalTrials().getStudiesBySMILES(similar_compound['smiles']) + \
                  api.eToxSys().getStudiesBySMILES(similar_compound['smiles'])
                  # api.DailyMed().getStudiesBySMILES(similar_compound['smiles']) + \
        print(f'Found {len(studies)} studies.')

if __name__ == "__main__":
    main()