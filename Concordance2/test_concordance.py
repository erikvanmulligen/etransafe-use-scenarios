import sys

import mysql.connector
from Concordance.condordance_utils import getName
from Concordance.meddra import MedDRA
import numpy as np
import pandas as pd

from Concordance2.mapper import Mapper
from knowledgehub.api import KnowledgeHubAPI


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
    except Exception as e:
        return None


def compute_sensitivity(group):
    tp = group['tp']
    fn = group['fn']
    return tp / (tp + fn) if (tp + fn) > 0 else None


def compute_specificity(group):
    fp = group['fp']
    tn = group['tn']
    return tn / (fp + tn) if (fp + tn) > 0 else None


def getPTDrugFindings(db, drug, clinical):
    cursor = db.cursor()
    cursor.execute(f'SELECT DISTINCT finding_code FROM findings WHERE inchi_group = "{drug}" AND clinical = {clinical} AND distance IS NOT NULL')
    return [r[0] for r in cursor.fetchall()]


def getAllPreclinicalClinicalDistances(db):
    cursor = db.cursor()
    cursor.execute('SELECT finding_code, min(distance) FROM findings WHERE distance is not NULL GROUP BY finding_code')
    return {finding[0]: finding[1] for finding in cursor.fetchall()}


def getAllPreClinicalClinicalPTs(db):
    cursor = db.cursor()
    cursor.execute(f'SELECT distinct finding_code FROM findings WHERE distance is not NULL')
    return [finding[0] for finding in cursor.fetchall()]


def getGroup(meddra, pt, level):
    if pt not in pt_to_group:
        if level == 'pt':
            group = meddra.getPt(pt)
        elif level == 'hlgt':
            group = meddra.getHLGT(pt)
        elif level == 'hlt':
            group = meddra.getHLT(pt)
        elif level == 'soc':
            group = meddra.getSoc(pt)
        pt_to_group[pt] = list(group.keys())[0] if len(group) > 0 else None
    return pt_to_group[pt]


def getClinicalDatabases(api):
    return {
        'ClinicalTrials': api.ClinicalTrials(),
        'Medline': api.Medline(),
        'Faers': api.Faers(),
        'DailyMed': api.DailyMed()
    }


def getPreclinicalDatabases(api):
    return {
        'eToxSys': api.eToxSys()
    }


api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
mapper = Mapper(api)

if not api.login('tester', 'tester'):
    print("Failed to login")
    sys.exit(1)
else:
    print("successfully logged in")

level = 'hlt'
pt_to_group = {}
db = mysql.connector.connect(host='localhost', database='concordance-20220524', user='root', password='crosby9')
meddra = MedDRA(username='root', password='crosby9')
ClinicalDatabases = getClinicalDatabases(api);
PreclinicalDatabases = getPreclinicalDatabases(api);

cursor = db.cursor()
cursor.execute('SELECT inchi_group, inchi_keys, names FROM drugs')
drugs = [{'inchi_group': r[0], 'inchi_keys': [i for i in r[1].split(',')], 'names':[i for i in r[2].split(',')]} for r in cursor.fetchall()]
print(f'{len(drugs)} drugs found')

groups = {}
preclinical_pts = {}
clinical_pts = {}

# collect the drugs and combine them per group
for drug in drugs:
    inchi_group = drug['inchi_group']
    preclinical_pts[inchi_group] = set([getGroup(meddra, pt, level) for pt in getPTDrugFindings(db=db, drug=inchi_group, clinical=0)])
    clinical_pts[inchi_group] = set([getGroup(meddra, pt, level) for pt in getPTDrugFindings(db=db, drug=inchi_group, clinical=1)])

all_preclinical_clinical_pts = set([getGroup(meddra, pt, level) for pt in getAllPreClinicalClinicalPTs(db=db)])
all_preclinical_clinical_distances = {getGroup(meddra, pt, level): distance for (pt, distance) in getAllPreclinicalClinicalDistances(db=db).items()}

for code in all_preclinical_clinical_pts:
    group = code

    if group is not None:
        if group not in groups:
            groups[group] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0, 'drugs': [], 'distance': all_preclinical_clinical_distances[code]}
        elif abs(groups[group]['distance']) > abs(all_preclinical_clinical_distances[code]):
            groups[group]['distance'] = all_preclinical_clinical_distances[code]

        for drug in drugs:
            inchi_group = drug['inchi_group']
            if inchi_group not in groups[group]['drugs']:
                groups[group]['drugs'].append(inchi_group)
                if code in preclinical_pts[inchi_group]:
                    if code in clinical_pts[inchi_group]:
                        groups[group]['tp'] += 1
                    else:
                        groups[group]['fp'] += 1
                else:
                    if code in clinical_pts[inchi_group]:
                        groups[group]['fn'] += 1
                    else:
                        groups[group]['tn'] += 1

group_title = 'MedDRA ' + level.upper()
pd.set_option('display.max_rows', None)
pd.set_option('display.colheader_justify', 'left')
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.options.display.float_format = '{:.2f}'.format
df = pd.DataFrame(np.random.rand(len(groups), 11), columns=[group_title, 'min.distance', 'TP', 'FP', 'FN', 'TN', 'Sensitivity', 'Specificity', 'LR+', 'LR-', 'chi-square'])
df[group_title] = [getName(meddra, code, level) for code in groups]
df['min.distance'] = [groups[code]['distance'] for code in groups]
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