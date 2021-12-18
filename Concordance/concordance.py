from knowledgehub.api import KnowledgeHubAPI
import argparse
import json
import os
import requests
import knowledgehub.constants as constants
import ast
import sys
from Concordance.condordance_utils import getAllFindings, getDrugsMapping
from Concordance.mapper import Mapper


def getInchiKey(api, smiles, pa_type):
    r = api.ChemistryService().paStandardize(smiles, pa_type)
    if r is None:
        return None
    else:
        return r[0]


def filterFindings(findings):
    return [f for f in findings if f['dose'] != 0]


def getAllFindingByIds(api, service, finding_ids):
    result = []

    if finding_ids is not None and len(finding_ids) > 0:
        query = {
                    "filter": {
                        "criteria": [
                                        [
                                            {
                                                "field": {
                                                            "dataClassKey": "FINDING",
                                                            "name": "id"
                                                        },
                                                "primitiveType": "Integer",
                                                "comparisonOperator": "IN",
                                                "values": None,
                                            }
                                        ],
                                    ]
                    },
                    "selectedFields": [
                        {
                            "dataClassKey": "FINDING",
                            "names": [
                                "specimenOrgan",
                                "specimenOrganCode",
                                "specimenOrganVocabulary",
                                "finding",
                                "findingCode",
                                "findingVocabulary",
                                "dose",
                                "treatmentRelated",
                            ]
                        }
                    ],
                    "offset": 0,
                    "limit": 500
                }

        for index in range(0, len(finding_ids), 500):
            query['filter']['criteria'][0][0]['values'] = [{'value': finding} for finding in finding_ids[index:index+500]]

            for tries in range(0, 5):
                r = requests.post(service.endpoint + 'query', verify=False, headers={"Authorization": f"Bearer {api.get_token()}"}, json=query, timeout=None)

                if r.status_code == 200:
                    response = json.loads(r.text)

                    for record in response['resultData']['data']:
                        if record['FINDING']['finding'] is not None and record['FINDING']['findingCode'] is not None and (record['FINDING']['dose'] is None or record['FINDING']['dose'] > 0.0):
                            record['source'] = response['origin']
                            if service.mode == constants.USE_SEVERITY:
                                record['FINDING']['count'] = int(record['FINDING']['severity'])
                            elif service.mode == constants.INITIALIZE_1:
                                record['FINDING']['count'] = 1
                            result.append(record)
                    break
                elif r.status_code == 401:
                    api.reconnect()
                    continue
                else:
                    raise Exception('failed to access KnowledgeHub')
    else:
        print(f"Cannot search in {service.endpoint()}")
        return None

    return result


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

    ClinicalDatabases = {'ClinicalTrials': api.ClinicalTrials(), 'Medline': api.Medline(), 'Faers': api.Faers(), 'DailyMed': api.DailyMed()}
    PreclinicalDatabases = {'eToxSys': api.eToxSys()}

    if args.drug_mappings is None:
        drugs = getDrugsMapping(api)
    else:
        if os.path.isfile(args.drug_mappings):
            with open(args.drug_mappings, 'r') as drug_file:
                drugs = json.loads(drug_file.read())
        else:
            drugs = getDrugsMapping(api)
            with open(args.drug_mappings, 'w') as drug_file:
                drug_file.write(json.dumps(drugs))

    # check which smiles are found in one of the clinical databases
    total_count = 0
    total_match = 0

    groups = {
        'all': {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0},
        'other': {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0},
    }

    all_preclinical_findings = set([mapper.getKey(f) for f in getAllFindings(args.host, args.database, args.dbuser, args.dbpass, "preclinical_findings", "WHERE findingCode IS NOT NULL")])
    all_clinical_findings = set([mapper.getKey(f) for f in getAllFindings(args.host, args.database, args.dbuser, args.dbpass, "clinical_findings", "WHERE findingCode IS NOT NULL")])
    all_preclinical_mapped_findings = set([mapper.getKey(f) for f in getAllFindings(args.host, args.database, args.dbuser, args.dbpass, "preclinical_findings", "WHERE findingCode IS NOT NULL AND mapped IS true")])
    all_preclinical_non_mapped_findings = set([mapper.getKey(f) for f in getAllFindings(args.host, args.database, args.dbuser, args.dbpass, "preclinical_findings", "WHERE findingCode IS NOT NULL AND mapped IS false")])
    all_clinical_mapped_findings = set([mapper.getKey(f) for f in getAllFindings(args.host, args.database, args.dbuser, args.dbpass, "clinical_findings", "WHERE findingCode IS NOT NULL AND mapped IS true")])

    print(f'{len(all_preclinical_findings)} all_preclinical_findings')
    print(f'{len(all_preclinical_mapped_findings)} all_preclinical_mapped_findings')
    print(f'{len(all_preclinical_non_mapped_findings)} all_preclinical_non_mapped_findings')
    print(f'{len(all_clinical_findings)} all_clinical_findings')
    print(f'{len(all_clinical_mapped_findings)} all_clinical_mapped_findings')

    # count per drug the animal observations that have or don't have a corresponding clinical observation
    cnt = 0
    finding2socs = {}
    for inchiKey in drugs:
        cnt += 1
        if cnt < 2:
            continue

        clinical_codes = set()
        preclinical_codes = set()
        print(f'drug:{drugs[inchiKey]["clinicalName"]}')

        # collect list of preclinical findings
        for database in PreclinicalDatabases:

            findings = [f['FINDING'] for f in getAllFindingByIds(api, PreclinicalDatabases[database], drugs[inchiKey][database])]
            socs = api.SemanticService().getSoc(findings)

            for f in findings:
                key = mapper.getKey(f)
                preclinical_codes.add(key)
                if socs is not None:
                    for soc in socs:
                        if soc['conceptCode'] == f['specimenOrganCode']:
                            for mapping in soc['mapping']:
                                if mapping['conceptName'] not in groups:
                                    groups[mapping['conceptName']] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
                                if key not in finding2socs:
                                    finding2socs[key] = []
                                if mapping['conceptName'] not in finding2socs[key]:
                                    finding2socs[key].append(mapping['conceptName'])

        for database in ClinicalDatabases:
            if database in drugs[inchiKey] and drugs[inchiKey][database] is not None:
                findings = [f['FINDING'] for f in getAllFindingByIds(api, ClinicalDatabases[database], drugs[inchiKey][database])]
                for f in findings:
                    key = mapper.getKey(f)
                    if key == '10046555/19787009,89837001':
                        print('found')
                    clinical_codes.add(key)
                socs = api.SemanticService().getSoc(findings)
                if socs is None:
                    print('failed to retrieve socs')
                    for soc in socs:
                        if soc['conceptCode'] == f['specimenOrganCode']:
                            for mapping in soc['mapping']:
                                if mapping['conceptName'] not in groups:
                                    groups[mapping['conceptName']] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
                                if key not in finding2socs:
                                    finding2socs[key] = []
                                if mapping['conceptName'] not in finding2socs[key]:
                                    finding2socs[key].append(mapping['conceptName'])

        # if preclinical code is mapped to a clinical we are dealing with a true positive.
        # if not, we deal with a false positive
        for preclinical_code in preclinical_codes:
            if preclinical_code not in finding2socs:
                finding2socs[preclinical_code] = ['other']
                print(f'added preclinical code {preclinical_code} to SOC "other"')

        for preclinical_code in preclinical_codes:
            if preclinical_code in all_preclinical_mapped_findings:
                if preclinical_code in finding2socs:
                    for socName in finding2socs[preclinical_code]:
                        groups[socName]['tp'] += 1
            else:
                if preclinical_code in finding2socs:
                    for socName in finding2socs[preclinical_code]:
                        groups[socName]['fp'] += 1

        # if a clinical code is not mapped to a preclinical we deal with a false negative
        for clinical_code in clinical_codes:
            if clinical_code not in all_clinical_mapped_findings:
                for socName in finding2socs[clinical_code]:
                    groups[socName]['fn'] += 1

        # if a preclinical code is not mapped and not part of the drug preclinical findings
        for preclinical_code in all_preclinical_non_mapped_findings:
            if preclinical_code not in preclinical_codes:
                for socName in finding2socs[preclinical_code]:
                    groups[socName]['tn'] += 1

        break

    for key in groups:
        print(f"{key},TP:{groups[key]['tp']},FP:{groups[key]['fp']},FN:{groups[key]['fn']},TN:{groups[key]['tn']}")
        
    print(f'total_count:{total_count}, total_match:{total_match}')


if __name__ == "__main__":
    main()

