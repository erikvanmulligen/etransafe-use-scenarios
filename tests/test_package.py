from knowledgehub.api import KnowledgeHubAPI

api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
api.login('tester', 'tester')
compoundSmile = api.ChemicalService().getSMILESByName('omeprazole')
print(f'Found SMILES {compoundSmile[0]} for {"omeprazole"}')
similar_compounds = api.SimilarityService().get(compoundSmile)
print(f'similar compounds:{similar_compounds}')
