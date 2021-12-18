"""
test how the response from eToxSys looks like
"""

# api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
from knowledgehub.api import KnowledgeHubAPI
import sys
from Concordance.condordance_utils import getPreclinicalCompounds

api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

status = api.login('tester', 'tester')
drugs = getPreclinicalCompounds(api)
for drug in drugs:
    print(drug)
