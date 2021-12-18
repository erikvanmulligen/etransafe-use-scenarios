
class Mapper:
    cacheToClinical = None
    cacheToPreclinical = None
    api = None

    def __init__(self, api):
        self.clear()
        self.api = api

    def clear(self):
        self.cacheToClinical = {}
        self.cacheToPreclinical = {}

    def codesToFindings(self, codes):
        return [{'code': code.split('/')[0], 'organCode': code.split('/')[1]} for code in codes]

    def mapToClinical(self, findings):
        result = {}
        for finding in findings:
            map_list = []
            key = self.getKey(finding)
            if key not in self.cacheToClinical:
                mappings = self.api.SemanticService().mapToClinical(finding['code'], finding['organCode'])
                if mappings is not None:
                    for item in mappings:
                        map_list += [{'code': concept['conceptCode']} for concept in item['concepts']]
                    self.cacheToClinical[key] = map_list
                else:
                    self.cacheToClinical[key] = []
            result[key] = self.cacheToClinical[key]
        return result

    def getKey(self, finding):
        if 'findingCode' in finding:
            try:
                specimenOrganCode = finding['specimenOrganCode'] if 'specimenOrganCode' in finding and finding['specimenOrganCode'] is not None and len(finding['specimenOrganCode']) > 0 else None
                return finding['findingCode'] + ('/' + specimenOrganCode if specimenOrganCode is not None else '')
            except Exception as e:
                print(f'error2:{e}')
        else:
            try:
                specimenOrganCode = finding[1] if finding[1] is not None and len(finding[1]) > 0 else None
                return finding[0] + ('/' + specimenOrganCode if specimenOrganCode is not None else '')
            except Exception as e:
                print(f'error:{e}')


    def mapToPreclinical(self, findings):
        result = {}
        for finding in findings:
            map_list = []
            key = self.getKey(finding)
            if key not in self.cacheToPreclinical:
                for item in self.api.SemanticService().mapToPreclinical(finding['code']):
                    map_list += [{'findingCode': concept['conceptCode'], 'specimenOrganCode': concept['organCode']} for concept in item['concepts']]
                self.cacheToPreclinical[key] = map_list
            result[key] = self.cacheToPreclinical[key]
        return result