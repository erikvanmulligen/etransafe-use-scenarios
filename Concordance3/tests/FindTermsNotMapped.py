"""
Find terms in the database that are not matched. Explore possibilities to group terms and match groups
"""

import mysql.connector
from Concordance3.settings import settings


if __name__ == '__main__':
    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'], username=settings['db']['user'], password=settings['db']['password'])

    cursor = db.cursor()
    cursor.execute(f'SELECT DISTINCT findingCode, specimenOrganCode FROM findings WHERE db="eToxSys"')
    records = [{'findingCode': r[0], 'specimenOrganCode': r[1]} for r in cursor.fetchall()]
    count = 0
    no_organ = 0
    for record in records:
        if record["specimenOrganCode"] != None:
            sql = f'SELECT COUNT(*) FROM mappings WHERE preclinicalFindingCode = \"{record["findingCode"]}\" AND preclinicalSpecimenOrganCode = \"{record["specimenOrganCode"]}\"'
        else:
            sql = f'SELECT COUNT(*) FROM mappings WHERE preclinicalFindingCode = \"{record["findingCode"]}\" AND preclinicalSpecimenOrganCode IS NULL'
            no_organ += 1
        cursor.execute(sql)
        r = cursor.fetchone()
        count_value = int(r[0])
        if count_value > 0:
            count += 1
    print(f'{count} of {len(records)} preclinical terms mapped')
    print(f'{no_organ} of {len(records)} has no organ')


