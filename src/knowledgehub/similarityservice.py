"""
Created on Aug 28, 2020

@author: mulligen
"""
import json
import requests
import urllib3
import time


class SimilarityService:
    
    def __init__(self, api, base):
        urllib3.disable_warnings()
        self.api = api
        self.base = base
        self.service = self.base + '/flame.kh.svc/api/v1/'
        self.space = 'faerspa_morganFP'
        self.headers = {"Authorization": f"Bearer {self.api.get_token()}"}

    def ready(self):
        r = requests.get(self.service + 'ready', verify=False, headers=self.headers)
        return r.status_code == 200

    def get(self, smile, nr_results=10, cutoff=0.5):
        url = self.service + 'search/space/' + self.space + '/version/0/smiles?numsel=' + str(nr_results) + '&cutoff=' + str(cutoff)
        r = requests.put(verify=False, url=url, headers=self.headers, data={'SMILES': smile})

        result = []

        # get the results from the backend
        if r.status_code == 200:
            search_id = r.text.replace('"', '')

            while True:
                r2 = requests.get(self.service + 'smanage/search/' + search_id, verify=False, headers=self.headers)
                if r2.status_code == 200:
                    obj = json.loads(r2.text)
                    if obj != None:
                        if ('search_results' in obj) and (len(obj['search_results']) == 1):
                            search_result = obj['search_results'][0]
                            if 'obj_nam' in search_result:
                                for i in range(len(search_result['obj_nam'])):
                                    result.append({'name': search_result['obj_nam'][i],
                                                   'smiles': search_result['SMILES'][i],
                                                   'distance': '{:.4f}'.format(search_result['distances'][i])})
                    return result
                elif r2.status_code == 500 or r2.status_code == 404 or r2.status_code == 405:
                    # wait a few seconds before trying next time
                    time.sleep(1)
                else:
                    print(f"failed getting results for {search_id}:{r2.status_code}")
                    return result
        else:
            print('request failed:' + str(r.status_code) + ', msg:' + r.text)
            return result


    def setSpace(self, space):
        self.space = space

    def spaces(self):
        r = requests.get(self.service + 'smanage/spaces', verify=False, headers=self.headers)
        return r.status_code == 200

