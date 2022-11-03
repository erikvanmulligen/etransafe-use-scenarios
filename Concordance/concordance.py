from pprint import pprint

from knowledgehub.api import KnowledgeHubAPI
import argparse
import json
import os
import sys
import mysql.connector
from Concordance.condordance_utils import intersection, getDrugsMapping, getClinicalDatabases, getPreclinicalDatabases, getSocs, getSocDrugFindings, getPTDrugFindings, getAllPreClinicalClinicalPTs, getAllPreclinicalClinicalDistances
from Concordance.meddra import MedDRA

level = 'soc'
pt_to_group = {}


def getGroups(meddra, pt, lv):
    global pt_to_group

    if pt not in pt_to_group:
        if lv == 'pt':
            group = meddra.getPt(pt)
        elif lv == 'hlt':
            group = meddra.getHLT(pt)
        elif lv == 'hlgt':
            group = meddra.getHLGT(pt)
        elif lv == 'soc':
            group = meddra.getSoc(pt)
        pt_to_group[pt] = list(group.keys())
    return pt_to_group[pt]


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    parser.add_argument('-host', required=True, help='mysql server')
    parser.add_argument('-database', required=True, help='mysql database')
    parser.add_argument('-dbuser', required=True, help='mysql database user')
    parser.add_argument('-dbpass', required=True, help='mysql database password')
    parser.add_argument('-drug_mappings', required=False, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    if args.drug_mappings is None:
        drugs = getDrugsMapping(api, getClinicalDatabases(api), getPreclinicalDatabases(api))
    else:
        if os.path.isfile(args.drug_mappings):
            with open(args.drug_mappings, 'r') as drug_file:
                drugs = json.loads(drug_file.read())
        else:
            drugs = getDrugsMapping(api, getClinicalDatabases(api), getPreclinicalDatabases(api))
            with open(args.drug_mappings, 'x') as drug_file:
                drug_file.write(json.dumps(drugs))


    db = mysql.connector.connect(host=args.host, database=args.database, username=args.dbuser, password=args.dbpass)

    meddra = MedDRA(username=args.dbuser, password=args.dbpass)
    ClinicalDatabases = getClinicalDatabases(api);
    PreclinicalDatabases = getPreclinicalDatabases(api)

    bins = {}
    preclinical_pts = {}
    clinical_pts = {}
    clinical_names = {}
    empty_intersections = 0
    non_empty_intersections = 0

    getPTDrugFindings(db=db, drugInfo=drugs['FIADGNVRKBPQEU'], databases=ClinicalDatabases.keys(), table='clinical_meddra')

    for drug in drugs:
        preclinical_pts[drug] = set(getPTDrugFindings(db=db, drugInfo=drugs[drug], databases=PreclinicalDatabases.keys(), table='preclinical_meddra'))
        clinical_pts[drug] = set(getPTDrugFindings(db=db, drugInfo=drugs[drug], databases=ClinicalDatabases.keys(), table='clinical_meddra'))
        clinical_names[drug] = [meddra.getPtName(pt) for pt in clinical_pts[drug]]
        intersection_pts = intersection(preclinical_pts[drug], clinical_pts[drug])
        if len(intersection_pts) == 0:
            empty_intersections += 1
            print('drug %s' % drug)
            print('preclinical_ptr: %s' % ([meddra.getPtName(pt) for pt in preclinical_pts[drug]]))
            print('clinical_ptr: %s' % ([meddra.getPtName(pt) for pt in clinical_pts[drug]]))
            print('intersection: %s' % ([meddra.getPtName(pt) for pt in intersection_pts]))
        else:
            non_empty_intersections += 1

    print('#drugs found: %d, %d no overlap, %d overlap' % (len(drugs), empty_intersections, non_empty_intersections))

    all_preclinical_clinical_pts = getAllPreClinicalClinicalPTs(db=db, tables=['preclinical_meddra', 'clinical_meddra'])
    all_preclinical_clinical_distances = getAllPreclinicalClinicalDistances(db=db, tables=['preclinical_meddra', 'clinical_meddra'])

    group_to_pt_TP = {}
    for pt in all_preclinical_clinical_pts:
        # now multiple groups can come back for a pt
        groups = getGroups(meddra, pt, level)

        for group in groups:
            if group not in bins:
                bins[group] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0, 'drugs': [], 'distance': all_preclinical_clinical_distances[pt]}
                group_to_pt_TP[group] = []
            elif abs(bins[group]['distance']) > abs(all_preclinical_clinical_distances[pt]):
                bins[group]['distance'] = all_preclinical_clinical_distances[pt]

            for drug in drugs:
                if drug not in bins[group]['drugs']:
                    bins[group]['drugs'].append(drug)
                    if pt in preclinical_pts[drug]:
                        if pt in clinical_pts[drug]:
                            bins[group]['tp'] += 1
                            group_to_pt_TP[group].append(pt)
                        else:
                            bins[group]['fp'] += 1
                    else:
                        if pt in clinical_pts[drug]:
                            bins[group]['fn'] += 1
                        else:
                            bins[group]['tn'] += 1

    # print pt_to_group
    for group in group_to_pt_TP:
        group_name = meddra.getSocName(group)
        pt_names = [meddra.getPtName(pt) for pt in group_to_pt_TP[group]]
        print('%s : %d : %s' % (group_name, len(pt_names), pt_names))


if __name__ == "__main__":
    main()

