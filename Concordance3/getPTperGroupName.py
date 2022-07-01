from Concordance.Concordance3.settings import settings
from Concordance.meddra import MedDRA
import mysql.connector
from Concordance.Concordance3.concordance_table import getDrugFindings, getGroup

def main():
    name = input('Enter name of group: ')
    inchiKey = input('Enter inchiKey: ')
    pt_to_group = {}

    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'], username=settings['db']['user'], password=settings['db']['password'])
    meddra = MedDRA(username=settings['db']['user'], password=settings['db']['password'])
    pts = meddra.getBySocName(name)
    for pt in pts:
        print(pt)

    preclinical_findings = getDrugFindings(db=db, drug=inchiKey, databases=['eToxSys'], clinical=False)
    clinical_findings = getDrugFindings(db=db, drug=inchiKey, databases=['Medline'], clinical=True)
    print(preclinical_findings)
    print(clinical_findings)


if __name__ == "__main__":
    main()