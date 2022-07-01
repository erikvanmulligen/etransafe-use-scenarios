import json
import os


def getClinicalDatabases(api):
    return {
        'ClinicalTrials': api.ClinicalTrials(),
        'Medline': api.Medline(),
        'Faers': api.Faers(),
        'DailyMed': api.DailyMed()
    }


def getPreclinicalDatabases(api):
    return {
        'eToxSys': api.eToxSys()
    }


def getPrimitiveAdapter(api, db):
    if db == 'eToxSys':
        return api.eToxSys()
    elif db == 'ClinicalTrials':
        return api.ClinicalTrials()
    elif db == 'Medline':
        return api.Medline()
    elif db == 'Faers':
        return api.Faers()
    elif db == 'DailyMed':
        return api.DailyMed()
    else:
        return None


def make_dict(record, attributes):
    result = {}
    for a in range(0, len(attributes)):
        result[attributes[a]] = record[a]
    return result


# retrieve the mappings for a particular finding_code
def get_mappings(db, finding_code, table):
    attributes = ['findingIdentifier', 'specimenOrgan', 'specimenOrganCode', 'specimenOrganVocabulary', 'finding',
                  'findingCode', 'findingVocabulary', 'findingType', 'mapped', 'SOC']
    cursor = db.cursor()
    cursor.execute(f'SELECT DISTINCT {",".join(attributes)} FROM {table} where findingCode = "{finding_code["findingCode"]}" AND specimenOrganCode = "{finding_code["specimenOrganCode"]}"')
    return [make_dict(r, attributes) for r in cursor.fetchall()]


def getPTDrugFindings(db, drugInfo, databases, table):
    fids = []
    for database in databases:
        if database in drugInfo and drugInfo[database] is not None:
            fids += drugInfo[database]
    unique_fids = set(fids)

    if len(fids) > 0:
        cursor = db.cursor()
        cursor.execute(f'SELECT DISTINCT PTCode FROM {table} where id in ({",".join([str(fid) for fid in unique_fids])})')
        return [r[0] for r in cursor.fetchall()]
    else:
        return []


def getAllDrugFindings(db, drugInfo, databases, table):
    fids = []
    for database in databases:
        if database in drugInfo and drugInfo[database] is not None:
            fids += drugInfo[database]

    if len(fids) > 0:
        cursor = db.cursor()
        cursor.execute(f'SELECT PTCode FROM {table} where id in ({",".join([str(fid) for fid in fids])})')
        return [r[0] for r in cursor.fetchall()]
    else:
        return []


def getSocDrugFindings(db, drugInfo, databases, table):
    fids = []
    for database in databases:
        if database in drugInfo and drugInfo[database] is not None:
            fids += drugInfo[database]

    if len(fids) > 0:
        cursor = db.cursor()
        cursor.execute(f'SELECT distinct SOC FROM {table} WHERE mapped > -1 AND id IN ({",".join([str(fid) for fid in fids])})')
        return [r[0] for r in cursor.fetchall()]
    else:
        return []


def getAllPTFindings(db, table):
    cursor = db.cursor()
    cursor.execute(f'SELECT distinct PTCode FROM {table}')
    return [r[0] for r in cursor.fetchall()]


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
        drugs = getDrugsMapping(api, getClinicalDatabases(), getPreclinicalDatabases())
    else:
        if os.path.isfile(filename):
            with open(filename, 'r') as drug_file:
                drugs = json.loads(drug_file.read())
        else:
            drugs = getDrugsMapping(api, getClinicalDatabases(), getPreclinicalDatabases())
            with open(filename, 'w') as drug_file:
                drug_file.write(json.dumps(drugs))
    return drugs

def normalizePreclinicalFields(records):
    return [{'findingCode': r[0], 'specimenOrganCode': r[1]} for r in records]

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def intersection_dicts(dict1, dict2):
    keys = intersection(list(dict1.keys()), list(dict2.keys()))
    return {key: dict1[key] for key in keys}

def getMedDRA_PTs(db, tables):
    result = []
    cursor = db.cursor()
    for table in tables:
        cursor.execute(f'SELECT distinct PTCode FROM {table}')
        result += [pt[0] for pt in cursor.fetchall()]
    return list(set(result))

def getAllPreClinicalClinicalPTs(db, tables):
    result = None
    cursor = db.cursor()
    for table in tables:
        cursor.execute(f'SELECT distinct PTCode FROM {table}')
        records = [pt[0] for pt in cursor.fetchall()]
        result = intersection(result, records) if result is not None else records
    return result

# method to retrieve from the databases a dictionary with the MedDRA preferred term as key and the distance as value.
def getAllPreclinicalClinicalDistances(db, tables):
    result = None
    cursor = db.cursor()
    for table in tables:
        cursor.execute(f'SELECT PTCode, min(distance) FROM {table} group by PTCode')
        records = {pt[0]: pt[1] for pt in cursor.fetchall()}
        result = intersection_dicts(result, records) if result is not None else records
    return result

def getName(meddra, code, type):
    if type == 'pt':
        return meddra.getPtName(code)
    elif type == 'hlt':
        return meddra.getHltName(code)
    elif type == 'soc':
        return meddra.getSocName(code)
    return None

def getSocs(db, tables):
    result = []
    cursor = db.cursor()
    for table in tables:
        cursor.execute("SELECT distinct SOC FROM " + table)
        result += [soc[0] for soc in cursor.fetchall()]
    return list(set(result))


def getDrugsMapping(api: object, ClinicalDatabases: object, PreclinicalDatabases: object) -> object:
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


def getDrugsMapping2(api, ClinicalDatabases, PreclinicalDatabases):
    result = {}
    clinicalCompounds = getCompounds(api, ClinicalDatabases)
    preclinicalCompounds = getCompounds(api, PreclinicalDatabases)

    for preclinicalCompound in preclinicalCompounds:
        inchiKey = preclinicalCompound['inchiKey'] if 'inchiKey' in preclinicalCompound else None
        if 'smiles' in preclinicalCompound and preclinicalCompound['smiles'] is not None:
            response = api.ChemistryService().paStandardize(preclinicalCompound['smiles'], 'preclinical')
            if response is not None and type(response) == tuple:
                inchiKey, smiles = response
        preclinicalCompound['standardInchiKey'] = inchiKey

    for clinicalCompound in clinicalCompounds:
        inchiKey = clinicalCompound['inchiKey'] if 'inchiKey' in clinicalCompound else None
        if 'name' in clinicalCompound and clinicalCompound['name'] is not None:
            response = api.ChemistryService().paStandardize(clinicalCompound['name'], 'clinical')
            if response is not None and type(response) == tuple:
                inchiKey, smiles = response
        clinicalCompound['standardInchiKey'] = inchiKey

    print(f'matching {len(clinicalCompounds)} clinical compounds with {len(preclinicalCompounds)} compounds')

    # iterate over the clinical and preclinical compounds and match them om inchiKey
    for clinicalCompound in clinicalCompounds:
        for preclinicalCompound in preclinicalCompounds:
            if ((clinicalCompound['inchiKey'] is not None) and clinicalCompound['inchiKey'] == preclinicalCompound['inchiKey']) or \
                    ((clinicalCompound['standardInchiKey'] is not None) and clinicalCompound['standardInchiKey'] == preclinicalCompound['standardInchiKey']) or \
                    (clinicalCompound['name'] is not None and preclinicalCompound['name'] is not None and clinicalCompound['name'].lower() == preclinicalCompound['name'].lower()):
                ik = clinicalCompound['inchiKey']
                if ik is not None:
                    if ik not in result:
                        result[ik] = {
                            'inchiKey': ik,
                            'clinicalName': clinicalCompound['name'],
                            'preclinicalName': preclinicalCompound['name']
                        }
                        result[ik][preclinicalCompound['source']] = preclinicalCompound['findingIds']
                    result[ik][clinicalCompound['source']] = clinicalCompound['findingIds']

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
