"""
This program maps the clinical codes to preclinical if not already existing in the mapping table
"""

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

    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS mappings (preclinicalFindingCode varchar(20) null, preclinicalSpecimenOrganCode varchar(20) null, clinicalFindingCode varchar(20) null, minDistance int null)')
    cursor.close()

    print('before getting all finding codes')
    all_clinical_findings = getAllFindingCodes(db, list(clinical_pas.keys()))
    print(f'after getting all finding codes: {len(all_clinical_findings)} findings')
    # for clinical_finding in all_clinical_findings:
    #     print(clinical_finding)
    all_clinical_codes = [record['findingCode'] for record in all_clinical_findings]
    print(f'after extracting all finding codes: {len(all_clinical_codes)} finding codes')
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
    print('begin collecting codes')
    cursor: object = db.cursor(prepared=True)
    db_str: str = ','.join(['"{}"'.format(value) for value in databases])
    query: str = f'select distinct findingCode, specimenOrganCode, finding, specimenOrgan from findings where db in ({db_str})'
    cursor.execute(query)
    result: list = []
    for record in cursor.fetchall():
        if record[1] is not None:
            specimenOrganCodes = record[1].split(',')
            if len(specimenOrganCodes) > 1:
                specimenOrgans = record[3].split(',')
            else:
                specimenOrgans = [record[3]]
        else:
            specimenOrgans = [None]
            specimenOrganCodes = [None]

        if len(specimenOrgans) == len(specimenOrganCodes):
            for i in range(0, len(specimenOrgans)):
                result.append({'findingCode': record[0], 'specimenOrganCode': specimenOrganCodes[i], 'finding': record[2], 'specimenOrgan': specimenOrgans[i]})
        else:
            print('different #codes and #organs')

        if len(result) % 100 == 0:
            print(f'{len(result)} records processed')

    return result

if __name__ == "__main__":
    main()