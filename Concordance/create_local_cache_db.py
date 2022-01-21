"""
    Program to retrieve all findings that are linked to the set of drugs that have been found
    in preclinical and clinical databases

    The idea is that only findings are included that are treatment related
"""
import argparse
from knowledgehub.api import KnowledgeHubAPI
import sys
import mysql.connector
from dateutil import parser

from Concordance import condordance_utils
from Concordance.condordance_utils import getDrugs, getSoc, getPreclinicalDatabases, getClinicalDatabases
from Concordance.mapper import Mapper


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

    print('populate database')
    drugs = getDrugs(api, args.drugs)
    for i in drugs:
        drug = drugs[i]
        print(f'processing {drug["clinicalName"]}...')
        preclinical_findings = []
        clinical_findings = []

        preclinicalDatabases = getPreclinicalDatabases(api)
        clinicalDatabases = getClinicalDatabases(api)

        for database in preclinicalDatabases:
            print('with findings from...' + database)
            preclinical_findings = preclinicalDatabases[database].getAllFindingByIds(drug[database])
            storeFindings(db, table="preclinical_findings", findings=preclinical_findings, treatmentRelated=True)

        for database in clinicalDatabases:
            print('with findings from...' + database)
            if database in drug and drug[database] is not None:
                clinical_findings = clinicalDatabases[database].getAllFindingByIds(drug[database])
                storeFindings(db, table="clinical_findings", findings=clinical_findings, treatmentRelated=False)

    print('find SOCS for clinical findings unknown SOCs to the database')
    cursor = db.cursor()
    cursor.execute('SELECT distinct findingCode FROM clinical_findings WHERE SOC IS NULL')
    findings = [f[0] for f in cursor.fetchall()]

    for offset in range(0, len(findings), 1000):
        values = []
        socs = api.SemanticService().getSocByCode(findings[offset:offset + 1000])
        for finding in findings[offset:offset + 1000]:
            socName = getSoc(socs, finding)
            if socName is not None:
                values.append((socName, finding))

        try:
            cursor = db.cursor(prepared=True)
            cursor.executemany('UPDATE clinical_findings SET SOC = %s WHERE findingCode = %s', values)
            db.commit()
        except mysql.connector.errors.InterfaceError as e:
            print(e)

        print(f'{offset} of {len(findings)} processed....')

    print('find SOCS for preclinical finding unknown SOCs to the database')
    cursor = db.cursor()
    cursor.execute('SELECT distinct specimenOrganCode FROM preclinical_findings WHERE SOC IS NULL')
    organs = [f[0] for f in cursor.fetchall()]

    for offset in range(0, len(organs), 1000):
        values = []
        socs = api.SemanticService().getSocByCode(organs[offset:offset + 1000])
        for organ in organs[offset:offset + 1000]:
            socName = getSoc(socs, organ)
            if socName is not None:
                values.append((socName, organ))

        try:
            cursor = db.cursor(prepared=True)
            cursor.executemany('UPDATE preclinical_findings SET SOC = %s WHERE specimenOrganCode = %s', values)
            db.commit()
        except mysql.connector.errors.InterfaceError as e:
            print(e)

        print(f'{offset} of {len(organs)} processed....')

    print('creating mappings from preclinical -> clinical')

    mapper = Mapper(api)
    cursor = db.cursor()

    cursor.execute("SELECT DISTINCT findingCode, specimenOrganCode FROM preclinical_findings WHERE mapped = -1")
    normalizePreclinicalFields = condordance_utils.normalizePreclinicalFields(cursor.fetchall())

    total = len(normalizePreclinicalFields)
    cnt = 0

    for normalizePreclinicalField in normalizePreclinicalFields:
        cnt += 1

        print(f'{cnt} processed of {total}')

        preclinical_code = mapper.getKey(normalizePreclinicalField)
        mapped_clinical_findings = mapper.mapToClinical([normalizePreclinicalField])

        present = len(mapped_clinical_findings[preclinical_code])
        values = [item['distance'] for item in mapped_clinical_findings[preclinical_code]]
        value = min(values) if len(values) > 0 else -1

        if normalizePreclinicalField['findingCode'] is not None and len(normalizePreclinicalField['findingCode']) > 0:
            if normalizePreclinicalField['specimenOrganCode'] is not None:
                sql = "UPDATE preclinical_findings SET mapped = " + str(value) + " WHERE findingCode = '" + normalizePreclinicalField['findingCode'] + "' AND specimenOrganCode = '" + normalizePreclinicalField['specimenOrganCode'] + "'"
                cursor.execute(sql)
            else:
                sql = "UPDATE preclinical_findings SET mapped = " + str(value) + " WHERE findingCode = '" + normalizePreclinicalField['findingCode'] + "' AND specimenOrganCode = NULL"
                cursor.execute(sql)

        if present:
            # update the clinical findings table
            for finding in mapped_clinical_findings[preclinical_code]:
                try:
                    sql = "UPDATE clinical_findings SET mapped = " + str(value) + " WHERE findingCode = '" + finding['findingCode'] + "'"
                    cursor.execute(sql)
                except Exception as e:
                    print(f'clinical update error: {e}')

        db.commit()


def storeFindings(db, table, findings, treatmentRelated):
    cursor = db.cursor(prepared=True)
    sql = "INSERT INTO " + table + " (id, findingIdentifier, specimenOrgan, specimenOrganCode, specimenOrganVocabulary, finding, " \
                                   "findingCode, findingVocabulary, findingType, severity, observation, frequency, dose, doseUnit, timepoint, timepointUnit, " \
                                   "treatmentRelated, compoundId, studyId, createdDate, modifiedDate, sex) " \
                                   "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    records = []
    for finding in findings:
        finding = finding['FINDING']
        if 'finding' in finding and finding['finding'] != 'No abnormalities detected' and finding['finding'] != 'Nothing abnormal detected' and \
                finding['finding'] != 'Microscopic comment' and finding['finding'] != 'Not examined/not present':
            if finding['dose'] != 0:
            #if finding['dose'] != 0 and (treatmentRelated is False or (finding['treatmentRelated'] is not False and finding['treatmentRelated'] is not None)):
                records.append((finding['id'], finding['findingIdentifier'], finding['specimenOrgan'], finding['specimenOrganCode'],
                                finding['specimenOrganVocabulary'], finding['finding'], finding['findingCode'], finding['findingVocabulary'],
                                finding['findingType'], finding['severity'], finding['observation'], finding['frequency'], finding['dose'], finding['doseUnit'],
                                finding['timepoint'], finding['timepointUnit'], finding['treatmentRelated'] is not False and finding['treatmentRelated'] is not None, finding['compoundId'], finding['studyId'],
                                convertTimestamp(finding['createdDate']), convertTimestamp(finding['modifiedDate']), finding['sex']))
            else:
                print(f'skip control group {finding["dose"]} or non treatment related finding {finding["treatmentRelated"]}')

    try:
        cursor.executemany(sql, records)
        db.commit()
    except mysql.connector.errors.InterfaceError as e:
        print(f'{e}')




def convertTimestamp(timestampStr):
    return parser.isoparse(timestampStr)


if __name__ == "__main__":
    main()
