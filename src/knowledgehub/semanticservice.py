# (C) 2020, Erasmus Medical Center Rotterdam, The Netherlands
# dept. of Medical Informatics
# Erik van Mulligen
#
# version: 1.0
#
# This code interacts with the semantic service on the knowledge hub


import json
import requests
import time
import urllib3
import urllib.parse


class SemanticService:
    service = None
    token = None
    headers = None
    session = None
    count = None
    elapsed = None

    def __init__(self, api, base):
        urllib3.disable_warnings()
        self.api = api
        self.service = base + "/api/semanticservice/v1/"
        self.session = requests.Session()

    def __get_token(self):
        return self.api.get_token()

    def lookup(self, inputTerm, vocabularies):
        params = {'query': inputTerm, 'vocabularies': vocabularies, 'count': 20}
        tries = 0
        while tries < 5:
            r = self.session.get(self.service + "concept/lookup?" + urllib.parse.urlencode(params), verify=False, headers={"Authorization": f"Bearer {self.__get_token()}"})
            if r.status_code == 200:
                return json.loads(r.text)
            elif r.status_code == 401:
                self.api.reconnect()
            else:
                time.sleep(2)
                tries += 1
        return None

    def normalize(self, term, vocabularies, nonpreferred=True):
        vocstr = ''
        for vocabulary in vocabularies:
            vocstr += '&vocabularies=' + vocabulary
        params = {'term': term, 'nonpreferred': nonpreferred}
        tries = 0
        while tries < 5:
            r = self.session.get(self.service + 'concept/normalize?' + urllib.parse.urlencode(params) + vocstr, verify=False, headers={"Authorization": f"Bearer {self.__get_token()}"})
            if r.status_code == 200:
                return json.loads(r.text)
            elif r.status_code == 401:
                self.api.reconnect()
            else:
                time.sleep(2)
                tries += 1
        return None

    def concept(self, conceptId):
        r = self.session.get(self.service + 'concept/' + conceptId, verify=False, headers={"Authorization": f"Bearer {self.__get_token()}"})
        if r.status_code == 200:
            return json.loads(r.text)
        elif r.status_code == 401:
            self.api.reconnect()
        else:
            return None

    '''
        This method first creates a list of all unique findings and subsequently passes them per chunks to the backend
    '''
    def getSocs(self, studies):
        finding2soc = {}
        for study in studies:
            study['FINDING']['__key'] = None
            if study['FINDING']['finding'] != 'No abnormalities detected':
                key = self.__getKey(study['FINDING'])
                study['FINDING']['__key'] = key
                if key is not None and key not in finding2soc:
                    finding2soc[key] = None

        # translate the findings to socs
        size = 100
        keys = list(finding2soc.keys())
        for i in range(0, len(keys), size):
            conceptCodes = []
            conceptNames = []
            for key in keys[i:i+size]:
                code_name, value = key.split('=', 2)
                if code_name == 'conceptCode':
                    conceptCodes.append(value)
                elif code_name == 'conceptName':
                    conceptNames.append(value)
                else:
                    print('non existing concept code/name')

            concepts = self.__getSocMap('conceptCodes=' + ','.join(conceptCodes) + '&conceptNames=' + ','.join(conceptNames))
            if concepts is not None:
                for concept in concepts:
                    if len(concept['mapping']) > 0:
                        soc = concept['mapping'][0]
                        if 'conceptCode='+concept['conceptCode'] in keys[i:i+size]:
                            finding2soc['conceptCode='+concept['conceptCode']] = soc['conceptName']
                        elif 'conceptName='+concept['conceptName'] in keys[i:i+size]:
                            finding2soc['conceptName='+concept['conceptName']] = soc['conceptName']
                    else:
                        finding2soc['conceptName=' + concept['conceptName']] = 'Other'
            else:
                print(f'no mappings found for {",".join(conceptCodes)}/{",".join(conceptNames)}')

        # add to each study the corresponding soc
        for study in studies:
            study['FINDING']['__soc'] = finding2soc[study['FINDING']['__key']] if study['FINDING']['__key'] in finding2soc and finding2soc[study['FINDING']['__key']] is not None else 'Other'

    @staticmethod
    def __getKey(finding):
        if 'specimenOrganCode' in finding and finding['specimenOrganVocabulary'] == 'MA':
            return ('conceptCode=' + finding['specimenOrganCode']) if 'specimenOrganCode' in finding and finding['specimenOrganCode'] is not None else None
        elif 'findingVocabulary' in finding and finding['findingVocabulary'] == 'MedDRA' and 'findingCode' in finding:
            return 'conceptCode=' + finding['findingCode']
        elif 'finding' in finding:
            return ('conceptName=' + finding['finding']) if finding['finding'] is not None else None
        else:
            return None

    '''
        Retrieve the system organ class for a concept code or a MA or PT concept name
    '''
    def getSoc(self, finding):
        key = self.__getKey(finding)
        return self.__getSocMap(key) if key is not None else None

    def __getSocMap(self, key):
        for tries in range(0, 5):
            r = self.session.get(f'{self.service}concept/map/soc?{key}', verify=False, headers={'Authorization': f'Bearer {self.__get_token()}'})
            if r.status_code == 200:
                return json.loads(r.text)
            elif r.status_code == 401:
                self.api.reconnect()
            else:
                break
        return None

    def getConcept(self, concept_id=None, concept_code=None, concept_name=None, vocabularies=[]):
        if concept_id is not None:
            r = self.session.get(f'{self.service}concept/{concept_id}', verify=False, headers={"Authorization": f"Bearer {self.__get_token()}"})
            if r.status_code == 200:
                obj = json.loads(r.text)
                return obj['concept']
            elif r.status_code == 401:
                self.api.reconnect()
            else:
                return None
        elif concept_name is not None:
            objs = self.normalize(concept_name, vocabularies, nonpreferred=False)
            if len(objs['concepts']) >= 1:
                return objs['concepts'][0]
            else:
                return None
        elif concept_code is not None:
            return None

    def expand(self, concept_id=None, concept_code=None, concept_name=None, parent_levels=None, child_levels=None, vocabularies=[]):
        # first translate code to concept id
        if concept_id is not None:
            concept = self.getConcept(concept_id=concept_id)
        elif concept_code is not None:
            concept = self.getConcept(concept_code=concept_code)
        elif concept_name is not None:
            concept = self.getConcept(concept_name=concept_name, vocabularies=vocabularies)
        else:
            concept = None

        if concept is not None:
            while True:
                params = {
                    'parentLevels': parent_levels if parent_levels is not None else '',
                    'childLevels': child_levels if child_levels is not None else '',
                    'vocabularies': ','.join(vocabularies)
                }
                r = self.session.get(f'{self.service}concept/{concept["conceptId"]}/expand?' + urllib.parse.urlencode(params), verify=False, headers={"Authorization": f"Bearer {self.__get_token()}"})
                if r.status_code == 200:
                    obj = json.loads(r.text)
                    return obj['concepts']
                elif r.status_code == 401:
                    self.api.reconnect()
