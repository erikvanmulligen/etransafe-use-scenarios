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

    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'],
                                 username=settings['db']['user'], password=settings['db']['password'])

    # if table doesn't exist, create it
    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS findings ('
                   'finding_id              int          not null,' +
                   'db                      varchar(20)  null,' +
                   'specimenOrgan           mediumtext   null,' +
                   'specimenOrganCode       mediumtext   null,' +
                   'specimenOrganVocabulary mediumtext   null,' +
                   'finding                 mediumtext   null,' +
                   'findingCode             varchar(50)  null,' +
                   'findingVocabulary       mediumtext   null,' +
                   'dose                    float        null,' +
                   'doseUnit                mediumtext   null,' +
                   'treatmentRelated        tinyint(1)   null,' +
                   'findingType             mediumtext   null,' +
                   'inchi_key               varchar(150) null,' +
                   'study_id                int          not null'
                   ')'
                   )
    cursor.close()

    # remove any existing data
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


def isValidFinding(finding: object) -> bool:
    return 'FINDING' in finding and \
            finding['FINDING']['finding'] != 'No abnormalities detected' and \
            finding['FINDING']['finding'] != 'Nothing abnormal detected' and \
            finding['FINDING']['finding'] != 'Microscopic comment' and \
            finding['FINDING']['finding'] != 'Not examined/not present'


def storeFindings(db, findings, database):
    cursor = db.cursor(prepared=True)
    sql = "insert into findings (finding_id, db, specimenOrgan, specimenOrganCode, specimenOrganVocabulary, finding, " \
          "findingCode, findingVocabulary, findingType, dose, doseUnit, treatmentRelated, inchi_key, study_id) " \
          "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    records = []
    skipped = 0
    processed = 0

    for finding in findings:

        # the following condition checks whether we deal with a valid finding
        if isValidFinding(finding):
            # sometimes specimen organ (codes) contain a list. First split the code on comma and if more
            # than one has been found, also split the organs. Note that some specimen organs contain a comma.
            if finding['FINDING']['specimenOrganCode'] is not None and finding['FINDING']['specimenOrgan'] is not None:
                specimenOrganCodes = finding['FINDING']['specimenOrganCode'].split(',')
                specimenOrgans = finding['FINDING']['specimenOrgan'].split(',') if len(specimenOrganCodes) > 1 else [finding['FINDING']['specimenOrgan']]
            else:
                specimenOrgans = [None]
                specimenOrganCodes = [None]

            # check if the same number of codes and organs is found. This could be different if the organs contain
            # comma's within a single name. If so, we have to fix that. Note that we don't use the name of the
            # organ in further processing steps.
            if len(specimenOrganCodes) == len(specimenOrgans):

                # for all organs found insert a record in the database
                for i in range(0, len(specimenOrganCodes)):
                    records.append(
                            (finding['FINDING']['findingIdentifier'],
                             database,
                             specimenOrgans[i],
                             specimenOrganCodes[i],
                             finding['FINDING']['specimenOrganVocabulary'],
                             finding['FINDING']['finding'],
                             finding['FINDING']['findingCode'].replace('MC:MA:', 'MC:'),  # this fix is needed since there is an MC:MA:0000857 code from eToxSys
                             finding['FINDING']['findingVocabulary'],
                             finding['FINDING']['findingType'],
                             finding['FINDING']['dose'],
                             finding['FINDING']['doseUnit'],
                             finding['FINDING']['treatmentRelated'] is not False and
                             finding['FINDING']['treatmentRelated'] is not None,
                             finding['FINDING']['inchi_key'],
                             finding['FINDING']['studyId']))
                    processed += 1
            else:
                print('unequal number of organs and organ codes', file=sys.stderr)
                print(f'\tspecimenOrgans: {str(specimenOrgans)}', file=sys.stderr)
                print(f'\tspecimenOrganCodes: {str(specimenOrganCodes)}', file=sys.stderr)
        else:
            skipped += 1
    try:
        cursor.executemany(sql, records)
        db.commit()
    except mysql.connector.errors.InterfaceError as e:
        print(f'{e}')

    print(f'{database}: {processed} records processed, {skipped} records skipped')


def getAllDatabases(db):
    cursor = db.cursor(prepared=True)
    cursor.execute('select distinct(db) from finding_ids');
    return [record[0] for record in cursor.fetchall()]


# retrieve all finding ids for a database
def getAllFindingInchisByDatabase(db, database, max_records: int = None):
    cursor = db.cursor(prepared=True)
    sql = f'select distinct finding_id, inchi_group from finding_ids where db = "{database}"' + ('' if max_records is None else f' LIMIT {max_records}')
    cursor.execute(sql)
    return {record[0]: record[1] for record in cursor.fetchall()}


if __name__ == "__main__":
    main()
