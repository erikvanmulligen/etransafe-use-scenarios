"""
    Program to retrieve all findings that are linked to the set of drugs that have been found
    in preclinical and clinical databases
"""
import argparse
from knowledgehub.api import KnowledgeHubAPI
import sys
import mysql.connector
from dateutil import parser
from Concordance.condordance_utils import getDrugs, getFindingsByIds


def main():
    argParser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    argParser.add_argument('-username', required=True, help='username')
    argParser.add_argument('-password', required=True, help='password')
    argParser.add_argument('-db_username', required=True, help='database username')
    argParser.add_argument('-db_password', required=True, help='database password')
    argParser.add_argument('-db_db', required=True, help='database name')
    argParser.add_argument('-db_server', required=True, help='database server')
    argParser.add_argument('-drugs', required=True, help='filename containing drugs')
    argParser.add_argument('-clear', required=False, action='store_true', help='clear database')
    args = argParser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    db = mysql.connector.connect(host=args.db_server, database=args.db_db, user=args.db_username, password=args.db_password)

    if args.clear:
        cursor = db.cursor(prepared=True)
        cursor.execute("DELETE FROM preclinical_findings")
        cursor.execute("DELETE FROM clinical_findings")
        db.commit()

    clinicalDatabases = {'ClinicalTrials': api.ClinicalTrials(), 'Medline': api.Medline(), 'Faers': api.Faers(), 'DailyMed': api.DailyMed()}
    preclinicalDatabases = {'eToxSys': api.eToxSys()}

    drugs = getDrugs(api, args.drugs)
    # preclinical_ids = []
    # clinical_ids = []
    for i in drugs:
        drug = drugs[i]
        print(f'processing {drug["clinicalName"]}...')
        preclinical_findings = []
        clinical_findings = []

        for database in preclinicalDatabases:
            preclinical_findings = getFindingsByIds(api, preclinicalDatabases[database], drug[database])
            # preclinical_ids += [f['id'] for f in preclinical_findings]
        storeFindings(db, "preclinical_findings", preclinical_findings)

        for database in clinicalDatabases:
            if database in drug and drug[database] is not None:
                clinical_findings = getFindingsByIds(api, clinicalDatabases[database], drug[database])
                # clinical_ids += [f['id'] for f in clinical_findings]
        storeFindings(db, "clinical_findings", clinical_findings)


def storeFindings(db, table, findings):
    cursor = db.cursor(prepared=True)
    sql = "INSERT INTO " + table + " (id, findingIdentifier, specimenOrgan, specimenOrganCode, specimenOrganVocabulary, finding, " \
          "findingCode, findingVocabulary, findingType, severity, observation, frequency, dose, doseUnit, timepoint, timepointUnit, " \
          "treatmentRelated, compoundId, studyId, createdDate, modifiedDate, sex) " \
          "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    records = []
    for finding in findings:
        records.append((finding['id'], finding['findingIdentifier'], finding['specimenOrgan'], finding['specimenOrganCode'],
                        finding['specimenOrganVocabulary'], finding['finding'], finding['findingCode'], finding['findingVocabulary'],
                        finding['findingType'], finding['severity'], finding['observation'], finding['frequency'], finding['dose'], finding['doseUnit'],
                        finding['timepoint'], finding['timepointUnit'], finding['treatmentRelated'], finding['compoundId'], finding['studyId'],
                        convertTimestamp(finding['createdDate']), convertTimestamp(finding['modifiedDate']), finding['sex']))
    try:
        cursor.executemany(sql, records)
        db.commit()
    except mysql.connector.errors.InterfaceError as e:
        print(f'{e}')


def convertTimestamp(timestampStr):
    return parser.isoparse(timestampStr)


if __name__ == "__main__":
    main()
