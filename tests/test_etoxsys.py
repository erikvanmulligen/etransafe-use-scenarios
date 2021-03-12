'''
This is a module to test what data comes back from eToxSys
'''

from kh.api import KnowledgeHubAPI

def main():
    api = KnowledgeHubAPI()

    socs = {}

    studies = api.eToxSys().getStudiesByCompoundNames(['omeprazole'])
    print(f'#studies:{len(studies)}')
    #print(studies[0])

    findings_per_specimen_organ = {}

    for study in studies:
        if study['FINDING']['finding'] != None and study['FINDING']['finding'] != 'No abnormalities detected' and len(study['FINDING']['finding']) > 0:
            specimenOrgans = api.SemanticService().getSocs(study['FINDING']['specimenOrgan'])
            for specimenOrgan in specimenOrgans:
                if len(specimenOrgan) > 0:
                    finding = study['FINDING']['specimenOrgan']

                    if specimenOrgan not in findings_per_specimen_organ:
                        findings_per_specimen_organ[specimenOrgan] = []
                    if finding not in findings_per_specimen_organ[specimenOrgan]:
                        findings_per_specimen_organ[specimenOrgan].append(finding)

    for specimen_organ in findings_per_specimen_organ:
        print(f'{specimen_organ}: {len(findings_per_specimen_organ[specimen_organ])}')
        for finding in findings_per_specimen_organ[specimen_organ]:
            print('     ' + finding)

    # for specimenOrgan in socs.keys():
    #     specimenOrgan
    #     for finding in socs[specimenOrgan]:
    #         print(f'{specimenOrgan}:{finding}:{socs[specimenOrgan][finding]}')

    # # specific specimen organ and finding
    # for study in studies:
    #     for specimenOrgan in api.SemanticService().getSocs(study['FINDING']['specimenOrgan']):
    #         if specimenOrgan == 'Gastrointestinal disorders':
    #             print(f'Gastrointestinal disorders({study["FINDING"]["specimenOrgan"]}):{study["FINDING"]["finding"]}')

if __name__ == "__main__":
    main()

