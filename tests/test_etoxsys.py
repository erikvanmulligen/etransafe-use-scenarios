'''
This is a module to test what data comes back from eToxSys
'''

from knowledgehub.api import KnowledgeHubAPI
import argparse


def main():
    parser = argparse.ArgumentParser(description='Process parameters for collecting findings from primitive adapter')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI()
    api.login(args.username, args.password)

    socs = {}

    #studies = api.eToxSys().getStudiesByCompoundNames(['omeprazole'])
    studies = api.eToxSys().getStudiesByCompoundIds(['COc1ccc2[nH]c([S+]([O-])Cc3ncc(C)c(OC)c3C)nc2c1'])
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

