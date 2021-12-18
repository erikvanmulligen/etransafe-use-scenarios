# The heatmap for omeprazole and similar compounds shows a large number of HPATH findings in the Other group for the eToxSys database.
# This program tries to list what kind of events are contained
# (C) Erasmus Medical Center Rotterdam, October 2021
# Erik van Mulligen
from knowledgehub.api import KnowledgeHubAPI
import argparse


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
    api.login(args.username, args.password)

    compoundSmile = api.ChemistryService().getSMILESByName('omeprazole')
    similar_compounds = api.SimilarityService().get(compoundSmile[0])

    names = []
    smiles = []
    similarities = []

    if similar_compounds is not None:
        for similar_compound in similar_compounds:
            names.append(similar_compound['name'])
            smiles.append(similar_compound['smiles'])
            similarities.append(similar_compound['distance'])

    studies = filterStudies(api.eToxSys().getStudiesByCompoundNames(names))
    print(f'Found {len(studies)} studies.')
    for study in studies:
        print(study)

    api.SemanticService().getSocs(studies)
    otherStudies = [study for study in studies if study['FINDING']['__soc'] == 'Other']
    print(f'#others:{len(otherStudies)}')


def filterStudies(studies):
    return [study for study in studies if study['FINDING']['findingVocabulary'] is not None and study['FINDING']['findingCode'] is not None and study['FINDING']['findingCode'] != 'MC:2000001' and study['FINDING']['dose'] != 0.0]


if __name__ == "__main__":
    main()