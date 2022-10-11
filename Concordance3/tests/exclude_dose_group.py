from Concordance3.settings import settings
from knowledgehub.api import KnowledgeHubAPI
import mysql.connector


def getAllFindingInchisByDatabase(db, database):
    cursor = db.cursor(prepared=True)
    cursor.execute(f'select distinct finding_id, inchi_group from finding_ids where db = "{database}" limit 1000');
    return {record[0]: record[1] for record in cursor.fetchall()}


def process():
    api = KnowledgeHubAPI(server=settings['kh']['server'], client_secret=settings['kh']['client_secret'])
    status = api.login(settings['kh']['user'], settings['kh']['password'])
    if status:
        print('successfully logged in')
        db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'],
                                     username=settings['db']['user'], password=settings['db']['password'])

        finding_inchis = getAllFindingInchisByDatabase(db, 'eToxSys')
        findings = api.eToxSys().getAllFindingByIds(list(finding_inchis.keys()))
        nocontrols = []
        for finding in findings:
            if finding['FINDING']['dose'] != '0':
                nocontrols.append(finding)
            else:
                print('found a dose group == 0')
        # nocontrols = [finding for finding in findings if finding['dose'] != '0']
        print(f'{len(findings)} -> {len(nocontrols)}')
    pass

if __name__ == '__main__':
    process()