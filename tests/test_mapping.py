from knowledgehub.api import KnowledgeHubAPI
import argparse

parser = argparse.ArgumentParser(description='Process parameters for collecting all data from eToxSys')
parser.add_argument('-username', required=True, help='username')
parser.add_argument('-password', required=True, help='password')
args = parser.parse_args()

api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
status = api.login(args.username, args.password)
print(status)

# result = api.SemanticService().normalize(term='necrosis', vocabularies='HPATH')
# print(result)
#
# result = api.SemanticService().normalize(term='liver', vocabularies='MA')
# print(result)

result = api.SemanticService().mapToClinical('MC:0000097', 'MA:0000139', 'ETOX2MEDDRAPT')
print(result)

