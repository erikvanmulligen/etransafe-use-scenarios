
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
import Concordance3.concordance_utils as conutils


def main():
    api = KnowledgeHubAPI(server=settings['kh']['server'], client_secret=settings['kh']['client_secret'])

    status = api.login(settings['kh']['user'], settings['kh']['password'])
    if not status:
        print('not successfully logged in')
        sys.exit(1)

    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'], username=settings['db']['user'], password=settings['db']['password'])
    meddra = MedDRA(username=settings['db']['user'], password=settings['db']['password'])

    level = 'soc'
    max_distance = 4

    cursor = db.cursor()
    cursor.execute('SELECT inchi_group, names FROM drugs')
    drugs = [{'inchi_group': r[0], 'inchi_key': r[0], 'names':[r[1].split(', ')]} for r in cursor.fetchall()]
    print(f'{len(drugs)} drugs found')

    all_cc_findings = conutils.getAllClinicalFindings(db)
    all_pc_findings = conutils.getAllPreclinicalFindings(db)
    all_cc_names = [conutils.getKey(f, True) for f in all_cc_findings]
    all_pc_names = [conutils.getKey(f, False) for f in all_pc_findings]

    all_mappings = conutils.getMappings(db, max_distance)
    df = pd.DataFrame([[None] * len(all_cc_names)] * len(all_pc_names), all_pc_names, all_cc_names)
    for m in all_mappings:
        pc_name = conutils.getKey(m, False)
        cc_name = conutils.getKey(m, True)
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
        drug_pc_findings = conutils.getAllDrugPreclinicalFindings(db, inchiKey)
        drug_cc_findings = conutils.getAllDrugClinicalFindings(db, inchiKey)

        drug_pc_groups = set()

        # map the drug_pc_findings to groups
        for pc in drug_pc_findings:
            # find the cc findings associated with it
            pc_name = conutils.getKey(pc, False)
            if pc_name in df.index:
                row = df.loc[pc_name]
                # retrieve the clinical codes that are mapped to the preclinical code to obtain the groups
                for code, value in row.items():
                    if value is not None:
                        code_group = meddra.map2name(code, level)
                        drug_pc_groups.add(code_group)
                        groups[code_group]['min_distance'] = conutils.amin(groups[code_group]['min_distance'], value)
                        groups[code_group]['max_distance'] = conutils.amax(groups[code_group]['max_distance'], value)

        # map the drug_cc_findings to groups
        drug_cc_groups = set([meddra.map2name(conutils.getKey(cc, True), level) for cc in drug_cc_findings])

        for group in groups:
            if group in drug_pc_groups and group in drug_cc_groups:
                groups[group]['tp'] += 1
            elif group in drug_pc_groups and group not in drug_cc_groups:
                groups[group]['fp'] += 1
            elif group not in drug_pc_groups and group in drug_cc_groups:
                groups[group]['fn'] += 1
            elif group not in drug_pc_groups and group not in drug_cc_groups:
                groups[group]['tn'] += 1

    group_title = f'MedDRA {level.upper()}, max distance = {max_distance}'
    pd.set_option('display.max_rows', None)
    pd.set_option('display.colheader_justify', 'left')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    pd.options.display.float_format = '{:.2f}'.format
    df = pd.DataFrame(np.random.rand(len(groups), 13), columns=[group_title, 'codes', 'min_dist', 'max_dist', 'TP', 'FP', 'FN', 'TN', 'Sensitivity', 'Specificity', 'LR+', 'LR-', 'chi-square'])
    df[group_title] = [code for code in groups]
    df['codes'] = [groups[code]['codes'] for code in groups]
    df['min_dist'] = [groups[code]['min_distance'] for code in groups]
    df['min_dist'] = df['min_dist'].fillna(999).astype(int)
    df['max_dist'] = [groups[code]['max_distance'] for code in groups]
    df['max_dist'] = df['max_dist'].fillna(999).astype(int)
    df.TP = [groups[code]['tp'] for code in groups]
    df.FP = [groups[code]['fp'] for code in groups]
    df.FN = [groups[code]['fn'] for code in groups]
    df.TN = [groups[code]['tn'] for code in groups]
    df['Sensitivity'] = [conutils.compute_sensitivity(groups[code]) for code in groups]
    df['Specificity'] = [conutils.compute_specificity(groups[code]) for code in groups]
    df['LR+'] = [conutils.compute_lrp(groups[code]) for code in groups]
    df['LR-'] = [conutils.compute_lrn(groups[code]) for code in groups]
    df['chi-square'] = [conutils.compute_chisquare(groups[code]) for code in groups]
    df.round(3)
    df = df.sort_values(by=['LR+'], ascending=False)


if __name__ == "__main__":
    main()