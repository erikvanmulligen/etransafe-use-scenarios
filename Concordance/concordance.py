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
            with open(args.drug_mappings, 'w') as drug_file:
                drug_file.write(json.dumps(drugs))

    print(f'#drugs found: {len(drugs.keys())}')

    db = mysql.connector.connect(host=args.host, database=args.database, username=args.dbuser, password=args.dbpass)

    ClinicalDatabases = getClinicalDatabases(api);
    PreclinicalDatabases = getPreclinicalDatabases(api)
    groups = {}
    # get first the list of SOCs
    socs = getSocs(db,['preclinical_findings', 'clinical_findings'])
    for soc in socs:
        groups[soc] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
        for drug in drugs:
            preclinical_findings = getSocDrugFindings(db=db, soc=soc, drugInfo=drugs[drug], databases=PreclinicalDatabases.keys(), table='preclinical_findings')
            clinical_findings = getSocDrugFindings(db=db, soc=soc, drugInfo=drugs[drug], databases=ClinicalDatabases.keys(), table='clinical_findings')

            if len(preclinical_findings) > 0:
                if len(clinical_findings) > 0:
                    groups[soc]['tp'] += 1
                else:
                    groups[soc]['fp'] += 1
            else:
                if len(clinical_findings) > 0:
                    groups[soc]['fn'] += 1
                else:
                    groups[soc]['tn'] += 1

        print(soc)
        pprint(groups[soc])

    # all_preclinical_findings = {mapper.getKey(f): {'findingCode': f[0], 'specimenOrganCode': f[1], 'SOC': f[2]} for f in getAllFindings(db, "preclinical_findings", "WHERE findingCode IS NOT NULL")}
    # all_clinical_findings = {mapper.getKey(f): {'findingCode': f[0], 'specimenOrganCode':f[1], 'SOC': f[2]} for f in getAllFindings(db, "clinical_findings", "WHERE findingCode IS NOT NULL")}
    # all_preclinical_mapped_findings = {mapper.getKey(f): {'findingCode': f[0], 'specimenOrganCode': f[1], 'SOC': f[2]} for f in getAllFindings(db, "preclinical_findings", "WHERE findingCode IS NOT NULL AND mapped IS true")}
    # all_preclinical_non_mapped_findings = {mapper.getKey(f): {'findingCode': f[0], 'specimenOrganCode': f[1], 'SOC': f[2]} for f in getAllFindings(db, "preclinical_findings", "WHERE findingCode IS NOT NULL AND mapped IS false")}
    # all_clinical_mapped_findings = {mapper.getKey(f): {'findingCode': f[0], 'specimenOrganCode': f[1], 'SOC': f[2]} for f in getAllFindings(db, "clinical_findings", "WHERE findingCode IS NOT NULL AND mapped IS true")}
    #
    # print(f'{len(all_preclinical_findings)} all_preclinical_findings')
    # print(f'{len(all_preclinical_mapped_findings)} all_preclinical_mapped_findings')
    # print(f'{len(all_preclinical_non_mapped_findings)} all_preclinical_non_mapped_findings')
    # print(f'{len(all_clinical_findings)} all_clinical_findings')
    # print(f'{len(all_clinical_mapped_findings)} all_clinical_mapped_findings')

    # count per drug the animal observations that have or don't have a corresponding clinical observation
    # for inchiKey in drugs:
    #     clinical_codes = set()
    #     preclinical_codes = set()
    #
    #     print(f'drug:{drugs[inchiKey]["clinicalName"]}, inchikey:{inchiKey}')

        # # collect list of preclinical findings
        # for database in PreclinicalDatabases:
        #     for f in [f['FINDING'] for f in PreclinicalDatabases[database].getAllFindingByIds(drugs[inchiKey][database])]:
        #         preclinical_codes.add(mapper.getKey(f))
        #
        # for database in ClinicalDatabases:
        #     if database in drugs[inchiKey] and drugs[inchiKey][database] is not None:
        #         for f in [f['FINDING'] for f in ClinicalDatabases[database].getAllFindingByIds(drugs[inchiKey][database])]:
        #             clinical_codes.add(mapper.getKey(f))
        #
        # for preclinical_code in preclinical_codes:
        #     soc = map_soc(all_preclinical_findings[preclinical_code]['SOC'])
        #     create_soc(groups, soc)
        #     if preclinical_code in all_preclinical_mapped_findings:
        #         groups['all']['tp'] += 1
        #         groups[soc]['tp'] += 1
        #     else:
        #         groups['all']['fp'] += 1
        #         groups[soc]['fp'] += 1
        #
        # # if a clinical code is not mapped to a preclinical we deal with a false negative
        # for clinical_code in clinical_codes:
        #     if clinical_code not in all_clinical_mapped_findings:
        #         soc = map_soc(all_clinical_findings[clinical_code]['SOC']) if clinical_code in all_clinical_findings else 'other'
        #         create_soc(groups, soc)
        #         groups['all']['fn'] += 1
        #         groups[soc]['fn'] += 1
        #
        # # if a preclinical code is not mapped and not part of the drug preclinical findings
        # for preclinical_code in all_preclinical_non_mapped_findings:
        #     soc = map_soc(all_preclinical_findings[preclinical_code]['SOC'])
        #     create_soc(groups, soc)
        #     if preclinical_code not in preclinical_codes:
        #         groups['all']['tn'] += 1
        #         groups[soc]['tn'] += 1

    # for key in groups:
    #     print(f"{key},TP:{groups[key]['tp']},FP:{groups[key]['fp']},FN:{groups[key]['fn']},TN:{groups[key]['tn']}")


if __name__ == "__main__":
    main()

