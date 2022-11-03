from pprint import pprint

from knowledgehub.api import KnowledgeHubAPI
import argparse
import json
import os
import sys
import mysql.connector

from Concordance.condordance_utils import getDrugsMapping, getClinicalDatabases, getPreclinicalDatabases, getSocs, getSocDrugFindings, getMedDRA_PTs, getPTDrugFindings, getNamePT, getAllDrugFindings, \
    getAllPTFindings, getAllPreClinicalClinicalPTs, getAllPreclinicalClinicalDistances
from Concordance.mapper import Mapper
from Concordance.meddra import MedDRA


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

    db = mysql.connector.connect(host=args.host, database=args.database, username=args.dbuser, password=args.dbpass)
    all_preclinical_clinical_distances = getAllPreclinicalClinicalDistances(db=db, tables=['preclinical_meddra','clinical_meddra'])

    meddra = MedDRA(username=args.dbuser, password=args.dbpass)
    print(meddra.getHLT('10010726'))


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


    ClinicalDatabases = getClinicalDatabases(api);
    PreclinicalDatabases = getPreclinicalDatabases(api)

    groups = {}
    # get first the list of SOCs

    preclinical_pts = {}
    clinical_pts = {}
    for drug in drugs:
        preclinical_pts[drug] = getPTDrugFindings(db=db, drugInfo=drugs[drug], databases=PreclinicalDatabases.keys(), table='preclinical_meddra')
        clinical_pts[drug] = getPTDrugFindings(db=db, drugInfo=drugs[drug], databases=ClinicalDatabases.keys(), table='clinical_meddra')

    c = 0
    all_preclinical_clinical_pts = getAllPreClinicalClinicalPTs(db=db, tables=['preclinical_meddra','clinical_meddra'])
    for pt in all_preclinical_clinical_pts:
        c += 1
        print(f'{c}/{len(all_preclinical_clinical_pts)}: {pt}')
        groups[pt] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
        for drug in drugs:

            if pt in preclinical_pts[drug]:
                if pt in clinical_pts[drug]:
                    groups[pt]['tp'] += 1
                else:
                    groups[pt]['fp'] += 1
            else:
                if pt in clinical_pts[drug]:
                    groups[pt]['fn'] += 1
                else:
                    groups[pt]['tn'] += 1


if __name__ == "__main__":
    main()

