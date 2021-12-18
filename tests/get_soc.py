from knowledgehub.api import KnowledgeHubAPI

api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
api.login('tester', 'tester')
socs = api.SemanticService().getSocByCode('10000060')
print(socs)
