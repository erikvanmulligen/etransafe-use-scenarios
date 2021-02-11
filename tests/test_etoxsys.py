'''
This is a module to test what data comes back from eToxSys
'''

from kh.api import KnowledgeHubAPI

def main():
    api = KnowledgeHubAPI()

    socs = {}

    studies = api.eToxSys().getStudiesByCompoundNames(['omeprazole'])
    print(f'#studies:{len(studies)}')
    for study in studies:
        source = study['source']
        if source != 'eTOXsys' or study['FINDING']['finding'] != 'No abnormalities detected':
            specimenOrgans = api.SemanticService().getSocs(study['FINDING']['specimenOrgan'])
            for specimenOrgan in specimenOrgans:
                if len(specimenOrgan) > 0:
                    if specimenOrgan not in socs:
                        socs[specimenOrgan] = {}
                    else:
                        finding = study['FINDING']['finding']
                        if finding not in socs[specimenOrgan]:
                            socs[specimenOrgan][finding] = 1
                        else:
                            socs[specimenOrgan][finding] += 1

    # for specimenOrgan in socs.keys():
    #     specimenOrgan
    #     for finding in socs[specimenOrgan]:
    #         print(f'{specimenOrgan}:{finding}:{socs[specimenOrgan][finding]}')

    # specific specimen organ and finding
    for study in studies:
        for specimenOrgan in api.SemanticService().getSocs(study['FINDING']['specimenOrgan']):
            if specimenOrgan == 'Gastrointestinal disorders':
                print(f'Gastrointestinal disorders({study["FINDING"]["specimenOrgan"]}):{study["FINDING"]["finding"]}')

if __name__ == "__main__":
    main()

