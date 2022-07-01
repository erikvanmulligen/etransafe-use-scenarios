
# This program retrieves the findings that are referenced by the drugs
# (C) 2022, Erasmus University Medical Center Rotterdam, the Netherlands

import sys

from knowledgehub.api import KnowledgeHubAPI
from settings import settings
import mysql.connector
from Concordance.condordance_utils import getClinicalDatabases, getPreclinicalDatabases

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
    cursor.execute('DELETE FROM findings')
    db.commit()

    databases = getAllDatabases(db)
    for database in databases:
        finding_inchis = getAllFindingInchisByDatabase(db, database)
        findings = pas[database].getAllFindingByIds(list(finding_inchis.keys()))
        for finding in findings:
            try:
                key = int(finding['FINDING']['id'])
                finding['FINDING']['inchi_key'] = finding_inchis[key]
            except KeyError as e:
                print(e)
        storeFindings(db, findings, database)


def storeFindings(db, findings, database):
    cursor = db.cursor(prepared=True)
    sql = "insert into findings (finding_id, db, specimenOrgan, specimenOrganCode, specimenOrganVocabulary, finding, " \
                                "findingCode, findingVocabulary, findingType, dose, doseUnit, treatmentRelated, inchi_key) " \
                                "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    records = []
    for finding in findings:
        if 'FINDING' in finding and finding['FINDING']['finding'] != 'No abnormalities detected' and finding['FINDING']['finding'] != 'Nothing abnormal detected' and finding['FINDING']['finding'] != 'Microscopic comment' and finding['FINDING']['finding'] != 'Not examined/not present':
            records.append((finding['FINDING']['findingIdentifier'], database,  finding['FINDING']['specimenOrgan'], finding['FINDING']['specimenOrganCode'],
                            finding['FINDING']['specimenOrganVocabulary'], finding['FINDING']['finding'], finding['FINDING']['findingCode'], finding['FINDING']['findingVocabulary'],
                            finding['FINDING']['findingType'], finding['FINDING']['dose'], finding['FINDING']['doseUnit'], finding['FINDING']['treatmentRelated'] is not False and finding['FINDING']['treatmentRelated'] is not None, finding['FINDING']['inchi_key']))
    try:
        cursor.executemany(sql, records)
        db.commit()
    except mysql.connector.errors.InterfaceError as e:
        print(f'{e}')

def getAllDatabases(db):
    cursor = db.cursor(prepared=True)
    cursor.execute('select distinct(db) from finding_ids');
    return [record[0] for record in cursor.fetchall()]

# retrieve all finding ids for a database
def getAllFindingInchisByDatabase(db, database):
    cursor = db.cursor(prepared=True)
    cursor.execute(f'select distinct finding_id, inchi_key from finding_ids where db = "{database}"');
    return {record[0]: record[1] for record in cursor.fetchall()}

if __name__ == "__main__":
    main()