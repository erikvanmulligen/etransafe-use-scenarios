import json
import requests
import urllib3


class PrimitiveAdapter:
    endpoint = None
    api = None

    def __init__(self, api, endpoint):
        urllib3.disable_warnings()
        self.api = api
        self.api = api
        self.endpoint = endpoint

    def get_token(self):
        return self.api.get_token()

    def index(self, conceptCode):
        json_data = {
            "searchConcept": None,
            "filter": {
                "criteria": [
                    [
                        {
                            "field": {
                                "dataClassKey": "COMPOUND",
                                "name": "name"
                            },
                            "primitiveType": "String",
                            "comparisonOperator": "EQUALS",
                            "caseSensitive": False,
                            "values": [
                                {
                                    "value": "terbinafine"
                                }
                            ]
                        }
                    ]
                ]
            },
            "selectedFields": [
                {
                    "dataClassKey": "FINDING",
                    "names": [
                        "id",
                        "compoundIdentifier",
                        "name",
                        "inchi",
                        "inchiKey",
                        "smiles",
                        "confidentiality",
                        "organisation",
                        "createdDate",
                        "modifiedDate"
                    ]
                }
            ],
            "sortFields": [
                {
                    "field": {
                        "dataClassKey": "COMPOUND",
                        "name": "id"
                    },
                    "order": "ASC"
                }
            ],
            "Offset": 0,
            "Limit": 100
        }

        r = requests.post(self.endpoint + 'query', verify=False, headers={"Authorization": f"Bearer {self.get_token()}"}, json=json_data)

        if r.status_code == 200:
            return json.loads(r.text)
        else:
            print(f"Cannot search in {self.endpoint}: {r.status_code}")
            return None

    #
    # retrieve all unique compounds using the data endpoint
    #
    def getAllCompounds(self):
        result = []

        r = requests.get(self.endpoint + 'count', verify=False, params={'dataClassKey': 'COMPOUND'}, headers={"Authorization": f"Bearer {self.get_token()}"})
        if r.status_code == 200:
            for offset in range(0, int(r.text), 1000):
                r = requests.get(self.endpoint + 'data', params={'dataClassKey': 'COMPOUND', 'limit': 1000, 'offset': offset}, verify=False, headers={"Authorization": f"Bearer {self.get_token()}"})

                if r.status_code == 200:
                    for compound in json.loads(r.text):
                        result.append(compound)
                else:
                    print(f"Cannot retrieve compoundIds from {self.endpoint}: {r.status_code}")

        return result

    #
    # retrieve all adverse events using the data endpoint
    # Mon 5 april: added the reconnect to handle expiration of a token with long running tasks.
    #
    def getAllFindings(self):
        result = []
        while True:
            r = requests.get(self.endpoint + 'count', verify=False, params={'dataClassKey': 'FINDING'}, headers={"Authorization": f"Bearer {self.get_token()}"})
            if r.status_code == 200:
                for offset in range(0, int(r.text), 1000):
                    print(f'retrieving records {offset}-{offset+1000}...')
                    retry = True
                    while retry:
                        r = requests.get(self.endpoint + 'data', params={'dataClassKey': 'FINDING', 'limit': 1000, 'offset': offset}, verify=False, headers={"Authorization": f"Bearer {self.get_token()}"})
                        if r.status_code == 200:
                            for finding in json.loads(r.text):
                                result.append(finding)
                            retry = False
                        elif r.status_code == 401:
                            self.api.reconnect()
                        else:
                            print(f"Cannot retrieve findings from {self.endpoint}: {r.status_code}")
                break
            elif r.status_code == 401:
                self.api.reconnect()

        return result
    # 
    #  retrieve the compound identifiers from the COMPOUND index using the names 
    #  as values. Repeat the query as long as we get limit records
    #
    def getCompoundIdsByNames(self, names):
        result = [];

        query = {
            "searchConcept": None,
            "filter": {
                "criteria": [
                    [
                        {
                            "field": {
                                "dataClassKey": "COMPOUND",
                                "name": "name"
                            },
                            "primitiveType": "String",
                            "comparisonOperator": "IN",
                            "caseSensitive": False,
                            "values": []
                        }
                    ]
                ]
            },
            "selectedFields": [
                {
                    "dataClassKey": "COMPOUND",
                    "names": [
                        "id"
                    ]
                }
            ]
        }

        for name in names:
            query['filter']['criteria'][0][0]['values'].append({'value': name})

        query['offset'] = 0
        query['limit'] = 100
        while True:
            r = requests.post(self.endpoint + 'query', verify=False, headers={"Authorization": f"Bearer {self.get_token()}"}, json=query)

            if r.status_code == 200:
                response = json.loads(r.text)
                data = response['resultData']['data']
                for compound in data:
                    compound_id = compound['COMPOUND']['id']
                    if compound_id not in result:
                        result.append(compound_id)
                nr_records = len(data)
            elif r.status_code == 401:
                self.api.reconnect()
                continue
            else:
                print(f"Cannot retrieve compoundIds from {self.endpoint}: {r.status_code}")
                nr_records = 0

            if nr_records < query['limit']:
                break
            else:
                query['offset'] += query['limit']

        return result

    def getStudiesByCompoundNames(self, compoundNames):
        result = []

        compound_ids = self.getCompoundIdsByNames(compoundNames)

        if len(compoundNames) > 0:
            query = {"searchConcept": {
                "concepts": None,
                "targetConceptGroups": None
            }, "filter": {
                "criteria": [
                    [
                        {
                            "field": {
                                "dataClassKey": "COMPOUND",
                                "name": "id"
                            },
                            "primitiveType": "Integer",
                            "comparisonOperator": "IN",
                            "values": []
                        }
                    ]
                ]
            }, "selectedFields": [
                {
                    "dataClassKey": "FINDING",
                    "names": [
                        # "id",
                        "specimenOrgan",
                        "finding",
                        "findingCode",
                        "findingVocabulary"
                    ]
                },
                {
                    "dataClassKey": "COMPOUND",
                    "names": [
                        "name",
                        "compoundIdentifier",
                    ]
                }
            ], 'offset': 0, 'limit': 1000}

            for compoundId in compound_ids:
                query['filter']['criteria'][0][0]['values'].append({'value': compoundId})

            while True:
                r = requests.post(self.endpoint + 'query', verify=False, headers={"Authorization": f"Bearer {self.get_token()}"}, json=query)

                if r.status_code == 200:
                    response = json.loads(r.text)
                    if query['offset'] == 0:
                        total = response['resultData']['total']

                    record_count = len(response['resultData']['data'])
                    for record in response['resultData']['data']:
                        record['source'] = response['origin']
                        result.append(record)
                elif r.status_code == 401:
                    self.api.reconnect()
                    continue
                else:
                    record_count = 0

                if record_count < query['limit']:
                    break

                query['offset'] += query['limit']
            return result
        else:
            print(f"No compound names specified for searching {self.endpoint}")
            return None

    #
    # This method retrieves compounds from the database by its identifier
    # 
    def getStudiesByCompoundIds(self, compound_ids):
        result = []

        if len(compound_ids) > 0:
            query = {"searchConcept": {
                "concepts": None,
                "targetConceptGroups": None
            }, "filter": {
                "criteria": [
                    [
                        {
                            "field": {
                                "dataClassKey": "COMPOUND",
                                "name": "compoundIdentifier"
                            },
                            "primitiveType": "String",
                            "comparisonOperator": "IN",
                            "caseSensitive": "True",
                            "values": []
                        }
                    ]
                ]
            }, "selectedFields": [
                {
                    "dataClassKey": "FINDING",
                    "names": [
                        "specimenOrgan",
                        "finding",
                        "findingCode",
                        "findingVocabulary"
                    ]
                },
                {
                    "dataClassKey": "COMPOUND",
                    "names": [
                        "name",
                        "compoundIdentifier",
                    ]
                }
            ], 'offset': 0, 'limit': 1000}

            for compound_id in compound_ids:
                query['filter']['criteria'][0][0]['values'].append({'value': compound_id})

            while True:
                r = requests.post(self.endpoint + 'query', verify=False, headers={"Authorization": f"Bearer {self.get_token()}"}, json=query)

                if r.status_code == 200:
                    response = json.loads(r.text)
                    if query['offset'] == 0:
                        total = response['resultData']['total']

                    record_count = len(response['resultData']['data'])
                    for record in response['resultData']['data']:
                        record['source'] = response['origin']
                        result.append(record)
                elif r.status_code == 401:
                    self.api.reconnect()
                    continue
                else:
                    record_count = 0

                if record_count < query['limit']:
                    break

                query['offset'] += query['limit']
            return result
        else:
            print(f"Cannot search in {self.endpoint}")
            return None