import argparse
import json
import sys

from Concordance.condordance_utils import getDrugsMapping, getClinicalDatabases, getPreclinicalDatabases
from knowledgehub.api import KnowledgeHubAPI


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    parser.add_argument('-host', required=True, help='mysql server')
    parser.add_argument('-database', required=True, help='mysql database')
    parser.add_argument('-dbuser', required=True, help='mysql database user')
    parser.add_argument('-dbpass', required=True, help='mysql database password')
    parser.add_argument('-drug_mappings', required=False, help='drug mapping')
    parser.add_argument('-drug', required=False, help='drug')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    with open(args.drug_mappings, 'r') as drug_file:
        drugs = json.loads(drug_file.read())

    print(f'#drugs found: {len(drugs.keys())}')

    for db in getClinicalDatabases(api):
        if db in drugs[args.drug]:
            print('%s : %s' % (db, drugs[args.drug][db]))
    for db in getPreclinicalDatabases(api):
        if db in drugs[args.drug]:
            print('%s : %s' % (db, drugs[args.drug][db]))


if __name__ == "__main__":
    main()