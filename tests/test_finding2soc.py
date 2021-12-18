import argparse
import sys

from src.knowledgehub.api import KnowledgeHubAPI
from pprint import pprint

def main():
    parser = argparse.ArgumentParser(description='Process parameters for retrieving data from primitive adapters')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    #api = KnowledgeHubAPI(server='TEST', client_secret='39c644b3-1f23-4d94-a71f-e0fb43ebd760')
    api.login(args.username, args.password)

    # services = api.Services().get()
    # for service in services:
    #     print(service)

    compoundNames = [
                 'Cloxazolam', 'Cerivastatin', 'Bicalutamide', 'Anastrozole', 'Ulobetasol Propionate',
                 'Picoplatin', 'Vandetanib', 'Letrozole', 'Rosuvastatin', 'Vatalanib', 'Sorafenib', 'TANOMASTAT',
                 'Carvedilol', 'Saquinavir', 'Fluvastatin', 'Oxcarbazepine', 'Nilotinib', 'Fingolimod', 'Imatinib Mesylate',
                 'Ciclosporin', 'Zoledronic acid', 'Tembotrione', 'Isoxaflutole', 'Roaccutan', 'Licarbazepine', 'Rimonabant',
                 'Itraconazole', 'Liarozole', 'Halometasone', 'Doramapimod', 'Denagliptin', 'Triclabendazole', 'Amodiaquine',
                 'Clarithromycin', 'Telithromycin', 'Amiodarone', 'Piboserod', 'Levofloxacin', 'Riluzole', 'Osanetant',
                 'Aminoglutethimide', 'Netupitant'
                ]

    compounds = []
    for compoundName in compoundNames:
        compoundSmile = api.ChemistryService().getSMILESByName(compoundName)
        if len(compoundSmile) == 1 and compoundSmile[0] is not None:
            compounds.append({'name': compoundName.lower(), 'smiles': compoundSmile[0]})
        else:
            print(f'{compoundName} no smiles')

    # compounds = []
    # for compoundName in compoundNames:
    #     compounds.append({'name': compoundName.lower(), 'smiles': None})

    medline_studies = []
    ct_studies = []
    faers_studies = []
    etoxsys_studies = []

    for c in compounds:
        medline_studies = api.Medline().getStudiesBySMILES([c['smiles']])
        medline_study_count = count_distinct_findings(medline_studies) if medline_studies is not None else 0
        faers_studies = api.Faers().getStudiesBySMILES([c['smiles']])
        faers_study_count = count_distinct_findings(faers_studies) if faers_studies is not None else 0
        ct_studies = api.ClinicalTrials().getStudiesBySMILES([c['smiles']])
        ct_study_count = count_distinct_findings(ct_studies) if ct_studies is not None else 0
        etoxsys_studies = api.eToxSys().getStudiesByCompoundNames([c['name']])
        et_study_count = count_distinct_findings(etoxsys_studies) if etoxsys_studies is not None else 0
        total = medline_study_count + faers_study_count + ct_study_count + et_study_count
        print(f'{c["name"]}:medline:{medline_study_count}, faers:{faers_study_count}, ct:{ct_study_count}, etoxsys:{et_study_count}, total:{total}')

    exit()

    studies = \
              medline_studies + \
              faers_studies + \
              ct_studies + \
              etoxsys_studies
    study_count = {'medline': len(medline_studies),
                   'ClinicalTrials': len(ct_studies),
                   'FAERS': len(faers_studies),
                   'eToxSys': len(etoxsys_studies)}
    print(study_count)

    socs = {}

    socs_dict = {}
    for study in studies:
        soc = study['FINDING']['__soc']
        if soc is not None:
            if soc not in socs_dict:
                socs_dict[soc] = study['FINDING']['count']
            else:
                socs_dict[soc] += study['FINDING']['count']
    pprint(socs_dict)

def count_distinct_findings(studies):
    findings = {}
    for study in studies:
        if 'FINDING' in study:
            findings[study['FINDING']['findingCode']] = True

    return len(findings)


if __name__ == "__main__":
    main()
