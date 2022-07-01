
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
from Concordance.meddra import MedDRA


def main():
    api = KnowledgeHubAPI(server=settings['kh']['server'], client_secret=settings['kh']['client_secret'])

    status = api.login(settings['kh']['user'], settings['kh']['password'])
    if not status:
        print('not successfully logged in')
        sys.exit(1)

    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'], username=settings['db']['user'], password=settings['db']['password'])
    meddra = MedDRA(username=settings['db']['user'], password=settings['db']['password'])

    level = 'hlt'

    cursor = db.cursor()
    cursor.execute('SELECT inchi_group, inchi_key, clinical_name, preclinical_name FROM drugs')
    drugs = [{'inchi_group': r[0], 'inchi_key': r[1], 'names':[r[2], r[3]]} for r in cursor.fetchall()]
    print(f'{len(drugs)} drugs found')

    all_cc_findings = getAllClinicalFindings(db)
    all_pc_findings = getAllPreclinicalFindings(db)
    all_cc_names = [getKey(f, True) for f in all_cc_findings]
    all_pc_names = [getKey(f, False) for f in all_pc_findings]

    all_mappings = getMappings(db)
    df = pd.DataFrame([[None] * len(all_cc_names)] * len(all_pc_names), all_pc_names, all_cc_names)
    for m in all_mappings:
        pc_name = getKey(m, False)
        cc_name = getKey(m, True)
        df.at[pc_name, cc_name] = m['minDistance']

    groups = {}

    # first collect all groups
    for column in df.columns:
        group = meddra.map2name(column, level)
        if group not in groups:
            groups[group] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0, 'codes': 1, 'min_distance': None, 'max_distance': None}
        else:
            groups[group]['codes'] += 1

    c = 0
    for drug in drugs:
        c += 1
        print(f'{c} of {len(drugs)} processed...')
        inchiKey = drug['inchi_key']
        drug_pc_findings = getAllDrugPreclinicalFindings(db, inchiKey)
        drug_cc_findings = getAllDrugClinicalFindings(db, inchiKey)

        drug_pc_groups = set()

        # map the drug_pc_findings to groups
        for pc in drug_pc_findings:
            # find the cc findings associated with it
            pc_name = getKey(pc, False)
            if pc_name in df.index:
                row = df.loc[pc_name]
                # retrieve the clinical codes that are mapped to the preclinical code to obtain the groups
                for code, value in row.items():
                    if value is not None:
                        code_group = meddra.map2name(code, level)
                        drug_pc_groups.add(code_group)
                        groups[code_group]['min_distance'] = amin(groups[code_group]['min_distance'], value)
                        groups[code_group]['max_distance'] = amax(groups[code_group]['max_distance'], value)

        # map the drug_cc_findings to groups
        drug_cc_groups = set([meddra.map2name(getKey(cc, True), level) for cc in drug_cc_findings])

        for group in groups:
            if group in drug_pc_groups and group in drug_cc_groups:
                groups[group]['tp'] += 1
            elif group in drug_pc_groups and group not in drug_cc_groups:
                groups[group]['fp'] += 1
            elif group not in drug_pc_groups and group in drug_cc_groups:
                groups[group]['fn'] += 1
            elif group not in drug_pc_groups and group not in drug_cc_groups:
                groups[group]['tn'] += 1

    group_title = 'MedDRA ' + level.upper()
    pd.set_option('display.max_rows', None)
    pd.set_option('display.colheader_justify', 'left')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    pd.options.display.float_format = '{:.2f}'.format
    df = pd.DataFrame(np.random.rand(len(groups), 13), columns=[group_title, 'codes', 'min_dist', 'max_dist', 'TP', 'FP', 'FN', 'TN', 'Sensitivity', 'Specificity', 'LR+', 'LR-', 'chi-square'])
    df[group_title] = [code for code in groups]
    df['codes'] = [groups[code]['codes'] for code in groups]
    df['min_dist'] = [groups[code]['min_distance'] for code in groups]
    df['max_dist'] = [groups[code]['max_distance'] for code in groups]
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


def amin(value1, value2):
    if value1 is None:
        if value2 is None:
            return None
        else:
            return value2
    else:
        if value2 is None:
            return value1
        else:
            if value1 >= 0:
                if value2 >= 0:
                    return min(value1, value2)
                else:
                    return value1
            else:
                if value2 >= 0:
                    return value2
                else:
                    return max(value1, value2)


def amax(value1, value2):
    if value1 is None:
        if value2 is None:
            return None
        else:
            return value2
    else:
        if value2 is None:
            return value1
        else:
            if value1 >= 0:
                if value2 >= 0:
                    return max(value1, value2)
                else:
                    return value1
            else:
                if value2 >= 0:
                    return value2
                else:
                    return min(value1, value2)

def identical(groups):
    for i in range(len(groups)):
        if groups[i] != groups[0]:
            return False
    return True


def getKey(finding, clinical):
    result = ''
    if clinical:
        result += finding['clinicalFindingCode']
    else:
        result += finding['preclinicalFindingCode']
        if finding['preclinicalSpecimenOrganCode'] is not None:
            result += '_' + finding['preclinicalSpecimenOrganCode']
    return result


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


def intersect(list1, list2):
    return [x for x in list1 if x in list2]


def getAllClinicalFindings(db):
    cursor = db.cursor()
    cursor.execute('select distinct clinicalFindingCode from mappings')
    result = []
    for r in cursor.fetchall():
        record = {}
        c = 0
        for value in r:
            record[cursor.column_names[c]] = value
            c += 1
        result.append(record)
    return result


def getAllPreclinicalFindings(db):
    cursor = db.cursor()
    cursor.execute('select distinct preclinicalFindingCode, preclinicalSpecimenOrganCode from mappings')
    result = []
    for r in cursor.fetchall():
        record = {}
        c = 0
        for value in r:
            record[cursor.column_names[c]] = value
            c += 1
        result.append(record)
    return result


def getAllDrugPreclinicalFindings(db, inchi):
    cursor = db.cursor()
    sql = f"SELECT findingCode as preclinicalFindingCode, specimenOrganCode as preclinicalSpecimenOrganCode from findings where inchi_key = '{inchi}' and db like 'eToxSys'"
    cursor.execute(sql)
    result = []
    for r in cursor.fetchall():
        record = {}
        c = 0
        for value in r:
            record[cursor.column_names[c]] = value
            c += 1
        result.append(record)
    return result


def convertSQLDict(cursor):
    result = []
    for r in cursor.fetchall():
        record = {}
        c = 0
        for value in r:
            record[cursor.column_names[c]] = value
            c += 1
        result.append(record)
    return result


def getAllDrugClinicalFindings(db, inchi):
    cursor = db.cursor()
    sql = f"SELECT findingCode as clinicalFindingCode from findings where inchi_key = '{inchi}' and db not like 'eToxSys'"
    cursor.execute(sql)
    return convertSQLDict(cursor)

def getMappings(db):
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT * FROM mappings")
    return convertSQLDict(cursor)


def getDrugFindings(db, drug, databases, clinical):
    cursor = db.cursor()
    db_str = ','.join(['"{}"'.format(value) for value in databases])
    if clinical:
        sql = f"select clinicalFindingCode from mappings where clinicalFindingCode in (SELECT DISTINCT findingCode from findings where inchi_key = '{drug}' and db in ({db_str}))"
    else:
        sql = f"select clinicalFindingCode from mappings where (preclinicalFindingCode, preclinicalSpecimenOrganCode) in (SELECT findingCode, specimenOrganCode from findings where inchi_key = '{drug}' and db in ({db_str}))"
    cursor.execute(sql)
    return [r[0] for r in cursor.fetchall()]

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


if __name__ == "__main__":
    main()