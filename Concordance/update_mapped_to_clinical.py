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
from tests.mapper import Mapper


def main():
    argParser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    argParser.add_argument('-username', required=True, help='username')
    argParser.add_argument('-password', required=True, help='password')
    args = argParser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print(f'{args.username} logged in')
    else:
        sys.exit(0)

    mapper = Mapper(api)
    db = mysql.connector.connect(host='localhost', database='eToxSys', user='root', password='crosby9')
    cursor = db.cursor()
    cursor.execute("SELECT findingCode, specimenOrganCode FROM unique_findings")
    normalizePreclinicalFields = condordance_utils.normalizePreclinicalFields(cursor.fetchall())
    for normalizePreclinicalField in normalizePreclinicalFields:
        preclinical_code = mapper.getKey(normalizePreclinicalField)
        mapped_clinical_findings = mapper.mapToClinical([normalizePreclinicalField])
        if len(mapped_clinical_findings[preclinical_code]):
            if normalizePreclinicalField['code'] is not None:
                try:
                    sql = "UPDATE customers SET mappedToClinical = True WHERE findingCode = '" + normalizePreclinicalField['code'] + "' AND specimenOrganCode = '" + normalizePreclinicalField['organCode'] + "'"
                    cursor.execute(sql)
                except:
                    print('error')
            else:
                print(f'found {normalizePreclinicalField["code"]}')
    db.commit()


if __name__ == "__main__":
    main()