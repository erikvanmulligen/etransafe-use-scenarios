'''
This program computes the drugs that can be found in the preclinical database and the clinical database
'''
import sys

from knowledgehub.api import KnowledgeHubAPI
from settings import settings
import mysql.connector
from Concordance.condordance_utils import getClinicalDatabases, getPreclinicalDatabases, intersection

def main():
    api = KnowledgeHubAPI(server=settings['kh']['server'], client_secret=settings['kh']['client_secret'])

    status = api.login(settings['kh']['user'], settings['kh']['password'])
    if not status:
        print('not successfully logged in')
        sys.exit(1)

    clinical_pas = getClinicalDatabases(api)
    preclinical_pas = getPreclinicalDatabases(api)

    preclinical_compounds = {}
    for db in settings['preclinical']:
        for compound in preclinical_pas[db].getAllCompounds():
            inchiKey = compound['inchiKey'] if 'inchiKey' in compound else None
            if 'smiles' in compound and compound['smiles'] is not None:
                response = api.ChemistryService().paStandardize(compound['smiles'], 'preclinical')
                if response is not None and type(response) == tuple:
                    inchiKey, smiles = response
            if inchiKey is not None:
                if inchiKey not in preclinical_compounds:
                    compound['standardInchiKey'] = inchiKey
                    preclinical_compounds[inchiKey] = compound
                preclinical_compounds[inchiKey][db] = compound['findingIds']

    clinical_compounds = {}
    for db in settings['clinical']:
        for compound in clinical_pas[db].getAllCompounds():
            inchiKey = compound['inchiKey'] if 'inchiKey' in compound else None
            if 'name' in compound and compound['name'] is not None:
                response = api.ChemistryService().paStandardize(compound['name'], 'clinical')
                if response is not None and type(response) == tuple:
                    inchiKey, smiles = response
            if inchiKey is not None:
                if inchiKey not in clinical_compounds:
                    compound['standardInchiKey'] = inchiKey
                    clinical_compounds[inchiKey] = compound
                clinical_compounds[inchiKey][db] = compound['findingIds']

    keys = intersection(preclinical_compounds.keys(), clinical_compounds.keys())
    db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'], username=settings['db']['user'], password=settings['db']['password'])

    cursor = db.cursor(prepared=True)
    cursor.execute('DELETE FROM drugs')
    cursor.execute('DELETE FROM finding_ids')
    db.commit()

    for key in keys:
        try:
            cursor = db.cursor(prepared=True)
            cursor.execute('INSERT INTO drugs (inchi_key,  inchi_group, preclinical_name, clinical_name) VALUES (%s, %s, %s, %s)', (key, key[0:14], preclinical_compounds[key]['name'], clinical_compounds[key]['name']))
            db.commit()

            cursor = db.cursor(prepared=True)
            for database in preclinical_pas:
                if database in preclinical_compounds[key]:
                    for finding_id in preclinical_compounds[key][database]:
                        cursor.execute('INSERT INTO finding_ids (inchi_key, db, finding_id) VALUES (%s, %s, %s)',(key, database, finding_id))
                        db.commit()

            for database in clinical_pas:
                if database in clinical_compounds[key]:
                    for finding_id in clinical_compounds[key][database]:
                        cursor.execute('INSERT INTO finding_ids (inchi_key, db, finding_id) VALUES (%s, %s, %s)',(key, database, finding_id))
            db.commit()

        except mysql.connector.errors.InterfaceError as e:
            print(e)


if __name__ == "__main__":
    main()