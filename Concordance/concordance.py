'''
This is a module to test what data comes back from eToxSys
'''

from knowledgehub.api import KnowledgeHubAPI
import argparse
import json
import os
import requests
import knowledgehub.constants as constants
import ast
import sys
from mapper import Mapper
import numpy as np
import pandas as pd

from Concordance.condordance_utils import getAllPreclinicalFindings, normalizePreclinicalFields


def getInchiKey(api, smiles, pa_type):
    r = api.ChemistryService().paStandardize(smiles, pa_type)
    if r is None:
        return None
    else:
        return r[0]


def getAllFindingByIds(api, service, finding_ids):
    result = []

    if len(finding_ids) > 0:
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
                                            },
                                            # {
                                            #     "field": {
                                            #         "dataClassKey": "FINDING",
                                            #         "name": "dose"
                                            #     },
                                            #     "primitiveType": "String",
                                            #     "comparisonOperator": "NOT_EQUAL",
                                            #     "values": "0.0",
                                            # }
                                        ]
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
                                "frequency",
                                "severity",
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


# def getAllFindingsCount(service):
#     for tries in range(0, 5):
#         r = requests.get(service.endpoint + 'count', verify=False, params={'dataClassKey': 'FINDING'}, headers={"Authorization": f"Bearer {service.get_token()}"}, timeout=None)
#         if r.status_code == 200:
#             return int(r.text)
#         elif r.status_code == 401:
#             service.api.reconnect()
#         else:
#             print(f"Cannot retrieve findings from {service.endpoint}: {r.status_code}")
#     return None

def getAllFindings(self, maximum: int = None):
    result = []
    tries = 0
    query = {
            "offset": 0,
            "limit": 100,
            "selectedFields": [
                {
                    "dataClassKey": "FINDING",
                    "names": [
                        "finding",
                        "findingCode",
                        "specimenOrgan",
                        "specimenOrganCode",
                    ]
                }
            ]
        }
    if maximum is None:
        for tries in range(0, 5):
            r = requests.get(self.endpoint + 'count', verify=False, params={'dataClassKey': 'FINDING'}, headers={"Authorization": f"Bearer {self.get_token()}"}, timeout=None)
            if r.status_code == 200:
                maximum = int(r.text)
            elif r.status_code == 401:
                self.api.reconnect()
            else:
                print(f"Cannot retrieve findings from {self.endpoint}: {r.status_code}")

    if maximum is not None:
        query = {

        }
        size = min(maximum, 1000)
        for offset in range(0, maximum, size):
            for tries in range(0, 5):
                print(f'retrieving records {offset}-{offset+size}...')
                r = requests.get(self.endpoint + 'data', params={'dataClassKey': 'FINDING', 'limit': size, 'offset': offset}, verify=False, headers={"Authorization": f"Bearer {self.get_token()}"})
                if r.status_code == 200:
                    for finding in json.loads(r.text):
                        result.append(finding)
                elif r.status_code == 401:
                    self.api.reconnect()
                else:
                    print(f"Cannot retrieve findings from {self.endpoint}: {r.status_code}")
                break

    return result


def getDrugsMapping(api):
    result = {}
    clinicalCompounds = getClinicalCompounds(api)

    # compute missing inchiKeys
    # c = 0
    # for clinicalCompound in clinicalCompounds:
    #     if c % 100 == 0:
    #         print(f'{c} of {len(clinicalCompounds)} clinical compounds processed')
    #     c += 1
    #     if clinicalCompound['inchiKey'] is None or len(clinicalCompound['inchiKey'].strip()) == 0:
    #         clinicalCompound['inchiKey'] = getInchikey(api, clinicalCompound['name'], 'clinical')

    c = 0
    preclinicalCompounds = getPreclinicalCompounds(api)
    # for preclinicalCompound in preclinicalCompounds:
    #     if c % 100 == 0:
    #         print(f'{c} of {len(preclinicalCompounds)} preclinical compounds processed')
    #     c += 1
    #     if preclinicalCompound['inchiKey'] is None or len(preclinicalCompound['inchiKey'].strip()) == 0:
    #         preclinicalCompound['inchiKey'] = getInchikey(api, preclinicalCompound['smiles'], 'preclinical')

    # iterate over the clinical and preclinical compounds and match them om inchiKey
    for clinicalCompound in clinicalCompounds:
        for preclinicalCompound in preclinicalCompounds:
            if (clinicalCompound['inchiKey'] is not None) and (clinicalCompound['inchiKey'] == preclinicalCompound['inchiKey']):
                inchiKey = clinicalCompound['inchiKey']
                if inchiKey not in result:
                    result[inchiKey] = {
                        'inchiKey': inchiKey,
                        'clinicalName': clinicalCompound['name'],
                        'preclinicalName': preclinicalCompound['name']
                    }
                    result[inchiKey][preclinicalCompound['source']] = preclinicalCompound['findingIds']
                result[inchiKey][clinicalCompound['source']] = clinicalCompound['findingIds']
    return result


def getClinicalCompounds(api):
    ct_compounds = api.ClinicalTrials().getAllCompounds();
    for ct_compound in ct_compounds:
        ct_compound['source'] = 'ClinicalTrials'
    ml_compounds = api.Medline().getAllCompounds();
    for ml_compound in ml_compounds:
        ml_compound['source'] = 'Medline'
    fa_compounds = api.Faers().getAllCompounds();
    for fa_compound in fa_compounds:
        fa_compound['source'] = 'Faers'
    dm_compounds = api.DailyMed().getAllCompounds();
    for dm_compound in dm_compounds:
        dm_compound['source'] = 'DailyMed'

    return ct_compounds + ml_compounds + fa_compounds + dm_compounds


def getPreclinicalCompounds(api):
    et_compounds = api.eToxSys().getAllCompounds()
    for et_compound in et_compounds:
        et_compound['source'] = 'eToxSys'
    return et_compounds


def getClinicalFindings(api, service, findingIds):
    findings = getAllFindingByIds(api, service, findingIds) if findingIds is not None else []
    cl_findings = [{
                    'code': finding['FINDING']['findingCode'],
                    'name': finding['FINDING']['finding'],
                    } for finding in findings]
    return [ast.literal_eval(el1) for el1 in set([str(el2) for el2 in cl_findings])]


def getPreclinicalFindings(api, service, findingIds):
    findings = getAllFindingByIds(api, service, findingIds) if findingIds is not None else []
    pc_findings = [{
                    'code': finding['FINDING']['findingCode'],
                    'name': finding['FINDING']['finding'],
                    'organ': finding['FINDING']['specimenOrgan'],
                    'organCode': finding['FINDING']['specimenOrganCode'] if 'specimenOrganCode' in finding['FINDING'] else None
                    } for finding in findings if finding['FINDING']['findingCode'] is not None and finding['FINDING']['findingCode'] != 'MC:2000001' and finding['FINDING']['dose'] > 0.0 and finding['FINDING']['treatmentRelated'] == 1]
    return [ast.literal_eval(el1) for el1 in set([str(el2) for el2 in pc_findings])]


def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3


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

    #api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    mapper = Mapper(api)

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
    print('searching for findings in eToxSys', flush=True)

    tp = 0
    fp = 0
    fn = 0
    tn = 0
    clinical_code_not_mapped = 0

    # first find all preclinical findings
    all_preclinical_findings = normalizePreclinicalFields(getAllPreclinicalFindings(args.host, args.database, args.dbuser, args.dbpass))
    # reduce this list to those that have a clinical counterpart
    all_preclinical_clinical_findings = []
    for all_preclinical_finding in all_preclinical_findings:
        mapped_preclinical_finding = mapper.mapToClinical([all_preclinical_finding])
        print(mapped_preclinical_finding)
        code = mapper.getKey(all_preclinical_finding)
        if len(mapped_preclinical_finding[code]) > 0:
            all_preclinical_clinical_findings.append(all_preclinical_finding)

    print(f'{len(all_preclinical_clinical_findings)} all_preclinical_clinical_findings')
    sys.exit(0)
    findings = normalizePreclinicalFields(getAllPreclinicalFindings(args.host, args.database, args.dbuser, args.dbpass))
    # make a unique list of codes
    all_preclinical_codes = [mapper.getKey(f) for f in findings]

    # count per drug the animal observations that have or don't have a corresponding clinical observation
    cnt = 0
    for inchiKey in drugs:
        cnt += 1
        if cnt < 2:
            continue

        clinical_codes = []
        preclinical_codes = []
        print(f'drug:{drugs[inchiKey]["clinicalName"]}')

        # collect list of clinical findings
        for database in PreclinicalDatabases:
            print(f'pc database:{database}')
            preclinical_findings = getPreclinicalFindings(api, PreclinicalDatabases[database], drugs[inchiKey][database])
            preclinical_codes += [mapper.getKey(m) for m in preclinical_findings]

        for database in ClinicalDatabases:
            if database in drugs[inchiKey]:
                clinical_findings = getClinicalFindings(api, ClinicalDatabases[database], drugs[inchiKey][database])
                clinical_codes += [mapper.getKey(m) for m in clinical_findings]

        array = [False] * len(preclinical_codes)*len(clinical_codes)
        mapping_preclinical_clinical = np.array(array, dtype=bool).reshape((len(preclinical_codes), len(clinical_codes)))
        preclinicalxClinical = pd.DataFrame(mapping_preclinical_clinical, index=preclinical_codes, columns=clinical_codes)

        # mark in the matrix which correspondences have been found in the data
        mapped_clinical_findings = mapper.mapToClinical(preclinical_findings)
        for preclinical_finding in preclinical_findings:
            preclinical_code = mapper.getKey(preclinical_finding)
            if preclinical_code in mapped_clinical_findings:
                for clinical_finding in mapped_clinical_findings[preclinical_code]:
                    clinical_code = mapper.getKey(clinical_finding)
                    if clinical_code in clinical_codes:
                        preclinicalxClinical.at[preclinical_code, clinical_code] = True

        for preclinical_code in preclinical_codes:
            value = False
            for clinical_code in clinical_codes:
                value = preclinicalxClinical.at[preclinical_code, clinical_code]
                if value:
                    break
            if value:
                tp += 1
            else:
                fp += 1

        # compute the false negatives as checking for which clinical codes there is no
        # preclinical code found at all.
        # Note: the assumption is that the mapping from clinical -> preclinical doesn't add
        # much to the mapping from preclinical -> clinical
        for clinical_code in clinical_codes:
            value = False
            for preclinical_code in preclinical_codes:
                value = preclinicalxClinical.at[preclinical_code, clinical_code]
                if value:
                    break
            if not value:
                fn += 1
            else:
                clinical_code_not_mapped += 1

        # take as an estimate for the true negatives those clinical findings for this drug that were not mapped
        # retrieve all findings found in eToxSys and subtract the findings used for this drug

        # first find the animal observations that are not found for this drug
        no_animal_observations = mapper.codesToFindings([code for code in all_preclinical_codes if code not in preclinical_codes])
        print(f'{len(no_animal_observations)} absent animal observations')

        no_animal_clinical_observations = []
        for no_animal_observation in no_animal_observations:
            mapped_clinical_observations = mapper.mapToClinical([no_animal_observation])
            code = mapper.getKey(no_animal_observation)
            if len(mapped_clinical_observations[code]) > 0:
                no_animal_clinical_observations.append(no_animal_observation)

        # check if mapped_clinical_observations are not part of the
        no_animal_clinical_codes = [mapper.getKey(m) for m in no_animal_clinical_observations]
        tn_codes = [m for m in no_animal_clinical_codes if m not in clinical_codes]
        tn += len(tn_codes)

        break

    print(f'TP:{tp},FP:{fp},FN:{fn},TN:{tn}')
        
    print(f'total_count:{total_count}, total_match:{total_match}')


def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))


def isPresent(findings, finding):
    for f in findings:
        if f['findingCode'] == finding['findingCode'] and f['specimenOrganCode'] == finding['specimenOrganCode']:
            return True
    return False


def filterStudies(studies):
    return [study for study in studies if study['FINDING']['findingVocabulary'] is not None and study['FINDING']['findingCode'] is not None and study['FINDING']['findingCode'] != 'MC:2000001' and study['FINDING']['dose'] != 0.0]


def dedup(list):
    result = []
    for obj in list:
        if obj['id'] not in result:
            try:
                result[obj['id']] = obj
            except Exception as e:
                print("OS error: {0}".format(e))
    return result


if __name__ == "__main__":
    main()

