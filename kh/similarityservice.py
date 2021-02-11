"""
Created on Aug 28, 2020

@author: mulligen
"""
import json
import requests
import urllib3
import os
import time
import tempfile
from rdkit import Chem


class SimilarityService:
    
    def __init__(self, token, base):
        urllib3.disable_warnings()
        self.token = token
        self.base = base
        self.service = self.base + '/flame.kh.svc/api/v1/'
        #self.space = 'clinicaltrialspa_RDKit_properties'
        self.space = 'faerspa_RDKit_properties'
        self.headers = {
            "Authorization": f"Bearer {self.token}",
        }

    def ready(self):
        r = requests.get(self.service + 'ready', verify=False, headers=self.headers)
        return r.status_code == 200
        
    def get(self, smile, nr_results=10, cutoff=0.7):
        fo = tempfile.NamedTemporaryFile()
        m = Chem.MolFromSmiles(smile)
        w = Chem.SDWriter(fo.name)
        w.write(m)
        w.flush()
        w.close()

        url = self.service + 'search/space/' + self.space + '/version/0?numsel=' + str(nr_results) + '&cutoff=' + str(cutoff)
        files = {
            'SDF': (os.path.basename(fo.name), open(fo.name, 'rb'))
        }

        r = requests.put(verify=False, url=url, headers=self.headers, files=files)

        # get the results from the backend
        if r.status_code == 200:
            search_id = r.text.replace('"', '')
            
            while True:
                r2 = requests.get(self.service + 'smanage/search/' + search_id, verify=False, headers=self.headers)
                if r2.status_code == 200:
                    return json.loads(r2.text)
                elif r2.status_code == 500:
                    # wait a few seconds before trying next time
                    time.sleep(2)
                else:
                    print(f"failed getting results for {search_id}:{r2.status_code}")
                    return None
        else:
            print('request failed:' + str(r.status_code) + ', msg:' + r.text)
            return None

    def setSpace(self, space):
        self.space = space

    def spaces(self):
        r = requests.get(self.service + 'smanage/spaces', verify=False, headers=self.headers)
        return r.status_code == 200

