import argparse
import csv
from kh.api import KnowledgeHubAPI


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-outfile', required=True, help='file to be store results')
    parser.add_argument('-infile', required=True, help='file with SMILES')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI()
    api.login(args.username, args.password)

    databases = {
        'medline': api.Medline(),
        'faers': api.Faers(),
        'clinicaltrials': api.ClinicalTrials()
    }

    out_file = open(args.outfile, 'w', newline='')
    in_file = open(args.infile, newline='')
    hepatobiliary_disorders = '10019805'

    reader = csv.reader(in_file,  delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer = csv.writer(out_file,  delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['db', 'organ', 'orig SMILES', 'similar SMILES', 'compound', 'finding', 'finding_code', 'atc'])

    c = 0
    for row in reader:
        if len(row) > 0:
            for db in databases.keys():
                smile = row[0]
                similars = api.SimilarityService().get(smile, 10, 0.8)
                for similar in similars['search_results'][0]['SMILES']:
                    print(similar)
                    for record in databases[db].getStudiesBySMILESandSOC(smile, hepatobiliary_disorders):
                        writer.writerow([db, record['FINDING']['specimenOrgan'], smile, similar, record['COMPOUND']['name'], record['FINDING']['finding'], record['FINDING']['findingCode'], ''])
                        c += 1
                        if c % 100 == 0:
                            print(f'{c} records processed', flush=True)
    in_file.close()
    out_file.close()


if __name__ == "__main__":
    main()
