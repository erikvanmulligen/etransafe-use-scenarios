import json
import requests
import urllib3


class PrimitiveAdapter:
    token = None
    endpoint = None

    def __init__(self, token, endpoint):
        urllib3.disable_warnings()
        self.token = token
        self.endpoint = endpoint

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

        r = requests.post(self.endpoint,
                          verify=False,
                          headers={
                              "Authorization": f"Bearer {self.token}"
                          },
                          json=json_data
                          )

        if r.status_code == 200:
            return json.loads(r.text)
        else:
            print(f"Cannot search in {self.endpoint}: {r.status_code}")
            return None

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
            r = requests.post(self.endpoint,
                              verify=False,
                              headers={
                                  "Authorization": f"Bearer {self.token}"
                              },
                              json=query
                              )

            if r.status_code == 200:
                response = json.loads(r.text)
                data = response['resultData']['data']
                for compound in data:
                    compoundId = compound['COMPOUND']['id']
                    if compoundId not in result:
                        result.append(compoundId)
                nrrecords = len(data)
            else:
                print(f"Cannot retrieve compoundIds from {self.endpoint}: {r.status_code}")
                nrrecords = 0

            if nrrecords < query['limit']:
                break
            else:
                query['offset'] += query['limit']

        return result

    def getStudiesByCompoundNames(self, compoundNames):
        result = []

        compoundIds = self.getCompoundIdsByNames(compoundNames)

        if len(compoundNames) > 0:
            query = {
                "searchConcept": {
                    "concepts": None,
                    "targetConceptGroups": None
                },
                "filter": {
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
                },
                "selectedFields": [
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
                ]
            }

            query['offset'] = 0;
            query['limit'] = 1000;
            for compoundId in compoundIds:
                query['filter']['criteria'][0][0]['values'].append({'value': compoundId})

            while True:
                r = requests.post(self.endpoint,
                                  verify=False,
                                  headers={
                                      "Authorization": f"Bearer {self.token}"
                                  },
                                  json=query
                                  )

                if r.status_code == 200:
                    response = json.loads(r.text)
                    if query['offset'] == 0:
                        total = response['resultData']['total']

                    nrrecords = len(response['resultData']['data'])
                    for record in response['resultData']['data']:
                        record['source'] = response['origin']
                        result.append(record)

                else:
                    nrrecords = 0

                if nrrecords < query['limit']:
                    break

                query['offset'] += query['limit']
            return result
        else:
            print(f"No compound names specified for searching {self.endpoint}")
            return None

    #
    # This method retrieves compounds from the database by its identifier
    # 
    def getStudiesByCompoundIds(self, compoundIds):
        result = []

        if len(compoundIds) > 0:
            query = {
                "searchConcept": {
                    "concepts": None,
                    "targetConceptGroups": None
                },
                "filter": {
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
                },
                "selectedFields": [
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
                ]
            }

            query['offset'] = 0;
            query['limit'] = 1000;
            for compoundId in compoundIds:
                query['filter']['criteria'][0][0]['values'].append({'value': compoundId})

            while True:
                r = requests.post(self.endpoint,
                                  verify=False,
                                  headers={
                                      "Authorization": f"Bearer {self.token}"
                                  },
                                  json=query
                                  )

                if r.status_code == 200:
                    response = json.loads(r.text)
                    if query['offset'] == 0:
                        total = response['resultData']['total']
                        # print(f'retrieving {total} records');

                    # print(f'retrieving {query["offset"]} of {total} {response["origin"]} records')

                    nrrecords = len(response['resultData']['data'])
                    for record in response['resultData']['data']:
                        record['source'] = response['origin']
                        result.append(record)

                else:
                    nrrecords = 0

                if nrrecords < query['limit']:
                    break

                query['offset'] += query['limit']
            return result
        else:
            print(f"Cannot search in {self.endpoint}")
            return None
