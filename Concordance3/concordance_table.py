
#
# This program computes the concordance tables for the mapped concepts.
# (C) 2022, Erasmus University Medical Center Rotterdam, the Netherlands
#

import sys

from knowledgehub.api import KnowledgeHubAPI
from settings import settings
import mysql.connector
import numpy as np
import pandas as pd
from Concordance.condordance_utils import getClinicalDatabases, getPreclinicalDatabases
from Concordance.meddra import MedDRA
from Concordance.condordance_utils import getName


def main():
    api = KnowledgeHubAPI(server=settings['kh']['server'], client_secret=settings['kh']['client_secret'])

    status = api.login(settings['kh']['user'], settings['kh']['password'])
    if not status:
        print('not successfully logged in')
        sys.exit(1)

    clinical_pas = getClinicalDatabases(api)
    preclinical_pas = getPreclinicalDatabases(api)

    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'], username=settings['db']['user'], password=settings['db']['password'])
    meddra = MedDRA(username=settings['db']['user'], password=settings['db']['password'])

    level = 'soc'

    cursor = db.cursor()
    cursor.execute('SELECT inchi_group, inchi_key, clinical_name, preclinical_name FROM drugs')
    drugs = [{'inchi_group': r[0], 'inchi_key': r[1], 'names':[r[2], r[3]]} for r in cursor.fetchall()]
    print(f'{len(drugs)} drugs found')

    groups = {}
    pt_to_group = {}
    preclinical_pts = {}
    clinical_pts = {}
    # all_clinical_findings = set()
    # all_preclinical_findings = set()

    # collect the findings per drug
    cnt = 0
    for drug in drugs:
        inchi = drug['inchi_key']
        cnt += 1
        print(f'{cnt} of {len(drugs)} drugs processed')
        preclinical_findings = getDrugFindings(db=db, drug=inchi, databases=['eToxSys'], clinical=False)
        preclinical_pts[inchi] = set([getGroup(pt_to_group, meddra, pt, level) for pt in preclinical_findings])
        clinical_findings = getDrugFindings(db=db, drug=inchi, databases=['Medline', 'ClinicalTrials'], clinical=True)
        clinical_pts[inchi] = set([getGroup(pt_to_group, meddra, pt, level) for pt in clinical_findings])
        # all_preclinical_findings = all_preclinical_findings | set(preclinical_findings)
        # all_clinical_findings = all_clinical_findings | set(clinical_findings)

    minimal_all_preclinical_clinical_distances = {}
    maximal_all_preclinical_clinical_distances = {}
    nr_codes = {}
    all_distances = getAllPreclinicalClinicalDistances(db, ['eToxSys'], ['Medline', 'ClinicalTrials'])
    for (pt, distance) in all_distances:
        group = getGroup(pt_to_group, meddra, pt, level)
        if group not in nr_codes:
            nr_codes[group] = 0
        nr_codes[group] += 1

        if group not in minimal_all_preclinical_clinical_distances:
            minimal_all_preclinical_clinical_distances[group] = distance
            maximal_all_preclinical_clinical_distances[group] = distance
        else:
            if distance >= 0 and minimal_all_preclinical_clinical_distances[group] >= 0:
                minimal_all_preclinical_clinical_distances[group] = min(distance, minimal_all_preclinical_clinical_distances[group])
            elif distance >= 0 and minimal_all_preclinical_clinical_distances[group] < 0:
                minimal_all_preclinical_clinical_distances[group] = distance
            elif distance < 0 and minimal_all_preclinical_clinical_distances[group] >= 0:
                minimal_all_preclinical_clinical_distances[group] = minimal_all_preclinical_clinical_distances[group]
            elif distance < 0 and minimal_all_preclinical_clinical_distances[group] < 0:
                minimal_all_preclinical_clinical_distances[group] = max(distance, minimal_all_preclinical_clinical_distances[group])

            if distance >= 0 and maximal_all_preclinical_clinical_distances[group] >= 0:
                maximal_all_preclinical_clinical_distances[group] = max(distance, maximal_all_preclinical_clinical_distances[group])
            elif distance >= 0 and maximal_all_preclinical_clinical_distances[group] < 0:
                maximal_all_preclinical_clinical_distances[group] = maximal_all_preclinical_clinical_distances[group]
            elif distance < 0 and maximal_all_preclinical_clinical_distances[group] >= 0:
                maximal_all_preclinical_clinical_distances[group] = distance
            elif distance < 0 and maximal_all_preclinical_clinical_distances[group] < 0:
                maximal_all_preclinical_clinical_distances[group] = min(distance, maximal_all_preclinical_clinical_distances[group])

    for group in minimal_all_preclinical_clinical_distances.keys():
        if group is not None:
            if group not in groups:
                min_distance = minimal_all_preclinical_clinical_distances[group]
                max_distance = maximal_all_preclinical_clinical_distances[group]
                groups[group] = {'codes': nr_codes[group], 'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0, 'drugs': [], 'min_distance': min_distance, 'max_distance': max_distance}
            else:
                if abs(groups[group]['min_distance']) > abs(minimal_all_preclinical_clinical_distances[group]):
                    groups[group]['min_distance'] = minimal_all_preclinical_clinical_distances[group]

                if abs(groups[group]['max_distance']) < abs(maximal_all_preclinical_clinical_distances[group]):
                    groups[group]['max_distance'] = maximal_all_preclinical_clinical_distances[group]

            # for pt in pt_to_group:
            #     if pt_to_group[pt] == group:
            #         if pt in all_preclinical_findings:
            #             groups[group]['pc'] += 1
            #         elif pt in all_clinical_findings:
            #             groups[group]['cc'] += 1

            for drug in drugs:
                inchi_group = drug['inchi_key']
                if inchi_group not in groups[group]['drugs']:
                    groups[group]['drugs'].append(inchi_group)
                    if group in preclinical_pts[inchi_group]:
                        if group in clinical_pts[inchi_group]:
                            groups[group]['tp'] += 1
                        else:
                            groups[group]['fp'] += 1
                    else:
                        if group in clinical_pts[inchi_group]:
                            groups[group]['fn'] += 1
                        else:
                            groups[group]['tn'] += 1

    group_title = 'MedDRA ' + level.upper()
    pd.set_option('display.max_rows', None)
    pd.set_option('display.colheader_justify', 'left')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    pd.options.display.float_format = '{:.2f}'.format
    df = pd.DataFrame(np.random.rand(len(groups), 13), columns=[group_title, 'min.distance', 'max.distance', 'codes', 'TP', 'FP', 'FN', 'TN', 'Sensitivity', 'Specificity', 'LR+', 'LR-', 'chi-square'])
    df[group_title] = [getName(meddra, code, level) for code in groups]
    df['min.distance'] = [groups[code]['min_distance'] for code in groups]
    df['max.distance'] = [groups[code]['max_distance'] for code in groups]
    df['codes'] = [groups[code]['codes'] for code in groups]
    df.TP = [groups[code]['tp'] for code in groups]
    df.FP = [groups[code]['fp'] for code in groups]
    df.FN = [groups[code]['fn'] for code in groups]
    df.TN = [groups[code]['tn'] for code in groups]
    df['Sensitivity'] = [compute_sensitivity(groups[code]) for code in groups]
    df['Specificity'] = [compute_specificity(groups[code]) for code in groups]
    df['LR+'] = [compute_lrp(groups[code]) for code in groups]
    df['LR-'] = [compute_lrn(groups[code]) for code in groups]
    df['chi-square'] = [compute_chisquare(groups[code]) for code in groups]
    df.round(3)
    df = df.sort_values(by=['LR+'], ascending=False)
    print(df)


def compute_lrp(grp):
    sensitivity = compute_sensitivity(grp)
    specificity = compute_specificity(grp)
    if specificity is not None and sensitivity is not None:
        return sensitivity / (1 - specificity) if specificity != 1 else None
    else:
        return None


def compute_lrn(grp):
    sensitivity = compute_sensitivity(grp)
    specificity = compute_specificity(grp)
    if specificity is not None and sensitivity is not None:
        return (1 - sensitivity) / specificity if specificity != 0 else None
    else:
        return None


def compute_chisquare(group):
    tp = group['tp']
    fp = group['fp']
    fn = group['fn']
    tn = group['tn']
    total = tp + fp + fn + tn
    e11 = ((tp + fp) * (tp + fn)) / total
    e12 = ((tp + fp) * (fp + tn)) / total
    e21 = ((fn + tn) * (tp + fn)) / total
    e22 = ((fn + tn) * (fp + tn)) / total
    try:
        return (((tp - e11) ** 2) / e11) + (((fp - e12) ** 2) / e12) + (((fn - e21) ** 2) / e21) + (
                    ((tn - e22) ** 2) / e22)
    except ZeroDivisionError as e:
        return None


def compute_sensitivity(group):
    tp = group['tp']
    fn = group['fn']
    return tp / (tp + fn) if (tp + fn) > 0 else None


def compute_specificity(group):
    fp = group['fp']
    tn = group['tn']
    return tn / (fp + tn) if (fp + tn) > 0 else None


def getDrugFindings(db, drug, databases, clinical):
    cursor = db.cursor()
    db_str = ','.join(['"{}"'.format(value) for value in databases])
    if clinical:
        sql = f"select clinicalFindingCode from mappings where clinicalFindingCode in (SELECT DISTINCT findingCode from findings where inchi_key = '{drug}' and db in ({db_str}))"
    else:
        sql = f"select clinicalFindingCode from mappings where (preclinicalFindingCode, preclinicalSpecimenOrganCode) in (SELECT findingCode, specimenOrganCode from findings where inchi_key = '{drug}' and db in ({db_str}))"
    cursor.execute(sql)
    return [r[0] for r in cursor.fetchall()]


# def getAllPreclinicalClinicalDistances(db, databases, clinical):
#     cursor = db.cursor()
#     db_str = ','.join(['"{}"'.format(value) for value in databases])
#     if clinical:
#         sql = f'select clinicalFindingCode, minDistance from mappings where clinicalFindingCode in (SELECT DISTINCT findingCode from findings where db in ({db_str}))'
#     else:
#         sql = f'select clinicalFindingCode, minDistance from mappings where (preclinicalFindingCode, preclinicalSpecimenOrganCode) in (SELECT findingCode, specimenOrganCode from findings where db in ({db_str}))'
#     cursor.execute(sql)
#     return [(r[0], r[1]) for r in cursor.fetchall()]

def getAllPreclinicalClinicalDistances(db, preclinical, clinical):
    cursor = db.cursor()
    pc_db_str = ','.join(['"{}"'.format(value) for value in preclinical])
    cc_db_str = ','.join(['"{}"'.format(value) for value in clinical])
    sql = f'SELECT clinicalFindingCode, minDistance FROM mappings WHERE clinicalFindingCode IN (SELECT DISTINCT findingCode FROM findings WHERE db IN ({cc_db_str})) ' \
          f'UNION ' \
          f'SELECT clinicalFindingCode, minDistance FROM mappings WHERE (preclinicalFindingCode, preclinicalSpecimenOrganCode) IN (SELECT findingCode, specimenOrganCode FROM findings WHERE db IN ({pc_db_str}))'
    cursor.execute(sql)
    return [(r[0], r[1]) for r in cursor.fetchall()]

def getAllDistances(db):
    cursor = db.cursor()
    cursor.execute('select clinicalFindingCode, min(minDistance) from mappings group by clinicalFindingCode')
    return [(r[0], r[1]) for r in cursor.fetchall()]


def getPreclinicalDistances(db, pts, databases):
    cursor = db.cursor()
    db_str = ','.join(['"{}"'.format(value) for value in databases])
    pts_str = ','.join(['"{}"'.format(pt) for pt in pts])
    sql = f'select clinicalFindingCode, minDistance from mappings where clinicalFindingCode in ({pts_str}) and (preclinicalFindingCode, preclinicalSpecimenOrganCode) in (SELECT findingCode, specimenOrganCode from findings where db in ({db_str}))'
    cursor.execute(sql)
    return [(r[0], r[1]) for r in cursor.fetchall()]


def getGroup(pt_to_group, meddra, pt, level):
    if pt not in pt_to_group:
        if level == 'pt':
            group = meddra.getPt(pt)
        elif level == 'hlgt':
            group = meddra.getHLGT(pt)
        elif level == 'hlt':
            group = meddra.getHLT(pt)
        elif level == 'soc':
            group = meddra.getSoc(pt)
        else:
            return None
        pt_to_group[pt] = list(group.keys())[0] if len(group) > 0 else None
    return pt_to_group[pt]


if __name__ == "__main__":
    main()