'''
    This program provides some insight in the mappings used for the concordance tables;
    - it reads the drug mappings
    - for each preclinical finding the mappings to clinical terms are retrieved (or None)
    - the results are outputted in a table
'''
import argparse
import csv
import json
import math
import sys
import mysql.connector
from Concordance.condordance_utils import getClinicalDatabases, getPreclinicalDatabases, getPTDrugFindings, get_mappings
from Concordance.mapper import Mapper
from knowledgehub.api import KnowledgeHubAPI


def get_drug_name(drug):
    name = drug['preclinicalName']
    if name is None:
        name = drug['clinicalName']
    if name is None:
        name = drug['inchiKey']
    return name


def format_str(float):
    return "{:.2f}".format(float) if float is not None else None


def avg(lst, default=None):
    return sum(lst) / len(lst) if len(lst) > 0 else default


def min_distance(lst, default=None):
    pos_min = None
    neg_min = None
    for item in lst:
        if item > 0:
            pos_min = min(pos_min, item) if pos_min is not None else item
        elif item < 0:
            neg_min = max(neg_min, item) if neg_min is not None else item

    if pos_min is not None:
        return pos_min
    elif neg_min is not None:
        return neg_min
    else:
        return default


def max_distance(lst, default=None):
    pos_max = None
    neg_max = None
    for item in lst:
        if item > 0:
            pos_max = max(pos_max, item) if pos_max is not None else item
        elif item < 0:
            neg_max = min(neg_max, item) if neg_max is not None else item

    if pos_max is not None:
        return pos_max
    elif neg_max is not None:
        return neg_max
    else:
        return default


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    parser.add_argument('-host', required=True, help='mysql server')
    parser.add_argument('-database', required=True, help='mysql database')
    parser.add_argument('-dbuser', required=True, help='mysql database user')
    parser.add_argument('-dbpass', required=True, help='mysql database password')
    parser.add_argument('-drug_mappings', required=True, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    db = mysql.connector.connect(host=args.host, database=args.database, username=args.dbuser, password=args.dbpass)
    mapper = Mapper(api)

    with open(args.drug_mappings, 'r') as drug_file:
        drugs = json.loads(drug_file.read())

    preclinical_databases = getPreclinicalDatabases(api)
    preclinical_findings = {}
    mapped_finding = {}

    with open('../data/drugs.tsv', 'w', newline='\n') as drugs_file:
        drug_writer = csv.writer(drugs_file, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
        drug_writer.writerow(['drug', 'name', 'finding_count', 'mapped_count', 'unmapped', 'min_pos_dist', 'avg_pos_dist', 'max_pos_dist', 'min_neg_dist', 'avg_neg_dist', 'max_neg_dist'])

        for drug in drugs:
            for database in preclinical_databases:
                if database in drugs[drug] and drugs[drug][database] is not None:
                    fids = drugs[drug][database]

                    # get the finding codes for the finding ids from the primitive adapter
                    findings = preclinical_databases[database].getAllFindingByIds(fids)
                    finding_codes = [{'key': mapper.getKey(finding['FINDING']), 'finding': finding['FINDING']['finding'], 'findingCode': finding['FINDING']['findingCode'], 'specimenOrgan': finding['FINDING']['specimenOrgan'], 'specimenOrganCode': finding['FINDING']['specimenOrganCode']} for finding in findings]

                    # get the associated mappings stored in the database per finding; if no exists it is None
                    mapped_count = 0
                    for finding_code in finding_codes:
                        if finding_code['key'] not in mapped_finding:
                            mappings = get_mappings(db=db, finding_code=finding_code, table='preclinical_findings')
                            if len(mappings) > 0:
                                distances = [mapping['mapped'] for mapping in mappings if mapping is not None]
                                mapped_finding[finding_code['key']] = {'mapped': True, 'min': min(distances, default=None)}
                            else:
                                mapped_finding[finding_code['key']] = {'mapped': False, 'min': None}
                        if mapped_finding[finding_code['key']]['mapped'] is True:
                            mapped_count += 1

                        if finding_code['key'] not in preclinical_findings:
                            preclinical_findings[finding_code['key']] = {'key': finding_code['key'], 'finding': finding_code['finding'], 'findingCode': finding_code['findingCode'], 'specimenOrgan': finding_code['specimenOrgan'], 'specimenOrganCode': finding_code['specimenOrganCode'], 'count': 0, 'mapping': mapped_finding[finding_code['key']]}
                        preclinical_findings[finding_code['key']]['count'] += 1

                    finding_count = len(finding_codes)
                    unmapped_count = finding_count - mapped_count
                    mapping_distances = [mapped_finding[finding_code['key']]['min'] for finding_code in finding_codes if mapped_finding[finding_code['key']]['min'] is not None]
                    pos_distances = [d for d in mapping_distances if d >= 0]
                    neg_distances = [d for d in mapping_distances if d < 0]
                    min_pos_dist = min(pos_distances, default=None)
                    max_pos_dist = max(pos_distances, default=None)
                    avg_pos_dist = avg(pos_distances, default=None)
                    min_neg_dist = min(neg_distances, default=None)
                    max_neg_dist = max(neg_distances, default=None)
                    avg_neg_dist = avg(neg_distances, default=None)

                    print(f'{get_drug_name(drugs[drug])}: preclinical_findings: {finding_count}, mapped:{mapped_count}, not_mapped:{unmapped_count}, pos:(min/avg/max):{min_pos_dist}/{format_str(avg_pos_dist)}/{max_pos_dist}, neg:{min_neg_dist}/{format_str(avg_neg_dist)}/{max_neg_dist}')
                    drug_writer.writerow([drug, get_drug_name(drugs[drug]), finding_count, mapped_count, unmapped_count, min_pos_dist, format_str(avg_pos_dist), max_pos_dist, min_neg_dist, format_str(avg_neg_dist), max_neg_dist])

    # print some examples of mapped items
    # sort on frequency of occurrence

    sorted_preclinical_findings = sorted(preclinical_findings.values(), key=lambda i: i['count'], reverse=True)
    mappings = mapper.mapToClinical(sorted_preclinical_findings)

    with open('../data/mappings.tsv', 'w', newline='\n') as mapping_file:
        mapping_writer = csv.writer(mapping_file, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
        mapping_writer.writerow(['Count', 'Mapped', 'Distance', 'pFinding', 'pOrgan', 'cFinding', 'cCode'])
        # top 10 %
        percent = math.ceil(len(sorted_preclinical_findings) * 0.1)
        cnt = 0
        for preclinical_finding in sorted_preclinical_findings:
            if preclinical_finding['finding'] != 'No abnormalities detected':
                cnt += 1
                if cnt >= percent:
                    break
                if preclinical_finding['mapping']['mapped']:
                    if len(mappings[preclinical_finding["key"]]) > 0:
                        mapping_writer.writerow([preclinical_finding["count"], 1, mappings[preclinical_finding["key"]][0]["distance"], preclinical_finding["finding"], preclinical_finding["specimenOrgan"], mappings[preclinical_finding["key"]][0]["name"], mappings[preclinical_finding["key"]][0]["findingCode"]])
                    else:
                        mapping_writer.writerow([preclinical_finding["count"], 0, '', preclinical_finding["finding"], preclinical_finding["specimenOrgan"], '', ''])
                else:
                    mapping_writer.writerow([preclinical_finding["count"], 0, '', preclinical_finding["finding"], preclinical_finding["specimenOrgan"], '', ''])
                    # print(f'{preclinical_finding["count"]}: {preclinical_finding["finding"]}/{preclinical_finding["specimenOrgan"]} -> no mappings found (2)')


if __name__ == "__main__":
    main()