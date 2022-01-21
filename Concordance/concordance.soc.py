from pprint import pprint

from knowledgehub.api import KnowledgeHubAPI
import argparse
import json
import os
import sys
import mysql.connector

from Concordance.condordance_utils import getDrugsMapping, getClinicalDatabases, getPreclinicalDatabases, getSocs, getSocDrugFindings
from Concordance.mapper import Mapper


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    parser.add_argument('-host', required=True, help='mysql server')
    parser.add_argument('-database', required=True, help='mysql database')
    parser.add_argument('-dbuser', required=True, help='mysql database user')
    parser.add_argument('-dbpass', required=True, help='mysql database password')
    parser.add_argument('-drug_mappings', required=False, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    mapper = Mapper(api)

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    if args.drug_mappings is None:
        drugs = getDrugsMapping(api, getClinicalDatabases(api), getPreclinicalDatabases(api))
    else:
        if os.path.isfile(args.drug_mappings):
            with open(args.drug_mappings, 'r') as drug_file:
                drugs = json.loads(drug_file.read())
        else:
            drugs = getDrugsMapping(api, getClinicalDatabases(api), getPreclinicalDatabases(api))
            with open(args.drug_mappings, 'x') as drug_file:
                drug_file.write(json.dumps(drugs))

    print(f'#drugs found: {len(drugs.keys())}')

    db = mysql.connector.connect(host=args.host, database=args.database, username=args.dbuser, password=args.dbpass)

    ClinicalDatabases = getClinicalDatabases(api);
    PreclinicalDatabases = getPreclinicalDatabases(api)
    groups = {}

    preclinical_findings = {}
    clinical_findings = {}
    for drug in drugs:
        preclinical_findings[drug] = getSocDrugFindings(db=db, drugInfo=drugs[drug], databases=PreclinicalDatabases.keys(), table='preclinical_findings')
        clinical_findings[drug] = getSocDrugFindings(db=db, drugInfo=drugs[drug], databases=ClinicalDatabases.keys(), table='clinical_findings')

    # get first the list of SOCs
    for soc in getSocs(db, ['preclinical_findings', 'clinical_findings']):
        groups[soc] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
        for drug in drugs:
            if soc in preclinical_findings[drug]:
                if soc in clinical_findings[drug]:
                    groups[soc]['tp'] += 1
                else:
                    groups[soc]['fp'] += 1
            else:
                if soc in clinical_findings[drug]:
                    groups[soc]['fn'] += 1
                else:
                    groups[soc]['tn'] += 1

        print(soc)
        pprint(groups[soc])


if __name__ == "__main__":
    main()

