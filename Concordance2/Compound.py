import json


class Compound:
    def __init__(self, database=None, inchi_group=None):
        self.__inchi_group = inchi_group
        self.__names = []
        self.__inchi_keys = []
        self.__clinical_count = 0
        self.__preclinical_count = 0
        self.__preclinical_findings = {}
        self.__preclinical_codes = None
        self.__clinical_findings = {}
        self.__clinical_codes = None
        self.__clinical_mapped_codes = None
        self.__preclinical_mapped_codes = None
        self.__database = database

    def name(self, name):
        if name is not None:
            self.__names.append(name)

    def inchi_group(self, inchi_group=None):
        if inchi_group is not None:
            self.__inchi_group = inchi_group
        return self.__inchi_group

    def get_by_inchi_group(self, inchi_group):
        cursor = self.__database.cursor(prepared=True)
        try:
            cursor.execute(f'SELECT inchi_group, inchi_keys, names, clinical_count, preclinical_count FROM drugs WHERE inchi_group = "{inchi_group}"')
            row = cursor.fetchone()
            if row is not None:
                self.__inchi_group = row[0]
                self.__inchi_keys = row[1].split(',')
                self.__names = row[2].split(',')
                self.__clinical_count = row[3]
                self.__preclinical_count = row[4]
                cursor.execute(f'SELECT finding_code, distance, clinical FROM findings WHERE inchi_group = "{inchi_group}"')
                self.__clinical_mapped_codes = {}
                self.__preclinical_mapped_codes = {}
                for row in cursor.fetchall():
                    clinical = row[2] == 1
                    if clinical:
                        self.__clinical_mapped_codes[row[0]] = row[1]
                    else:
                        self.__preclinical_mapped_codes[row[0]] = row[1]

            cursor.close()
        except:
            print('error')

    def clinical_count(self):
        self.__clinical_count += 1

    def preclinical_count(self):
        self.__preclinical_count += 1

    def has_preclinical_and_clinical(self):
        return len(self.__preclinical_findings) > 0 and len(self.__clinical_findings) > 0

    def preclinical_findings(self, database, findings=None):
        if findings is not None:
            if database not in self.__preclinical_findings:
                self.__preclinical_findings[database] = []
            self.__preclinical_findings[database].extend(findings)
        return self.__preclinical_findings

    def clinical_findings(self, database, findings=None):
        if findings is not None:
            if database not in self.__clinical_findings:
                self.__clinical_findings[database] = []
            self.__clinical_findings[database].extend(findings)
        return self.__clinical_findings[database]

    def clinical_codes(self, api):
        if self.__clinical_codes is None:
            self.__clinical_codes = self.__convert_from_finding_to_code(api, self.__clinical_findings, True)
        return self.__clinical_codes

    def preclinical_codes(self, api):
        if self.__preclinical_codes is None:
            self.__preclinical_codes = self.__convert_from_finding_to_code(api, self.__preclinical_findings, False)
        return self.__preclinical_codes

    def preclinical_mapped_codes(self, mapper, all_clinical_codes):
        if self.__preclinical_mapped_codes is None:
            mappedCodes = {code: distance for (code, distance) in mapper.mapPreclinicalToClinical(self.__preclinical_codes, all_clinical_codes).items() if distance is not None}
            self.__preclinical_mapped_codes = mappedCodes
        return self.__preclinical_mapped_codes.keys()

    def clinical_mapped_codes(self, mapper, all_preclinical_codes):
        if self.__clinical_mapped_codes is None:
            mappedCodes = {code: distance for (code, distance) in mapper.mapClinicalToPreclinical(self.__clinical_codes, all_preclinical_codes).items() if distance is not None}
            self.__clinical_mapped_codes = mappedCodes
        return self.__clinical_mapped_codes.keys()

    def __convert_from_finding_to_code(self, api, finding_ids, is_clinical):
        codes = []
        for db in finding_ids:
            for record in [item['FINDING'] for item in self.__primitive_adapter(api, db).getAllFindingByIds(finding_ids[db])]:
                if 'finding' in record and record['finding'] != 'No abnormalities detected' and record['finding'] != 'Nothing abnormal detected' and \
                        record['finding'] != 'Microscopic comment' and record['finding'] != 'Not examined/not present' and record['dose'] != 0:

                    if is_clinical is False:
                        specimenOrganCodes = record['specimenOrganCode'] if 'specimenOrganCode' in record and record['specimenOrganCode'] is not None else 'None'
                        for specimenOrganCode in specimenOrganCodes.split(','):
                            finding_code = specimenOrganCode + '/' + record['findingCode']
                            if finding_code not in codes:
                                codes.append(finding_code)
                    else:
                        codes.append(record['findingCode'])
        return codes

    def inchi_key(self, inchi_key=None):
        if inchi_key is not None:
            if inchi_key not in self.__inchi_keys:
                self.__inchi_keys.append(inchi_key)
        else:
            return self.__inchi_keys

    # check if the compound has both clinical codes and preclinical codes attached
    def is_valid(self, api, mapper, all_clinical_codes, all_preclinical_codes):
        preclinical_count = sum([len(self.__preclinical_findings[db]) for db in self.__preclinical_findings])
        clinical_count = sum([len(self.__clinical_findings[db]) for db in self.__clinical_findings])
        if preclinical_count > 0 and clinical_count > 0:
            if len(self.clinical_codes(api)) > 0 and len(self.preclinical_codes(api)) > 0:
                # check if has clinical mapped codes and preclinical mapped codes attached
                preclinical_mapped_codes = self.preclinical_mapped_codes(mapper, all_clinical_codes)
                clinical_mapped_codes = self.clinical_mapped_codes(mapper, all_preclinical_codes)
                return len(clinical_mapped_codes) > 0 and len(preclinical_mapped_codes) > 0
        else:
            return False

    def __primitive_adapter(self, api, db):
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

    def store_drug_info(self, db):
        cursor = db.cursor(prepared=True)
        cursor.execute('INSERT INTO drugs (inchi_group, inchi_keys, names, nr_inchi_keys, clinical_count, preclinical_count) VALUES(?, ?, ?, ?, ?, ?)', (self.__inchi_group, ','.join(self.__inchi_keys), ','.join(self.__names), len(self.__inchi_keys), self.__clinical_count, self.__preclinical_count))
        if self.__clinical_findings is not None:
            for database in self.__clinical_findings:
                cursor.executemany('INSERT INTO finding_ids (inchi_group, database, finding_id) VALUES(?, ?, ?)',[(self.__inchi_group, database, finding_id) for finding_id in self.__clinical_findings[database]])
        if self.__preclinical_findings is not None:
            for database in self.__preclinical_findings:
                cursor.executemany('INSERT INTO finding_ids (inchi_group, database, finding_id) VALUES(?, ?, ?)',[(self.__inchi_group, database, finding_id) for finding_id in self.__preclinical_findings[database]])
        db.commit()
        cursor.close()

    def store(self, db):
        cursor = db.cursor(prepared=True)
        cursor.execute('INSERT INTO drugs (inchi_group, inchi_keys, names, nr_inchi_keys, clinical_count, preclinical_count) VALUES(?, ?, ?, ?, ?, ?)', (self.__inchi_group, ','.join(self.__inchi_keys), ','.join(self.__names), len(self.__inchi_keys), self.__clinical_count, self.__preclinical_count))
        cursor.executemany('INSERT INTO findings (inchi_group, finding_code, distance, clinical) VALUES(?, ?, ?, ?)', [(self.__inchi_group, finding_code, self.__clinical_mapped_codes[finding_code], True) for finding_code in self.__clinical_mapped_codes])
        cursor.executemany('INSERT INTO findings (inchi_group, finding_code, distance, clinical) VALUES(?, ?, ?, ?)', [(self.__inchi_group, finding_code, self.__preclinical_mapped_codes[finding_code], False) for finding_code in self.__preclinical_mapped_codes])
        db.commit()
        cursor.close()

    def json_dump_obj(self) -> dict:
        return {
            '_classname_': self.__class__.__name__,
            '__inchi_group': self.__inchi_group,
            '__inchi_keys': self.__inchi_keys,
            '__names': self.__names,
            '__preclininical_count': self.__preclinical_count,
            '__preclininical_findings': self.__preclinical_findings,
            '__preclinical_mapped_codes': self.__preclinical_mapped_codes,
            '__clininical_count': self.__clinical_count,
            '__clininical_findings': self.__clinical_findings,
            '__clinical_mapped_codes': self.__clinical_mapped_codes,
        }

    def __str__(self):
        return json.dumps(self, default=Compound.json_dump_obj, indent=4)

