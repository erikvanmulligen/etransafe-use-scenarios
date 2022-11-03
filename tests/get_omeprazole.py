from knowledgehub.api import KnowledgeHubAPI
import argparse


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting all data from eToxSys')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    api.login(args.username, args.password)

    compoundName = 'omeprazole'
    smiles = api.ChemistryService().getSMILESByName(compoundName)
    # similar_compounds = api.SimilarityService().get(smiles[0])
    #
    # names = []
    # similarities = []
    #
    # for similar_compound in similar_compounds:
    #     names.append(similar_compound['name'])
    #     smiles.append(similar_compound['smiles'])
    #     similarities.append(similar_compound['distance'])

    # faers_studies = filterStudies(api.Faers().getStudiesBySMILES(smiles))
    # api.SemanticService().getSocs(faers_studies, algorithm='MEDDRAPT2MEDDRASOC')
    # medline_studies = filterStudies(api.Medline().getStudiesBySMILES(smiles))
    # api.SemanticService().getSocs(medline_studies, algorithm='MEDDRAPT2MEDDRASOC')
    # ct_studies = filterStudies(api.ClinicalTrials().getStudiesBySMILES(smiles))
    # api.SemanticService().getSocs(ct_studies, algorithm='MEDDRAPT2MEDDRASOC')
    # dailymed_studies = filterStudies(api.DailyMed().getStudiesBySMILES(smiles))
    # api.SemanticService().getSocs(dailymed_studies, algorithm='MEDDRAPT2MEDDRASOC')
    studies = api.eToxSys().getStudiesByCompoundNames([compoundName])
    etox_studies = filterStudies(studies)
    api.SemanticService().getSocs(etox_studies, algorithm='MA2MEDDRASOC')

    studies = etox_studies
    # studies = faers_studies + medline_studies + ct_studies + dailymed_studies + etox_studies
    print(f'{len(studies)} studies')
    socs = {}

    all_studies = set()
    for study in studies:
        if study['FINDING']['findingVocabulary'] is not None and study['FINDING']['findingCode'] is not None:
            soc = study['FINDING']['__soc']
            if soc not in socs:
                socs[soc] = set()
            socs[soc].add(study['STUDY']['id'])
            all_studies.add(study['STUDY']['id'])

    # for soc in socs:
    #     print(f'{soc}:{len(socs[soc])}')
    # print(f'total: {len(all_studies)}')


def filterStudies(studies):
    return [study for study in studies if study['FINDING']['findingVocabulary'] is not None and study['FINDING']['findingCode'] is not None and study['FINDING']['findingCode'] != 'MC:2000001'
            and ('dose' not in study['FINDING'] or study['FINDING']['dose'] != 0.0)]


if __name__ == "__main__":
    main()