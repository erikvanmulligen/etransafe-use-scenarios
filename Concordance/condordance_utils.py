import json
import os

def getClinicalDatabases(api):
    return {
        'ClinicalTrials': api.ClinicalTrials(),
        'Medline': api.Medline(),
        # 'Faers': api.Faers(),
        'DailyMed': api.DailyMed()
    }

def getPreclinicalDatabases(api):
    return {
        'eToxSys': api.eToxSys()
    }


def getSocDrugFindings(db, soc, drugInfo, databases, table):
    ids = []
    for database in databases:
        if database in drugInfo and drugInfo[database] is not None:
            ids += drugInfo[database]

    if len(ids) > 0:
        return getAllFindings(db=db, table=table, where=f'where SOC="{soc}" and mapped > -1 and id in ({",".join([str(id) for id in ids])})')
    else:
        return []


def getAllFindings(db, table, where):
    cursor = db.cursor()
    cursor.execute("SELECT distinct findingCode, specimenOrganCode, SOC, mapped FROM " + table + " " + where)
    return [{'findingCode': r[0], 'specimenOrganCode': r[1], 'SOC': r[2], 'mapped': r[3]} for r in cursor.fetchall()]


def map_soc(soc):
    return soc if soc is not None else 'other'


def create_soc(groups, soc):
    if soc not in groups:
        groups[soc] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}


def getDrugs(api, filename):
    if filename is None:
        drugs = getDrugsMapping(api)
    else:
        if os.path.isfile(filename):
            with open(filename, 'r') as drug_file:
                drugs = json.loads(drug_file.read())
        else:
            drugs = getDrugsMapping(api)
            with open(filename, 'w') as drug_file:
                drug_file.write(json.dumps(drugs))
    return drugs

def normalizePreclinicalFields(records):
    return [{'findingCode':r[0], 'specimenOrganCode': r[1]} for r in records]


def getSocs(db, tables):
    result = []
    cursor = db.cursor()
    for table in tables:
        cursor.execute("SELECT distinct SOC FROM " + table)
        result += [soc[0] for soc in cursor.fetchall()]
    return list(set(result))


def getDrugsMapping(api, ClinicalDatabases, PreclinicalDatabases):
    result = {}
    clinicalCompounds = getCompounds(api, ClinicalDatabases)
    preclinicalCompounds = getCompounds(api, PreclinicalDatabases)

    # iterate over the clinical and preclinical compounds and match them om inchiKey
    for clinicalCompound in clinicalCompounds:
        for preclinicalCompound in preclinicalCompounds:
            if (clinicalCompound['inchiKey'] is not None) and (clinicalCompound['inchiKey'] == preclinicalCompound['inchiKey']):
                inchiKey = clinicalCompound['inchiKey']
                if inchiKey not in result:
                    result[inchiKey] = {
                        'inchiKey': inchiKey,
                        'clinicalName': clinicalCompound['name'],
                        'preclinicalName': preclinicalCompound['name']
                    }
                    result[inchiKey][preclinicalCompound['source']] = preclinicalCompound['findingIds']
                result[inchiKey][clinicalCompound['source']] = clinicalCompound['findingIds']
    return result


def getCompounds(api, databases):
    compounds = []

    for database in databases:
        db_compounds = databases[database].getAllCompounds();
        for compound in db_compounds:
            compound['source'] = database;
        compounds += db_compounds
    return compounds

# def getFindingsByIds(api, service, findingIds):
#     result = []
#     record_count = 0
#
#     query = {
#         "filter": {
#             "criteria": [
#                 [
#                     {
#                         "field": {
#                             "dataClassKey": "FINDING",
#                             "name": "id"
#                         },
#                         "primitiveType": "Integer",
#                         "comparisonOperator": "IN",
#                         "values": None
#                     },
#                 ]
#             ]
#         },
#         "selectedFields": [
#             {
#                 "dataClassKey": "FINDING",
#                 "names": [
#                     "id",
#                     "specimenOrgan", "specimenOrganCode", "specimenOrganVocabulary",
#                     "findingIdentifier", "finding", "findingCode", "findingVocabulary", "findingType",
#                     "severity", "observation", "frequency",
#                     "dose", "doseUnit",
#                     "timepoint", "timepointUnit",
#                     "treatmentRelated",
#                     "compoundId",
#                     "studyId",
#                     "createdDate", "modifiedDate", "sex"
#                 ]
#             }
#         ],
#         "offset": 0,
#         "limit": 500
#     }
#
#     for offset in range(0, len(findingIds), 500):
#         query['filter']['criteria'][0][0]['values'] = [{'value': findingId} for findingId in findingIds[offset:offset+500]]
#         r = requests.post(service.endpoint + 'query', verify=False, headers={"Authorization": f"Bearer {api.get_token()}"}, json=query, timeout=None)
#
#         if r.status_code == 200:
#             response = json.loads(r.text)
#             for record in response['resultData']['data']:
#                 record['FINDING']['source'] = response['origin']
#                 result.append(record['FINDING'])
#         elif r.status_code == 401:
#             api.reconnect()
#             continue
#
#     return result

def getSoc(socs, finding):
    if socs is not None:
        for soc in socs:
            if soc['conceptCode'] == finding:
                if 'mapping' in soc and len(soc['mapping']) > 0:
                    return soc['mapping'][0]['conceptName']
    return None

