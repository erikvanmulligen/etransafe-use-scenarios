"""
This program computes the drugs that can be found in the preclinical database and the clinical database
"""

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

    try:
        db = mysql.connector.connect(host=settings['db']['host'], database=settings['db']['database'], username=settings['db']['user'], password=settings['db']['password'])
    except mysql.connector.errors.ProgrammingError as e:
        if e.errno == 1049: # database non existing
            db = mysql.connector.connect(host=settings['db']['host'], username=settings['db']['user'], password=settings['db']['password'])
            cursor = db.cursor()
            cursor.execute(f'CREATE DATABASE `{settings["db"]["database"]}`')
            cursor.execute(f'USE `{settings["db"]["database"]}`')
            cursor.close()
        else:
            raise(e)

    # prepare the tables if non existing
    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS drugs (nr_inchi_keys int null, names mediumtext null, inchi_group mediumtext null, inchi_keys mediumtext null)')
    cursor.execute('CREATE TABLE IF NOT EXISTS finding_ids (inchi_group varchar(15) null, db varchar(100) null, finding_id int null)')
    cursor.close()

    clinical_pas = getClinicalDatabases(api)
    preclinical_pas = getPreclinicalDatabases(api)

    preclinical_compounds = {}
    for database in settings['preclinical']:
        for compound in preclinical_pas[database].getAllCompounds():
            inchiKey = compound['inchiKey'] if 'inchiKey' in compound else None
            if 'smiles' in compound and compound['smiles'] is not None:
                response = api.ChemistryService().paStandardize(compound['smiles'], 'preclinical')
                if response is not None and type(response) == tuple:
                    inchiKey, smiles = response
            if inchiKey is not None:
                inchi_group = inchiKey[0:14]
                if inchi_group not in preclinical_compounds:
                    compound['standardInchiKey'] = inchiKey
                    compound['inchiGroup'] = inchi_group
                    preclinical_compounds[inchi_group] = compound
                preclinical_compounds[inchi_group][database] = compound['findingIds']

    clinical_compounds = {}
    not_found = 0
    for database in settings['clinical']:
        for compound in clinical_pas[database].getAllCompounds():
            inchiKey = compound['inchiKey']
            if inchiKey is not None:
                inchi_group = inchiKey[0:14]
                if inchiKey not in clinical_compounds:
                    compound['standardInchiKey'] = inchiKey
                    compound['inchiGroup'] = inchiKey[0:14]
                    clinical_compounds[inchi_group] = compound
                clinical_compounds[inchi_group][database] = compound['findingIds']
            else:
                not_found += 1

    print(f'no inchi_key for {not_found} compounds')

    # find the compounds that are both preclinically and clinically present and store these in the database
    common_compounds = []
    for pc in preclinical_compounds:
        preclinical_compound = preclinical_compounds[pc]
        for cc in clinical_compounds:
            clinical_compound = clinical_compounds[cc]
            if preclinical_compound['inchiGroup'] == clinical_compound['inchiGroup']:
                if preclinical_compound['inchiGroup'] not in common_compounds:
                    common_compound = {
                        'inchi_group': preclinical_compound['inchiGroup'],
                        'inchi_keys': set(),
                        'names': set(),
                    }
                    for database in settings['preclinical']:
                        common_compound[database] = []
                    for database in settings['clinical']:
                        common_compound[database] = []

                    common_compounds.append(common_compound)
                else:
                    common_compound = common_compounds['inchiGroup']

                if preclinical_compound['standardInchiKey'] is not None:
                    common_compound['inchi_keys'].add(preclinical_compound['standardInchiKey'])
                if preclinical_compound['name'] is not None:
                    common_compound['names'].add(preclinical_compound['name'])
                if clinical_compound['standardInchiKey'] is not None:
                    common_compound['inchi_keys'].add(clinical_compound['standardInchiKey'])
                if clinical_compound['name'] is not None:
                    common_compound['names'].add(clinical_compound['name'])

                # copy the finding ids of the different databases
                for database in settings['preclinical']:
                    if database in preclinical_compound:
                        if database == 'Preclinical':
                            print(preclinical_compound[database])
                        else:
                            common_compound[database].extend(preclinical_compound[database])
                for database in settings['clinical']:
                    if database in clinical_compound:
                        common_compound[database].extend(clinical_compound[database])

    print('clearing database')
    cursor = db.cursor(prepared=True)
    cursor.execute('DELETE FROM drugs')
    cursor.execute('DELETE FROM finding_ids')
    db.commit()

    count = 0
    for common_compound in common_compounds:

        print(f'{count} of {len(common_compounds)} records processed')
        count += 1

        try:
            cursor = db.cursor(prepared=True)
            cursor.execute('INSERT INTO drugs (inchi_group, names, inchi_keys, nr_inchi_keys) VALUES (%s, %s, %s, %s)',
                           (common_compound['inchi_group'],
                            ', '.join(common_compound['names']),
                            ', '.join(common_compound['inchi_keys']),
                            len(common_compound['inchi_keys'])))
            db.commit()

            for database in settings['preclinical']:
                for finding_id in common_compound[database]:
                    cursor.execute('INSERT INTO finding_ids (inchi_group, db, finding_id) VALUES (%s, %s, %s)',
                                   (common_compound['inchi_group'], database, finding_id))
            for database in settings['clinical']:
                for finding_id in common_compound[database]:
                    cursor.execute('INSERT INTO finding_ids (inchi_group, db, finding_id) VALUES (%s, %s, %s)',
                                   (common_compound['inchi_group'], database, finding_id))
            db.commit()

        except mysql.connector.errors.InterfaceError as e:
            print(e)


if __name__ == "__main__":
    main()