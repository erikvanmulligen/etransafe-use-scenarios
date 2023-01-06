"""
    code to evaluate the heatmap logic
"""
import sys
from knowledgehub.api import KnowledgeHubAPI
import argparse
import numpy as np
import pandas


def filterStudies(studies):
    return [study for study in studies if study['FINDING']['findingVocabulary'] is not None and study['FINDING']['findingCode'] is not None and study['FINDING']['findingCode'] != 'MC:2000001'
            and ('dose' not in study['FINDING'] or study['FINDING']['dose'] != 0.0)]


def count_studies(studies):
    unique_studies = set([study['STUDY']['studyIdentifier'] for study in studies])
    return len(unique_studies)


def flatten(l):
    return [item for sublist in l for item in sublist]


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting all data from eToxSys')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    parser.add_argument('-compound', required=True, help='compound')
    args = parser.parse_args()

    # api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')

    if api.login(args.username, args.password) is False:
        print("Failed to login")
        sys.exit(0)
    else:
        print("successfully logged in")

    compoundSmile = None

    print(f'retrieving smiles for {args.compound}')
    compoundSmile = api.ChemistryService().getSMILESByName(args.compound)
    print(f'Found SMILES {compoundSmile} for {args.compound}')

    similar_compounds = api.SimilarityService().get(compoundSmile[0])
    compoundNames = []
    names = []
    smiles = []
    similarities = []

    if similar_compounds is not None:
        for similar_compound in similar_compounds:
            names.append(similar_compound['name'])
            smiles.append(similar_compound['smiles'])
            similarities.append(similar_compound['distance'])

    df = pandas.DataFrame(np.random.rand(len(names), 3), columns=['NAME', 'SMILES', 'SIMILARITY'])
    df.NAME = names
    df.SMILES = smiles
    df.SIMILARITY = similarities
    df.round(3)

    print(df)

    # filter studies on being able to have a findingCode and findingVocabulary and not having findings for dose is 0.0 (control group)

    studies = {}
    # studies['faerspa'] = filterStudies(api.Faers().getStudiesBySMILES(smiles))
    # print(f'{count_studies(studies["faerspa"])} FAERS studies')
    # api.SemanticService().getSocs(studies['faerspa'], algorithm='MEDDRAPT2MEDDRASOC')
    # studies['medlinepa'] = filterStudies(api.Medline().getStudiesBySMILES(smiles))
    # print(f'{count_studies(studies["medlinepa"])} MEDLINE studies')
    # api.SemanticService().getSocs(studies['medlinepa'], algorithm='MEDDRAPT2MEDDRASOC')
    # studies['clinicaltrialspa'] = filterStudies(api.ClinicalTrials().getStudiesBySMILES(smiles))
    # api.SemanticService().getSocs(studies['clinicaltrialspa'], algorithm='MEDDRAPT2MEDDRASOC')
    # studies['dailymedpa'] = filterStudies(api.DailyMed().getStudiesBySMILES(smiles))
    # print(f'{count_studies(studies["dailymedpa"])} DAILYMED studies')
    # api.SemanticService().getSocs(studies['dailymedpa'], algorithm='MEDDRAPT2MEDDRASOC')
    studies['eTOXsys'] = filterStudies(api.eToxSys().getStudiesByCompoundNames(names))
    print(f'{count_studies(studies["eTOXsys"])} eTOX studies')
    api.SemanticService().getSocs(studies['eTOXsys'], algorithm='MA2MEDDRASOC')

    service_names = [
                        # {'name': 'faerspa', 'title': 'FAERS'},
                        # {'name': 'medlinepa', 'title': 'MEDLINE'},
                        # {'name': 'eTOXsys', 'title': 'eTOXsys'},
                        # {'name': 'dailymedpa', 'title': 'DailyMed'},
                        {'name': 'clinicaltrialspa', 'title': 'ClinicalTrials'},
                    ]

    system = {}
    all_compounds = [c.lower() for c in names]
    socs = {}

    for service in service_names:
        source = service['name']
        if source in studies:
            for study in studies[source]:
                soc = study['FINDING']['__soc']
                if soc not in socs:
                    if soc not in socs:
                        socs[soc] = set()
                    socs[soc].add(study['STUDY']['id'])

    # sort the socs per count
    all_socs = {k: v for k, v in sorted(socs.items(), key=lambda item: item[1], reverse=True)}

    # traverse all studies and create a matrix per source
    total_count = {}

    for service in service_names:
        source = service['name']
        if source in studies:
            source_study_ids = set()
            system[source] = {
                                'data': np.zeros((len(all_socs), len(all_compounds)), dtype=int).tolist(),
                                # 'studies': [[] * len(all_compounds)] * len(all_socs),
                                'studies': [[set() for i in range(len(all_compounds))] for j in range(len(all_socs))],
                                # 'studies': [[set()] * len(all_compounds) for i in range(len(all_socs))],
                                'rows': list(all_socs.keys()),
                                'cols': all_compounds
                              }

            for study in studies[source]:
                soc = study['FINDING']['__soc']
                row = system[source]['rows'].index(soc)
                col = system[source]['cols'].index(study['COMPOUND']['name'].lower())
                system[source]['data'][row][col] += 1
                system[source]['studies'][row][col].add(study['STUDY']['id'])
                source_study_ids.update(system[source]['studies'][row][col])
            total_count[source] = len(source_study_ids)

    print(f'total_count[source] = {total_count["clinicaltrialspa"]}')

    for source, value in system.items():
        data = system[source]['data']

        col_count = [0] * len(all_compounds)
        col_studies = [set() for i in range(0, len(all_compounds))]
        for row in range(len(all_socs)):
            for col in range(0, len(all_compounds)):
                col_count[col] += data[row][col]
                col_studies[col].update(system[source]['studies'][row][col])

        col_labels = [f'{all_compounds[c]} (N={col_count[c]})' for c in range(0, len(all_compounds))]
        print(f'col_labels = {col_labels}')
        col_labels = [f'{all_compounds[c]} (N={len(col_studies[c])})' for c in range(0, len(all_compounds))]
        print(f'col_labels = {col_labels}')

if __name__ == "__main__":
    main()
