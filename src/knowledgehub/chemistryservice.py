import json
import requests
import urllib3


class ChemistryService:
    endpoint = None
    api = None

    def __init__(self, api, base):
        urllib3.disable_warnings()
        self.api = api
        self.service = base + "/chemistryservice.kh.svc/v1/"

    def get_token(self):
        return self.api.get_token()

    #
    #  retrieve the compound identifiers from the COMPOUND index using the names 
    #  as values. Repeat the query as long as we get limit records
    #
    def getCompoundByName(self, name):
        retries = 0
        while retries < 5:
            retries += 1
            r = requests.get(f'{self.service}name_to_structure', verify=False, params={'name': name}, headers={"Authorization": f"Bearer {self.get_token()}"})
            if r.status_code == 200:
                return r.json()['result'].replace('(\'', '').replace('\')', '').split("', '")[1]
            elif r.status_code == 401:
                self.api.reconnect()
                continue
            else:
                print(f"Cannot retrieve compoundIds from {self.service}: {r.status_code}")
                return None

    def getSMILESByName(self, name):
        return [self.getCompoundByName(name)]
