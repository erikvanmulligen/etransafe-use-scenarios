import json

import requests

from knowledgehub.api import KnowledgeHubAPI
from Concordance3.settings import settings
from dataclass import DataClass
from datasource import DataSource, DataSources


def main():
    api = KnowledgeHubAPI(server=settings['kh']['server'], client_secret=settings['kh']['client_secret'])
    if api.login(settings['kh']['user'], settings['kh']['password']):
        compounds = api.PreclinicalDb().getAllCompounds()
        for compound in compounds:
            for studyId in compound['studyIds']:
                findings = external_additional_property(api.get_token(), api.get_base(), studyId, 'MI', DataClass.STUDY, DataSources.PRECLINICAL)
                print(f'{len(findings)} findings found')


def external_additional_property(token, url, idx: int, property_name: str, data_class: DataClass, data_source: DataSource):
    url = f'{url}{data_source.path}/data/{data_class.key()}/{idx}/additionalproperties'
    batch_size = 1000
    query = {
        "propertyName": property_name,
        "resultType": "TREE",
        "offset": 0,
        "limit": batch_size
    }
    total = 1
    result = []
    while total > query['offset']:
        r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json=query)
        if r.status_code == 200:
            response = json.loads(r.text)
            result.extend(response['data'])
            total = response['total']
            query['offset'] += batch_size
        else:
            print(f"Cannot retrieve compoundIds from {url}: {r.status_code}")
            break
    return result


if __name__ == '__main__':
    main()