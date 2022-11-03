import math


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

    def mapPreclinicalToClinical(self, finding_ids, all_clinical_codes):
        result = {}
        for key in finding_ids:
            map_list = []
            if key not in self.cacheToClinical:
                organ_id, finding_id = key.split('/')
                mappings = self.api.SemanticService().mapToClinical(finding_id, organ_id)

                if mappings is not None:
                    map_list = []
                    for item in mappings:
                        # only include mappings if the organ matches
                        if item['distance'] >= 0:
                            for concept in item['concepts']:
                                if concept['conceptCode'] in all_clinical_codes:
                                    map_list += [{concept['conceptCode']: item['distance']}]

                    # fallback: if no mapping is found include all mappings
                    if len(map_list) == 0:
                        for item in mappings:
                            # only include mappings if the organ matches
                            if item['distance'] >= 0:
                                for concept in item['concepts']:
                                    map_list += [{concept['conceptCode']: item['distance']}]
                    else:
                        print(f'was able to reduce the mappings from {len(mappings)} to {len(map_list)}')
                    self.cacheToClinical[key] = map_list
                else:
                    self.cacheToClinical[key] = None

            if self.cacheToClinical[key] is not None:
                for finding_codes in self.cacheToClinical[key]:
                    for finding_code in finding_codes:
                        result[finding_code] = finding_codes[finding_code]
        return result

    def mapClinicalToPreclinical(self, finding_ids, all_preclinical_codes):
        result = {}
        for key in finding_ids:
            if key not in self.cacheToPreclinical:
                mappings = self.api.SemanticService().mapToPreclinical(key)
                map_list = []
                if mappings is not None:
                    if item['distance'] >= 0:
                        for concept in item['concepts']:
                            if concept['conceptCode'] in all_preclinical_codes:
                                map_list += [{concept['conceptCode']: item['distance']}]

                        # fallback: if no mapping is found include all mappings
                        if len(map_list) == 0:
                            for item in mappings:
                                # only include mappings if the organ matches
                                if item['distance'] >= 0:
                                    for concept in item['concepts']:
                                        map_list += [{concept['conceptCode']: item['distance']}]
                        self.cacheToPreclinical[key] = map_list
                else:
                    self.cacheToPreclinical[key] = None
            result[key] = self.cacheToPreclinical[key]
        return result

    @staticmethod
    def __min(values):
        min_positive_value = min([value for value in values if value >= 0], default=None)
        max_negative_value = max([value for value in values if value < 0], default=None)
        return min_positive_value if min_positive_value is not None else (max_negative_value if max_negative_value is not None else -1)
