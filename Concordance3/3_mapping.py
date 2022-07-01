
#
# This program maps a preclinical code to a clinical code. It favours mappings to clinical codes used in the database.
# Only mapped codes are stored in the mapping
# (C) 2022, Erasmus University Medical Center Rotterdam, the Netherlands
#

import sys

from knowledgehub.api import KnowledgeHubAPI
from settings import settings
import mysql.connector
from Concordance.condordance_utils import getClinicalDatabases, getPreclinicalDatabases, intersection

def main():
    api = KnowledgeHubAPI(server=settings['kh']['server'], client_secret=settings['kh']['client_secret'])

    status = api.login(settings['kh']['user'], settings['kh']['password'])
    if not status:
        print('not successfully logged in')
        sys.exit(1)

    clinical_pas = getClinicalDatabases(api)
    preclinical_pas = getPreclinicalDatabases(api)
    pas = {**clinical_pas, **preclinical_pas}

    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'], username=settings['db']['user'], password=settings['db']['password'])

    cursor = db.cursor(prepared=True)
    cursor.execute('delete from mappings')
    db.commit()

    # response = api.SemanticService().mapToClinical('MC:0000126', 'MA:0000145')
    # print(response)
    # sys.exit(0)

    all_clinical_findings = getAllFindingCodes(db, list(clinical_pas.keys()))
    all_clinical_codes = [record['findingCode'] for record in all_clinical_findings]
    for preclinical_finding in getAllFindingCodes(db, preclinical_pas.keys()):
        mappings = api.SemanticService().mapToClinical(preclinical_finding['findingCode'], preclinical_finding['specimenOrganCode'])
        if mappings is not None and len(mappings) > 0:
            distanceMappings = organizePerDistance(mappings)
            distance, clinical_concepts = getMinimumDistance(preclinical_finding, distanceMappings, all_clinical_codes)
            if distance is not None and clinical_concepts is not None:
                storeMappings(db, preclinical_finding['findingCode'], preclinical_finding['specimenOrganCode'], clinical_concepts, distance)


def storeMappings(db, preclinical_code, preclinical_specimen_organ_code, clinical_codes, distance):
    cursor = db.cursor(prepared=True)
    sql = "insert into mappings (preclinicalFindingCode, preclinicalSpecimenOrganCode, clinicalFindingCode, minDistance) values(?, ?, ?, ?)"
    try:
        cursor.executemany(sql, [(preclinical_code, preclinical_specimen_organ_code, clinical_code, distance) for clinical_code in clinical_codes])
        db.commit()
    except mysql.connector.errors.InterfaceError as e:
        print(f'{e}')

def getMinimumDistance(preclinical_finding, distanceMappings, matching_codes):
    distances = list(distanceMappings.keys())
    positives = [x for x in distances if x >= 0]
    positives.sort()
    negatives = [abs(x) for x in distances if x < 0]
    negatives.sort()
    try:
        max_value = max(max(positives, default=-1), max(negatives, default=-1))
        sorted = []
        for index in range(0, max_value + 1):
            if index in positives:
                sorted.append(index)
            if index in negatives:
                sorted.append(-index)

        for index in sorted:
            distanceCodes = [mapping['conceptCode'] for mapping in distanceMappings[index]]
            mapping_codes = intersection(distanceCodes, matching_codes)
            if len(mapping_codes) > 0:
                return index, mapping_codes
            # else:
            #     print(f'no mapping found for {preclinical_finding["finding"]}/{preclinical_finding["specimenOrgan"]}-{preclinical_finding["findingCode"]}/{preclinical_finding["specimenOrganCode"]}')
    except ValueError as e:
        print(e)

    return None, None


def organizePerDistance(mappings):
    result = {}
    for mapping in mappings:
        if mapping['distance'] not in result:
            result[mapping['distance']] = []
        for concept in mapping['concepts']:
            result[mapping['distance']].append(concept)
    return result

def getAllFindingCodes(db, databases):
    cursor = db.cursor(prepared=True)
    db_str = ','.join(['"{}"'.format(value) for value in databases])
    query = f'select distinct findingCode, specimenOrganCode, finding, specimenOrgan from findings where db in ({db_str})'
    cursor.execute(query)
    return [{'findingCode': record[0], 'specimenOrganCode': record[1], 'finding': record[2], 'specimenOrgan': record[3]} for record in cursor.fetchall()]

if __name__ == "__main__":
    main()