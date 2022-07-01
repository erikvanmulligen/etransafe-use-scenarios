"""
    Program to retrieve all drugs that are found
    in preclinical and clinical databases and match them

    (C) 2022, dept of Medical Informatics, Erasmus University Medical Center.
    Erik M. van Mulligen
"""
import argparse
import sys
import mysql.connector

from Concordance2.mapper import Mapper
from Concordance2.Compound import Compound
from knowledgehub.api import KnowledgeHubAPI
from Concordance.condordance_utils import getPrimitiveAdapter


def main():
    argParser = argparse.ArgumentParser(description='Process parameters for collecting compounds from primitive adapter')
    argParser.add_argument('-username', help='username', default='erik.mulligen')
    argParser.add_argument('-password', help='password', default='Crosby99!')
    argParser.add_argument('-db_username', help='database username', default='root')
    argParser.add_argument('-db_password', help='database password', default='crosby9')
    argParser.add_argument('-db_db', help='database name', default='concordance-medline')
    argParser.add_argument('-db_server', help='database server', default='localhost')
    argParser.add_argument('-clear', action='store_true', help='clear database', default=True)
    args = argParser.parse_args()

    #api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')

    status = api.login(args.username, args.password)
    if status:
        print('logged in')
    else:
        sys.exit(0)

    db = mysql.connector.connect(host=args.db_server, database=args.db_db, user=args.db_username, password=args.db_password)

    if args.clear:
        cursor = db.cursor(prepared=True)
        cursor.execute("DELETE FROM findings")
        cursor.execute("DELETE FROM drugs")
        db.commit()

    mapper = Mapper(api)

    #store_compounds(api, db, mapper, ['eToxSys'], ['Medline', 'Faers', 'DailyMed', 'ClinicalTrials'])
    store_compounds(api, db, mapper, ['eToxSys'], ['Medline'])


'''
    This method stores the compounds in the database for which the inchiGroup (first 14 characters of the inchi_key) match and which
    have preclinical and clinical findings. (Note that the findingIds are not the same as findingCodes and that we store findingCodes)
'''
def store_compounds(api, db, mapper, preclinical_databases, clinical_databases):

    all_grouped_compounds = {}
    for database in preclinical_databases:
        create_compound(api, database, all_grouped_compounds, False)

    # collect all clinical codes
    for database in clinical_databases:
        create_compound(api, database, all_grouped_compounds, True)


    for group_inchi_key in all_grouped_compounds:
        if all_grouped_compounds[group_inchi_key].is_valid(api, mapper):
            print(f'{group_inchi_key}:{all_grouped_compounds[group_inchi_key]}')
            all_grouped_compounds[group_inchi_key].store(db)


def create_compound(api, db, all_grouped_compounds, clinical_flag):
    print(f'processing {db}')

    # get a list of preclinical compounds
    cnt = 0
    compounds = getPrimitiveAdapter(api, db).getAllCompounds()
    for pc_compound in compounds:
        cnt += 1
        # get the standardized inchi_key
        response = None
        if pc_compound['smiles'] is not None:
            response = api.ChemistryService().paStandardize(pc_compound['smiles'], 'preclinical')
        elif pc_compound['name'] is not None:
            response = api.ChemistryService().paStandardize(pc_compound['name'], 'clinical')
        standardized_inchi_key = response[0] if response is not None else pc_compound['inchiKey']

        if standardized_inchi_key is not None:
            group_inchi_key = standardized_inchi_key[0:14]
            if len(group_inchi_key) == 14:
                if group_inchi_key not in all_grouped_compounds:
                    all_grouped_compounds[group_inchi_key] = Compound(group_inchi_key)
                else:
                    print(f'compound {group_inchi_key} already present: {cnt} of {len(compounds)}')

                compound = all_grouped_compounds[group_inchi_key]
                compound.inchi_key(standardized_inchi_key)
                compound.name(pc_compound['name'])
                if clinical_flag is True:
                    compound.clinical_count()
                    compound.clinical_findings(db, pc_compound['findingIds'])
                else:
                    compound.preclinical_count()
                    compound.preclinical_findings(db, pc_compound['findingIds'])


if __name__ == "__main__":
    main()
