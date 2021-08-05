#
# Copyright (C) 2021, dept of Medical Informatics, Erasmus University Medical Center, Rotterdam, The Netherlands
# Erik M. van Mulligen, e.vanmulligen@erasmusmc.nl
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Erasmus University Medical Center, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import argparse
from pprint import pprint
from src.knowledgehub.api import KnowledgeHubAPI


def main():
    parser = argparse.ArgumentParser(description='Process parameters for retrieving data from primitive adapters')
    parser.add_argument('-username', required=True, help='username')
    parser.add_argument('-password', required=True, help='password')
    parser.add_argument('-pa', required=True, help='primitive adapter')
    args = parser.parse_args()

    api = KnowledgeHubAPI(server='DEV', client_secret='3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab')
    api.login(args.username, args.password)

    for service in api.Services().get():
        print(service['title'])

    print(api.SemanticService().expand(concept_name='edema', vocabularies=[]))

    smiles = api.ChemistryService().getSMILESByName('omeprazole')
    print(f'smiles:{smiles}')

    similar_compounds = api.SimilarityService().get(smiles, nr_results=20, cutoff=0.5)
    print(f'similar compounds:{similar_compounds}')
    smiles = [similar_compound['smiles'] for similar_compound in similar_compounds]
    print(f'smiles:{smiles}')
    names = [similar_compound['name'] for similar_compound in similar_compounds]
    print(f'names:{names}')

    studies = api.Medline().getStudiesBySMILES(smiles) + \
              api.Faers().getStudiesBySMILES(smiles) + \
              api.ClinicalTrials().getStudiesBySMILES(smiles) + \
              api.eToxSys().getStudiesByCompoundNames(names)

    study_count = {}
    for study in studies:
        if study['source'] not in study_count:
            study_count[study['source']] = 0
        study_count[study['source']] += 1

    print(study_count)

    socs = {}

    # traverse all studies and collect the system organ classes; keep track of the # studies per class

    api.SemanticService().getSocs(studies)

    socs_dict = {}
    for study in studies:
        soc = study['FINDING']['__soc']
        if soc is not None:
            if soc not in socs_dict:
                socs_dict[soc] = study['FINDING']['count']
            else:
                socs_dict[soc] += study['FINDING']['count']
    pprint(socs_dict)


if __name__ == "__main__":
    main()
