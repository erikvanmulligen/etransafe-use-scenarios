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
    etoxSocs = {
        'Adrenal gland': 'Endocrine disorders',
        'Epididymis': 'Reproductive system and breast disorders',
        'Gallbladder': 'Hepatobiliary disorders',
        'Kidney': 'Renal and urinary disorders',
        'Liver': 'Hepatobiliary disorders',
        'Lung': 'Respiratory, thoracic and mediastinal disorders',
        'Prostate gland': 'Reproductive system and breast disorders',
        'Stomach': 'Gastrointestinal disorders',
        'Testis': 'Endocrine disorders',
        'Thyroid gland': 'Endocrine disorders',
        'Eye': 'Eye disorders',
        'Ovary': 'Reproductive system and breast disorders',
        'Pituitary gland': 'Endocrine disorders',
        'Salivary gland': 'Gastrointestinal disorders',
        'Skin': 'Skin and subcutaneous tissue disorders',
        'Urinary bladder': 'Renal and urinary disorders',
        'Heart': 'Cardiac disorders',
        'Brain': 'Nervous system disorders',
        'Spleen': 'Blood and lymphatic system disorders',
        'Thymus': 'Blood and lymphatic system disorders',
        'Uterus': 'Reproductive system and breast disorders',
        'Bone marrow': 'Investigations',
        'Axillary lymph node': 'Blood and lymphatic system disorders',
        'Mesenteric lymph node': 'Blood and lymphatic system disorders',
        'Trachea': 'Respiratory, thoracic and mediastinal disorders',
        'Pancreas': 'Gastrointestinal disorders',
        'Tongue': 'Gastrointestinal disorders',
        'Submandibular gland': 'Gastrointestinal disorders',
        'Jejunum': 'Gastrointestinal disorders',
        'Cervical lymph node': 'Blood and lymphatic system disorders',
        'Parathyroid gland': 'Endocrine disorders',
        'Stomach pyloric antrum': 'Gastrointestinal disorders',
        'Vagina': 'Reproductive system and breast disorders',
        'Mammary gland': 'Reproductive system and breast disorders',
        'Female reproductive gland/organ': 'Reproductive system and breast disorders',
        'Colon': 'Gastrointestinal disorders',
        'Jugular vein': 'Vascular disorders',
        'Mediastinal lymph node': 'Respiratory, thoracic and mediastinal disorders',
        'Submandibular lymph node': 'Gastrointestinal disorders',
        'Intestine': 'Gastrointestinal disorders',
        'Muscle organ': 'Musculoskeletal and connective tissue disorders',
        'Ileum': 'Gastrointestinal disorders',
        'Aorta': 'Vascular disorders',
        'Femur': 'Musculoskeletal and connective tissue disorders',
        'Sternum': 'Musculoskeletal and connective tissue disorders',
        'Cecum': 'Gastrointestinal disorders',
        'Duodenum': 'Endocrine disorders',
        'Rectum': 'Gastrointestinal disorders',
        'Lacrimal gland': 'Eye disorders',
        'Larynx': 'Respiratory, thoracic and mediastinal disorders',
        'Set of skeletal muscles': 'Musculoskeletal and connective tissue disorders',
        'Sciatic nerve': 'Nervous system disorders',
        'Esophagus': 'Gastrointestinal disorders',
        'Parotid gland': 'Gastrointestinal disorders',
        'Sublingual gland': 'Gastrointestinal disorders',
        'Spinal cord': 'Nervous system disorders',
        'Uterine cervix': 'Reproductive system and breast disorders',
        'Lymph node bronchial': 'Blood and lymphatic system disorders',
        'Tail': 'Musculoskeletal and connective tissue disorders',
        'Trunk': 'Musculoskeletal and connective tissue disorders',
        'Stomach body': 'Gastrointestinal disorders',
        'Kidney pelvis': 'Renal and urinary disorders',
        'Kidney tubule': 'Renal and urinary disorders',
        'Kidney interstitium': 'Renal and urinary disorders',
        'Kidney distal tubule': 'Renal and urinary disorders',
        'Kidney proximal tubule': 'Renal and urinary disorders',
        'Product issues': 'Other',
        'Application site': 'Other',
        'Pregnancy, puerperium and perinatal conditions': 'Pregnancy, puerperium and perinatal conditions',
        'Large intestine': 'Gastrointestinal disorders',
        'Small intestine': 'Gastrointestinal disorders',
        'Lymph node': 'Blood and lymphatic system disorders',
    }

    def __init__(self, token, base):
        urllib3.disable_warnings()
        self.token = token
        self.service = base + "/api/semanticservice/v1/"
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def lookup(self, inputTerm, vocabularies):
        params = {'query': inputTerm, 'vocabularies': vocabularies, 'count': 20}
        tries = 0
        while tries < 5:
            r = requests.get(self.service + "concept/lookup?" + urllib.parse.urlencode(params), verify=False, headers=self.headers)
            if r.status_code == 200:
                return json.loads(r.text)
            else:
                time.sleep(2)
                tries += 1
        return None

    def normalize(self, term, vocabularies):
        vocstr = ''
        for vocabulary in vocabularies:
            vocstr += '&vocabularies=' + vocabulary
        params = {'term': term}
        tries = 0
        while tries < 5:
            r = requests.get(self.service + 'concept/normalize?' + urllib.parse.urlencode(params) + vocstr, verify=False, headers=self.headers)
            if r.status_code == 200:
                return json.loads(r.text)
            else:
                time.sleep(2)
                tries += 1
        return None

    def concept(self, conceptId):
        res = str(conceptId)
        print(res)
        r = requests.get(self.service + 'concept/' + res, verify=False, headers=self.headers)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            return None
    
    # map organs to a list of system organ classes if they appear in the dict
    def getSocs(self, organs):
        result = []
        if organs is not None:
            for organ in organs.split('; '):
                if organ in self.etoxSocs:
                    for o in self.etoxSocs[organ].split('; '):
                        result.append(o)
                else:
                    if not organ == 'Excluded term':
                        result.append(organ)
        return result
