"""
    (C) 2022 Erasmus Medical Center
    19 mei 2022, Erik van Mulligen

    Dit programma vindt alle findings per SOC groep en toont de finding met de afstand uit de mapping tabel
"""
from Concordance3.QueryBuilder import QueryBuilder
from Concordance3.settings import settings
from Concordance.meddra import MedDRA
import mysql.connector


def main(name):
    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'], username=settings['db']['user'], password=settings['db']['password'])
    meddra = MedDRA(username=settings['db']['user'], password=settings['db']['password'])
    socs = meddra.getBySocName(name)

    qb = QueryBuilder(db)

    findings = [pt for pt in getAllClinicalFindingsFromMapping(db) if ptHasSoc(meddra, pt, socs)]
    for pt in findings:
        print(f'{pt}:{meddra.getPtName(pt)}:{getDistance(db, pt)}')


def ptHasSoc(meddra, pt, socs):
    for k in meddra.getSoc(pt).keys():
        if int(k) in socs:
            return pt

def getDistance(db, pt):
    cursor = db.cursor()
    cursor.execute(f'select * from mappings where clinicalFindingCode = {pt}')
    result = []
    for r in cursor.fetchall():
        record = {}
        c = 0
        for value in r:
            record[cursor.column_names[c]] = value
            c += 1
        result.append(record)
    return result


def getAllClinicalFindingsFromMapping(db):
    cursor = db.cursor()
    cursor.execute('select distinct clinicalFindingCode from mappings')
    return [r[0] for r in cursor.fetchall()]


if __name__ == "__main__":
    main('Vascular disorders')