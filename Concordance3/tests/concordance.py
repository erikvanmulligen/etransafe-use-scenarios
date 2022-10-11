# %% md
# eTransafe Concordance analysis

import os
import sys

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)
from knowledgehub.api import KnowledgeHubAPI
from Concordance.mapper import Mapper
from Concordance.meddra import MedDRA
import Concordance3.concordance_utils as conutils

import ipywidgets as w
from IPython.display import display, Markdown, clear_output, Javascript
from ipypublish import nb_setup
import numpy as np
import mysql.connector


api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
mapper = Mapper(api)

if api.login('tester', 'tester') == False:
    print("Failed to login")
else:
    print("successfully logged in")


db = mysql.connector.connect(host='localhost', database='concordance-30082022', user='root', password='crosby9')
meddra = MedDRA(username='root', password='crosby9')


def getDrugs(db):
    cursor = db.cursor(prepared=True)
    cursor.execute('select names, inchi_group, inchi_keys from drugs')
    result = [{'names': record[0].split(', '), 'inchi_group': record[1], 'inchi_keys': record[2].split(', ')} for record
              in cursor.fetchall()]
    return result


drugs = getDrugs(db)
print(f'{len(drugs)} drugs found')

pd = nb_setup.setup_pandas(escape_latex=False)
df = pd.DataFrame(np.random.rand(len(drugs), 3), columns=['inchiKey', 'inchiGroup', 'name'])
df.inchiKey = [drug['inchi_keys'][0] for drug in drugs]
df.inchiGroup = [drug['inchi_group'] for drug in drugs]
df.name = [drug['names'][0] for drug in drugs]
df.round(3)

max_distance = 4
all_cc_findings = conutils.getAllClinicalFindings(db)
all_pc_findings = conutils.getAllPreclinicalFindings(db)
all_cc_names = [conutils.getKey(f, True) for f in all_cc_findings]
all_pc_names = [conutils.getKey(f, False) for f in all_pc_findings]

all_mappings = conutils.getMappings(db, max_distance)
all_df = pd.DataFrame([[None] * len(all_cc_names)] * len(all_pc_names), all_pc_names, all_cc_names)
for m in all_mappings:
    pc_name = conutils.getKey(m, False)
    cc_name = conutils.getKey(m, True)
    all_df.at[pc_name, cc_name] = m['minDistance']

ct = nb_setup.setup_pandas(escape_latex=False)
ct.set_option('display.max_rows', None)
ct.set_option('display.colheader_justify', 'left')
ct.set_option('display.max_columns', None)
ct.set_option('display.width', 200)
ct.options.display.float_format = '{:.2f}'.format


def createGroups(all_df, level):
    groups = {}

    # first collect all groups
    for column in all_df.columns:
        group = meddra.map2name(column, level)
        if group not in groups:
            groups[group] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0, 'codes': 1, 'min_distance': None, 'max_distance': None}
        else:
            groups[group]['codes'] += 1


    progress = 0
    for drug in drugs:
        progress += 1
        completed = (progress * 1.0) / len(drugs)
        print('{0:.0%}'.format(completed))
        inchiKey = drug['inchi_group']
        drug_pc_findings = conutils.getAllDrugPreclinicalFindings(db, inchiKey)
        drug_cc_findings = conutils.getAllDrugClinicalFindings(db, inchiKey)

        drug_pc_groups = set()

        # map the drug_pc_findings to groups
        for pc in drug_pc_findings:
            # find the cc findings associated with it
            pc_name = conutils.getKey(pc, False)
            if pc_name in all_df.index:
                row = all_df.loc[pc_name]
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
    return groups


def displayGroups(df, groups, level, title):
    df[title] = [code for code in groups]
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
    df = df.sort_values(by=['LR+'], ascending=False)
    df.round(3)
    return df


groups = {}
for level in ['soc', 'hlgt', 'hlt', 'pt']:
    groups[level] = createGroups(all_df, level)

df = {}
for level in ['soc', 'hlgt', 'hlt', 'pt']:
    title = f'MedDRA {level.upper()}'
    df[level] = ct.DataFrame(np.random.rand(len(groups[level]), 13),
                             columns=[title, 'codes', 'min_dist', 'max_dist', 'TP', 'FP', 'FN', 'TN', 'Sensitivity',
                                      'Specificity', 'LR+', 'LR-', 'chi-square'])
    table = displayGroups(df[level], groups[level], level, title)
    display(table)