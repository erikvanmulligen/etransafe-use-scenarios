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
        if e.errno == 1049:  # database non existing
            db = mysql.connector.connect(host=settings['db']['host'], username=settings['db']['user'], password=settings['db']['password'])
            cursor = db.cursor()
            cursor.execute(f'CREATE DATABASE `{settings["db"]["database"]}`')
            cursor.execute(f'USE `{settings["db"]["database"]}`')
            cursor.close()
        else:
            raise e

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
            standardInchiKey = compound['standardInchiKey']
            if standardInchiKey is not None:
                inchiGroup = standardInchiKey[0:14]
                if inchiGroup not in preclinical_compounds:
                    compound['standardInchiKey'] = standardInchiKey
                    compound['inchiGroup'] = inchiGroup
                    preclinical_compounds[inchiGroup] = compound
                    preclinical_compounds[inchiGroup][database] = []
                preclinical_compounds[inchiGroup][database].extend(compound['findingIds'])

    clinical_compounds = {}
    for database in settings['clinical']:
        for compound in clinical_pas[database].getAllCompounds():
            standardInchiKey = compound['standardInchiKey']
            if standardInchiKey is not None:
                inchiGroup = standardInchiKey[0:14]
                if inchiGroup not in clinical_compounds:
                    compound['standardInchiKey'] = standardInchiKey
                    compound['inchiGroup'] = inchiGroup
                    clinical_compounds[inchiGroup] = compound
                    clinical_compounds[inchiGroup][database] = []
                clinical_compounds[inchiGroup][database].extend(compound['findingIds'])

    # find the compounds that are both preclinical and clinical present and store these in the database
    common_compounds = []
    for pc in preclinical_compounds:
        preclinical_compound = preclinical_compounds[pc]
        for cc in clinical_compounds:
            clinical_compound = clinical_compounds[cc]
            if preclinical_compound['standardInchiKey'] == clinical_compound['standardInchiKey']:
                if preclinical_compound['standardInchiKey'] not in common_compounds:
                    common_compound = {
                        'standardInchiKey': preclinical_compound['standardInchiKey'],
                        'inchiGroup': preclinical_compound['inchiGroup'],
                        'inchiKeys': set(),
                        'names': set(),
                    }
                    for database in settings['preclinical']:
                        common_compound[database] = []
                    for database in settings['clinical']:
                        common_compound[database] = []

                    common_compounds.append(common_compound)
                else:
                    common_compound = common_compounds['standardInchiKey']

                if preclinical_compound['name'] is not None:
                    common_compound['names'].add(preclinical_compound['name'])
                common_compound['inchiKeys'].add(preclinical_compound['standardInchiKey'])
                if clinical_compound['name'] is not None:
                    common_compound['names'].add(clinical_compound['name'])
                common_compound['inchiKeys'].add(clinical_compound['standardInchiKey'])

                # copy the finding ids of the different databases
                for database in settings['preclinical']:
                    if database in preclinical_compound:
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
                           (common_compound['inchiGroup'],
                            ', '.join(common_compound['names']),
                            ', '.join(common_compound['inchiKeys']),
                            len(common_compound['inchiKeys'])))
            db.commit()

            for database in settings['preclinical']:
                for finding_id in common_compound[database]:
                    cursor.execute('INSERT INTO finding_ids (inchi_group, db, finding_id) VALUES (%s, %s, %s)',
                                   (common_compound['inchiGroup'], database, finding_id))
            for database in settings['clinical']:
                for finding_id in common_compound[database]:
                    cursor.execute('INSERT INTO finding_ids (inchi_group, db, finding_id) VALUES (%s, %s, %s)',
                                   (common_compound['inchiGroup'], database, finding_id))
            db.commit()

        except mysql.connector.errors.InterfaceError as e:
            print(e)


if __name__ == "__main__":
    main()