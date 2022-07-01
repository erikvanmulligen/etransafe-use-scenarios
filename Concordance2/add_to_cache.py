"""
    Program to retrieve all drugs that are found
    in preclinical and clinical databases and match them

    (C) 2022, dept of Medical Informatics, Erasmus University Medical Center.
    Erik M. van Mulligen
"""
import argparse
import json
import sys
import mysql.connector
from knowledgehub.api import KnowledgeHubAPI
from Concordance.condordance_utils import getPreclinicalDatabases, getClinicalDatabases


def storeCompoundsInDatabase(db, paName, compounds, preclinical):

    drug_insert = '''INSERT INTO drugs (id, db, compoundIdentifier, name, inchiKey, standardizedInchiKey, smiles, standardizedSmiles, preclinical) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    finding_insert = '''INSERT INTO drugFindings (id, db, findingId) VALUES(?, ?, ?)'''
    print(f'store {len(compounds)} {"preclinical" if preclinical else "clinical"} compounds from {paName} in database', flush=True)

    for compound in compounds:
        cursor = db.cursor(prepared=True)
        cursor.execute(drug_insert, (compound['id'], paName, compound['compoundIdentifier'], compound['name'], compound['inchiKey'], compound['standardizedInchiKey'], compound['smiles'], compound['standardizedSmiles'], preclinical))

        cursor.executemany(finding_insert, [(compound['id'], paName, findingId) for findingId in compound['findingIds']])
        db.commit()
        cursor.close()


def getCompounds(connection, databases):
    result = []
    for database in databases:
        cursor = connection.cursor()
        cursor.execute(f'SELECT id, db, compoundIdentifier, name, inchiKey, standardizedInchiKey, smiles, standardizedSmiles, preclinical FROM DRUGS WHERE db = "{database}"')
        records = cursor.fetchall()
        for record in records:
            result.append({'id': record[0], 'db': record[1], 'compoundIdentifier': record[2], 'name': record[3],
                           'inchiKey': record[4], 'standardizedInchiKey': record[5], 'smiles': record[6],
                           'standardizedSmiles': record[7], 'preclinical': record[8]})
    return result


def groupCompounds(records):
    result = {}
    for record in records:
        if record['standardizedInchiKey'] is not None:
            key = record['standardizedInchiKey'][0:14]
            if key not in result:
                result[key] = []
            result[key].append(record)
    return result


def main():
    argParser = argparse.ArgumentParser(description='Process parameters for collecting compounds from primitive adapter')
    argParser.add_argument('-username', required=True, help='username')
    argParser.add_argument('-password', required=True, help='password')
    argParser.add_argument('-db_username', required=True, help='database username')
    argParser.add_argument('-db_password', required=True, help='database password')
    argParser.add_argument('-db_db', required=True, help='database name')
    argParser.add_argument('-db_server', required=True, help='database server')
    argParser.add_argument('-drugs', required=True, help='filename containing drugs')
    argParser.add_argument('-clear', required=False, action='store_true', help='clear database')
    args = argParser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    preclinicalDatabases = getPreclinicalDatabases(api)
    clinicalDatabases = getClinicalDatabases(api)

    db = mysql.connector.connect(host=args.db_server, database=args.db_db, user=args.db_username, password=args.db_password)

    # if args.clear:
    #     cursor = db.cursor(prepared=True)
    #     cursor.execute("DELETE FROM drugFindings")
    #     cursor.execute("DELETE FROM drugs")
    #     db.commit()
    #
    #
    # for database in preclinicalDatabases:
    #     print(f'processing {database}')
    #     pc_compounds = preclinicalDatabases[database].getAllCompounds()
    #     records = []
    #
    #     for pc_compound in pc_compounds:
    #         if pc_compound['smiles'] is not None:
    #             response = api.ChemistryService().paStandardize(pc_compound['smiles'], 'preclinical')
    #         elif pc_compound['name'] is not None:
    #             response = api.ChemistryService().paStandardize(pc_compound['name'], 'clinical')
    #         else:
    #             response = None
    #
    #         if response is not None:
    #             pc_compound['standardizedInchiKey'] = response[0]
    #             pc_compound['standardizedSmiles'] = response[1]
    #             records.append(pc_compound)
    #         # pc_compound['standardizedInchiKey'] = pc_compound['inchiKey']
    #         # pc_compound['standardizedSmiles'] = pc_compound['smiles']
    #         # records.append(pc_compound)
    #
    #     storeCompoundsInDatabase(db, database, records, True)
    #
    # # store compounds from clinical databases
    # for database in clinicalDatabases:
    #     print(f'processing {database}')
    #     compounds = clinicalDatabases[database].getAllCompounds()
    #     records = []
    #     for cl_compound in compounds:
    #         cl_compound['standardizedInchiKey'] = cl_compound['inchiKey']
    #         cl_compound['standardizedSmiles'] = cl_compound['smiles']
    #         records.append(cl_compound)
    #
    #     storeCompoundsInDatabase(db, database, records, False)

    preclinicalCompounds = getCompounds(db, preclinicalDatabases)
    groupedPreclinicalCompounds = groupCompounds(preclinicalCompounds)
    clinicalCompounds = getCompounds(db, clinicalDatabases)
    groupedClinicalCompounds = groupCompounds(clinicalCompounds)
    drugs_mapping = {}
    for groupedPreclinicalCompound in groupedPreclinicalCompounds:
        if groupedPreclinicalCompound in groupedClinicalCompounds:
            print(f'{groupedPreclinicalCompound} has {len(groupedPreclinicalCompounds[groupedPreclinicalCompound])} preclinical compounds and {len(groupedClinicalCompounds[groupedPreclinicalCompound])} clinical compounds')
            if groupedPreclinicalCompound not in drugs_mapping:
                drugs_mapping[groupedPreclinicalCompound] = {
                    'inchiKey': groupedPreclinicalCompound,
                    'clinicalName': getName(groupedClinicalCompounds[groupedPreclinicalCompound]),
                    'preclinicalName': getName(groupedPreclinicalCompounds[groupedPreclinicalCompound]),
                }
                for compound in groupedPreclinicalCompounds[groupedPreclinicalCompound]:
                    for database in preclinicalDatabases:
                        if database == compound['db']:
                            if database not in drugs_mapping[groupedPreclinicalCompound]:
                                drugs_mapping[groupedPreclinicalCompound][database] = []
                            drugs_mapping[groupedPreclinicalCompound][database].extend(getFindings(db, compound['id'], compound['db']))

                for compound in groupedClinicalCompounds[groupedPreclinicalCompound]:
                    for database in clinicalDatabases:
                        if database == compound['db']:
                            if database not in drugs_mapping[groupedPreclinicalCompound]:
                                drugs_mapping[groupedPreclinicalCompound][database] = []
                            drugs_mapping[groupedPreclinicalCompound][database].extend(getFindings(db, compound['id'], compound['db']))

    with open(args.drugs, 'w') as drug_file:
        drug_file.write(json.dumps(drugs_mapping))


def getFindings(connection, id, database):
    cursor = connection.cursor()
    cursor.execute(f'SELECT findingId FROM DRUGFINDINGS WHERE id = {id} AND db = "{database}"')
    return [record[0] for record in cursor.fetchall()]


def getName(compounds):
    for compound in compounds:
        return compound['name'] if compound['name'] is not None else compound['compoundIdentifier']


if __name__ == "__main__":
    main()
