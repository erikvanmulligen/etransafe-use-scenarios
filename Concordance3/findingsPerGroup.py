from Concordance.Concordance3.settings import settings
from Concordance.meddra import MedDRA
import mysql.connector
from Concordance.Concordance3.concordance_table import getGroup


def process():
    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'],
                                 username=settings['db']['user'], password=settings['db']['password'])
    meddra = MedDRA(username=settings['db']['user'], password=settings['db']['password'])

    # for drug in drugs:
    #     inchi = drug['inchi_key']
    #     preclinical_findings = getDrugFindings(db=db, drug=inchi, databases=list(preclinical_pas.keys()), clinical=False)
    #     preclinical_pts[inchi] = set([getGroup(pt_to_group, meddra, pt, level) for pt in preclinical_findings])
    #     clinical_findings = getDrugFindings(db=db, drug=inchi, databases=list(clinical_pas.keys()), clinical=True)
    #     clinical_pts[inchi] = set([getGroup(pt_to_group, meddra, pt, level) for pt in clinical_findings])
    #     all_preclinical_findings = all_preclinical_findings | set(preclinical_findings)
    #     all_clinical_findings = all_clinical_findings | set(clinical_findings)

    level = 'soc'
    pt_to_group = {}

    soc_info = {}
    allDistances = getAllDistances(db)
    for (pt, distance) in allDistances:
        group = getGroup(pt_to_group, meddra, pt, level)
        if group not in soc_info:
            soc_info[group] = []
        soc_info[group].append((pt, distance))

    for soc in soc_info:
        print(f'{soc}:{meddra.getSocName(soc)}:{len(soc_info[soc])}')
        for (pt, distance) in soc_info[soc]:
            print(f'\t{pt}:{meddra.getPtName(pt)}:{distance}')


def getAllDistances(db):
    cursor = db.cursor()
    cursor.execute('select clinicalFindingCode, min(minDistance) from mappings group by clinicalFindingCode')
    return [(r[0], r[1]) for r in cursor.fetchall()]


def getDrugs(db):
    cursor = db.cursor()
    cursor.execute('SELECT inchi_group, inchi_key, clinical_name, preclinical_name FROM drugs')
    drugs = [{'inchi_group': r[0], 'inchi_key': r[1], 'names':[r[2], r[3]]} for r in cursor.fetchall()]
    print(f'{len(drugs)} drugs found')
    return drugs


if __name__ == "__main__":
    process()
    pass
