"""
This program updates the database with preclinical findings (from eToxSys) with a flag that
indicates whether a preclinical finding can be mapped to a clinical finding

(C) 2021 - 2022 Erasmus Medical Center Rotterdam, The Netherlands
"""

import argparse
from knowledgehub.api import KnowledgeHubAPI
import sys
import mysql.connector
from Concordance import condordance_utils
from Concordance.mapper import Mapper
from joblib import Parallel, delayed, parallel_backend


def main():
    argParser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    argParser.add_argument('-username', required=True, help='username')
    argParser.add_argument('-password', required=True, help='password')
    argParser.add_argument('-clear', required=False, action='store_true', help='clear database')
    args = argParser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print(f'{args.username} logged in')
    else:
        sys.exit(0)

    mapper = Mapper(api)
    config = {
        "host": "localhost",
        "database": "concordance",
        "user": "root",
        "password": "crosby9",
        "autocommit": False
    }

    db = mysql.connector.connect(pool_name="mypool", pool_size=16, **config)
    cursor = db.cursor()

    if args.clear:
        cursor.execute("UPDATE preclinical_findings SET mapped = NULL")
        cursor.execute("UPDATE clinical_findings SET mapped = NULL")
        db.commit()

    cursor.execute("SELECT DISTINCT findingCode, specimenOrganCode FROM preclinical_findings WHERE mapped IS NULL")
    normalizePreclinicalFields = condordance_utils.normalizePreclinicalFields(cursor.fetchall())

    total = len(normalizePreclinicalFields)
    cnt = 0

    # cursor1 = db.cursor()
    # cursor2 = db.cursor()
    for normalizePreclinicalField in normalizePreclinicalFields:
        cnt += 1
        # p_data = []
        # c_data = []

        print(f'{cnt} processed of {total}')

        preclinical_code = mapper.getKey(normalizePreclinicalField)
        mapped_clinical_findings = mapper.mapToClinical([normalizePreclinicalField])

        present = len(mapped_clinical_findings[preclinical_code])

        sql = ""
        if normalizePreclinicalField['code'] is not None and len(normalizePreclinicalField['code']) > 0:
            if normalizePreclinicalField['organCode'] is not None:
                # p_data.append((1 if present else 0, normalizePreclinicalField['code'], normalizePreclinicalField['organCode']))
                sql = "UPDATE preclinical_findings SET mapped = " + ("True" if present else "False") + " WHERE findingCode = '" + normalizePreclinicalField['code'] + "' AND specimenOrganCode = '" + normalizePreclinicalField['organCode'] + "'"
                cursor.execute(sql)
            else:
                # p_data.append((1 if present else 0, normalizePreclinicalField['code'], 'NULL'))
                sql = "UPDATE preclinical_findings SET mapped = " + ("True" if present else "False") + " WHERE findingCode = '" + normalizePreclinicalField['code'] + "' AND specimenOrganCode = NULL"
                cursor.execute(sql)

        if present:
            # update the clinical findings table
            for finding in mapped_clinical_findings[preclinical_code]:
                try:
                    # c_data.append((1, finding['code']))
                    sql = "UPDATE clinical_findings SET mapped = True WHERE findingCode = '" + finding['code'] + "'"
                    cursor.execute(sql)
                except Exception as e:
                    print(f'clinical update error: {e}')

        # if len(p_data) > 0:
        #     cursor1.executemany("UPDATE preclinical_findings SET mapped=%d WHERE findingCode=%s AND specimenOrganCode=%s", p_data)
        # if len(c_data) > 0:
        #     cursor2.executemany("UPDATE clinical_findings SET mapped=%d WHERE findingCode=%s", c_data)
        db.commit()


if __name__ == "__main__":
    main()