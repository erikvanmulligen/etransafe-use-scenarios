import argparse
import sys

import mysql.connector

from Concordance.meddra import MedDRA
from knowledgehub.api import KnowledgeHubAPI
from Concordance.mapper import Mapper


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    parser.add_argument('-host', required=True, help='mysql server')
    parser.add_argument('-database', required=True, help='mysql database')
    parser.add_argument('-dbuser', required=True, help='mysql database user')
    parser.add_argument('-dbpass', required=True, help='mysql database password')
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
    meddra = MedDRA(username=args.dbuser, password=args.dbpass)

    if args.clear:
        cursor = db.cursor(prepared=True)
        cursor.execute("DELETE FROM preclinical_meddra")
        cursor.execute("DELETE FROM clinical_meddra")
        db.commit()

    records = []

    # retrieve the preclinical records and map them to MedDRA
    cursor = db.cursor(prepared=True)
    cursor.execute('SELECT distinct id, findingCode, specimenOrganCode FROM preclinical_findings')
    cnt = 0
    for r in cursor.fetchall():

        if cnt % 33 == 0:
            print('processed %d of %d...' % (cnt, cursor.rowcount))
        cnt += 1

        mapped_clinical_findings = mapper.mapToClinical([{'findingCode': r[1], 'specimenOrganCode': r[2]}])

        preclinical_code = mapper.getKey({'findingCode': r[1], 'specimenOrganCode': r[2]})
        if len(mapped_clinical_findings[preclinical_code]) > 0:

            # find the mapping(s) with the minimal absolute distance; negative distance indicates that the organ is not included in the match
            # a positive distance indicates that the organ and the finding are both matched
            neg_distances = [item['distance'] for item in mapped_clinical_findings[preclinical_code] if item['distance'] < 0]
            pos_distances = [item['distance'] for item in mapped_clinical_findings[preclinical_code] if item['distance'] >= 0]

            neg_minimum = max(neg_distances, default=None)
            pos_minimum = min(pos_distances, default=None)

            # check first if the match with organ has the same score as without organ; in that case take with organ
            if pos_minimum is not None:
                if neg_minimum is not None:
                    if pos_minimum <= -neg_minimum:
                        min_values = [item for item in mapped_clinical_findings[preclinical_code] if item['distance'] == pos_minimum]
                    else:
                        min_values = [item for item in mapped_clinical_findings[preclinical_code] if item['distance'] == neg_minimum]
                else:
                    min_values = [item for item in mapped_clinical_findings[preclinical_code] if item['distance'] == pos_minimum]
            else:
                if neg_minimum is not None:
                    min_values = [item for item in mapped_clinical_findings[preclinical_code] if item['distance'] == neg_minimum]
                else:
                    print('no match at all')
                    min_values = []

            for min_value in min_values:
                ptCodes = meddra.getPt(min_value['findingCode'])
                ptCode = None
                for item in ptCodes:
                    ptCode = item
                    break
                if ptCode is None:
                    ptCode = min_value['findingCode']
                ptName = meddra.getPtName(ptCode)
                socCodes = meddra.getSoc(ptCode)
                hltCodes = meddra.getHLT(ptCode)
                hlgtCodes = meddra.getHLGT(ptCode)
                records.append((r[0], r[1], r[2], ptCode, ptName,
                                ','.join(socCodes.keys()), ','.join(socCodes.values()),
                                ','.join(hltCodes.keys()), ','.join(hltCodes.values()),
                                ','.join(hlgtCodes.keys()), ','.join(hlgtCodes.values()),
                                min_value['distance']))

    # store the mappings
    try:
        cursor = db.cursor(prepared=True)
        cursor.executemany('INSERT INTO preclinical_meddra (id, findingCode, specimenOrganCode, ptCode, ptName, socCodes, socNames, hltCodes, hltNames, hlgtCodes, hlgtNames, distance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', records)
        db.commit()
    except mysql.connector.errors.InterfaceError as e:
        print(e)

    records = []
    cnt = 0

    # retrieve the clinical records and store them in the database
    try:
        cursor = db.cursor(prepared=True)
        cursor.execute('SELECT distinct id, findingCode, specimenOrganCode, findingCode, finding, mapped FROM clinical_findings WHERE mapped > -1')
        for r in cursor.fetchall():

            if cnt % 33 == 0:
                print('processed %d of %d...' % (cnt, cursor.rowcount))
            cnt += 1

            ptCode = r[1]
            ptName = meddra.getPtName(ptCode)
            socCodes = meddra.getSoc(ptCode)
            hltCodes = meddra.getHLT(ptCode)
            hlgtCodes = meddra.getHLGT(ptCode)
            records.append((r[0], r[1], r[2], ptCode, ptName,
                            ','.join(socCodes.keys()), ','.join(socCodes.values()),
                            ','.join(hltCodes.keys()), ','.join(hltCodes.values()),
                            ','.join(hlgtCodes.keys()), ','.join(hlgtCodes.values()),
                            r[5]))
            #cursor2.executemany('INSERT INTO clinical_meddra (id, findingCode, specimenOrganCode, PTCode, name, distance) VALUES (%s, %s, %s, %s, %s, %s)', cursor.fetchall())
        cursor.executemany('INSERT INTO clinical_meddra (id, findingCode, specimenOrganCode, ptCode, ptName, socCodes, socNames, hltCodes, hltNames, hlgtCodes, hlgtNames, distance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', records)
        db.commit()
    except mysql.connector.errors.InterfaceError as e:
        print(e)


# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()

if __name__ == "__main__":
    main()


