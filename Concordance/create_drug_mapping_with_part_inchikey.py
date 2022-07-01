"""
    Program to retrieve all drugs that are found
    in preclinical and clinical databases

    (C) 2022, dept of Medical Informatics, Erasmus University Medical Center.
    Erik M. van Mulligen
"""
import argparse
import json
import sys

from knowledgehub.api import KnowledgeHubAPI

from Concordance.condordance_utils import getDrugsMapping, getClinicalDatabases, getPreclinicalDatabases, getDrugsMapping2


def main():
    argParser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    argParser.add_argument('-username', required=True, help='username')
    argParser.add_argument('-password', required=True, help='password')
    argParser.add_argument('-drugs', required=True, help='filename containing drugs')
    args = argParser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    drugs = getDrugsMapping2(api, getClinicalDatabases(api), getPreclinicalDatabases(api))
    with open(args.drugs, 'x') as drug_file:
        drug_file.write(json.dumps(drugs))


if __name__ == "__main__":
    main()