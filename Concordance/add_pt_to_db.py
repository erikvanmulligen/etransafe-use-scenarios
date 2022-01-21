import argparse
import sys

import mysql.connector
from knowledgehub.api import KnowledgeHubAPI

from Concordance.condordance_utils import getPTDrugFindings, normalizePreclinicalFields
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
    parser.add_argument('-clear', required=False, action='store_true', help='clear database')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    mapper = Mapper(api)

    logged_in = api.login(args.username, args.password)
    if logged_in:
        print(f'logged in')
    else:
        print(f'not logged in')
        sys.exit(0)

    db = mysql.connector.connect(host=args.host, database=args.database, username=args.dbuser, password=args.dbpass)

    if args.clear:
        cursor = db.cursor(prepared=True)
        cursor.execute("DELETE FROM preclinical_meddra")
        cursor.execute("DELETE FROM clinical_meddra")
        db.commit()

    records = []

    # retrieve the preclinical records and map them to MedDRA
    maximum = 0
    cursor = db.cursor(prepared=True)
    cursor.execute('SELECT distinct id, findingCode, specimenOrganCode FROM preclinical_findings WHERE mapped > -1')
    for r in cursor.fetchall():
        mapped_clinical_findings = mapper.mapToClinical([{'findingCode': r[1], 'specimenOrganCode': r[2]}])
        preclinical_code = mapper.getKey({'findingCode': r[1], 'specimenOrganCode': r[2]})

        # find the mapping(s) with the minimal absolute distance
        values = [item['distance'] for item in mapped_clinical_findings[preclinical_code]]
        if len(values) > 0:
            minimum = min(values)
            min_values = [item for item in mapped_clinical_findings[preclinical_code] if item['distance'] == minimum]
            if len(min_values) > maximum:
                maximum = len(min_values)
            for min_value in min_values:
                records.append((r[0], r[1], r[2], min_value['findingCode'], min_value['name'], min_value['distance']))

    # store the mappings
    try:
        cursor = db.cursor(prepared=True)
        cursor.executemany('INSERT INTO preclinical_meddra (id, findingCode, specimenOrganCode, PTCode, name, distance) VALUES (%s, %s, %s, %s, %s, %s)', records)
        db.commit()
    except mysql.connector.errors.InterfaceError as e:
        print(e)

    # retrieve the clinical records and store them in the database
    try:
        cursor = db.cursor(prepared=True)
        cursor2 = db.cursor(prepared=True)
        cursor.execute('SELECT distinct id, findingCode, specimenOrganCode, findingCode, finding, mapped FROM clinical_findings WHERE mapped > -1')
        cursor2.executemany('INSERT INTO clinical_meddra (id, findingCode, specimenOrganCode, PTCode, name, distance) VALUES (%s, %s, %s, %s, %s, %s)', cursor.fetchall())
        db.commit()
    except mysql.connector.errors.InterfaceError as e:
        print(e)


if __name__ == "__main__":
    main()
