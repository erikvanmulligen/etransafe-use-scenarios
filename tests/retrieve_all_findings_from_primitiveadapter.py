import argparse
from kh.api import KnowledgeHubAPI
import sys
import xlsxwriter


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-database', required=True, help='database to query')
    parser.add_argument('-file', required=True, help='file to be store results')
    args = parser.parse_args()

    api = KnowledgeHubAPI()
    api.login('erik.mulligen', 'Crosby99!')

    databases = {
        'etoxsys': api.eToxSys(),
        'medline': api.Medline(),
        'faers': api.Faers(),
        'clinicaltrials': api.ClinicalTrials()
    }

    if not args.database.lower() in databases.keys():
        print('database should be one of ' + ', '.join(databases.keys()))
        sys.exit()

    # build a dictionary on finding and specimenOrgan and a count
    accumulation = {}
    for finding in databases[args.database.lower()].getAllFindings():
        if ('findingCode' in finding and finding['findingCode'] is not None) and ('specimenOrganCode' in finding and finding['specimenOrganCode'] is not None):
            specimenOrganCodes = finding['specimentOrganCode'].split(';')
            specimenOrgans = finding['specimentOrgans'].split(';')

            for i in range(0, len(specimenOrganCodes)):
                key = finding['findingCode'] + ':' + specimenOrganCodes[i]
                if key not in accumulation:
                    accumulation[key] = {
                        'finding': finding['finding'],
                        'findingCode': finding['findingCode'],
                        'specimenOrgan': specimenOrgans[i],
                        'specimenOrganCode': specimenOrganCodes[i],
                        'count': 0
                    }
                accumulation[key]['count'] += 1

    # sort on count
    acc_sorted = {k: v for k, v in sorted(accumulation.items(), key=lambda item: item[1]['count'], reverse=True)}

    workbook = xlsxwriter.Workbook(args.file)
    worksheet = workbook.add_worksheet()

    worksheet.write('A1', 'finding')
    worksheet.write('B1', 'findingCode')
    worksheet.write('C1', 'specimenOrgan')
    worksheet.write('D1', 'specimenOrganCode')
    worksheet.write('E1', 'count')

    row = 1
    for key in acc_sorted:
        row += 1
        worksheet.write('A' + str(row), accumulation[key]['finding'])
        worksheet.write('B' + str(row), accumulation[key]['findingCode'])
        worksheet.write('C' + str(row), accumulation[key]['specimenOrgan'])
        worksheet.write('D' + str(row), accumulation[key]['specimenOrganCode'])
        worksheet.write('E' + str(row), accumulation[key]['count'])

    workbook.close()

if __name__ == "__main__":
    main()
