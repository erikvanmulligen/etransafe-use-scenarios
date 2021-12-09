import argparse

from knowledgehub.api import KnowledgeHubAPI
import sys
import mysql.connector
from dateutil import parser
import requests
import json


def main():
    argparser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    argparser.add_argument('-username', required=True, help='username')
    argparser.add_argument('-password', required=True, help='password')
    argparser.add_argument('-clear', required=False, action='store_true', help='clear database')
    args = argparser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    db = mysql.connector.connect(host='localhost', database='eToxSys', user='root', password='crosby9')

    if args.clear:
        cursor = db.cursor(prepared=True)
        cursor.execute("DELETE FROM findings")
        db.commit()

    storeAllFindings(db, api, api.eToxSys(), 0  )


def storeAllFindings(db, api, service, offset=0):
    for tries in range(0, 5):
        r = requests.get(service.endpoint + 'count', verify=False, params={'dataClassKey': 'FINDING'}, headers={"Authorization": f"Bearer {api.get_token()}"}, timeout=None)
        if r.status_code == 200:
            maximum = int(r.text)
        elif r.status_code == 401:
            api.reconnect()
        else:
            print(f"Cannot retrieve findings from {service.endpoint}: {r.status_code}")

    if maximum is not None:
        sql = "INSERT INTO findings (id, findingIdentifier, specimenOrgan, specimenOrganCode, specimenOrganVocabulary, finding, " \
              "findingCode, findingVocabulary, findingType, severity, observation, frequency, dose, doseUnit, timepoint, timepointUnit, " \
              "treatmentRelated, compoundId, studyId, createdDate, modifiedDate, sex) " \
              "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        size = 5000
        for offset in range(offset, maximum, size):
            for tries in range(0, 5):
                print(f'retrieving records {offset}-{offset+size} of {maximum}...')
                r = requests.get(service.endpoint + 'data', params={'dataClassKey': 'FINDING', 'limit': size, 'offset': offset}, verify=False, headers={"Authorization": f"Bearer {service.get_token()}"})
                print(f'retrieved records')
                if r.status_code == 200:
                    cursor = db.cursor(prepared=True)
                    val = []
                    for finding in json.loads(r.text):
                        val.append((finding['id'], finding['findingIdentifier'], finding['specimenOrgan'], finding['specimenOrganCode'],
                                    finding['specimenOrganVocabulary'], finding['finding'], finding['findingCode'], finding['findingVocabulary'],
                                    finding['findingType'], finding['severity'], finding['observation'], finding['frequency'], finding['dose'], finding['doseUnit'],
                                    finding['timepoint'], finding['timepointUnit'], finding['treatmentRelated'], finding['compoundId'], finding['studyId'],
                                    convertTimestamp(finding['createdDate']), convertTimestamp(finding['modifiedDate']), finding['sex']))
                    try:
                        cursor.executemany(sql, val)
                        db.commit()
                    except mysql.connector.errors.InterfaceError as e:
                        max_len = max([len(v[5]) for v in val])
                        print(f'{e}, len(finding) = {max_len}')

                elif r.status_code == 401:
                    api.reconnect()
                else:
                    print(f"Cannot retrieve findings from {service.endpoint}: {r.status_code}")
                break


def convertTimestamp(timestampStr):
    return parser.isoparse(timestampStr)


if __name__ == "__main__":
    main()